//! Groth16 (BN254) proof that a custody record's temperature readings all lie
//! inside a public band `[min, max]` and open a public Poseidon commitment.
//!
//! Statement proven:
//! "I know readings `r_0..r_7` and a blinding value `b` such that every
//! `min <= r_i <= max`, and `C = Poseidon(r_0..r_7, b)`", where `C`, `min`
//! and `max` are public.
//!
//! Encoding: temperatures are fixed-point integers in centi-degrees Celsius
//! (4.50 C -> 450). A reading is checked by bit-decomposing `r - min` and
//! `max - r` into `RANGE_BITS` bits, so each difference is in `[0, 2^16)`;
//! this implies `min <= r <= max` for any bounds that fit in the field, and
//! the band width must be below 655.36 C.
//!
//! SETUP WARNING: `setup` runs a circuit-specific Groth16 trusted setup driven
//! by the caller's RNG. It is a development setup: whoever knows the toxic
//! waste can forge proofs. Production use requires a multi-party ceremony.

use std::sync::OnceLock;

use ark_bn254::{Bn254, Fr};
use ark_crypto_primitives::sponge::{
    constraints::CryptographicSpongeVar,
    poseidon::{
        constraints::PoseidonSpongeVar, find_poseidon_ark_and_mds, PoseidonConfig, PoseidonSponge,
    },
    CryptographicSponge, FieldBasedCryptographicSponge,
};
use ark_ff::PrimeField;
use ark_groth16::{Groth16, Proof, ProvingKey, VerifyingKey};
use ark_r1cs_std::{
    alloc::AllocVar,
    boolean::Boolean,
    eq::EqGadget,
    fields::{fp::FpVar, FieldVar},
};
use ark_relations::gr1cs::{
    ConstraintSynthesizer, ConstraintSystem, ConstraintSystemRef, SynthesisError,
};
use ark_serialize::{CanonicalDeserialize, CanonicalSerialize};
use ark_snark::SNARK;
use ark_std::rand::{CryptoRng, RngCore};
use serde::{Deserialize, Serialize};

/// Number of temperature readings in one custody record (fixed circuit shape).
pub const READINGS: usize = 8;
/// Bit width of each range-check decomposition.
pub const RANGE_BITS: usize = 16;
/// Poseidon rate and capacity (t = 3, S-box alpha = 5, 8 full + 57 partial rounds).
const POSEIDON_RATE: usize = 2;
const POSEIDON_CAPACITY: usize = 1;
const POSEIDON_FULL_ROUNDS: usize = 8;
const POSEIDON_PARTIAL_ROUNDS: usize = 57;
const POSEIDON_ALPHA: u64 = 5;

/// Proof type tag stored alongside serialized proofs.
pub const PROOF_TYPE: &str = "Groth16-BN254-Custody-Band-v2";

/// Errors from setup, proving and encoding.
#[derive(Debug, thiserror::Error)]
pub enum ZkError {
    /// The witness does not satisfy the circuit: a reading is outside the band,
    /// or the readings and blinding do not open the public commitment.
    #[error("witness rejected: a reading is outside the band or the commitment does not match")]
    Unsatisfied,
    /// Underlying proof system or constraint synthesis failure.
    #[error("proof system error: {0}")]
    ProofSystem(String),
    /// A stored proof or key could not be decoded.
    #[error("malformed proof encoding")]
    MalformedEncoding,
}

impl From<SynthesisError> for ZkError {
    fn from(e: SynthesisError) -> Self {
        ZkError::ProofSystem(format!("{e:?}"))
    }
}

/// Proving and verifying keys for the band-commitment circuit.
pub struct CustodyKeys {
    pub proving_key: ProvingKey<Bn254>,
    pub verifying_key: VerifyingKey<Bn254>,
}

/// Private witness: the readings (centi-degrees) and the commitment blinding.
#[derive(Debug, Clone)]
pub struct CustodyWitness {
    pub readings_centi: [i64; READINGS],
    pub blinding: Fr,
}

/// Public statement: commitment `C` and the band bounds (centi-degrees).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CustodyStatement {
    pub commitment: Fr,
    pub min_centi: i64,
    pub max_centi: i64,
}

impl CustodyStatement {
    /// Builds the statement that a witness should satisfy, computing `C` from it.
    pub fn for_witness(witness: &CustodyWitness, min_centi: i64, max_centi: i64) -> Self {
        Self {
            commitment: commit(&witness.readings_centi, &witness.blinding),
            min_centi,
            max_centi,
        }
    }

