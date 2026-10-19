# 4. Compliance Protocols for 1099 Driver Risk

> This section is a risk map for counsel, not legal advice. Every legal conclusion below needs review by a licensed attorney in each state where OpenHaul operates. Citations are leads to check, not verified authority.

## 4.1 What the existing documents say

- **Insurance (HNOA policy, OH-LEG-INS-2026-V1).** Three states of coverage. IDLE: the driver's personal auto policy is primary. EN_ROUTE and IN_CUSTODY: a $1,000,000 CSL "OpenHaul HNOA Master Policy" applies. The driver's policy is excess. Cargo coverage is $250,000 per occurrence, and only in State 3. Physical damage excludes State 1.
- **Governance (OH-GOV-DAO-2026-V1).** Nine elected core maintainers control repo access, the treasury, and a 5-of-9 multisig over the 22% take rate. Auditors have a binding veto over cryptography and ZK changes. Drivers elect a "Driver Senate" that proposes changes but has no stated binding vote.
- **Classification approach.** The policy cites California's ABC test (Labor Code §2775), the DOL economic-realities test, and the Restatement (Second) of Agency. Its three prongs are: (A) no uniforms and unrestricted dispatch; (B) OpenHaul is a "cryptographic communications facilitator" and the shipper–operator contract is the merchant of record; (C) the operator runs a business entity with "zero subsidies."
- **Dispute terms (§4.3).** Individual AAA arbitration with class and PAGA waivers.

## 4.2 Where the documents conflict with each other

These are internal contradictions. Each one weakens the classification argument, so fix them before any driver signs.

| # | Conflict | Why it matters |
|---|---|---|
| 1 | **Prong B vs §2 coverage.** OpenHaul buys primary liability and cargo coverage for loads and runs escrow settlement. Prong B says OpenHaul owns no freight and is a facilitator. | Buying coverage and settling payments for each load looks like the business is the carrier, not a platform. |
| 2 | **Prong A vs §2 telemetry.** Prong A promises "complete, unilateral autonomy." States 2 and 3 require mandatory RFID handshakes and high-frequency GPS. | Mandatory control over how and when work is done is a core factor under the ABC and economic-realities tests. |
| 3 | **Prong C vs premiums.** Prong C says "zero subsidies." If OpenHaul pays the accruing premiums ($0.08, $0.42, $0.78 per hour), that is a subsidy. The documents don't say who pays. | The contract's own words can be used against it. Resolve who pays before signing. |
| 4 | **Ambiguous excess language.** The driver's policy is "contingent excess where permitted" in §2 and plain "Excess" in §1. | Coverage disputes at the moment of a crash are the most common failure mode for this model. |
| 5 | **Indemnity wording.** §4.1 indemnifies "gross negligence, willful misconduct, or violation of state traffic regulations" outside active manifests. The "or" makes ordinary traffic tickets indemnifiable. | Read literally, drivers indemnify OpenHaul for routine violations. Narrow the list to intentional or grossly negligent acts. |
| 6 | **Unnamed insured.** The "OpenHaul Consortium" is not a legal entity, so it cannot clearly be an insured or indemnitee. | Coverage and indemnity can fail if the named party does not exist. Form the entity first. |

## 4.3 Legal risks to take to counsel

These are issues that counsel should evaluate. None is a conclusion.

- **PAGA waiver (§4.3).** In California, pre-dispute waivers of representative PAGA claims have generally been held unenforceable (see *Iskanian*, and later *Adolph v. Uber* in 2023). The clause is likely void as written. Do not rely on it.
- **Evidence clause (§4.2).** A contract cannot by itself make OpenHaul's logs admissible as business records under FRE 803(6). The clause that promises logs "without reservation of rights" is a promise in a contract, not a policy.
- **Insurance placement.** Confirm with a licensed broker that the HNOA master policy, the driver's personal policy, and the cargo cover actually stack the way the state tables describe, in each state of operation.
- **Passenger-vehicle freight.** Carrying parcels, pharmaceuticals, or blood in personal or commercial passenger vehicles raises motor-carrier registration, hazmat, and cold-chain rules that the documents do not address. Confirm which federal and state permits apply before any launch.
- **Disaster operations.** Federal disaster work runs under Stafford Act and FEMA contracting rules, which differ from commercial law. Confirm the rules before operating under the FEMA positioning in §3.

## 4.4 Protocols to adopt now

1. **Classification review.** Counsel reviews the operator agreement against the ABC test in every state of operation before onboarding. Remove any control that is not needed for safety or legal compliance.
2. **Choose one story about who is the carrier.** The platform, the shipper, or the operator. Make the insurance, settlement, and contract say the same thing.
3. **Settle the premium question.** Write down who pays each premium, and stop any payment that could be called a subsidy if the answer is OpenHaul.
4. **Narrow indemnity.** Limit indemnity to intentional and grossly negligent acts. Remove routine traffic violations.
5. **Form the entity.** Create a real legal entity for the "Consortium" and name it as insured and indemnitee.
6. **Replace the PAGA waiver** with terms counsel confirms are enforceable in each state.
7. **Driver safety and pay transparency.** Publish the pay formula and the driver share, and log every dispute with a timeline. This is the evidence that matters most if classification is challenged.
8. **Incident response.** Define who gets called after a crash, a cold-chain failure, or an RFID dispute, and how custody records are preserved.

## 4.5 Numbers that conflict across documents

| Item | Bid kit | Other source | Action |
|---|---|---|---|
| Per-mile rate | $2.40 standard / $3.15 catastrophic per loaded mile | `sam-gov-mcp` manifest: $2.40 | Pick one; keep the bid and manifest in sync |
| Standby rate | $38.00 / $45.00 per hour | `sam-gov-mcp`: $38.00 | Same |
| Y3 margin | "44.9%" in a model note | Model header: "44%+" (floored from computed 44.9%) | Resolved |
| Driver share | 82% standard | Take rate 18% | Consistent, but the FEMA surge sheet also uses 18% and 15%; confirm |

## 4.6 Government-status claims to verify before any bid

The bid kit asserts several facts that the repo cannot verify. Check each one directly before it appears in a submission:

- SAM.gov registration and the Disaster Response Registry listing (Stafford Act §307, "Tier-1").
- UEI and CAGE code.
- "Registered Small Business Concern" status.
- "Full Compliance / Attestation Filed" and "NIST SP 800-171 & CMMC Level 2 … Audit Passed."

A false attestation to the federal government carries serious liability. None of these should be submitted until someone with authority has confirmed it against the source record.
