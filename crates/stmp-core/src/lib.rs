use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Spatial coordinate representation.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Coordinate {
    pub lat: f64,
    pub lng: f64,
}

impl Coordinate {
    pub const fn new(lat: f64, lng: f64) -> Self {
        Self { lat, lng }
    }

    /// Approximate Haversine distance in kilometers.
    pub fn distance_to(&self, other: &Coordinate) -> f64 {
        let r = 6371.0; // Earth radius in km
        let d_lat = (other.lat - self.lat).to_radians();
        let d_lng = (other.lng - self.lng).to_radians();
        let a = (d_lat / 2.0).sin().powi(2)
            + self.lat.to_radians().cos()
                * other.lat.to_radians().cos()
                * (d_lng / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());
        r * c
    }
}

/// Lightweight H3 cell abstraction supporting index parsing and distance computation.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct H3Cell {
    pub index_hex: String,
    pub resolution: u8,
}

impl H3Cell {
    pub fn new(index_hex: impl Into<String>, resolution: u8) -> Self {
        Self {
            index_hex: index_hex.into().to_lowercase(),
            resolution,
        }
    }

    /// Parses `index_hex` into an h3o `CellIndex`.
    fn to_cell_index(&self) -> Option<h3o::CellIndex> {
        let raw = u64::from_str_radix(&self.index_hex, 16).ok()?;
        h3o::CellIndex::try_from(raw).ok()
    }

    /// Grid (k-ring) distance in cells between two H3 indices, computed with h3o.
    ///
    /// Returns `u32::MAX` when either index fails to parse, when the two cells
    /// are at different resolutions, or when h3o cannot define a grid distance
    /// between them (for example, cells on different base cells or pentagon
    /// distortion cases where the local IJ coordinate system is undefined).
    pub fn grid_distance(&self, other: &H3Cell) -> u32 {
        let (Some(a), Some(b)) = (self.to_cell_index(), other.to_cell_index()) else {
            return u32::MAX;
        };
        if a.resolution() != b.resolution() {
            return u32::MAX;
        }
        match a.grid_distance(b) {
            Ok(d) => u32::try_from(d).unwrap_or(u32::MAX),
            Err(_) => u32::MAX,
        }
    }
}

/// 1099 Independent contractor driver capacity matrix.
/// Spec: 500-1000 lbs, 15-60 cu ft, cold-chain flag, planned trajectory.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriverCapacityMatrix {
    pub driver_id: String,
    /// Maximum payload weight in lbs (typically 500 - 1000 lbs)
    pub max_weight_lbs: f64,
    /// Available payload weight in lbs
    pub available_weight_lbs: f64,
    /// Maximum cargo volume in cu ft (typically 15 - 60 cu ft)
    pub max_volume_cuft: f64,
    /// Available cargo volume in cu ft
    pub available_volume_cuft: f64,
    /// Active cold-chain capability flag (e.g. refrigerated cooler / active freezer)
    pub cold_chain_capable: bool,
    /// Current driver location
    pub current_location: Coordinate,
    /// Current H3 cell
    pub current_cell: H3Cell,
    /// Planned trajectory waypoints with anticipated timestamps
    pub planned_trajectory: Vec<TrajectoryWaypoint>,
    /// Driver status
    pub is_online: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrajectoryWaypoint {
    pub sequence: u32,
    pub coordinate: Coordinate,
    pub cell: H3Cell,
    pub estimated_arrival_epoch_s: u64,
}

impl DriverCapacityMatrix {
    pub fn can_accommodate(&self, request: &DeliveryRequest) -> bool {
        if !self.is_online {
            return false;
        }
        if request.requires_cold_chain && !self.cold_chain_capable {
            return false;
        }
        if request.weight_lbs > self.available_weight_lbs {
            return false;
        }
        if request.volume_cuft > self.available_volume_cuft {
            return false;
        }
        true
    }

    pub fn reserve_capacity(&mut self, request: &DeliveryRequest) -> Result<(), &'static str> {
        if !self.can_accommodate(request) {
            return Err("Driver does not meet capacity or cold-chain constraints");
        }
        self.available_weight_lbs -= request.weight_lbs;
        self.available_volume_cuft -= request.volume_cuft;
        Ok(())
    }
}

/// Delivery request priority tier.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum PriorityLevel {
    Standard = 1,
    Expedited = 2,
    MedicalCritical = 3,
    DisasterTriageFema = 4,
}