    /// Public inputs in circuit order: `[C, min, max]`.
    pub fn public_inputs(&self) -> Vec<Fr> {
        vec![
            self.commitment,
            fr_from_i64(self.min_centi),
            fr_from_i64(self.max_centi),
        ]
    }
}

/// Deterministic Poseidon parameters (generated from the Grain LFSR, so no
/// hand-typed constants).
pub fn poseidon_config() -> &'static PoseidonConfig<Fr> {
    static CONFIG: OnceLock<PoseidonConfig<Fr>> = OnceLock::new();
    CONFIG.get_or_init(|| {
        let (ark, mds) = find_poseidon_ark_and_mds::<Fr>(
            Fr::MODULUS_BIT_SIZE as u64,
            POSEIDON_RATE,
            POSEIDON_FULL_ROUNDS as u64,
            POSEIDON_PARTIAL_ROUNDS as u64,
            0,
        );
        PoseidonConfig::new(
            POSEIDON_FULL_ROUNDS,
            POSEIDON_PARTIAL_ROUNDS,
            POSEIDON_ALPHA,
            mds,
            ark,
            POSEIDON_RATE,
            POSEIDON_CAPACITY,
        )
    })
}

/// Commitment `C = Poseidon(readings..., blinding)` as a BN254 scalar.
pub fn commit(readings_centi: &[i64; READINGS], blinding: &Fr) -> Fr {
    let mut inputs: Vec<Fr> = readings_centi.iter().map(|r| fr_from_i64(*r)).collect();
    inputs.push(*blinding);
    let mut sponge = PoseidonSponge::<Fr>::new(poseidon_config());
    sponge.absorb(&inputs);
    sponge.squeeze_native_field_elements(1)[0]
}

/// Circuit for the band-and-commitment statement. Witness fields are `None`
/// during setup.
#[derive(Clone)]
pub struct BandCommitmentCircuit {
    pub readings_centi: Option<[i64; READINGS]>,
    pub blinding: Option<Fr>,
    pub commitment: Option<Fr>,
    pub min_centi: Option<i64>,
    pub max_centi: Option<i64>,
}

impl BandCommitmentCircuit {
    fn empty() -> Self {
        Self {
            readings_centi: None,
            blinding: None,
            commitment: None,
            min_centi: None,
            max_centi: None,
        }
    }
}

impl ConstraintSynthesizer<Fr> for BandCommitmentCircuit {
    fn generate_constraints(self, cs: ConstraintSystemRef<Fr>) -> Result<(), SynthesisError> {
        let commitment = FpVar::new_input(cs.clone(), || {
            self.commitment.ok_or(SynthesisError::AssignmentMissing)
        })?;
        let min = FpVar::new_input(cs.clone(), || {
            self.min_centi
                .map(fr_from_i64)
                .ok_or(SynthesisError::AssignmentMissing)
        })?;
        let max = FpVar::new_input(cs.clone(), || {
            self.max_centi
                .map(fr_from_i64)
                .ok_or(SynthesisError::AssignmentMissing)
        })?;

        let mut readings = Vec::with_capacity(READINGS);
        for i in 0..READINGS {
            readings.push(FpVar::new_witness(cs.clone(), || {
                self.readings_centi
                    .map(|r| fr_from_i64(r[i]))
                    .ok_or(SynthesisError::AssignmentMissing)
            })?);
        }
        let blinding = FpVar::new_witness(cs.clone(), || {
            self.blinding.ok_or(SynthesisError::AssignmentMissing)
        })?;

        for i in 0..READINGS {
            // r - min in [0, 2^16) and max - r in [0, 2^16).
            let lower_diff = self
                .readings_centi
                .zip(self.min_centi)
                .map(|(r, m)| (r[i] as i128) - (m as i128));
            let upper_diff = self
                .readings_centi
                .zip(self.max_centi)
                .map(|(r, m)| (m as i128) - (r[i] as i128));
            enforce_bits_sum_to(cs.clone(), lower_diff, &(&readings[i] - &min))?;
            enforce_bits_sum_to(cs.clone(), upper_diff, &(&max - &readings[i]))?;
        }

        let mut sponge = PoseidonSpongeVar::<Fr>::new(cs.clone(), poseidon_config());
        let mut absorbed = readings;
        absorbed.push(blinding);
        sponge.absorb(&absorbed)?;
        let digest = sponge.squeeze_field_elements(1)?;
        digest[0].enforce_equal(&commitment)?;
        Ok(())
    }
}

