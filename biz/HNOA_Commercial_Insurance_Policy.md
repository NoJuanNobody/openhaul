# Hired & Non-Owned Auto (HNOA) Commercial Insurance & Legal Policy
**Document Reference:** `OH-LEG-INS-2026-V1`  
**Underwriting Framework:** Dynamic Telematics-Triggered Commercial Surplus Lines Master Facility  
**Subject:** OpenHaul Independent Contractor Autonomy, HNOA Policy Primacy, and Worker Classification Defense  

---

## 1. Executive Summary & Policy Architecture

OpenHaul operates as an open-source decentralized logistics communications protocol and marketplace technology platform. It is neither a motor carrier nor an employer of drivers. Vehicles utilized across the OpenHaul network are owned, leased, or rented by independent contractor owner-operators ("Drivers").

To insulate the platform, shippers, and municipal/federal partners against catastrophic vehicular tort liability, OpenHaul deploys a **Dynamic Hired & Non-Owned Auto (HNOA) Master Policy**. Coverage is dynamically bound and triggered in real-time according to the immutable driver state-machine managed by the mobile application and verified by cryptographic signatures on the STMP protocol.

```
+-----------------------------------------------------------------------------------------+
|                               APP STATE TRANSITION LIFECYCLE                            |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [ STATE 1: IDLE ]                                                                      |
|  Driver Online, Searching Orders                                                        |
|  Insurance: Driver Personal Auto Policy (PAP) Primary                                   |
|  OpenHaul Exposure: ZERO ($0.00)                                                        |
|                                                                                         |
|          │ Accept Order Dispatch (STMP Order Cryptographic Signature)                   |
|          ▼                                                                              |
|  [ STATE 2: EN_ROUTE ]                                                                  |
|  Traveling to Shipper / Warehouse Pickup Node                                           |
|  Insurance: OpenHaul HNOA Primary Third-Party Liability ($1,000,000 CSL)                |
|  Driver PAP: excess to the Master Policy in State 2 and State 3, primary in State 1     |
|  [COUNSEL TO CONFIRM WITH BROKER]                                                       |
|                                                                                         |
|          │ BLE / UHF RFID Cryptographic Handshake (`zk-custody` Seal)                   |
|          ▼                                                                              |
|  [ STATE 3: IN_CUSTODY_RFID_VERIFIED ]                                                  |
|  Cargo Loaded, Transit to Destination Consignee                                         |
|  Insurance: OpenHaul HNOA Primary Liability ($1M) + Motor Truck Cargo ($250k)          |
|             + Physical Damage Contingent Collision/Comprehensive                        |
|                                                                                         |
|          │ Recipient Signature & Final Handshake Proof                                  |
|          ▼                                                                              |
|  [ BACK TO STATE 1: IDLE ]                                                              |
|  Reversion to Driver Personal Auto Policy (PAP)                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Dynamic 3-State Telematics Insurance Binding Matrix

| Parameter / Dimension | State 1: IDLE | State 2: EN_ROUTE | State 3: IN_CUSTODY_RFID_VERIFIED |
| :--- | :--- | :--- | :--- |
| **System Definition** | App active/online; driver viewing open freight bids; no dispatch accepted. | Driver accepted a binding dispatch contract; navigating to pickup facility. | Cargo scanned via BLE/RFID; ZK custody proof submitted; transit in progress. |
| **Primary Auto Liability** | **Driver Personal Auto Policy (PAP)** | **OpenHaul HNOA Master Policy** ($1,000,000 CSL) | **OpenHaul HNOA Master Policy** ($1,000,000 CSL) |
| **Secondary / Excess** | State minimum personal coverage | Driver PAP: excess to the Master Policy in State 2 and State 3, primary in State 1 [COUNSEL TO CONFIRM WITH BROKER] | Driver PAP: excess to the Master Policy in State 2 and State 3, primary in State 1 [COUNSEL TO CONFIRM WITH BROKER] |
| **Motor Truck Cargo (MTC)** | Excluded ($0) | Excluded ($0 - no cargo on board) | **OpenHaul Primary Cargo** ($250,000 per occurrence) |
| **Contingent Physical Damage** | Excluded | Actual Cash Value (ACV) subject to $1,000 deductible | ACV subject to $1,000 deductible |
| **Underwriting Premium Accrual** | $0.08 / hour standby pool reserve | $0.42 / hour active transit | $0.78 / hour active transit + cargo |
| **Audit Verification Proof** | Driver location heartbeat (low-frequency ping) | High-frequency GPS route telemetry hash | Cryptographic ZK-SNARK custody manifest + sensor proofs |

**Premium payment:** The Operator pays the accruing premiums at the rates above ($0.08, $0.42, and $0.78 per hour, by state). The premium is charged to the Operator's account. OpenHaul does not pay or subsidize any part of these premiums.

---

## 3. Worker Classification Defense & Independent Contractor (1099) Autonomy

OpenHaul's operating model is architected specifically to withstand scrutiny under state and federal worker classification tests, including California's strict "ABC" test (*Dynamex Operations West, Inc. v. Superior Court* / Cal. Labor Code § 2775), the federal Department of Labor (DOL) Economic Realities Test, and the Restatement (Second) of Agency common-law control test.

### 3.1 Overcoming the "ABC" Test

#### Prong A: Absence of Control
- **Freedom of Execution:** Drivers retain complete, unilateral autonomy over their schedules, work hours, and routes. Drivers select their own GPS navigation tools and driving techniques.
- **No Uniforms or Mandatory Branding:** Drivers are strictly prohibited from being compelled to display OpenHaul decals, uniforms, or vehicle wraps.
- **Unrestricted Dispatch Selection:** Drivers possess the unfettered right to accept, reject, bid on, or ignore any dispatch offer without punitive algorithmic de-prioritization or penalties.
- **Multi-App Parity:** Drivers may run competing rideshare, courier, and freight dispatch applications simultaneously with OpenHaul.

#### Prong B: Outside the Usual Course of the Hiring Entity's Business
- **Protocol Definition:** OpenHaul is legally and technically organized as a technology consortium maintaining open-source peer-to-peer messaging protocol software (`stmp-core`) and matching algorithms. OpenHaul owns no freight, leases no commercial vehicles, employs no dispatchers, and owns no physical cross-dock terminals.
- **Merchant of Record:** The commercial contract for carriage is formed directly between the Shipper/Consignor and the Independent Owner-Operator, with OpenHaul acting solely as a cryptographic communications facilitator and escrow settlement provider.

#### Prong C: Customarily Engaged in an Independently Established Trade
- **Entity Enablement:** OpenHaul requires all participating fleet operators to attest to operating an independent business enterprise (Sole Proprietorship, LLC, or S-Corp) with their own Commercial General Liability, DOT numbers (where applicable), or personal vehicle ownership.
- **Equipment Ownership:** Drivers provide 100% of their own tools, vehicles, smartphones, maintenance, and fuel. OpenHaul provides zero subsidies for capital equipment depreciation and pays none of the accruing HNOA premium, which the Operator pays as set out in §2.

---

## 4. Contractual Primacy & Dispute Resolution Terms

All driver onboarding agreements and platform terms of service mandate the following legal covenants:

### 4.1 Indemnification & Hold Harmless
```
"Operator agrees to defend, indemnify, and hold harmless [OPENHAUL LLC — legal name pending formation; COUNSEL TO CONFIRM], 
its contributors, and core maintainers against any third-party claims, liabilities, 
damages, or expenses arising from Operator's intentional misconduct or gross negligence (and not routine traffic violations), 
while operating in State 1 (IDLE) or 
outside the verified parameters of an active STMP manifest. Routine traffic violations, including citations, are not indemnifiable under this section. [COUNSEL TO CONFIRM]"
```

### 4.2 Telemetric Evidentiary Admissibility
The driver and shipper agree that:
1. OpenHaul will preserve, and will produce on lawful request, the cryptographic event logs generated by the OpenHaul application—including state transitions (`IDLE`, `EN_ROUTE`, `IN_CUSTODY_RFID_VERIFIED`), RFID custody handshakes, and GPS route hashes—which the parties intend to use for determining insurance policy activation, claim primacy, and liability allocation. This is a commitment to preserve and produce records only; no promise is made about whether any record is admissible in any proceeding. [COUNSEL TO CONFIRM]
2. In the event of a vehicular collision during State 2 or State 3, the HNOA insurer shall immediately assume primary defense of the Operator up to the $1,000,000 policy limit without reservation of rights based on worker classification status.

### 4.3 Mandatory Individual Arbitration & Class Action Waiver
All disputes concerning compensation, platform fees, classification, or contract terms are subject to binding individual arbitration administered by the American Arbitration Association (AAA) under its Commercial Arbitration Rules, with an explicit waiver of class and collective actions. Nothing in this agreement waives a non-waivable right to bring a representative action where such waiver is unenforceable under applicable state law. [COUNSEL TO CONFIRM STATE-BY-STATE]
