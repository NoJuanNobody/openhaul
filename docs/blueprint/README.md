# OpenHaul Blueprint

Scope: the technical and strategic blueprint requested in the original brief. Three parts, plus this index.

1. [Technical architecture](01-technical.md): STMP matching, custody and proofs, dispatch loop, verification status, and the decisions the owner must make.
2. [Team and marketing](02-team-and-marketing.md): AI-augmented team composition, the viral strategy, world-building, and the claims that must be fixed before publishing.
3. [Compliance](03-compliance.md): 1099 risk map, internal document conflicts, protocols to adopt, and government-status claims to verify.

## Summary

The core idea is coherent: a matching protocol, cold-chain custody, and a platform that connects owner-operators to disaster and last-mile freight. The repo is ahead on the matching simulation and behind on everything that has to be true before a pilot.

**Built and tested:** greedy welfare matching, the capacity model, cold-chain invariant checks, the HNOA state machine, the 2-second dispatch loop in simulation, and the CI and Docker paths.

**Not true yet, and must be fixed before external use:**
- The "ZK-SNARK" is a SHA-256 hash that anyone can forge.
- The RFID signature check is a string test.
- The H3 distance is a numeric difference, not a grid distance.
- Two of the chaos invariants pass by construction.
- The Rust and Python matchers are separate implementations.

**Blocking for any driver or government deal:** the classification conflicts in §4.2, the premium question, the unnamed insured entity, and the unverified SAM.gov and attestation claims.

**Marketing:** the story is strong, but several claims in the reels and the pilot episode are the product's own unverified claims. Fix them before publishing.

## Owner decisions

1. Real ZK stack, and budget for circuit audit.
2. Single source of truth for matching.
3. Real H3 distance.
4. Signature scheme for tags and readers.
5. Who is the carrier: platform, shipper, or operator.
6. Who pays the premiums.
7. Form the legal entity for the insured.
8. Which marketing claims to remove or prove.

This blueprint is planning material, not legal advice. Counsel must review §4 before any driver contract, insurance binder, or government submission.
