"""Unit and integration tests for graph_loop module."""

import unittest
from python.graph_loop.matcher import (
    BipartiteMatcher,
    Coordinate,
    DeliveryRequest,
    Driver,
    PriorityTier,
)
from python.graph_loop.obfuscator import WaypointObfuscator
from python.graph_loop.loop import DispatchGraphLoop


class TestGraphLoop(unittest.TestCase):
    def setUp(self):
        self.pickup = Coordinate(lat=29.9511, lng=-90.0715)
        self.dropoff = Coordinate(lat=29.9800, lng=-90.0400)
        self.matcher = BipartiteMatcher()
        self.obfuscator = WaypointObfuscator()

    def test_matcher_cold_chain_and_capacity_constraints(self):
        # Driver cannot do cold chain
        driver_dry = Driver(
            driver_id="drv_dry",
            max_weight_lbs=800.0,
            available_weight_lbs=800.0,
            max_volume_cuft=40.0,
            available_volume_cuft=40.0,
            cold_chain_capable=False,
            current_location=self.pickup,
            current_h3_cell="8844594245fffff",
        )

        # Driver with cold chain
        driver_reefer = Driver(
            driver_id="drv_reefer",
            max_weight_lbs=800.0,
            available_weight_lbs=800.0,
            max_volume_cuft=40.0,
            available_volume_cuft=40.0,
            cold_chain_capable=True,
            current_location=self.pickup,
            current_h3_cell="8844594245fffff",
        )

        cold_req = DeliveryRequest(
            request_id="req_vaccines",
            pickup_location=self.pickup,
            pickup_h3_cell="8844594245fffff",
            dropoff_location=self.dropoff,
            dropoff_h3_cell="8844594247fffff",
            weight_lbs=120.0,
            volume_cuft=10.0,
            requires_cold_chain=True,
            priority=PriorityTier.MEDICAL_CRITICAL,
            deadline_epoch_s=1770000000,
            payout_usd=150.0,
        )

        self.assertFalse(driver_dry.can_accommodate(cold_req))
        self.assertTrue(driver_reefer.can_accommodate(cold_req))

        matches = self.matcher.match(
            drivers={"drv_dry": driver_dry, "drv_reefer": driver_reefer},
            requests={"req_vaccines": cold_req},
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].driver_id, "drv_reefer")
        self.assertEqual(matches[0].request_id, "req_vaccines")

    def test_waypoint_obfuscation_progressive_disclosure(self):
        route = self.obfuscator.generate_obfuscated_route(
            request_id="req_high_value",
            driver_id="drv_agent",
            pickup=self.pickup,
            destination=self.dropoff,
        )

        # Initially at pickup: terminal is withheld
        nav_pt = self.obfuscator.get_current_nav_instruction(route, self.pickup)
        self.assertFalse(nav_pt.is_terminal)
        self.assertFalse(route.terminal_k_ring_entered)

        # Driver moves close to destination (within terminal radius)
        near_dropoff = Coordinate(lat=29.9798, lng=-90.0401)
        terminal_nav = self.obfuscator.get_current_nav_instruction(route, near_dropoff)
        self.assertTrue(terminal_nav.is_terminal)
        self.assertTrue(route.terminal_k_ring_entered)
        self.assertEqual(terminal_nav.coordinate, self.dropoff)

    def test_dispatch_graph_loop_tick_latency(self):
        loop = DispatchGraphLoop()
        for i in range(50):
            d = Driver(
                driver_id=f"drv_{i}",
                max_weight_lbs=800.0,
                available_weight_lbs=800.0,
                max_volume_cuft=35.0,
                available_volume_cuft=35.0,
                cold_chain_capable=(i % 2 == 0),
                current_location=Coordinate(lat=29.95 + (i * 0.001), lng=-90.07),
                current_h3_cell="8844594245fffff",
            )
            loop.register_driver(d)

            req = DeliveryRequest(
                request_id=f"req_{i}",
                pickup_location=Coordinate(lat=29.95, lng=-90.07 + (i * 0.001)),
                pickup_h3_cell="8844594245fffff",
                dropoff_location=Coordinate(lat=29.98, lng=-90.04),
                dropoff_h3_cell="8844594247fffff",
                weight_lbs=100.0,
                volume_cuft=5.0,
                requires_cold_chain=(i % 3 == 0),
                priority=PriorityTier.STANDARD,
                deadline_epoch_s=1770000000,
                payout_usd=50.0,
            )
            loop.submit_request(req)

        matches = loop.tick()
        self.assertGreater(len(matches), 40)
        self.assertLess(loop.metrics.last_tick_duration_ms, 2000.0, "Latency exceeded 2000ms SLA")


if __name__ == "__main__":
    unittest.main()
