"""
Driver-to-request matching for the Python dispatch loop.

The matching rules (priority multipliers, deadhead cost, capacity feasibility,
greedy non-overlapping assignment) live only in the Rust crate `crates/stmp-core`.
This module serializes drivers and requests to JSON, runs the `stmp_match` binary,
and maps the result back onto the Python dataclasses. It contains no weighting logic.

Binary lookup:
  1. `OPENHAUL_STMP_MATCH_BIN` if set (must be an existing executable file).
  2. `<repo>/target/debug/stmp_match`, produced by `cargo build --bin stmp_match`.
A missing binary raises RuntimeError. There is no Python fallback.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, Union

BIN_ENV_VAR = "OPENHAUL_STMP_MATCH_BIN"
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIN_PATH = _REPO_ROOT / "target" / "debug" / "stmp_match"

# Python's H3 cells are 15-hex-digit res-8 strings; the Rust wire format needs the resolution.
H3_RESOLUTION = 8


class PriorityTier(IntEnum):
    STANDARD = 1
    EXPEDITED = 2
    MEDICAL_CRITICAL = 3
    DISASTER_TRIAGE_FEMA = 4


# Serde variant names of stmp_core::PriorityLevel.
_RUST_PRIORITY_NAMES = {
    PriorityTier.STANDARD: "Standard",
    PriorityTier.EXPEDITED: "Expedited",
    PriorityTier.MEDICAL_CRITICAL: "MedicalCritical",
    PriorityTier.DISASTER_TRIAGE_FEMA: "DisasterTriageFema",
}


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


def resolve_match_binary(path: Union[str, os.PathLike, None] = None) -> Path:
    """Returns the stmp_match path, or raises RuntimeError if it is not an executable file."""
    if path is None:
        override = os.environ.get(BIN_ENV_VAR)
        path = override if override else DEFAULT_BIN_PATH
    candidate = Path(path)
    if not (candidate.is_file() and os.access(candidate, os.X_OK)):
        raise RuntimeError(
            f"stmp_match binary not found or not executable at {candidate}. "
            "Build it from the repo root with `cargo build --bin stmp_match`, "
            f"or set {BIN_ENV_VAR} to its path."
        )
    return candidate


def _coord_to_wire(c: Coordinate) -> dict:
    return {"lat": c.lat, "lng": c.lng}


def _cell_to_wire(index_hex: str) -> dict:
    return {"index_hex": index_hex, "resolution": H3_RESOLUTION}


def _driver_to_wire(d: Driver) -> dict:
    return {
        "driver_id": d.driver_id,
        "max_weight_lbs": d.max_weight_lbs,
        "available_weight_lbs": d.available_weight_lbs,
        "max_volume_cuft": d.max_volume_cuft,
        "available_volume_cuft": d.available_volume_cuft,
        "cold_chain_capable": d.cold_chain_capable,
        "current_location": _coord_to_wire(d.current_location),
        "current_cell": _cell_to_wire(d.current_h3_cell),
        # The Rust matcher does not read trajectories; the wire field is kept empty.
        "planned_trajectory": [],
        "is_online": d.is_online,
    }


def _request_to_wire(r: DeliveryRequest) -> dict:
    return {
        "request_id": r.request_id,
        "pickup_location": _coord_to_wire(r.pickup_location),
        "pickup_cell": _cell_to_wire(r.pickup_h3_cell),
        "dropoff_location": _coord_to_wire(r.dropoff_location),
        "dropoff_cell": _cell_to_wire(r.dropoff_h3_cell),
        "weight_lbs": r.weight_lbs,
        "volume_cuft": r.volume_cuft,
        "requires_cold_chain": r.requires_cold_chain,
        "min_temp_celsius": r.min_temp_celsius,
        "max_temp_celsius": r.max_temp_celsius,
        "priority": _RUST_PRIORITY_NAMES[PriorityTier(r.priority)],
        "deadline_epoch_s": int(r.deadline_epoch_s),
        "payout_usd": r.payout_usd,
    }


class BipartiteMatcher:
    """
    Thin client for the Rust matcher. Each call to `match` runs `stmp_match` once
    with the current drivers and requests on stdin.
    """

    def __init__(self, binary_path: Union[str, os.PathLike, None] = None):
        self.binary_path = resolve_match_binary(binary_path)

    def match(
        self,
        drivers: Dict[str, Driver],
        requests: Dict[str, DeliveryRequest],
    ) -> List[MatchResult]:
        """
        Returns non-conflicting driver -> request assignments, highest welfare first.
        Matched drivers have their capacity decremented, as before.
        """
        if not drivers or not requests:
            return []

        payload = {
            "drivers": [_driver_to_wire(d) for d in drivers.values()],
            "requests": [_request_to_wire(r) for r in requests.values()],
        }
        proc = subprocess.run(
            [str(self.binary_path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"stmp_match exited with status {proc.returncode}: {proc.stderr.strip()}"
            )
        try:
            output = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"stmp_match produced invalid JSON: {exc}") from exc

        results: List[MatchResult] = []
        for edge in output["matches"]:
            driver = drivers[edge["driver_id"]]
            request = requests[edge["request_id"]]
            if not driver.allocate(request):
                raise RuntimeError(
                    f"stmp_match assigned {driver.driver_id} to {request.request_id}, "
                    "but the Python capacity check rejects it; the two sides disagree."
                )
            results.append(
                MatchResult(
                    driver_id=edge["driver_id"],
                    request_id=edge["request_id"],
                    deadhead_km=edge["deadhead_distance_km"],
                    delivery_km=edge["delivery_distance_km"],
                    welfare_score=edge["welfare_score"],
                )
            )
        return results