/// Welfare multiplier applied to payout for `PriorityLevel::DisasterTriageFema`.
/// This is the single source of the FEMA weight; Python does not duplicate it.
pub const FEMA_TRIAGE_WELFARE_MULTIPLIER: f64 = 6.0;

pub const DEADHEAD_CUTOFF_KM: f64 = 40.0;

impl PriorityLevel {
    /// Multiplier applied to a request's payout when scoring welfare.
    pub const fn welfare_multiplier(self) -> f64 {
        match self {
            PriorityLevel::Standard => 1.0,
            PriorityLevel::Expedited => 1.5,
            PriorityLevel::MedicalCritical => 2.5,
            PriorityLevel::DisasterTriageFema => FEMA_TRIAGE_WELFARE_MULTIPLIER,
        }
    }
}

/// Delivery request specification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeliveryRequest {
    pub request_id: String,
    pub pickup_location: Coordinate,
    pub pickup_cell: H3Cell,
    pub dropoff_location: Coordinate,
    pub dropoff_cell: H3Cell,
    pub weight_lbs: f64,
    pub volume_cuft: f64,
    pub requires_cold_chain: bool,
    pub min_temp_celsius: Option<f64>,
    pub max_temp_celsius: Option<f64>,
    pub priority: PriorityLevel,
    pub deadline_epoch_s: u64,
    pub payout_usd: f64,
}

/// Bipartite match candidate edge between a driver and a request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchEdge {
    pub driver_id: String,
    pub request_id: String,
    pub deadhead_distance_km: f64,
    pub delivery_distance_km: f64,
    pub welfare_score: f64,
    pub is_feasible: bool,
}

/// Bipartite graph structure containing driver partition and request partition.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BipartiteGraph {
    pub drivers: HashMap<String, DriverCapacityMatrix>,
    pub requests: HashMap<String, DeliveryRequest>,
    pub candidate_edges: Vec<MatchEdge>,
}

impl BipartiteGraph {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_driver(&mut self, driver: DriverCapacityMatrix) {
        self.drivers.insert(driver.driver_id.clone(), driver);
    }

    pub fn add_request(&mut self, request: DeliveryRequest) {
        self.requests.insert(request.request_id.clone(), request);
    }

    /// Evaluates candidate edges across partitions and scores social welfare.
    pub fn compute_candidate_edges(&mut self) {
        self.candidate_edges.clear();
        for (d_id, driver) in &self.drivers {
            for (r_id, req) in &self.requests {
                if !driver.can_accommodate(req) {
                    continue;
                }
                let deadhead = driver.current_location.distance_to(&req.pickup_location);
                if deadhead > DEADHEAD_CUTOFF_KM {
                    continue;
                }
                let delivery_dist = req.pickup_location.distance_to(&req.dropoff_location);

                // Welfare formulation:
                // Base reward from payout and priority multiplier, penalized by deadhead distance
                let welfare_score = (req.payout_usd * req.priority.welfare_multiplier())
                    - (deadhead * 0.75)
                    + (delivery_dist * 0.2);

                self.candidate_edges.push(MatchEdge {
                    driver_id: d_id.clone(),
                    request_id: r_id.clone(),
                    deadhead_distance_km: deadhead,
                    delivery_distance_km: delivery_dist,
                    welfare_score,
                    is_feasible: true,
                });
            }
        }
        // Sort candidate edges descending by welfare score; ties break on ids so the
        // result does not depend on HashMap iteration order.
        self.candidate_edges.sort_by(|a, b| {
            b.welfare_score
                .partial_cmp(&a.welfare_score)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| a.driver_id.cmp(&b.driver_id))
                .then_with(|| a.request_id.cmp(&b.request_id))
        });
    }

    /// Greedy bipartite matching solver maximizing welfare under non-overlapping assignment.
    pub fn solve_greedy_welfare_max(&self) -> Vec<MatchEdge> {
        let mut assigned_drivers = std::collections::HashSet::new();
        let mut assigned_requests = std::collections::HashSet::new();
        let mut assignments = Vec::new();

        for edge in &self.candidate_edges {
            if !assigned_drivers.contains(&edge.driver_id)
                && !assigned_requests.contains(&edge.request_id)
            {
                assigned_drivers.insert(edge.driver_id.clone());
                assigned_requests.insert(edge.request_id.clone());
                assignments.push(edge.clone());
            }
        }
        assignments
    }
}

