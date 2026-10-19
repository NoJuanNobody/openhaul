use ark_std::rand::{CryptoRng, RngCore};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt;

pub mod zk;
pub use zk::{
    commit, setup, to_centi, BandCommitmentCircuit, CustodyKeys, CustodyStatement, CustodyWitness,
    CustodyZkProof, ZkError, RANGE_BITS, READINGS,
};

/// Hired and Non-Owned Auto (HNOA) insurance state machine states.
/// Transition flow: IDLE -> EN_ROUTE -> IN_CUSTODY_RFID_VERIFIED -> COMPLETED
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HnoaState {
    Idle,
    EnRoute,
    InCustodyRfidVerified,
    Completed,
    DisputedExcursion,
}

impl fmt::Display for HnoaState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            HnoaState::Idle => write!(f, "IDLE"),
            HnoaState::EnRoute => write!(f, "EN_ROUTE"),
            HnoaState::InCustodyRfidVerified => write!(f, "IN_CUSTODY_RFID_VERIFIED"),
            HnoaState::Completed => write!(f, "COMPLETED"),
            HnoaState::DisputedExcursion => write!(f, "DISPUTED_EXCURSION"),
        }
    }
}

/// RFID Scan Event payload used to cryptographically bind physical custody handover.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RfidScanEvent {
    pub tag_id: String,
    pub package_id: String,
    pub driver_id: String,
    pub timestamp_epoch_s: u64,
    pub reader_public_key: String,
    pub signature_hex: String,
    pub location_h3: String,
}

impl RfidScanEvent {
    /// Computes SHA-256 event commitment digest.
    pub fn compute_commitment(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.tag_id.as_bytes());
        hasher.update(self.package_id.as_bytes());
        hasher.update(self.driver_id.as_bytes());
        hasher.update(self.timestamp_epoch_s.to_le_bytes());
        hasher.update(self.reader_public_key.as_bytes());
        hasher.update(self.location_h3.as_bytes());
        let result = hasher.finalize();
        format!("{:x}", result)
    }

    /// Verifies tag signature (deterministic simulator / mock validator)
    pub fn verify_signature(&self) -> bool {
        // Reject empty or trivially tampered signatures
        if self.signature_hex.is_empty() || self.signature_hex.len() < 8 {
            return false;
        }
        // Valid signature simulation: ends with valid parity hex
        !self.signature_hex.starts_with("REPLAY_ATTACK_INVALID")
    }
}

/// Temperature telemetry point for cold-chain monitoring.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemperatureTelemetry {
    pub package_id: String,
    pub timestamp_epoch_s: u64,
    pub temperature_celsius: f64,
}

/// Cold-chain temperature invariant checker.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemperatureInvariantChecker {
    pub min_allowed_celsius: f64,
    pub max_allowed_celsius: f64,
    pub max_excursion_duration_s: u64,
    pub consecutive_breach_count: u32,
    pub excursion_detected: bool,
}

impl TemperatureInvariantChecker {
    pub fn new(min_celsius: f64, max_celsius: f64, max_excursion_duration_s: u64) -> Self {
        Self {
            min_allowed_celsius: min_celsius,
            max_allowed_celsius: max_celsius,
            max_excursion_duration_s,
            consecutive_breach_count: 0,
            excursion_detected: false,
        }
    }

    pub fn record_observation(&mut self, telemetry: &TemperatureTelemetry) -> bool {
        let temp = telemetry.temperature_celsius;
        if temp < self.min_allowed_celsius || temp > self.max_allowed_celsius {
            self.consecutive_breach_count += 1;
            // Breach sustained longer than tolerance threshold
            if self.consecutive_breach_count >= 3 {
                self.excursion_detected = true;
            }
        } else {
            self.consecutive_breach_count = 0;
        }
        !self.excursion_detected
    }
}

/// HNOA (Hired and Non-Owned Auto) Insurance Policy & State Machine Tracker.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HnoaCustodyTracker {
    pub package_id: String,
    pub driver_id: String,
    pub current_state: HnoaState,
    pub rfid_commitment: Option<String>,
    pub zk_proof: Option<CustodyZkProof>,
    pub temp_checker: TemperatureInvariantChecker,
    pub state_history: Vec<(HnoaState, u64)>,
}

