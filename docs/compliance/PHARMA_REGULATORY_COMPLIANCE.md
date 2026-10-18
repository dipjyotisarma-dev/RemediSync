# Pharmaceutical Regulatory Compliance & Patient Safety Specification

## 1. Statutory Regulatory Context
Pharmacy inventory software in India is subject to statutory regulations governed by the **Drugs and Cosmetics Act (1940)**, the **Drugs and Cosmetics Rules (1945)**, and subsequent amendments governing digital prescription management, batch traceability, and dangerous drug scheduling.

RemediSync embeds these compliance requirements directly into its schema, inventory workflows, and purchase order audit logs.

---

## 2. Drug Scheduling & Dispensing Compliance Matrix

Every medicine in RemediSync is assigned an immutable statutory schedule classification:

| Schedule Category | Clinical Scope in RemediSync | Statutory Legal Requirements | RemediSync Operational Rule |
| :--- | :--- | :--- | :--- |
| **Schedule H** | Most prescription drugs (e.g., Telmisartan, Metformin, Pantoprazole, Atorvastatin) | Must be sold only against a registered medical practitioner's prescription; records retained for 2 years. | Flagged in dispensing views as `PRESCRIPTION_REQUIRED`. Automated purchase orders retain 2-year audit trail. |
| **Schedule H1** | High-potency antibiotics, 3rd/4th gen cephalosporins, anti-TB agents (e.g., Augmentin 625, Azithromycin, Cefixime) | Separate Schedule H1 register must record patient name, prescriber details, drug name, batch number, and quantity dispensed. | System records batch numbers against all transactions. Flags sudden surges to prevent antimicrobial hoarding. |
| **Schedule X** | Psychotropic, habit-forming, and narcotic drugs | Triplicate copies of prescriptions; locked storage; separate monthly returns submitted to state drug controller. | Strict dual-authorization required for inventory adjustments. Stockout service level set to maximum. |
| **Non-Scheduled (OTC)** | Paracetamol, multivitamins, ORS, topical antiseptics, antacid liquids | May be sold over the counter without a prescription. | Standard replenishment optimization; dynamic promotion and bulk carton rounding. |

---

## 3. Cold-Chain Storage & Temperature Assurance

### 3.1 Scope of Cold-Chain Therapeutics
Certain critical therapeutics—specifically **Insulins** (e.g., Human Mixtard, Lantus, Novorapid), biological injectables, and specific ophthalmic solutions—lose potency and undergo protein denaturation if stored outside the statutory temperature range of **$2^\circ\text{C}$ to $8^\circ\text{C}$**.

### 3.2 RemediSync Cold-Chain Protocols
1. **Cold-Chain Flagging (`is_cold_chain = TRUE`):**
   - Cold-chain items are visually highlighted in red within all dashboard views and supplier purchase orders.
2. **Buffer Against Expedited Transit:**
   - Standard courier delivery or open-air two-wheeler runner pickup is strictly prohibited for cold-chain items.
   - The replenishment engine automatically enforces a minimum lead-time safety margin of **2 days** to account for cold-box packaging with calibrated gel ice packs.
3. **Quarantine on Power Failure:**
   - In case of backup generator failure at a branch, the inventory status of affected cold-chain batches can be transitioned to `QUARANTINED_PENDING_INSPECTION`, removing them from available dispensing stock.

---

## 4. Batch Lot Traceability & Near-Expiry Return Window

Under the Drugs and Cosmetics Rules, selling or stocking an expired medicine is a non-bailable offense that can result in immediate cancellation of a pharmacy retail license.

### 4.1 The 90-Day Distributor Return Rule
- **Commercial Agreement:** In Indian pharmaceutical distribution, authorized C&F (Clearing and Forwarding) agents and stockists guarantee 100% financial credit or product replacement for unsold stock **only if the return is formally lodged at least 90 days before the batch expiry date**.
- **The Financial Trap:** If a pharmacy retains stock until 89 days before expiry, the distributor is legally entitled to reject the return, forcing the pharmacy to absorb a 100% loss.

### 4.2 RemediSync Expiry Protection Engine
```
                  ┌────────────────────────────────────────────────────────┐
                  │                BATCH EXPIRATION CLOCK                  │
                  └───────────────────────────┬────────────────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
          Days to Expiry >= 90 Days                       Days to Expiry < 90 Days
                      │                                               │
             Predicted Sales > Stock?                     CRITICAL REGULATORY WINDOW
             ├── YES: Safe (FEFO Dispensing)                          │
             └── NO:  PREDICTIVE WRITE-OFF RISK                       ▼
                      (Run Clearance / Transfer)          IMMEDIATE STOCKIST RETURN ALERT
                                                          (Generate Debit Note for Credit)
```

1. **Automated Return Debit Note Generation:**
   When a batch enters the 90-to-105 day window with current stock exceeding forecasted sales, RemediSync generates a pre-formatted **Stockist Return Debit Note**.
2. **First-Expired, First-Out (FEFO) Enforcement:**
   Dispensing recommendations strictly order inventory by earliest expiration date, preventing floor clerks from mistakenly opening new lots while older lots expire on the shelf.

---

## 5. Audit Logging & Non-Repudiation

To ensure full compliance during state drug inspector audits:
- **Immutable Purchase Records:** Every approved purchase order stores the exact timestamp, approver user ID, calculated demand rationale, and supplier ID.
- **Inventory Discrepancy Audits:** Any manual override of stock levels requires an operator reason code (e.g., `DAMAGED_IN_TRANSIT`, `BREAKAGE`, `STATUTORY_SAMPLING`).
- **Data Retention:** All transactional telemetry and batch ledgers are archived for a minimum statutory duration of **5 years**.