/// Wire input for one matching pass (the JSON document read by `stmp_match`).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchInput {
    pub drivers: Vec<DriverCapacityMatrix>,
    pub requests: Vec<DeliveryRequest>,
}

/// Wire output for one matching pass (the JSON document written by `stmp_match`).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchOutput {
    pub matches: Vec<MatchEdge>,
}

/// Builds the bipartite graph, scores feasible edges, and returns the greedy
/// welfare-maximizing non-overlapping assignment.
pub fn run_matching(input: MatchInput) -> MatchOutput {
    let mut graph = BipartiteGraph::new();
    for driver in input.drivers {
        graph.add_driver(driver);
    }
    for request in input.requests {
        graph.add_request(request);
    }
    graph.compute_candidate_edges();
    MatchOutput {
        matches: graph.solve_greedy_welfare_max(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const FEMA_VS_STANDARD: &str = include_str!("../tests/fixtures/fema_vs_standard.json");

    #[test]
    fn match_json_fixture_round_trip_prefers_fema() {
        let input: MatchInput = serde_json::from_str(FEMA_VS_STANDARD).expect("fixture parses");
        let output = run_matching(input);
        let text = serde_json::to_string(&output).expect("output serializes");
        let back: MatchOutput = serde_json::from_str(&text).expect("output round-trips");

        assert_eq!(back.matches.len(), 1);
        assert_eq!(back.matches[0].driver_id, "drv_001");
        assert_eq!(back.matches[0].request_id, "req_fema");
        // Deadhead is zero (driver starts at pickup), so welfare is payout * 6.0 + delivery * 0.2.
        assert!(back.matches[0].welfare_score > 600.0);
    }

    #[test]
    fn h3_grid_distance_self_is_zero() {
        let cell = H3Cell::new("8844594245fffff", 8);
        assert_eq!(cell.grid_distance(&cell), 0);
    }

    #[test]
    fn h3_grid_distance_neighbor_is_one() {
        let origin = h3o::CellIndex::try_from(0x8844594245fffff_u64).unwrap();
        let neighbor = origin
            .grid_disk::<Vec<_>>(1)
            .into_iter()
            .find(|c| *c != origin)
            .expect("grid_disk(1) yields at least one neighbor");
        let a = H3Cell::new(format!("{:x}", u64::from(origin)), 8);
        let b = H3Cell::new(format!("{:x}", u64::from(neighbor)), 8);
        assert_eq!(a.grid_distance(&b), 1);
    }

    #[test]
    fn h3_grid_distance_invalid_hex_is_max() {
        let good = H3Cell::new("8844594245fffff", 8);
        let bad = H3Cell::new("not-hex", 8);
        assert_eq!(good.grid_distance(&bad), u32::MAX);
        assert_eq!(bad.grid_distance(&good), u32::MAX);
    }

    #[test]
    fn test_driver_capacity_matrix_and_matching() {
        let coord_a = Coordinate::new(29.9511, -90.0715); // New Orleans
        let coord_b = Coordinate::new(29.9650, -90.0500);

        let driver = DriverCapacityMatrix {
            driver_id: "drv_001".to_string(),
            max_weight_lbs: 800.0,
            available_weight_lbs: 800.0,
            max_volume_cuft: 45.0,
            available_volume_cuft: 45.0,
            cold_chain_capable: true,
            current_location: coord_a,
            current_cell: H3Cell::new("8844594245fffff", 8),
            planned_trajectory: vec![],
            is_online: true,
        };

        let req = DeliveryRequest {
            request_id: "req_fema_101".to_string(),
            pickup_location: coord_a,
            pickup_cell: H3Cell::new("8844594245fffff", 8),
            dropoff_location: coord_b,
            dropoff_cell: H3Cell::new("8844594247fffff", 8),
            weight_lbs: 250.0,
            volume_cuft: 18.0,
            requires_cold_chain: true,
            min_temp_celsius: Some(2.0),
            max_temp_celsius: Some(8.0),
            priority: PriorityLevel::DisasterTriageFema,
            deadline_epoch_s: 1770000000,
            payout_usd: 120.0,
        };

        assert!(driver.can_accommodate(&req));

        let mut graph = BipartiteGraph::new();
        graph.add_driver(driver);
        graph.add_request(req);
        graph.compute_candidate_edges();

        let matches = graph.solve_greedy_welfare_max();
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].driver_id, "drv_001");
        assert_eq!(matches[0].request_id, "req_fema_101");
        assert!(matches[0].welfare_score > 0.0);
    }
}
