"""
Bipartite welfare maximization solver matching drivers to delivery requests.
Accounts for deadhead transit time, capacity constraints, cold-chain compatibility,
and disaster triage priority tiers (Standard, Expedited, MedicalCritical, FEMA).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Set, Tuple


class PriorityTier(IntEnum):
    STANDARD = 1
    EXPEDITED = 2
    MEDICAL_CRITICAL = 3
    DISASTER_TRIAGE_FEMA = 4


@dataclass
class Coordinate:
    lat: float
    lng: float

    def distance_km(self, other: Coordinate) -> float:
        """Haversine distance in km."""
        r = 6371.0
        d_lat = math.radians(other.lat - self.lat)
        d_lng = math.radians(other.lng - self.lng)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(self.lat))
            * math.cos(math.radians(other.lat))
            * math.sin(d_lng / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        return r * c


@dataclass
class Driver:
    driver_id: str
    max_weight_lbs: float  # 500 - 1000 lbs
    available_weight_lbs: float
    max_volume_cuft: float  # 15 - 60 cu ft
    available_volume_cuft: float
    cold_chain_capable: bool
    current_location: Coordinate
    current_h3_cell: str
    is_online: bool = True
    planned_trajectory: List[Coordinate] = field(default_factory=list)

    def can_accommodate(self, request: DeliveryRequest) -> bool:
        if not self.is_online:
            return False
        if request.requires_cold_chain and not self.cold_chain_capable:
            return False
        if request.weight_lbs > self.available_weight_lbs:
            return False
        if request.volume_cuft > self.available_volume_cuft:
            return False
        return True

    def allocate(self, request: DeliveryRequest) -> bool:
        if not self.can_accommodate(request):
            return False
        self.available_weight_lbs -= request.weight_lbs
        self.available_volume_cuft -= request.volume_cuft
        return True


@dataclass
class DeliveryRequest:
    request_id: str
    pickup_location: Coordinate
    pickup_h3_cell: str
    dropoff_location: Coordinate
    dropoff_h3_cell: str
    weight_lbs: float
    volume_cuft: float
    requires_cold_chain: bool
    priority: PriorityTier
    deadline_epoch_s: float
    payout_usd: float
    min_temp_celsius: Optional[float] = None
    max_temp_celsius: Optional[float] = None


@dataclass
class MatchResult:
    driver_id: str
    request_id: str
    deadhead_km: float
    delivery_km: float
    welfare_score: float


class BipartiteMatcher:
    """
    Solves bipartite matching between drivers and delivery requests to maximize
    social and operational welfare.
    """

    def __init__(self, deadhead_weight: float = 0.85, max_deadhead_km: float = 40.0):
        self.deadhead_weight = deadhead_weight
        self.max_deadhead_km = max_deadhead_km

    def compute_edge_welfare(self, driver: Driver, request: DeliveryRequest) -> Optional[MatchResult]:
        if not driver.can_accommodate(request):
            return None

        deadhead = driver.current_location.distance_km(request.pickup_location)
        if deadhead > self.max_deadhead_km:
            return None

        delivery_dist = request.pickup_location.distance_km(request.dropoff_location)

        # Priority weights strongly prioritize life-safety / FEMA disaster cargo
        priority_multipliers = {
            PriorityTier.STANDARD: 1.0,
            PriorityTier.EXPEDITED: 1.6,
            PriorityTier.MEDICAL_CRITICAL: 3.0,
            PriorityTier.DISASTER_TRIAGE_FEMA: 6.0,
        }
        multiplier = priority_multipliers.get(request.priority, 1.0)

        # Objective: Maximize priority-weighted payout minus deadhead transit cost
        welfare = (request.payout_usd * multiplier) - (deadhead * self.deadhead_weight) + (delivery_dist * 0.15)

        return MatchResult(
            driver_id=driver.driver_id,
            request_id=request.request_id,
            deadhead_km=deadhead,
            delivery_km=delivery_dist,
            welfare_score=welfare,
        )

    def match(
        self,
        drivers: Dict[str, Driver],
        requests: Dict[str, DeliveryRequest],
    ) -> List[MatchResult]:
        """
        Executes maximum welfare matching with priority triage ordering.
        Returns non-conflicting assignments of driver -> request.
        """
        candidate_edges: List[MatchResult] = []

        for driver in drivers.values():
            for req in requests.values():
                res = self.compute_edge_welfare(driver, req)
                if res is not None:
                    candidate_edges.append(res)

        # Sort candidate edges by descending welfare score
        candidate_edges.sort(key=lambda edge: edge.welfare_score, reverse=True)

        assigned_drivers: Set[str] = set()
        assigned_requests: Set[str] = set()
        matches: List[MatchResult] = []

        for edge in candidate_edges:
            if edge.driver_id not in assigned_drivers and edge.request_id not in assigned_requests:
                driver = drivers[edge.driver_id]
                req = requests[edge.request_id]
                if driver.allocate(req):
                    assigned_drivers.add(edge.driver_id)
                    assigned_requests.add(edge.request_id)
                    matches.append(edge)

        return matches
