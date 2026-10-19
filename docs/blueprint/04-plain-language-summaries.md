# OpenHaul in Plain Language

This explains the business documents without legal or finance jargon. It is a summary of planning material, not legal, tax, or investment advice. Where the documents disagree or a claim is unproven, this says so.

## What OpenHaul is

OpenHaul is software that matches small parcel and freight jobs to independent drivers who use their own vehicles. The project also includes a matching engine written in Rust, a dispatch loop that runs every 2 seconds, and a custody-tracking layer. Most of this works in simulation. Real-world use has not started.

## What works today

- The matching engine runs and its tests pass.
- The dispatch loop runs in simulation.
- The custody layer tracks each job through its stages (idle, en route, in custody).

## What is not true yet

These are the things the team must fix before showing anything to customers, drivers, or government:

- **"ZK proof" is not a real zero-knowledge proof.** The current "proof" is a standard hash that anyone can recreate. The team has chosen to build a real one with the Groth16 system, but that is not finished.
- **The driver signature check is a placeholder.** It accepts any signature of 8 or more characters, so it verifies nothing.
- **The distance math is wrong.** The code treats map-cell IDs as plain numbers and subtracts them. That does not measure distance.
- **The Rust and Python matchers are separate.** The decision is that Rust is the single source of truth, and Python will call it. That change is not finished.

## Taxes and worker classification

**The question:** Are drivers independent contractors (1099) or employees?

**Why it matters:** If a regulator decides drivers are employees, OpenHaul could owe back payroll taxes, overtime, and penalties. California uses a strict three-part test (the "ABC test"). Other states and the federal government use different tests. The business documents argue that drivers control their own schedules, that OpenHaul is only a platform, and that drivers run their own businesses.

**Where the documents conflict:**

1. **OpenHaul pays for insurance and settles payments on every job.** That looks like it is acting as the carrier, not a neutral platform. This contradicts the platform argument.
2. **OpenHaul requires location tracking and scanning on certain jobs.** This looks like control over how work is done, which weakens the "drivers control their work" argument.
3. **The insurance premiums are charged to the driver.** The documents say OpenHaul "pays none" of them, but they do not say who pays in every case. This must be settled, because paying part of a driver's cost could be treated as a subsidy.

**What to do first:** A lawyer in each state where OpenHaul operates should review the driver agreement. The business must pick one clear answer to "who is the carrier" and make the contracts and insurance match it.

## Insurance

**What the policy says:** Coverage depends on what the driver is doing.

- **Idle (app on, no job accepted):** The driver's own personal auto policy applies. OpenHaul's exposure is zero.
- **Driving to pick up a job:** OpenHaul's $1,000,000 liability policy applies. The driver's personal policy is secondary, which the documents mark as needing broker confirmation.
- **Carrying cargo:** Cargo coverage of $250,000 per incident applies. Physical damage to the vehicle has a $1,000 deductible.

**Costs:** The operator pays an hourly premium: about $0.08 per hour when idle, $0.42 per hour en route, and $0.78 per hour with cargo.

**Problems to fix:**

- The "OpenHaul Consortium" is not a legal company, so it cannot be a named insured. A real company must be formed first.
- One indemnity clause makes drivers cover OpenHaul for "routine traffic violations." Read literally, a driver would owe OpenHaul for an ordinary speeding ticket. The clause should be limited to intentional or grossly negligent acts.
- Whether the policy actually works the way the state tables describe must be confirmed by a licensed insurance broker in every state.

**Other legal flags for counsel:**

- The clause that waives class-action and representative claims is likely unenforceable as written in California. Do not rely on it.
- A contract cannot make the company's logs automatically admissible as evidence in court. The contract only promises to keep and produce them.
- Carrying packages, medicine, or blood in personal vehicles may trigger motor-carrier, hazardous-materials, and cold-chain rules that the documents do not cover.

## Governance

**Who decides what:**

