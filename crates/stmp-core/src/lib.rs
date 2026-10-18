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
            + self.lat.to_radians().cos() * other.lat.to_radians().cos() * (d_lng / 2.0).sin().powi(2);
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

    /// Computes grid ring distance approximation between two H3 indices.
    pub fn grid_distance(&self, other: &H3Cell) -> u32 {
        if self.index_hex == other.index_hex {
            return 0;
        }
        // Approximate distance based on hex integer diff or fallback
        let a = u64::from_str_radix(&self.index_hex, 16).unwrap_or(0);
        let b = u64::from_str_radix(&other.index_hex, 16).unwrap_or(0);
        let diff = (a as i64 - b as i64).unsigned_abs();
        if diff == 0 {
            0
        } else if diff < 16 {
            1
        } else if diff < 64 {
            2
        } else {
            ((diff as f64).log2().max(1.0)) as u32
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
                let delivery_dist = req.pickup_location.distance_to(&req.dropoff_location);

                // Welfare formulation:
                // Base reward from payout and priority multiplier, penalized by deadhead distance
                let priority_multiplier = match req.priority {
                    PriorityLevel::Standard => 1.0,
                    PriorityLevel::Expedited => 1.5,
                    PriorityLevel::MedicalCritical => 2.5,
                    PriorityLevel::DisasterTriageFema => 5.0,
                };

                let welfare_score = (req.payout_usd * priority_multiplier) - (deadhead * 0.75) + (delivery_dist * 0.2);

                self.candidate_edges.push(MatchEdge {
                    driver_id: d_id.clone(),
                    request_id: r_id.clone(),
                    deadhead_distance_km: deadhead,
                    welfare_score,
                    is_feasible: true,
                });
            }
        }
        // Sort candidate edges descending by welfare score
        self.candidate_edges.sort_by(|a, b| {
            b.welfare_score
                .partial_cmp(&a.welfare_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
    }

    /// Greedy bipartite matching solver maximizing welfare under non-overlapping assignment.
    pub fn solve_greedy_welfare_max(&self) -> Vec<MatchEdge> {
        let mut assigned_drivers = std::collections::HashSet::new();
        let mut assigned_requests = std::collections::HashSet::new();
        let mut assignments = Vec::new();

        for edge in &self.candidate_edges {
            if !assigned_drivers.contains(&edge.driver_id) && !assigned_requests.contains(&edge.request_id) {
                assigned_drivers.insert(edge.driver_id.clone());
                assigned_requests.insert(edge.request_id.clone());
                assignments.push(edge.clone());
            }
        }
        assignments
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
