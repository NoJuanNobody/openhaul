"""Unit and integration tests for chaos_sim module."""

import unittest
from python.chaos_sim.generator import SimulationScenario, TelemetryGenerator
from python.chaos_sim.runner import ChaosRunner


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