/// Allocates `RANGE_BITS` boolean witnesses whose weighted sum must equal `value`.
/// `native` is the value the prover claims (None during setup).
fn enforce_bits_sum_to(
    cs: ConstraintSystemRef<Fr>,
    native: Option<i128>,
    value: &FpVar<Fr>,
) -> Result<(), SynthesisError> {
    let mut bits = Vec::with_capacity(RANGE_BITS);
    for bit in 0..RANGE_BITS {
        bits.push(Boolean::new_witness(cs.clone(), || {
            native
                .map(|v| (v >> bit) & 1 == 1)
                .ok_or(SynthesisError::AssignmentMissing)
        })?);
    }
    let mut sum = FpVar::<Fr>::zero();
    for (bit, b) in bits.iter().enumerate() {
        let weight = FpVar::constant(Fr::from(1u64 << bit));
        sum += FpVar::from(b.clone()) * weight;
    }
    sum.enforce_equal(value)
}

/// Runs the Groth16 circuit-specific setup. DEV ONLY: see the module docs.
pub fn setup<R: RngCore + CryptoRng>(rng: &mut R) -> Result<CustodyKeys, ZkError> {
    let (proving_key, verifying_key) =
        Groth16::<Bn254>::circuit_specific_setup(BandCommitmentCircuit::empty(), rng)
            .map_err(|e| ZkError::ProofSystem(format!("{e:?}")))?;
    Ok(CustodyKeys {
        proving_key,
        verifying_key,
    })
}

/// Groth16 proof of the band-and-commitment statement, with its public statement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CustodyZkProof {
    pub proof_type: String,
    pub commitment_hex: String,
    pub min_centi: i64,
    pub max_centi: i64,
    pub proof_bytes_hex: String,
}

impl CustodyZkProof {
    /// Proves the statement for `witness`. Fails with `ZkError::Unsatisfied` if
    /// any reading is outside `[min_centi, max_centi]` or the commitment in
    /// `statement` is not opened by the witness. The constraint check runs
    /// before proving, so an invalid witness never yields a proof.
    pub fn generate_proof<R: RngCore + CryptoRng>(
        keys: &CustodyKeys,
        witness: &CustodyWitness,
        statement: &CustodyStatement,
        rng: &mut R,
    ) -> Result<Self, ZkError> {
        let circuit = BandCommitmentCircuit {
            readings_centi: Some(witness.readings_centi),
            blinding: Some(witness.blinding),
            commitment: Some(statement.commitment),
            min_centi: Some(statement.min_centi),
            max_centi: Some(statement.max_centi),
        };

        let cs = ConstraintSystem::<Fr>::new_ref();
        circuit.clone().generate_constraints(cs.clone())?;
        if !cs.is_satisfied()? {
            return Err(ZkError::Unsatisfied);
        }

        let proof = Groth16::<Bn254>::prove(&keys.proving_key, circuit, rng)
            .map_err(|e| ZkError::ProofSystem(format!("{e:?}")))?;

        Ok(Self {
            proof_type: PROOF_TYPE.to_string(),
            commitment_hex: fr_to_hex(&statement.commitment)?,
            min_centi: statement.min_centi,
            max_centi: statement.max_centi,
            proof_bytes_hex: bytes_to_hex(&serialize(&proof)?),
        })
    }

    /// Verifies this proof against the caller's `expected` statement. Returns
    /// false if the stored statement differs from `expected`, the encoding is
    /// malformed, or the Groth16 check fails.
    pub fn verify(&self, verifying_key: &VerifyingKey<Bn254>, expected: &CustodyStatement) -> bool {
        if self.proof_type != PROOF_TYPE
            || self.min_centi != expected.min_centi
            || self.max_centi != expected.max_centi
        {
            return false;
        }
        match fr_to_hex(&expected.commitment) {
            Ok(hex) if hex == self.commitment_hex => {}
            _ => return false,
        }
        let Ok(bytes) = hex_to_bytes(&self.proof_bytes_hex) else {
            return false;
        };
        let Ok(proof) = Proof::<Bn254>::deserialize_compressed(&bytes[..]) else {
            return false;
        };
        let Ok(pvk) = Groth16::<Bn254>::process_vk(verifying_key) else {
            return false;
        };
        Groth16::<Bn254>::verify_with_processed_vk(&pvk, &expected.public_inputs(), &proof)
            .unwrap_or(false)
    }
}

/// Converts a signed integer to a BN254 scalar (negative values map to `p - |v|`).
pub fn fr_from_i64(v: i64) -> Fr {
    if v >= 0 {
        Fr::from(v as u64)
    } else {
        -Fr::from(v.unsigned_abs())
    }
}

