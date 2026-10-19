# 1. Technical Architecture

Status key: **Built** = present and tested in the repo. **Partial** = present but does not do what its name says. **Planned** = described, not in code.

## 1.1 System overview

OpenHaul matches parcel and freight requests to independent drivers using their own passenger vehicles. Three layers do the work:

| Layer | Location | Job | Status |
|---|---|---|---|
| Matching protocol (Rust) | `crates/stmp-core` | Capacity model, spatial cells, bipartite welfare graph | Partial |
| Custody and insurance (Rust) | `crates/zk-custody` | RFID scan commitments, cold-chain invariant, HNOA state machine, proof object | Partial (proof is simulated) |
| Dispatch loop (Python) | `python/graph_loop` | 2 s tick matching, waypoint obfuscation | Built (in simulation) |
| Chaos harness (Python) | `python/chaos_sim` | Synthetic metro and disaster scenarios, invariant checks | Built, invariants partly tautological |

The Rust and Python matchers are separate implementations. The Python loop does not call the Rust crates. That split needs an owner decision (see §1.6).

## 1.2 Spatio-Temporal Matching Protocol (STMP)

**Spatial index.** `stmp-core` declares the `h3o` crate (v0.6), but `H3Cell::grid_distance` does not use it. It parses the hex index as a `u64` and returns the numeric difference. That number is not a grid distance, so any matching that depends on it is wrong. **Partial. Fix before relying on it.** The Python side uses hardcoded H3-looking strings (for example `8844594247fffff`) and a haversine distance, with no H3 library.

**Capacity model.** `DriverCapacityMatrix` tracks weight, volume, and cold-chain capability for each driver, with `can_accommodate` and `reserve_capacity`. Python's generator draws drivers in the 500–1000 lb and 15–60 cu ft range. **Built**, with unit tests.

**Welfare matching.** `BipartiteGraph::compute_candidate_edges` scores driver-request edges, and `solve_greedy_welfare_max` picks matches greedily. Python's `matcher.py` applies a 6.0× weight to `DISASTER_TRIAGE_FEMA` requests. **Built as greedy heuristic.** Greedy is fast and simple, but it is not optimal and has no approximation bound. The blueprint should say so to any reviewer.

**Priority tiers.** `Standard`, `Expedited`, `MedicalCritical`, `DisasterTriageFema`. The tier set is the same in both languages.

**Timing.** The Python loop ticks every 2.0 s. Benchmarks in the README (4–10 ms per tick) come from the simulator with synthetic fleets. They are not measured against a real city's driver density or a real network.

## 1.3 Custody, cold chain, and insurance state (zk-custody)

**RFID commitment.** `RfidScanEvent::compute_commitment` is a SHA-256 hash over tag, package, driver, timestamp, reader key, and H3 location. **Built.** It is a hash commitment, not a hiding commitment scheme. Anyone who can guess the inputs can test them against it.

**Signature check.** `verify_signature` accepts any signature of 8+ characters that does not begin with `REPLAY_ATTACK_INVALID`. **Simulated.** It verifies nothing cryptographic. A real deployment needs an ECDSA or EdDSA verification against a provisioned tag or reader key.

**Proof object.** `CustodyZkProof::generate_proof` hashes public inputs and returns a proof_type string of `Arkworks-Groth16-Custody-v1`. `verify()` recomputes the same hash from `public_inputs_hash`, which is a public field.

> **This is not a zero-knowledge proof and not a SNARK.** Anyone can produce a passing proof for any package by calling the same hash function with the same constants. The README's claim that the system "verifies physical custody handover and thermal compliance without leaking driver GPS routes or PII" is not supported by the code. Real Groth16 or Plonk circuits (arkworks, circom, or a managed prover) are required before anyone relies on the claim. Until then, describe this layer as an integrity commitment and audit log.

**Cold-chain invariant.** `TemperatureInvariantChecker` tracks excursions outside a band (README: 2.0–8.0 °C) over a maximum duration. **Built**, with unit tests.

**HNOA state machine.** `HnoaCustodyTracker` moves through `IDLE` → `EN_ROUTE` → `IN_CUSTODY_RFID_VERIFIED` → `COMPLETED`, with `DISPUTED_EXCURSION` as a side state. **Built.** The name HNOA (Hired and Non-Owned Auto) refers to an insurance coverage type. The state machine does not itself implement insurance; §4 covers that.

## 1.4 Anti-hijacking waypoint obfuscation (graph_loop)

`WaypointObfuscator` generates intermediate waypoints every 2.0 km and withholds the true destination until the driver is within 0.8 km of it. **Built, in simulation.** Caveats:

- The threshold stops a driver from seeing the drop-off address early. It does not stop a driver who already knows the address, or a driver who reads the pickup and drop-off from the dispatch screen. The obfuscation applies only to the route the app shows.
- The obfuscator and the RFID scan share no secret, so the destination is not cryptographically protected.

## 1.5 Verification status

| Check | Result |
|---|---|
| `cargo test --workspace` | 4 tests pass |
| `cargo clippy --workspace --all-targets -D warnings` | Pass |
| `cargo fmt --check` | Pass after fix |
| `python3 -m unittest python.tests.*` | 6 tests pass |
| `python3 -m python.chaos_sim.runner --verify-invariants` | Pass (CLI added in this pass) |

**What the tests do not cover:** the ZK proof's soundness, the RFID signature's security, the H3 distance math, and real-world latency. The chaos invariants partly pass by construction: `verify_rfid_replay_defense` checks a string it builds itself, and `verify_cold_chain_defense` checks a hardcoded list. Those two checks should be rewritten to exercise the real code paths.

## 1.6 Decisions the technical blueprint needs from the owner

1. **Proof system.** Choose a real ZK stack (for example Groth16 via arkworks, or a managed prover) and budget for circuit audits. Until then, drop "zero-knowledge" from external material.
2. **Single matcher.** Decided: Rust stmp-core is the source of truth; Python calls it.
3. **Spatial index.** Replace the `u64` difference with real `h3o` grid distance, and derive cells from coordinates rather than hardcoded strings.
4. **Signature scheme.** Define per-tag or per-reader keys and a verification path before any pilot.
5. **Privacy claims.** Route the GPS and PII claims through counsel before they appear in marketing.
