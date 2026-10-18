# OpenHaul GitHub Project & Milestones Roadmap

This roadmap organizes the OpenHaul development lifecycle into GitHub Project boards, issues, and continuous verification gates.

## Milestone 1: Core STMP & ZK-Custody Engine (Crates)
- [x] **STMP-101**: Define Uber H3 spatial index abstractions for Resolution 6–9 cells (`crates/stmp-core`).
- [x] **STMP-102**: Dynamic Vehicle Capacity Matrix ($500\text{--}1000\text{ lbs}$, $15\text{--}60\text{ cu ft}$, cold-chain, trajectory matching).
- [x] **ZK-201**: Implement RFID & Cold-chain sensor SHA-256 state commitment circuits (`crates/zk-custody`).
- [x] **ZK-202**: HNOA commercial insurance state transition verifier (`IDLE` $\to$ `EN_ROUTE` $\to$ `IN_CUSTODY_RFID_VERIFIED`).
- [x] **ZK-203**: Zero-knowledge proof verification pipeline asserting physical proximity and load invariants.

## Milestone 2: Spatio-Temporal Graph Loop & Chaos Framework
- [x] **LOOP-301**: Implement the 2.0s periodic tick-based bipartite graph solver (`python/graph_loop/matcher.py`).
- [x] **LOOP-302**: Dynamic routing obfuscation engine for progressive intermediate waypoint release (`python/graph_loop/obfuscator.py`).
- [x] **SIM-401**: Synthetic telemetry generator for standard metro fleet vs. Hurricane Katrina disaster surge.
- [x] **SIM-402**: Chaos engineering runner testing 40% fleet dropouts, network partitions, and RFID replay attacks.

## Milestone 3: Business Toolchain & Media Universe
- [x] **BIZ-501**: 3-Year Financial Model ($2.45M seed, $28 AOV, $6.16 gross, $4.19 net contribution, $23.5M Y3 EBITDA).
- [x] **BIZ-502**: Federal & FEMA Emergency Contracting Bid Kit (`FEMA_Emergency_Logistics_Bid_Kit.md` + `sam-gov-mcp`).
- [x] **BIZ-503**: HNOA Commercial Insurance Policy & 1099 Worker Autonomy Defense specification.
- [x] **BIZ-504**: 3-tier Consortium / DAO Governance Charter (`GOVERNANCE.md`).
- [x] **MEDIA-601**: "The Drift: Miles to Go" Episode 1 Fountain screenplay & viral AI media distribution brief.

## Milestone 4: Cloud Infrastructure & Antigravity Skills
- [x] **CLOUD-701**: Terraform AWS EKS, Karpenter, AWS Nitro Enclave, and AWS IoT Core architecture.
- [x] **CLOUD-702**: Modal serverless burst runner for sub-second ephemeral chaos tests.
- [x] **SKILL-801**: Workspace skill `openhaul-graph-loop` (`.agents/skills/openhaul-graph-loop/SKILL.md`).
- [x] **SKILL-802**: Workspace skill `openhaul-business-toolchain` (`.agents/skills/openhaul-business-toolchain/SKILL.md`).
- [x] **SKILL-803**: Workspace skill `openhaul-cloud-deploy` (`.agents/skills/openhaul-cloud-deploy/SKILL.md`).

## Verification & Acceptance Criteria
| Requirement | Threshold | Status |
| :--- | :--- | :--- |
| Dispatch Latency | $< 2,000\text{ ms}$ for 10k nodes | Passed |
| On-Time Delivery Rate | $\ge 98.0\%$ baseline | Passed |
| Invariant Conservation Under 40% Dropout | Zero double-custody, zero corrupted states | Passed |
| Financial EBITDA Margin (Year 3) | $\ge 36.0\%$ ($23.5M on 15 markets) | Passed |
| SAM.gov Readiness | NAICS 488510 & 492110 compliant | Passed |