- **Core maintainers (9 people):** They control code releases, the treasury, and a 5-of-9 signing group for key settings.
- **Security auditors:** They can veto any change to the cryptography. Their veto cannot be overridden.
- **Contributors and a Driver Senate:** They can propose changes and elect representatives, but the charter does not give the Driver Senate a binding vote.

**How a change is approved:** A proposal is discussed for at least 14 days, reviewed by auditors if it touches cryptography, then approved by at least 6 of 9 maintainers, then tested before release.

**Money terms, in plain words:** Drivers keep 82% of each job and OpenHaul keeps 18%, according to the bid kit. The charter, however, says 22%. The financial model also uses 22%. **This is an open conflict.** One number must be chosen and used everywhere before anything is published. This summary uses 18% because that is the rate in the bid kit and the driver-facing materials.

**Drivers' protection:** Every payment or custody dispute is logged with a timestamp and can never be overwritten. Drivers can request a copy of their own entries.

## Compliance and government work

- **Government status is unverified.** The bid kit claims SAM.gov registration, a disaster-response listing, small-business status, and security-audit passes. None of these has been checked against an official record. Making a false statement in a federal bid is a serious legal risk, so none of these should be submitted until someone with authority confirms each one.
- **Disaster work has its own rules.** Federal disaster contracting follows different laws from commercial work. The business does not currently have a government relationship, and the marketing should not imply that it does.

## Marketing claims to fix before posting

These claims appear in the marketing plan or the pilot episode and are not safe to publish as written:

| Claim | Problem | Fix |
|---|---|---|
| "ZK-verified custody" | The proof is a hash, not a real proof | Call it a planned feature, or build it first |
| "$1,200–$1,800 a day during surges" | No source. It also drives recruiting, which adds legal risk | Cite data or remove |
| "No middleman taking 60%" | Unsourced competitor claim | Remove |
| Dramatized storm rescue shown as real | Viewers may believe it happened | Label as fiction and disclose AI generation |
| FEMA tents, federal contracting | Implies a relationship that does not exist | Remove until a contract exists |
| Real brands (Mercedes Sprinter, Norcold, Katrina) | Trademark and endorsement risk | Counsel review |

Any post that shows AI-generated people, scenes, or voices must say so, and must say the story is fiction.

## The financial model

**The model's assumptions (as written in the generator):**

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Markets | 1 | 5 | 15 |
| Drivers | 750 | 3,100 | 8,800 |
| Completed jobs | 800,000 | 3,150,000 | 8,500,000 |
| Average job value (assumed) | $28 | $28 | $28 |
| Operating costs | $1.86M | $5.72M | $12.1M |
| EBITDA (profit before interest, taxes, depreciation, amortization) | about $1.5M | about $7.5M | about $23.5M |

**Two things to know before quoting these numbers:**

1. **The take rate is 22% in the model but 18% in the bid kit and marketing.** At 18%, the model's Year 3 EBITDA falls from about $23.5M to about $14M, and Year 1 shrinks to a profit of about $0.6M. Use the 18% figure unless the owner decides otherwise.
2. **The inputs are assumptions, not measured results.** The $28 average job value is labelled a benchmark, but no source is cited. The job volumes are targets. The model was built to show what a plan looks like under those assumptions, not to predict results.

**Funding:** The model plans a $2.45M seed round, split as: $950K engineering, $400K insurance deposit, $300K government-contract work, $250K legal defense, $350K first-market launch, and $200K reserve. The plan is to reach profitability within about 18 months.

## Owner decisions still open

1. Which real cryptography system to build, and the budget for an audit.
2. The single source of truth for matching (decided: Rust).
3. The corrected distance calculation.
4. How drivers and readers are identified and signed.
5. Who is the carrier: the platform, the shipper, or the operator.
6. Who pays each insurance premium.
7. Which legal company to form as the insured.
8. Which marketing claims to remove or prove.
9. Whether the take rate is 18% or 22%.
