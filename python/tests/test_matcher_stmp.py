"""Tests that the Python matcher delegates to the Rust stmp_match binary."""

import json
import subprocess
import unittest
from pathlib import Path

from python.graph_loop.matcher import (
    BipartiteMatcher,
    Coordinate,
    DeliveryRequest,
    Driver,
    PriorityTier,
    resolve_match_binary,
)

FIXTURE = Path(__file__).resolve().parents[2] / "crates" / "stmp-core" / "tests" / "fixtures" / "fema_vs_standard.json"

PICKUP = Coordinate(lat=29.9511, lng=-90.0715)
DROPOFF = Coordinate(lat=29.9800, lng=-90.0400)


class TestStmpMatchBinary(unittest.TestCase):
    def test_fema_request_preferred_over_standard(self):
        driver = Driver(
            driver_id="drv_001",
            max_weight_lbs=800.0,
            available_weight_lbs=800.0,
            max_volume_cuft=45.0,
            available_volume_cuft=45.0,
            cold_chain_capable=False,
            current_location=PICKUP,
            current_h3_cell="8844594245fffff",
        )

        def request(request_id: str, priority: PriorityTier) -> DeliveryRequest:
            return DeliveryRequest(
                request_id=request_id,
                pickup_location=PICKUP,
                pickup_h3_cell="8844594245fffff",
                dropoff_location=DROPOFF,
                dropoff_h3_cell="8844594247fffff",
                weight_lbs=100.0,
                volume_cuft=5.0,
                requires_cold_chain=False,
                priority=priority,
                deadline_epoch_s=1770000000,
                payout_usd=100.0,
            )

        requests = {
            "req_standard": request("req_standard", PriorityTier.STANDARD),
            "req_fema": request("req_fema", PriorityTier.DISASTER_TRIAGE_FEMA),
        }

        matches = BipartiteMatcher().match({"drv_001": driver}, requests)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].request_id, "req_fema")
        self.assertEqual(matches[0].driver_id, "drv_001")
        self.assertGreater(matches[0].welfare_score, 600.0)  # payout * 6.0 minus small terms

    def test_binary_runs_on_fixture_and_prefers_fema(self):
        binary = resolve_match_binary()
        proc = subprocess.run(
            [str(binary)],
            input=FIXTURE.read_text(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = json.loads(proc.stdout)
        self.assertEqual(len(output["matches"]), 1)
        self.assertEqual(output["matches"][0]["request_id"], "req_fema")

    def test_missing_binary_fails_loudly(self):
        with self.assertRaises(RuntimeError) as ctx:
            resolve_match_binary("/nonexistent/stmp_match")
        self.assertIn("cargo build --bin stmp_match", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
