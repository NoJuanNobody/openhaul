"""
Dynamic Waypoint Obfuscation Engine.
Withholds final delivery destination to protect sensitive/high-value cargo from hijacking,
and only progressively releases intermediate navigation checkpoints until the vehicle
enters the terminal H3 k-ring (within terminal radius, e.g., 500m).
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional
from .matcher import Coordinate


@dataclass
class ObfuscatedWaypoint:
    checkpoint_index: int
    coordinate: Coordinate
    h3_cell_approx: str
    is_terminal: bool
    checkpoint_token: str


@dataclass
class ObfuscatedRoute:
    request_id: str
    driver_id: str
    all_checkpoints: List[Coordinate]
    disclosed_index: int = 0
    terminal_k_ring_entered: bool = False
    terminal_destination: Coordinate = field(repr=False, default=None)  # type: ignore


class WaypointObfuscator:
    """
    Progressive waypoint disclosure service.
    """

    def __init__(self, terminal_threshold_km: float = 0.8, intermediate_step_km: float = 2.0):
        self.terminal_threshold_km = terminal_threshold_km
        self.intermediate_step_km = intermediate_step_km

    def generate_obfuscated_route(
        self,
        request_id: str,
        driver_id: str,
        pickup: Coordinate,
        destination: Coordinate,
    ) -> ObfuscatedRoute:
        """
        Synthesizes an intermediate checkpoint corridor between pickup and destination.
        Terminal destination is withheld from initial release.
        """
        total_dist = pickup.distance_km(destination)
        num_steps = max(2, int(total_dist / self.intermediate_step_km))

        checkpoints: List[Coordinate] = []
        for i in range(num_steps):
            ratio = i / float(num_steps)
            # Interpolated coordinate along path
            lat = pickup.lat + ratio * (destination.lat - pickup.lat)
            lng = pickup.lng + ratio * (destination.lng - pickup.lng)
            checkpoints.append(Coordinate(lat=round(lat, 5), lng=round(lng, 5)))

        return ObfuscatedRoute(
            request_id=request_id,
            driver_id=driver_id,
            all_checkpoints=checkpoints,
            disclosed_index=0,
            terminal_k_ring_entered=False,
            terminal_destination=destination,
        )

    def get_current_nav_instruction(
        self,
        route: ObfuscatedRoute,
        driver_current_location: Coordinate,
    ) -> ObfuscatedWaypoint:
        """
        Evaluates driver's current position against route checkpoints.
        If driver has reached the current waypoint, unlocks the next waypoint.
        Only unlocks the true final destination once within the terminal threshold.
        """
        dist_to_destination = driver_current_location.distance_km(route.terminal_destination)

        # Check if terminal k-ring reached
        if dist_to_destination <= self.terminal_threshold_km:
            route.terminal_k_ring_entered = True
            token = hashlib.sha256(
                f"{route.request_id}-terminal-{route.terminal_destination.lat}-{route.terminal_destination.lng}".encode()
            ).hexdigest()[:16]
            return ObfuscatedWaypoint(
                checkpoint_index=len(route.all_checkpoints),
                coordinate=route.terminal_destination,
                h3_cell_approx="8844594247fffff",
                is_terminal=True,
                checkpoint_token=token,
            )

        # Check progress along intermediate checkpoints
        curr_idx = route.disclosed_index
        if curr_idx < len(route.all_checkpoints):
            curr_target = route.all_checkpoints[curr_idx]
            dist_to_checkpoint = driver_current_location.distance_km(curr_target)
            if dist_to_checkpoint < 0.3 and curr_idx + 1 < len(route.all_checkpoints):
                route.disclosed_index += 1
                curr_idx = route.disclosed_index

        active_waypoint = route.all_checkpoints[min(curr_idx, len(route.all_checkpoints) - 1)]
        token = hashlib.sha256(
            f"{route.request_id}-step-{curr_idx}-{active_waypoint.lat}".encode()
        ).hexdigest()[:16]

        return ObfuscatedWaypoint(
            checkpoint_index=curr_idx,
            coordinate=active_waypoint,
            h3_cell_approx="8844594245fffff",
            is_terminal=False,
            checkpoint_token=token,
        )
