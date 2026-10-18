# OpenHaul Consortium Governance Charter
**Document Reference:** `OH-GOV-DAO-2026-V1`  
**Consortium Structure:** Open-Source Tri-Cameral Protocol Governance  
**License:** Apache 2.0 / MIT Dual License  

---

## 1. Consortium Philosophy & Governance Purpose

The OpenHaul Consortium is organized to maintain, evolve, and secure the **Short-Haul Transport Messaging Protocol (STMP)**, its reference cryptographic zero-knowledge custody engines (`zk-custody`), and distributed mesh dispatch frameworks.

To balance agility in market deployment with mathematical security and decentralized community participation, OpenHaul operates under a **Three-Tier Consortium Governance Model**:

```
                         TRI-CAMERAL DAO GOVERNANCE
                         
             ┌─────────────────────────────────────────────────┐
             │                   TIER 1                        │
             │           CORE PROTOCOL MAINTAINERS             │
             │   - Architectural Roadmap & Releases            │
             │   - Emergency Hotfix & Multi-Sig Escrow         │
             │   - 5-of-9 Multi-Signature Keyholders           │
             └───────────────────────┬─────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
  ┌─────────────────────────────┐         ┌─────────────────────────────┐
  │           TIER 2            │         │           TIER 3            │
  │     FORMAL ZK / MATH        │         │    GENERAL CONTRIBUTORS     │
  │    SECURITY AUDITORS        │         │      & DRIVER SENATE        │
  │ - Circuit Verification      │         │ - EIP-Style Proposals (OHIP)│
  │ - Cryptographic Peer Review │         │ - Feature Bounties & RFCs   │
  │ - VETO Power on Math Spec   │         │ - Regional Node Feedback    │
  └─────────────────────────────┘         └─────────────────────────────┘
```

---

## 2. The Three-Tier Consortium Model

### Tier 1: Core Maintainers (Protocol Steering Committee)
- **Composition:** 9 elected maintainers representing distributed systems engineering, mobile systems, logistics operations, and legal/regulatory compliance.
- **Responsibilities:**
  - Git repository write access, code review merging, and crate release tagging for `stmp-core` and mobile SDKs.
  - Stewardship of the Consortium treasury, seed capital allocation ($2.45M), and grant distribution.
  - Operation of the 5-of-9 protocol multi-signature threshold contract governing critical parameters (such as the default 22% take rate, emergency protocol pauses, and treasury disbursements).
- **Election & Term:** Staggered 2-year terms, elected through weighted community voting based on verified technical commits and node operational uptime.

### Tier 2: Formal ZK / Math Security Auditors (Cryptographic Council)
- **Composition:** Independent cryptographic engineering firms, academic researchers, and zero-knowledge circuit security specialists.
- **Responsibilities:**
  - Mandatory pre-release formal verification of all Halo2, Groth16, or STARK circuits utilized in `zk-custody` and proof-of-handshake systems.
  - Review of cryptographic entropy, curve parameters, and signature aggregation pipelines.
- **Special Authority (VETO Power):** Tier 2 auditors possess absolute, binding veto authority over any protocol proposal (OHIP) that alters cryptographic primitives, custody handshake formulas, or privacy-preserving telemetry zero-knowledge circuits. A Tier 2 veto cannot be overridden by Tier 1 or Tier 3.

### Tier 3: General Contributors & Driver Senate
- **Composition:** Open-source software contributors, independent fleet operators, owner-operators, freight brokers, and municipal disaster coordination liaisons.
- **Responsibilities:**
  - Submission of **OpenHaul Improvement Proposals (OHIPs)** covering UI/UX, routing optimizations, API specifications, and local market tuning.
  - Election of Driver Senate representatives to advocate for fair compensation splits, HNOA insurance fairness, and fuel index adjustments.
  - Peer code review, localized language translations, and documentation enhancement.

---

## 3. Proposal Lifecycle (OHIP — OpenHaul Improvement Proposal)

```
[Idea / RFC in Forum] 
        │
        ▼
[Formal OHIP Draft Submitted (GitHub PR)]
        │
        ├──> Tier 3 Technical & Community Discussion (Minimum 14 Days)
        │
        ├──> If touching ZK circuits / Crypto Primitives:
        │    └──> Tier 2 Cryptographic Audit & Formal Sign-Off (M-of-N consensus)
        │
        ├──> Tier 1 Core Maintainer Quorum Review
        │    └──> Requires 6-of-9 affirmative votes
        │
        ▼
[Merge to Staging & Chaos Test Simulation]
        │
        ▼
[Production Deployment / Network Activation]
```

### 3.1 Proposal Types
1. **Standards Track (Core):** Protocol changes impacting `stmp-core`, packet format, network wire protocol, and RPC endpoints.
2. **Security Track (ZK/Math):** Circuit logic alterations, proof serialization, or signature schemes. Requires mandatory Tier 2 sign-off.
3. **Economic Track:** Take rate alterations, emergency relief subsidy pools, insurance deductible allocations, and treasury grants.
4. **Informational / Process:** Operational guidelines, legal templates, and disaster deployment runbooks.

---

## 4. Emergency Governance & Circuit Breakers

In the event of an active zero-day vulnerability, cryptographic exploit, or catastrophic physical network failure during a FEMA disaster mobilization:
- **Emergency Hotfix Authority:** A 5-of-9 threshold of Tier 1 Core Maintainers can activate the **Protocol Circuit Breaker**, pausing state-machine updates or routing payments through a secure escrow freeze for a maximum period of 72 hours.
- **Post-Incident Review:** Within 7 calendar days of an emergency action, a full public post-mortem and independent audit report must be published by Tier 2 auditors, followed by an immediate community ratification vote.
