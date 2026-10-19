# 2. AI-Augmented Team

## 2.1 What the repo establishes

The financial model and bid kit name no roles and no headcount. They budget by function only:

| Budget line (Year 1) | Amount | Source |
|---|---|---|
| Core Engineering & ZK Rust Development | $920,000 | `biz/generate_financial_model.py` |
| Regional Operations & FEMA Desk | $450,000 | same |
| Protocol maintainers | note only, no figure | same |

The bid kit describes drivers as 1099 independent operators in "rotating driver pods," not employees. That is a legal choice, covered in §4.

Total Year 1 OpEx is $1,860,000 against a $2,450,000 seed.

## 2.2 Proposed composition (planning assumption, not a decision)

The roles below follow from the technical gaps in §1.5 and §1.6. They are a starting point for the owner to size, not a hiring plan.

| Role | Why it's needed now | Human lead | AI-augmented work |
|---|---|---|---|
| **Cryptography engineer** (ZK) | Replace the SHA-256 "proof" with a real circuit; define signature scheme | Required, senior | Draft circuits and tests with a coding model; a human owns soundness review |
| **Spatial/routing engineer** | Fix H3 distance; decide one matcher | Required | Generate test fixtures and property tests; human validates geometry |
| **Backend/platform engineer** | Make the 2 s loop run against real telemetry; infra on EKS | Required | Scaffold Helm and Terraform; human owns deploy approval |
| **Trust & safety / operations lead** | Driver vetting, disputes, cold-chain incidents | Required | Triage tickets, draft dispute summaries; human decides on driver status |
| **Insurance and compliance counsel** (outside) | HNOA coverage, 1099 classification, FEMA contracting | Outside firm | Summarize policy changes; counsel signs |
| **Government contracts lead** | SAM.gov, FAR, CMMC | Required before any bid | Draft capability statements; the human checks every attestation |
| **Growth and content lead** | Viral strategy in §3 | Required | Draft scripts and variants; human approves every public claim |

Rule for the whole team: **AI drafts, a named human approves anything that is shipped, published, filed, or signed.** This matters most for claims about security, insurance, government status, and real people.

## 2.3 Staffing sequence

1. **Before any pilot:** cryptography, spatial, and counsel. These close the claims that would otherwise be false in front of a regulator or a customer.
2. **Pilot (one metro):** add backend and trust & safety.
3. **Surge readiness:** add the FEMA desk and government contracts lead. Do not bid on federal work before the attestations in the bid kit are verified (see §4.6).

---

# 3. Viral Marketing Strategy

## 3.1 Channels in the current plan

| Channel | Tactic | Goal |
|---|---|---|
| TikTok, YouTube Shorts | 45–60 s POV reels | Driver waitlist, downloads |
| YouTube long-form | *The Drift: Miles to Go*, 12–18 min episodes | Loyalty, sponsorships |
| X, Substack | Engineering breakdowns | Contributors, GitHub stars |
| LinkedIn, GovTech | Case study on disaster logistics | Municipal MOUs, federal bids |
| Growth loops | #BuiltForOpenHaul van contest; "Proof-of-Haul" badges; hackathons on `stmp-core` | Retention, community |

## 3.2 Audiences

1. **Vanlife and Sprinter owner-operators.** The core driver supply.
2. **Open-source Rust and crypto engineers.** Contributors and credibility.
3. **Emergency management and municipal buyers.** Revenue.

## 3.3 World-building: *The Drift*

The pilot episode (`biz/the-drift-ep1.fountain`, "Episode 101 - Cold Chain") carries the product story:

- **Premise.** Leo Carter drives a 2021 Sprinter with pediatric insulin and whole blood through a storm on Big Sur's Highway 1. A fuse fails. He fixes it, and the cold chain holds.
- **Characters.** Leo Carter; Dr. Elena Vance at a Monterey County emergency clinic.
- **Lore.** The OpenHaul app, the STMP mesh, RFID custody, a ZK "CUSTODY UNBROKEN" stamp, and a $148.50 escrow payout.

The narrative is strong, and the story's details are the product's claims. That is the main risk, covered next.

## 3.4 Claims that must be fixed before publishing

Each item below was found in the marketing doc or the episode. None is safe to publish as written.

| Issue | Where | Why it matters | Fix |
|---|---|---|---|
| "ZK-proof" and "CUSTODY UNBROKEN" as verified custody | Episode, doc | The proof is a SHA-256 hash that anyone can forge (§1.3) | Show it as a planned feature, or make it real first |
| "$1,200–$1,800/day during surges" | Doc | No source; also drives driver recruitment, so it carries legal risk | Cite data or remove |
| "No middleman taking 60%" | Doc | Unsourced competitor claim | Remove or substantiate |
| Dramatized storm rescue ("60 kids need insulin") shown as a real POV | Reels | Viewers may read it as a real event | Label as fiction and disclose AI generation |
| FEMA tents, "FEMA dispatch queues," federal contracting | Reels, doc | Implies an endorsement or relationship that is not established | Remove until the contract exists |
| Voice cloning of named characters | Plan | No consent source stated | Use licensed or original voices |
| Real brands: Mercedes Sprinter, Norcold, Katrina | Episode, reels | Trademark and endorsement risk | Counsel review |
| Internal inconsistencies: "four hours" vs "six hours" ago; "sixty families" vs "sixty vials" vs "sixty kids" | Doc vs episode | Reduces credibility with engineering audiences | Pick one version |

## 3.5 Disclosure rule

Any reel that shows AI-generated people, scenes, or voices must carry the platform's AI-content label, and the caption must say the story is fiction. Counsel should confirm the FTC endorsement rules for any driver who is paid to appear.

## 3.6 Sequencing

1. Publish only the engineering and product content that is already true (§1.5).
2. Hold the emergency-response storyline until the FEMA desk exists and the claims in §3.4 are resolved.
3. Use the driver waitlist as the first measurable goal, and measure it against real onboarding, not views.
