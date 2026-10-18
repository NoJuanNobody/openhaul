"""
Synthetic Telemetry Generator for OpenHaul.
Simulates two distinct operational regimes:
1. Normal Metro Day (predictable traffic, balanced supply & demand, high cold-chain compliance)
2. Hurricane Katrina / FEMA Disaster Surge (severe grid damage, road closures, massive medical & supply demand, priority triage)
"""

from __future__ import annotations
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
from ..graph_loop.matcher import Coordinate, DeliveryRequest, Driver, PriorityTier


class SimulationScenario(str, Enum):
    NORMAL_METRO = "normal_metro"
    FEMA_DISASTER_SURGE = "fema_disaster_surge"


class TelemetryGenerator:
    """
    Generates synthetic drivers, telemetry pings, and delivery requests.
    Centered on New Orleans Metro (29.9511 N, 90.0715 W) to reflect coastal disaster resilience.
    """

    def __init__(self, base_lat: float = 29.9511, base_lng: float = -90.0715, seed: int = 42):
        self.base_lat = base_lat
        self.base_lng = base_lng
        self.rng = random.Random(seed)

    def _random_coordinate(self, radius_km: float = 15.0) -> Coordinate:
        # Approx 1 deg lat ~= 111 km, 1 deg lng ~= 96 km at lat 30
        lat_offset = (self.rng.uniform(-radius_km, radius_km)) / 111.0
        lng_offset = (self.rng.uniform(-radius_km, radius_km)) / 96.0
        return Coordinate(
            lat=round(self.base_lat + lat_offset, 5),
            lng=round(self.base_lng + lng_offset, 5),
        )

    def generate_fleet(self, count: int, cold_chain_ratio: float = 0.35) -> List[Driver]:
        drivers: List[Driver] = []
        for i in range(count):
            loc = self._random_coordinate(radius_km=20.0)
            weight = self.rng.choice([500.0, 750.0, 1000.0])
            volume = self.rng.choice([20.0, 35.0, 50.0, 60.0])
            is_cold = self.rng.random() < cold_chain_ratio

            drivers.append(
                Driver(
                    driver_id=f"drv_{i:04d}",
                    max_weight_lbs=weight,
                    available_weight_lbs=weight,
                    max_volume_cuft=volume,
                    available_volume_cuft=volume,
                    cold_chain_capable=is_cold,
                    current_location=loc,
                    current_h3_cell=f"884459424{i%16:x}fffff",
                    is_online=True,
                )
            )
        return drivers

    def generate_requests(
        self,
        count: int,
        scenario: SimulationScenario = SimulationScenario.NORMAL_METRO,
    ) -> List[DeliveryRequest]:
        requests: List[DeliveryRequest] = []
        now = time.time()

        for i in range(count):
            pickup = self._random_coordinate(radius_km=15.0)
            dropoff = self._random_coordinate(radius_km=25.0)

            if scenario == SimulationScenario.FEMA_DISASTER_SURGE:
                # 60% FEMA/medical critical priority, higher weights, emergency supplies
                priority_roll = self.rng.random()
                if priority_roll < 0.45:
                    priority = PriorityTier.DISASTER_TRIAGE_FEMA
                    payout = self.rng.uniform(150.0, 350.0)
                    requires_cold = self.rng.random() < 0.5  # Vaccines, insulin, blood
                elif priority_roll < 0.75:
                    priority = PriorityTier.MEDICAL_CRITICAL
                    payout = self.rng.uniform(100.0, 220.0)
                    requires_cold = True
                else:
                    priority = PriorityTier.EXPEDITED
                    payout = self.rng.uniform(70.0, 140.0)
                    requires_cold = False

                weight = self.rng.uniform(50.0, 600.0)
                volume = self.rng.uniform(5.0, 35.0)
            else:
                # Normal Metro distribution
                priority_roll = self.rng.random()
                if priority_roll < 0.70:
                    priority = PriorityTier.STANDARD
                    payout = self.rng.uniform(25.0, 60.0)
                    requires_cold = False
                elif priority_roll < 0.90:
                    priority = PriorityTier.EXPEDITED
                    payout = self.rng.uniform(50.0, 90.0)
                    requires_cold = False
                else:
                    priority = PriorityTier.MEDICAL_CRITICAL
                    payout = self.rng.uniform(80.0, 150.0)
                    requires_cold = True

                weight = self.rng.uniform(10.0, 300.0)
                volume = self.rng.uniform(2.0, 20.0)

            requests.append(
                DeliveryRequest(
                    request_id=f"req_{scenario.value[:3]}_{i:04d}",
                    pickup_location=pickup,
                    pickup_h3_cell=f"884459424{i%16:x}fffff",
                    dropoff_location=dropoff,
                    dropoff_h3_cell=f"884459425{i%16:x}fffff",
                    weight_lbs=round(weight, 1),
                    volume_cuft=round(volume, 1),
                    requires_cold_chain=requires_cold,
                    priority=priority,
                    deadline_epoch_s=now + self.rng.uniform(1800, 7200),
                    payout_usd=round(payout, 2),
                    min_temp_celsius=2.0 if requires_cold else None,
                    max_temp_celsius=8.0 if requires_cold else None,
                )
            )
        return requests