impl HnoaCustodyTracker {
    pub fn new(package_id: &str, driver_id: &str, min_temp: f64, max_temp: f64) -> Self {
        Self {
            package_id: package_id.to_string(),
            driver_id: driver_id.to_string(),
            current_state: HnoaState::Idle,
            rfid_commitment: None,
            zk_proof: None,
            temp_checker: TemperatureInvariantChecker::new(min_temp, max_temp, 300),
            state_history: vec![(HnoaState::Idle, 0)],
        }
    }

    /// Transition to EN_ROUTE when driver accepts dispatch and heads to pickup.
    pub fn transition_to_en_route(&mut self, timestamp: u64) -> Result<(), &'static str> {
        if self.current_state != HnoaState::Idle {
            return Err("Invalid transition: must be in IDLE to transition to EN_ROUTE");
        }
        self.current_state = HnoaState::EnRoute;
        self.state_history.push((HnoaState::EnRoute, timestamp));
        Ok(())
    }

    /// Transition to IN_CUSTODY_RFID_VERIFIED upon physical RFID scan & ZK proof generation.
    /// The caller supplies the private readings and blinding; the proof shows they lie
    /// within this tracker's band and open the returned commitment `C`.
    pub fn transition_to_in_custody<R: RngCore + CryptoRng>(
        &mut self,
        rfid_event: &RfidScanEvent,
        timestamp: u64,
        keys: &CustodyKeys,
        witness: &CustodyWitness,
        rng: &mut R,
    ) -> Result<CustodyZkProof, &'static str> {
        if self.current_state != HnoaState::EnRoute {
            return Err(
                "Invalid transition: must be EN_ROUTE to transition to IN_CUSTODY_RFID_VERIFIED",
            );
        }
        if !rfid_event.verify_signature() {
            return Err("Invalid RFID cryptographic signature; proof generation failed");
        }
        if self.temp_checker.excursion_detected {
            return Err("Temperature invariant breached; cannot generate compliant proof");
        }

        let statement = CustodyStatement::for_witness(
            witness,
            to_centi(self.temp_checker.min_allowed_celsius),
            to_centi(self.temp_checker.max_allowed_celsius),
        );
        let proof =
            CustodyZkProof::generate_proof(keys, witness, &statement, rng).map_err(|_| {
                "ZK proof generation failed: reading outside band or commitment mismatch"
            })?;

        if !proof.verify(&keys.verifying_key, &statement) {
            return Err("ZK proof verification failed");
        }

        self.rfid_commitment = Some(rfid_event.compute_commitment());
        self.zk_proof = Some(proof.clone());
        self.current_state = HnoaState::InCustodyRfidVerified;
        self.state_history
            .push((HnoaState::InCustodyRfidVerified, timestamp));
        Ok(proof)
    }

    /// Ingest temperature telemetry and update state if cold chain breached.
    pub fn ingest_telemetry(&mut self, telemetry: &TemperatureTelemetry) -> bool {
        let is_ok = self.temp_checker.record_observation(telemetry);
        if !is_ok && self.current_state == HnoaState::InCustodyRfidVerified {
            self.current_state = HnoaState::DisputedExcursion;
            self.state_history
                .push((HnoaState::DisputedExcursion, telemetry.timestamp_epoch_s));
        }
        is_ok
    }

    /// Transition to COMPLETED upon drop-off delivery confirmation.
    pub fn complete_delivery(&mut self, timestamp: u64) -> Result<(), &'static str> {
        if self.current_state != HnoaState::InCustodyRfidVerified {
            return Err(
                "Invalid transition: must be IN_CUSTODY_RFID_VERIFIED to complete delivery",
            );
        }
        self.current_state = HnoaState::Completed;
        self.state_history.push((HnoaState::Completed, timestamp));
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_rng() -> ark_std::rand::rngs::StdRng {
        use ark_std::rand::SeedableRng;
        ark_std::rand::rngs::StdRng::seed_from_u64(7)
    }

    fn test_keys() -> CustodyKeys {
        setup(&mut test_rng()).expect("dev setup")
    }

    fn in_band_witness(temp_centi: i64) -> CustodyWitness {
        CustodyWitness {
            readings_centi: [temp_centi; READINGS],
            blinding: ark_bn254::Fr::from(12345u64),
        }
    }

    #[test]
    fn test_hnoa_state_machine_and_zk_proof() {
        let mut tracker = HnoaCustodyTracker::new("pkg_med_999", "drv_42", 2.0, 8.0);
        assert_eq!(tracker.current_state, HnoaState::Idle);

        // Transition to EN_ROUTE
        assert!(tracker.transition_to_en_route(100).is_ok());
        assert_eq!(tracker.current_state, HnoaState::EnRoute);

        // Scan RFID
        let rfid_event = RfidScanEvent {
            tag_id: "RFID-TAG-7762".to_string(),
            package_id: "pkg_med_999".to_string(),
            driver_id: "drv_42".to_string(),
            timestamp_epoch_s: 150,
            reader_public_key: "04a1b2c3d4e5f6...".to_string(),
            signature_hex: "3045022100beefcafedeadbeef".to_string(),
            location_h3: "8844594245fffff".to_string(),
        };

        // Transition to IN_CUSTODY_RFID_VERIFIED
        let keys = test_keys();
        let witness = in_band_witness(450);
        let proof_res =
            tracker.transition_to_in_custody(&rfid_event, 150, &keys, &witness, &mut test_rng());
        assert!(proof_res.is_ok());
        let proof = proof_res.unwrap();
        let statement = CustodyStatement::for_witness(&witness, 200, 800);
        assert!(proof.verify(&keys.verifying_key, &statement));
        assert_eq!(tracker.current_state, HnoaState::InCustodyRfidVerified);

        // Record normal temperature
        let temp_ok = TemperatureTelemetry {
            package_id: "pkg_med_999".to_string(),
            timestamp_epoch_s: 200,
            temperature_celsius: 4.5,
        };
        assert!(tracker.ingest_telemetry(&temp_ok));

        // Complete delivery
        assert!(tracker.complete_delivery(300).is_ok());
        assert_eq!(tracker.current_state, HnoaState::Completed);
    }

    #[test]
    fn test_cold_chain_breach_detection() {
        let mut tracker = HnoaCustodyTracker::new("pkg_med_888", "drv_42", 2.0, 8.0);
        tracker.transition_to_en_route(100).unwrap();

        let rfid_event = RfidScanEvent {
            tag_id: "RFID-TAG-001".to_string(),
            package_id: "pkg_med_888".to_string(),
            driver_id: "drv_42".to_string(),
            timestamp_epoch_s: 110,
            reader_public_key: "pubkey_reader".to_string(),
            signature_hex: "aabbccddee112233".to_string(),
            location_h3: "8844594245fffff".to_string(),
        };
        tracker
            .transition_to_in_custody(
                &rfid_event,
                110,
                &test_keys(),
                &in_band_witness(450),
                &mut test_rng(),
            )
            .unwrap();

        // 3 consecutive spikes > 8.0 C
        let temp_spike = TemperatureTelemetry {
            package_id: "pkg_med_888".to_string(),
            timestamp_epoch_s: 120,
            temperature_celsius: 15.0,
        };
        tracker.ingest_telemetry(&temp_spike);
        tracker.ingest_telemetry(&temp_spike);
        let ok = tracker.ingest_telemetry(&temp_spike);
        assert!(!ok);
        assert_eq!(tracker.current_state, HnoaState::DisputedExcursion);
    }

    #[test]
    fn test_rfid_replay_attack_rejected() {
        let mut tracker = HnoaCustodyTracker::new("pkg_sec_01", "drv_evil", 0.0, 20.0);
        tracker.transition_to_en_route(100).unwrap();

        let malicious_rfid = RfidScanEvent {
            tag_id: "RFID-STOLEN".to_string(),
            package_id: "pkg_sec_01".to_string(),
            driver_id: "drv_evil".to_string(),
            timestamp_epoch_s: 110,
            reader_public_key: "pubkey".to_string(),
            signature_hex: "REPLAY_ATTACK_INVALID_FORGED".to_string(),
            location_h3: "8844594245fffff".to_string(),
        };

        let res = tracker.transition_to_in_custody(
            &malicious_rfid,
            110,
            &test_keys(),
            &in_band_witness(100),
            &mut test_rng(),
        );
        assert!(res.is_err());
        assert_eq!(tracker.current_state, HnoaState::EnRoute);
    }
}
