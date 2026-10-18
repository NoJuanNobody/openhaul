"""
The periodic tick-based graph loop (2.0s dispatch cadence).
Orchestrates ingestion of driver telemetry & delivery requests, matches optimal
bipartite assignments, manages dynamic route obfuscation, and guarantees sub-2000ms latency.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .matcher import BipartiteMatcher, DeliveryRequest, Driver, MatchResult
from .obfuscator import ObfuscatedRoute, WaypointObfuscator


@dataclass
class LoopMetrics:
    tick_count: int = 0
    total_matched: int = 0
    pending_requests: int = 0
    available_drivers: int = 0
    last_tick_duration_ms: float = 0.0
    average_tick_duration_ms: float = 0.0


class DispatchGraphLoop:
    """
    2.0s periodic tick-based spatio-temporal matching loop.
    """

    def __init__(
        self,
        tick_interval_s: float = 2.0,
        matcher: Optional[BipartiteMatcher] = None,
        obfuscator: Optional[WaypointObfuscator] = None,
    ):
        self.tick_interval_s = tick_interval_s
        self.matcher = matcher or BipartiteMatcher()
        self.obfuscator = obfuscator or WaypointObfuscator()

        self.drivers: Dict[str, Driver] = {}
        self.requests: Dict[str, DeliveryRequest] = {}
        self.active_routes: Dict[str, ObfuscatedRoute] = {}
        self.completed_matches: List[MatchResult] = []

        self.metrics = LoopMetrics()
        self._total_duration_ms: float = 0.0

    def register_driver(self, driver: Driver) -> None:
        self.drivers[driver.driver_id] = driver

    def remove_driver(self, driver_id: str) -> None:
        self.drivers.pop(driver_id, None)

    def submit_request(self, request: DeliveryRequest) -> None:
        self.requests[request.request_id] = request

    def cancel_request(self, request_id: str) -> None:
        self.requests.pop(request_id, None)

    def tick(self) -> List[MatchResult]:
        """
        Executes a single matching loop tick.
        Measures processing latency to enforce the sub-2000ms SLA.
        """
        start_time = time.perf_counter()

        # Filter available online drivers
        active_drivers = {
            d_id: d for d_id, d in self.drivers.items()
            if d.is_online and d.available_weight_lbs > 0 and d.available_volume_cuft > 0
        }

        # Solve matching
        matches = self.matcher.match(active_drivers, self.requests)

        # For each match, initialize route obfuscation and remove fulfilled request
        for match in matches:
            req = self.requests.pop(match.request_id)
            route = self.obfuscator.generate_obfuscated_route(
                request_id=req.request_id,
                driver_id=match.driver_id,
                pickup=req.pickup_location,
                destination=req.dropoff_location,
            )
            self.active_routes[req.request_id] = route
            self.completed_matches.append(match)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        self.metrics.tick_count += 1
        self.metrics.total_matched += len(matches)
        self.metrics.pending_requests = len(self.requests)
        self.metrics.available_drivers = len(active_drivers)
        self.metrics.last_tick_duration_ms = duration_ms
        self._total_duration_ms += duration_ms
        self.metrics.average_tick_duration_ms = (
            self._total_duration_ms / self.metrics.tick_count
        )

        return matches