/// Converts centi-degrees Celsius from an f64 temperature, rounding to nearest.
pub fn to_centi(celsius: f64) -> i64 {
    (celsius * 100.0).round() as i64
}

fn serialize<T: CanonicalSerialize>(value: &T) -> Result<Vec<u8>, ZkError> {
    let mut buf = Vec::new();
    value
        .serialize_compressed(&mut buf)
        .map_err(|e| ZkError::ProofSystem(format!("{e:?}")))?;
    Ok(buf)
}

fn fr_to_hex(value: &Fr) -> Result<String, ZkError> {
    Ok(bytes_to_hex(&serialize(value)?))
}

fn bytes_to_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn hex_to_bytes(s: &str) -> Result<Vec<u8>, ZkError> {
    if !s.len().is_multiple_of(2) || !s.is_ascii() {
        return Err(ZkError::MalformedEncoding);
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(|_| ZkError::MalformedEncoding))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_rng() -> ark_std::rand::rngs::StdRng {
        use ark_std::rand::SeedableRng;
        ark_std::rand::rngs::StdRng::seed_from_u64(7)
    }
    use std::time::Instant;

    const MIN: i64 = 200;
    const MAX: i64 = 800;

    fn witness(readings: [i64; READINGS]) -> CustodyWitness {
        CustodyWitness {
            readings_centi: readings,
            blinding: Fr::from(987_654_321u64),
        }
    }

    #[test]
    fn in_band_record_proof_verifies() {
        let keys = setup(&mut test_rng()).unwrap();
        let w = witness([200, 450, 800, 300, 512, 799, 201, 650]);
        let stmt = CustodyStatement::for_witness(&w, MIN, MAX);

        let start = Instant::now();
        let proof = CustodyZkProof::generate_proof(&keys, &w, &stmt, &mut test_rng()).unwrap();
        eprintln!(
            "groth16 prove time (8 readings, 16-bit range): {:?}",
            start.elapsed()
        );

        assert!(proof.verify(&keys.verifying_key, &stmt));
    }

    #[test]
    fn out_of_band_reading_cannot_be_proven() {
        let keys = setup(&mut test_rng()).unwrap();
        // Reading 7 is 801 centi-degrees, one step above max.
        let w = witness([450, 450, 450, 450, 450, 450, 450, 801]);
        let stmt = CustodyStatement::for_witness(&w, MIN, MAX);
        let result = CustodyZkProof::generate_proof(&keys, &w, &stmt, &mut test_rng());
        assert!(matches!(result, Err(ZkError::Unsatisfied)));

        // Below-min reading is rejected too.
        let w_low = witness([450, 450, 450, 450, 450, 450, 450, 199]);
        let stmt_low = CustodyStatement::for_witness(&w_low, MIN, MAX);
        assert!(matches!(
            CustodyZkProof::generate_proof(&keys, &w_low, &stmt_low, &mut test_rng()),
            Err(ZkError::Unsatisfied)
        ));
    }

    #[test]
    fn proof_fails_against_different_commitment() {
        let keys = setup(&mut test_rng()).unwrap();
        let w = witness([450; READINGS]);
        let stmt = CustodyStatement::for_witness(&w, MIN, MAX);
        let proof = CustodyZkProof::generate_proof(&keys, &w, &stmt, &mut test_rng()).unwrap();

        let other = CustodyStatement {
            commitment: stmt.commitment + Fr::from(1u64),
            ..stmt.clone()
        };
        assert!(!proof.verify(&keys.verifying_key, &other));

        let other_band = CustodyStatement {
            max_centi: MAX + 1,
            ..stmt.clone()
        };
        assert!(!proof.verify(&keys.verifying_key, &other_band));
    }

    #[test]
    fn tampered_proof_bytes_fail() {
        let keys = setup(&mut test_rng()).unwrap();
        let w = witness([450; READINGS]);
        let stmt = CustodyStatement::for_witness(&w, MIN, MAX);
        let mut proof = CustodyZkProof::generate_proof(&keys, &w, &stmt, &mut test_rng()).unwrap();
        assert!(proof.verify(&keys.verifying_key, &stmt));

        let mut bytes = hex_to_bytes(&proof.proof_bytes_hex).unwrap();
        let idx = bytes.len() / 2;
        bytes[idx] ^= 0x01;
        proof.proof_bytes_hex = bytes_to_hex(&bytes);
        assert!(!proof.verify(&keys.verifying_key, &stmt));
    }
}
