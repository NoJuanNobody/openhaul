"""Unit and integration tests for chaos_sim module."""

import unittest
from python.chaos_sim.generator import SimulationScenario, TelemetryGenerator
from python.chaos_sim.runner import (
    ChaosRunner,
    cold_chain_breach_detected,
    is_replayed_scan,
)


class TestColdChainDetector(unittest.TestCase):
    def test_three_consecutive_breaches_detected(self):
        self.assertTrue(cold_chain_breach_detected([4.0, 9.5, 10.1, 11.0, 5.0]))

    def test_breaches_broken_by_in_range_readings_not_detected(self):
        self.assertFalse(cold_chain_breach_detected([9.0, 9.5, 5.0, 9.1, 9.2, 4.0, 10.0]))

    def test_entirely_in_range_not_detected(self):
        self.assertFalse(cold_chain_breach_detected([2.0, 5.0, 8.0, 3.5, 7.9]))


class TestRfidReplayDetector(unittest.TestCase):
    def test_replayed_scan_is_flagged(self):
        seen: set = set()
        self.assertFalse(is_replayed_scan(seen, "abc"))
        self.assertTrue(is_replayed_scan(seen, "abc"))

    def test_fresh_scan_is_not_flagged(self):
        seen = {"abc"}
        self.assertFalse(is_replayed_scan(seen, "def"))
        self.assertIn("def", seen)


class TestChaosSim(unittest.TestCase):
    def setUp(self):
        self.runner = ChaosRunner(seed=1337)
        self.generator = TelemetryGenerator(seed=42)

    def test_generator_fleet_and_requests(self):
        fleet = self.generator.generate_fleet(30)
        self.assertEqual(len(fleet), 30)
        for d in fleet:
            self.assertGreaterEqual(d.max_weight_lbs, 500.0)
            self.assertLessEqual(d.max_weight_lbs, 1000.0)
            self.assertGreaterEqual(d.max_volume_cuft, 15.0)
            self.assertLessEqual(d.max_volume_cuft, 60.0)

        requests = self.generator.generate_requests(20, SimulationScenario.FEMA_DISASTER_SURGE)
        self.assertEqual(len(requests), 20)

    def test_normal_metro_baseline_benchmark(self):
        report = self.runner.run_normal_metro_baseline(fleet_size=80, request_count=60)
        self.assertTrue(report.passed_all_invariants)
        self.assertEqual(report.capacity_overrun_violations, 0)
        self.assertEqual(report.double_dispatch_violations, 0)
        self.assertLess(report.avg_loop_tick_latency_ms, 2000.0)
        self.assertGreaterEqual(report.match_rate_percent, 95.0)

    def test_hurricane_katrina_chaos_resilience(self):
        report = self.runner.run_hurricane_katrina_chaos(
            fleet_size=120, request_count=80, dropout_ratio=0.40
        )
        self.assertTrue(report.passed_all_invariants)
        self.assertEqual(report.capacity_overrun_violations, 0)
        self.assertEqual(report.double_dispatch_violations, 0)
        self.assertTrue(report.rfid_replay_attack_rejected)
        self.assertTrue(report.cold_chain_excursion_caught)
        self.assertGreaterEqual(report.fema_critical_match_rate_percent, 70.0)
        self.assertLess(report.avg_loop_tick_latency_ms, 2000.0)


if __name__ == "__main__":
    unittest.main()
