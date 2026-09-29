"""
Enterprise Configuration & Domain Parameters for RemediSync.

Defines the authentic operational parameters for:
- 4 Assam retail pharmacy branches (Kamakhya Gate, Dharapur, Azara, Rani Gate)
- 30 Guwahati medicine stockists & distributors (Express Pickup vs. Direct Delivery)
- Authentic Indian pharmaceutical SKU master catalog (~120 core medicines)
- Simulation timeframe and revenue target parameters.
"""

from typing import Dict, List, Any
from datetime import date

# ---------------------------------------------------------------------------
# 1. SIMULATION HORIZON & TARGETS
# ---------------------------------------------------------------------------
SIMULATION_START_DATE: date = date(2025, 1, 1)
SIMULATION_END_DATE: date = date(2026, 9, 30)  # 638 calendar days

# Network daily revenue range in INR
TARGET_DAILY_REVENUE_MIN: float = 180000.0   # ~45k per branch on slow days
TARGET_DAILY_REVENUE_MAX: float = 280000.0   # ~70k per branch on peak days

# ---------------------------------------------------------------------------
# 2. OPERATIONAL PHARMACY BRANCHES (ASSAM NETWORK)
# ---------------------------------------------------------------------------
BRANCHES: List[Dict[str, Any]] = [
    {
        "branch_id": "BR001",
        "branch_name": "Kamakhya Gate Branch",
        "location_type": "TRANSIT_HUB",
        "address": "Kamakhya Gate, Maligaon, Guwahati, Assam 781011",
        "daily_target_revenue": 58000.0,
        "acute_factor": 1.25,    # High emergency, acute, pain relief & OTC sales
        "chronic_factor": 0.85,
        "is_active": True
    },
    {
        "branch_id": "BR002",
        "branch_name": "Dharapur Branch",
        "location_type": "SUBURBAN_RESIDENTIAL",
        "address": "Dharapur Chariali, Guwahati, Assam 781017",
        "daily_target_revenue": 52000.0,
        "acute_factor": 0.90,
        "chronic_factor": 1.25,  # Established family residential, high chronic refills
        "is_active": True
    },
    {
        "branch_id": "BR003",
        "branch_name": "Azara Branch",
        "location_type": "HOSPITAL_PERIMETER",
        "address": "Airport Road, Azara, Guwahati, Assam 781017",
        "daily_target_revenue": 64000.0,
        "acute_factor": 1.20,    # High velocity antibiotics, surgicals & general acute
        "chronic_factor": 1.10,
        "is_active": True
    },
    {
        "branch_id": "BR004",
        "branch_name": "Rani Gate Branch",
        "location_type": "RESIDENTIAL_EDGE",
        "address": "Rani Gate, Rani, Kamrup, Assam 781131",
        "daily_target_revenue": 48000.0,
        "acute_factor": 0.95,    # Seasonal infections, pediatric, and essential OTC
        "chronic_factor": 1.00,
        "is_active": True
    }
]

# ---------------------------------------------------------------------------
# 3. PHARMACEUTICAL STOCKISTS & DISTRIBUTORS (GUWAHATI REGION)
# ---------------------------------------------------------------------------
# 20 Express Evening Pickup (1-Day turnaround) + 10 Direct Delivery (2-3 Days)
SUPPLIERS: List[Dict[str, Any]] = [
    # --- 20 EXPRESS PICKUP STOCKISTS (Lead time = 1 day, ordered 10 AM, picked up 6 PM) ---
    {"supplier_id": "SUP001", "supplier_name": "Guwahati Drug House", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP002", "supplier_name": "Brahmaputra Healthcare Agencies", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP003", "supplier_name": "Pragjyotish Pharma Stockists", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP004", "supplier_name": "Kamakhya Medico Distributors", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP005", "supplier_name": "Assam Medical Syndicate", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP006", "supplier_name": "North East Pharma Traders", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP007", "supplier_name": "Panbazar Drug Centre", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP008", "supplier_name": "Paltan Bazar Medical Corp", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP009", "supplier_name": "Maligaon Wholesale Pharmaceuticals", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP010", "supplier_name": "Suraksha Healthcare Stockists", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP011", "supplier_name": "Eastern Drug Distributors", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP012", "supplier_name": "Apex Pharma Logistics", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP013", "supplier_name": "City Drug Agency Guwahati", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP014", "supplier_name": "Arogya Medical Wholesalers", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP015", "supplier_name": "Jalukbari Pharma Suppliers", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP016", "supplier_name": "Dispur Medico Trade Links", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP017", "supplier_name": "Shree Ganesh Pharma Agency", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP018", "supplier_name": "Aditya Drug Corporation", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP019", "supplier_name": "United Pharma Stockists", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP020", "supplier_name": "Heritage Medical Distributors", "fulfillment_type": "EXPRESS_PICKUP", "lead_time_days": 1, "city": "Guwahati", "is_active": True},

    # --- 10 DISTRIBUTOR DELIVERY STOCKISTS (Lead time = 2 to 3 days) ---
    {"supplier_id": "SUP021", "supplier_name": "Sun Pharma Regional C&F Assam", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 2, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP022", "supplier_name": "Cipla Depot Assam", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 3, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP023", "supplier_name": "Alkem Laboratories Regional Depot", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 2, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP024", "supplier_name": "Mankind Pharma Central Stockist", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 3, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP025", "supplier_name": "Abbott Healthcare Distribution", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 2, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP026", "supplier_name": "Torrent Pharma Guwahati Depot", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 3, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP027", "supplier_name": "Dr. Reddy's Regional Agency", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 2, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP028", "supplier_name": "Zydus Healthcare Stockists", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 3, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP029", "supplier_name": "Lupin Pharmaceuticals C&F", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 2, "city": "Guwahati", "is_active": True},
    {"supplier_id": "SUP030", "supplier_name": "Glenmark Pharmaceuticals Depot", "fulfillment_type": "DISTRIBUTOR_DELIVERY", "lead_time_days": 3, "city": "Guwahati", "is_active": True},
]

# ---------------------------------------------------------------------------
# 4. AUTHENTIC INDIAN PHARMACEUTICAL MASTER CATALOG (120 CORE SKUS)
# ---------------------------------------------------------------------------
# Includes brand name, chemical salt, strength, dosage form, manufacturer,
# MRP (₹), PTR wholesale cost (₹), packaging, units_per_pack, and velocity profile.
MEDICINES: List[Dict[str, Any]] = [
    # === ANTIPYRETICS & ANALGESICS (High-velocity, essential fever & pain) ===
    {
        "medicine_id": "MED001", "brand_name": "Dolo 650", "generic_salt": "Paracetamol", "strength": "650mg",
        "dosage_form": "Tablet", "category": "Antipyretic", "manufacturer": "Micro Labs Ltd",
        "mrp": 33.50, "cost_price": 26.80, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP001", "base_daily_demand": 28.0
    },
    {
        "medicine_id": "MED002", "brand_name": "Calpol 500", "generic_salt": "Paracetamol", "strength": "500mg",
        "dosage_form": "Tablet", "category": "Antipyretic", "manufacturer": "GSK India",
        "mrp": 22.00, "cost_price": 17.60, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP002", "base_daily_demand": 18.0
    },
    {
        "medicine_id": "MED003", "brand_name": "Crocin 650", "generic_salt": "Paracetamol", "strength": "650mg",
        "dosage_form": "Tablet", "category": "Antipyretic", "manufacturer": "GSK India",
        "mrp": 34.00, "cost_price": 27.20, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP001", "base_daily_demand": 12.0
    },
    {
        "medicine_id": "MED004", "brand_name": "Pacimol 650", "generic_salt": "Paracetamol", "strength": "650mg",
        "dosage_form": "Tablet", "category": "Antipyretic", "manufacturer": "Ipca Laboratories",
        "mrp": 31.00, "cost_price": 24.80, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP003", "base_daily_demand": 9.0
    },
    {
        "medicine_id": "MED005", "brand_name": "Combiflam", "generic_salt": "Ibuprofen + Paracetamol", "strength": "400mg+325mg",
        "dosage_form": "Tablet", "category": "Analgesic", "manufacturer": "Sanofi India",
        "mrp": 45.00, "cost_price": 36.00, "pack_size": "20 Tablets", "units_per_pack": 20,
        "velocity_class": "FAST", "primary_supplier_id": "SUP004", "base_daily_demand": 22.0
    },
    {
        "medicine_id": "MED006", "brand_name": "Meftal-Spas", "generic_salt": "Mefenamic Acid + Dicyclomine", "strength": "250mg+10mg",
        "dosage_form": "Tablet", "category": "Antispasmodic", "manufacturer": "Blue Cross Labs",
        "mrp": 52.00, "cost_price": 41.60, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP005", "base_daily_demand": 15.0
    },
    {
        "medicine_id": "MED007", "brand_name": "Ultracet", "generic_salt": "Tramadol + Paracetamol", "strength": "37.5mg+325mg",
        "dosage_form": "Tablet", "category": "Analgesic", "manufacturer": "Janssen / J&J",
        "mrp": 215.00, "cost_price": 172.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "SLOW", "primary_supplier_id": "SUP006", "base_daily_demand": 3.0
    },
    {
        "medicine_id": "MED008", "brand_name": "Sumo", "generic_salt": "Nimesulide + Paracetamol", "strength": "100mg+325mg",
        "dosage_form": "Tablet", "category": "Analgesic", "manufacturer": "Alkem Laboratories",
        "mrp": 88.00, "cost_price": 70.40, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP023", "base_daily_demand": 10.0
    },

    # === GASTROINTESTINAL & ANTACIDS (High-frequency daily essentials) ===
    {
        "medicine_id": "MED009", "brand_name": "Pan-D", "generic_salt": "Pantoprazole + Domperidone", "strength": "40mg+30mg",
        "dosage_form": "Capsule", "category": "Gastrointestinal", "manufacturer": "Alkem Laboratories",
        "mrp": 199.00, "cost_price": 159.20, "pack_size": "15 Capsules", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP023", "base_daily_demand": 26.0
    },
    {
        "medicine_id": "MED010", "brand_name": "Pan 40", "generic_salt": "Pantoprazole", "strength": "40mg",
        "dosage_form": "Tablet", "category": "Gastrointestinal", "manufacturer": "Alkem Laboratories",
        "mrp": 155.00, "cost_price": 124.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP023", "base_daily_demand": 18.0
    },
    {
        "medicine_id": "MED011", "brand_name": "Pantocid 40", "generic_salt": "Pantoprazole", "strength": "40mg",
        "dosage_form": "Tablet", "category": "Gastrointestinal", "manufacturer": "Sun Pharma",
        "mrp": 162.00, "cost_price": 129.60, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP021", "base_daily_demand": 16.0
    },
    {
        "medicine_id": "MED012", "brand_name": "Pantocid DSR", "generic_salt": "Pantoprazole + Domperidone SR", "strength": "40mg+30mg",
        "dosage_form": "Capsule", "category": "Gastrointestinal", "manufacturer": "Sun Pharma",
        "mrp": 218.00, "cost_price": 174.40, "pack_size": "15 Capsules", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP021", "base_daily_demand": 20.0
    },
    {
        "medicine_id": "MED013", "brand_name": "Omez 20", "generic_salt": "Omeprazole", "strength": "20mg",
        "dosage_form": "Capsule", "category": "Gastrointestinal", "manufacturer": "Dr. Reddy's",
        "mrp": 62.00, "cost_price": 49.60, "pack_size": "20 Capsules", "units_per_pack": 20,
        "velocity_class": "FAST", "primary_supplier_id": "SUP027", "base_daily_demand": 19.0
    },
    {
        "medicine_id": "MED014", "brand_name": "Omez-D", "generic_salt": "Omeprazole + Domperidone", "strength": "20mg+10mg",
        "dosage_form": "Capsule", "category": "Gastrointestinal", "manufacturer": "Dr. Reddy's",
        "mrp": 124.00, "cost_price": 99.20, "pack_size": "15 Capsules", "units_per_pack": 15,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP027", "base_daily_demand": 11.0
    },
    {
        "medicine_id": "MED015", "brand_name": "Rantac 150", "generic_salt": "Ranitidine", "strength": "150mg",
        "dosage_form": "Tablet", "category": "Gastrointestinal", "manufacturer": "J.B. Chemicals",
        "mrp": 42.00, "cost_price": 33.60, "pack_size": "30 Tablets", "units_per_pack": 30,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP007", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED016", "brand_name": "Rabekind-DSR", "generic_salt": "Rabeprazole + Domperidone", "strength": "20mg+30mg",
        "dosage_form": "Capsule", "category": "Gastrointestinal", "manufacturer": "Mankind Pharma",
        "mrp": 140.00, "cost_price": 112.00, "pack_size": "10 Capsules", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP024", "base_daily_demand": 16.0
    },
    {
        "medicine_id": "MED017", "brand_name": "Gelusil MPS Mint", "generic_salt": "Magnesium Hydroxide + Aluminium Hydroxide", "strength": "200ml",
        "dosage_form": "Syrup", "category": "Gastrointestinal", "manufacturer": "Pfizer India",
        "mrp": 135.00, "cost_price": 108.00, "pack_size": "200ml Bottle", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP008", "base_daily_demand": 7.0
    },
    {
        "medicine_id": "MED018", "brand_name": "Digene Mint Flavour", "generic_salt": "Dried Aluminium Hydroxide + Magnesium Aluminium", "strength": "200ml",
        "dosage_form": "Syrup", "category": "Gastrointestinal", "manufacturer": "Abbott India",
        "mrp": 145.00, "cost_price": 116.00, "pack_size": "200ml Bottle", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP025", "base_daily_demand": 8.0
    },

    # === ANTIBIOTICS & ANTIMICROBIALS (High prescription volume, acute infections) ===
    {
        "medicine_id": "MED019", "brand_name": "Augmentin 625 Duo", "generic_salt": "Amoxicillin + Clavulanic Acid", "strength": "625mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "GSK India",
        "mrp": 223.00, "cost_price": 178.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP002", "base_daily_demand": 21.0
    },
    {
        "medicine_id": "MED020", "brand_name": "Moxikind-CV 625", "generic_salt": "Amoxicillin + Clavulanic Acid", "strength": "625mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Mankind Pharma",
        "mrp": 175.00, "cost_price": 140.00, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP024", "base_daily_demand": 17.0
    },
    {
        "medicine_id": "MED021", "brand_name": "Azithral 500", "generic_salt": "Azithromycin", "strength": "500mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Alembic Pharma",
        "mrp": 132.00, "cost_price": 105.60, "pack_size": "5 Tablets", "units_per_pack": 5,
        "velocity_class": "FAST", "primary_supplier_id": "SUP009", "base_daily_demand": 18.0
    },
    {
        "medicine_id": "MED022", "brand_name": "Azee 500", "generic_salt": "Azithromycin", "strength": "500mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Cipla",
        "mrp": 130.00, "cost_price": 104.00, "pack_size": "5 Tablets", "units_per_pack": 5,
        "velocity_class": "FAST", "primary_supplier_id": "SUP022", "base_daily_demand": 15.0
    },
    {
        "medicine_id": "MED023", "brand_name": "Taxim-O 200", "generic_salt": "Cefixime", "strength": "200mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Alkem Laboratories",
        "mrp": 115.00, "cost_price": 92.00, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP023", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED024", "brand_name": "Cefix 200", "generic_salt": "Cefixime", "strength": "200mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Cipla",
        "mrp": 112.00, "cost_price": 89.60, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP022", "base_daily_demand": 10.0
    },
    {
        "medicine_id": "MED025", "brand_name": "Mahacef 200", "generic_salt": "Cefixime", "strength": "200mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Mankind Pharma",
        "mrp": 108.00, "cost_price": 86.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP024", "base_daily_demand": 9.0
    },
    {
        "medicine_id": "MED026", "brand_name": "Monocef-O 200", "generic_salt": "Cefpodoxime Proxetil", "strength": "200mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Aristo Pharma",
        "mrp": 178.00, "cost_price": 142.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP010", "base_daily_demand": 8.0
    },
    {
        "medicine_id": "MED027", "brand_name": "Ciplox 500", "generic_salt": "Ciprofloxacin", "strength": "500mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Cipla",
        "mrp": 48.00, "cost_price": 38.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP022", "base_daily_demand": 12.0
    },
    {
        "medicine_id": "MED028", "brand_name": "Norflox-TZ", "generic_salt": "Norfloxacin + Tinidazole", "strength": "400mg+600mg",
        "dosage_form": "Tablet", "category": "Antibiotic", "manufacturer": "Cipla",
        "mrp": 96.00, "cost_price": 76.80, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP022", "base_daily_demand": 14.0
    },

    # === ANTIDIABETICS (Chronic maintenance, 1st-7th month payday refill spikes) ===
    {
        "medicine_id": "MED029", "brand_name": "Glycomet 500 SR", "generic_salt": "Metformin", "strength": "500mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "USV Ltd",
        "mrp": 48.00, "cost_price": 38.40, "pack_size": "20 Tablets", "units_per_pack": 20,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP003", "base_daily_demand": 24.0
    },
    {
        "medicine_id": "MED030", "brand_name": "Glycomet 1g SR", "generic_salt": "Metformin", "strength": "1000mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "USV Ltd",
        "mrp": 68.00, "cost_price": 54.40, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP003", "base_daily_demand": 16.0
    },
    {
        "medicine_id": "MED031", "brand_name": "Glycomet-GP 1", "generic_salt": "Glimepiride + Metformin", "strength": "1mg+500mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "USV Ltd",
        "mrp": 128.00, "cost_price": 102.40, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP003", "base_daily_demand": 18.0
    },
    {
        "medicine_id": "MED032", "brand_name": "Glycomet-GP 2", "generic_salt": "Glimepiride + Metformin", "strength": "2mg+500mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "USV Ltd",
        "mrp": 156.00, "cost_price": 124.80, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP003", "base_daily_demand": 20.0
    },
    {
        "medicine_id": "MED033", "brand_name": "Janumet 50/500", "generic_salt": "Sitagliptin + Metformin", "strength": "50mg+500mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "MSD Pharma",
        "mrp": 380.00, "cost_price": 304.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP011", "base_daily_demand": 7.0
    },
    {
        "medicine_id": "MED034", "brand_name": "Galvus Met 50/500", "generic_salt": "Vildagliptin + Metformin", "strength": "50mg+500mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "Novartis India",
        "mrp": 320.00, "cost_price": 256.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP012", "base_daily_demand": 9.0
    },
    {
        "medicine_id": "MED035", "brand_name": "Teneliglip-M 500", "generic_salt": "Teneligliptin + Metformin", "strength": "20mg+500mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "Mankind Pharma",
        "mrp": 120.00, "cost_price": 96.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP024", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED036", "brand_name": "Amaryl 1mg", "generic_salt": "Glimepiride", "strength": "1mg",
        "dosage_form": "Tablet", "category": "Antidiabetic", "manufacturer": "Sanofi India",
        "mrp": 84.00, "cost_price": 67.20, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP004", "base_daily_demand": 10.0
    },

    # === CARDIOVASCULAR & ANTIHYPERTENSIVES (Chronic life-saving maintenance) ===
    {
        "medicine_id": "MED037", "brand_name": "Telma 40", "generic_salt": "Telmisartan", "strength": "40mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Glenmark Pharma",
        "mrp": 218.00, "cost_price": 174.40, "pack_size": "30 Tablets", "units_per_pack": 30,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP030", "base_daily_demand": 22.0
    },
    {
        "medicine_id": "MED038", "brand_name": "Telma-H", "generic_salt": "Telmisartan + Hydrochlorothiazide", "strength": "40mg+12.5mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Glenmark Pharma",
        "mrp": 265.00, "cost_price": 212.00, "pack_size": "30 Tablets", "units_per_pack": 30,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP030", "base_daily_demand": 15.0
    },
    {
        "medicine_id": "MED039", "brand_name": "Telmikind 40", "generic_salt": "Telmisartan", "strength": "40mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Mankind Pharma",
        "mrp": 62.00, "cost_price": 49.60, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP024", "base_daily_demand": 16.0
    },
    {
        "medicine_id": "MED040", "brand_name": "Amlong 5", "generic_salt": "Amlodipine", "strength": "5mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Micro Labs Ltd",
        "mrp": 42.00, "cost_price": 33.60, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP001", "base_daily_demand": 17.0
    },
    {
        "medicine_id": "MED041", "brand_name": "Amlopres-AT", "generic_salt": "Amlodipine + Atenolol", "strength": "5mg+50mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Cipla",
        "mrp": 145.00, "cost_price": 116.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP022", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED042", "brand_name": "Concor 5", "generic_salt": "Bisoprolol", "strength": "5mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Merck / Procter & Gamble",
        "mrp": 138.00, "cost_price": 110.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP013", "base_daily_demand": 8.0
    },
    {
        "medicine_id": "MED043", "brand_name": "Atorva 10", "generic_salt": "Atorvastatin", "strength": "10mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Zydus Healthcare",
        "mrp": 125.00, "cost_price": 100.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP028", "base_daily_demand": 18.0
    },
    {
        "medicine_id": "MED044", "brand_name": "Atorva 20", "generic_salt": "Atorvastatin", "strength": "20mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Zydus Healthcare",
        "mrp": 210.00, "cost_price": 168.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP028", "base_daily_demand": 13.0
    },
    {
        "medicine_id": "MED045", "brand_name": "Rosuvas 10", "generic_salt": "Rosuvastatin", "strength": "10mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "Sun Pharma",
        "mrp": 242.00, "cost_price": 193.60, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP021", "base_daily_demand": 12.0
    },
    {
        "medicine_id": "MED046", "brand_name": "Ecosprin 75", "generic_salt": "Aspirin", "strength": "75mg",
        "dosage_form": "Tablet", "category": "Cardiovascular", "manufacturer": "USV Ltd",
        "mrp": 6.50, "cost_price": 5.20, "pack_size": "14 Tablets", "units_per_pack": 14,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP003", "base_daily_demand": 25.0
    },
    {
        "medicine_id": "MED047", "brand_name": "Ecosprin-AV 75", "generic_salt": "Aspirin + Atorvastatin", "strength": "75mg+10mg",
        "dosage_form": "Capsule", "category": "Cardiovascular", "manufacturer": "USV Ltd",
        "mrp": 55.00, "cost_price": 44.00, "pack_size": "15 Capsules", "units_per_pack": 15,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP003", "base_daily_demand": 16.0
    },

    # === RESPIRATORY, COUGH & ANTI-ALLERGIC (Seasonal surges in winter and monsoon) ===
    {
        "medicine_id": "MED048", "brand_name": "Ascoril D Plus", "generic_salt": "Dextromethorphan + Phenylephrine", "strength": "100ml",
        "dosage_form": "Syrup", "category": "Respiratory", "manufacturer": "Glenmark Pharma",
        "mrp": 128.00, "cost_price": 102.40, "pack_size": "100ml Bottle", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP030", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED049", "brand_name": "Ascoril LS", "generic_salt": "Levosalbutamol + Ambroxol + Guaiphenesin", "strength": "100ml",
        "dosage_form": "Syrup", "category": "Respiratory", "manufacturer": "Glenmark Pharma",
        "mrp": 118.00, "cost_price": 94.40, "pack_size": "100ml Bottle", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP030", "base_daily_demand": 16.0
    },
    {
        "medicine_id": "MED050", "brand_name": "Grilinctus", "generic_salt": "Dextromethorphan + Chlorpheniramine", "strength": "100ml",
        "dosage_form": "Syrup", "category": "Respiratory", "manufacturer": "Franco-Indian Pharma",
        "mrp": 122.00, "cost_price": 97.60, "pack_size": "100ml Bottle", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP014", "base_daily_demand": 18.0
    },
    {
        "medicine_id": "MED051", "brand_name": "Benadryl Cough Formula", "generic_salt": "Diphenhydramine + Ammonium Chloride", "strength": "100ml",
        "dosage_form": "Syrup", "category": "Respiratory", "manufacturer": "Johnson & Johnson",
        "mrp": 135.00, "cost_price": 108.00, "pack_size": "100ml Bottle", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP006", "base_daily_demand": 12.0
    },
    {
        "medicine_id": "MED052", "brand_name": "Cheston Cold", "generic_salt": "Cetirizine + Paracetamol + Phenylephrine", "strength": "5mg+325mg+10mg",
        "dosage_form": "Tablet", "category": "Respiratory", "manufacturer": "Cipla",
        "mrp": 48.00, "cost_price": 38.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP022", "base_daily_demand": 20.0
    },
    {
        "medicine_id": "MED053", "brand_name": "Montair-LC", "generic_salt": "Montelukast + Levocetirizine", "strength": "10mg+5mg",
        "dosage_form": "Tablet", "category": "Respiratory", "manufacturer": "Cipla",
        "mrp": 215.00, "cost_price": 172.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP022", "base_daily_demand": 17.0
    },
    {
        "medicine_id": "MED054", "brand_name": "Montek-LC", "generic_salt": "Montelukast + Levocetirizine", "strength": "10mg+5mg",
        "dosage_form": "Tablet", "category": "Respiratory", "manufacturer": "Sun Pharma",
        "mrp": 210.00, "cost_price": 168.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP021", "base_daily_demand": 15.0
    },
    {
        "medicine_id": "MED055", "brand_name": "Allegra 120", "generic_salt": "Fexofenadine", "strength": "120mg",
        "dosage_form": "Tablet", "category": "Antiallergic", "manufacturer": "Sanofi India",
        "mrp": 212.00, "cost_price": 169.60, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP004", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED056", "brand_name": "Cetzine 10", "generic_salt": "Cetirizine", "strength": "10mg",
        "dosage_form": "Tablet", "category": "Antiallergic", "manufacturer": "Dr. Reddy's",
        "mrp": 24.00, "cost_price": 19.20, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP027", "base_daily_demand": 22.0
    },
    {
        "medicine_id": "MED057", "brand_name": "Levocet 5", "generic_salt": "Levocetirizine", "strength": "5mg",
        "dosage_form": "Tablet", "category": "Antiallergic", "manufacturer": "Hetero Healthcare",
        "mrp": 48.00, "cost_price": 38.40, "pack_size": "10 Tablets", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP015", "base_daily_demand": 16.0
    },

    # === VITAMINS, MINERALS & NUTRACEUTICALS (Daily family staples) ===
    {
        "medicine_id": "MED058", "brand_name": "Shelcal 500", "generic_salt": "Calcium + Vitamin D3", "strength": "500mg+250IU",
        "dosage_form": "Tablet", "category": "Nutritional", "manufacturer": "Torrent Pharma",
        "mrp": 142.00, "cost_price": 113.60, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP026", "base_daily_demand": 25.0
    },
    {
        "medicine_id": "MED059", "brand_name": "Becosules Z", "generic_salt": "B-Complex + Vitamin C + Zinc", "strength": "Capsule",
        "dosage_form": "Capsule", "category": "Nutritional", "manufacturer": "Pfizer India",
        "mrp": 49.00, "cost_price": 39.20, "pack_size": "20 Capsules", "units_per_pack": 20,
        "velocity_class": "FAST", "primary_supplier_id": "SUP008", "base_daily_demand": 28.0
    },
    {
        "medicine_id": "MED060", "brand_name": "Neurobion Forte", "generic_salt": "Vitamin B Complex", "strength": "Tablet",
        "dosage_form": "Tablet", "category": "Nutritional", "manufacturer": "Procter & Gamble Health",
        "mrp": 42.00, "cost_price": 33.60, "pack_size": "30 Tablets", "units_per_pack": 30,
        "velocity_class": "FAST", "primary_supplier_id": "SUP013", "base_daily_demand": 24.0
    },
    {
        "medicine_id": "MED061", "brand_name": "Zincovit", "generic_salt": "Multivitamin + Multimineral + Grape Seed Extract", "strength": "Tablet",
        "dosage_form": "Tablet", "category": "Nutritional", "manufacturer": "Apex Laboratories",
        "mrp": 115.00, "cost_price": 92.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP012", "base_daily_demand": 22.0
    },
    {
        "medicine_id": "MED062", "brand_name": "Limcee 500", "generic_salt": "Vitamin C (Ascorbic Acid)", "strength": "500mg",
        "dosage_form": "Chewable", "category": "Nutritional", "manufacturer": "Abbott India",
        "mrp": 25.00, "cost_price": 20.00, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "FAST", "primary_supplier_id": "SUP025", "base_daily_demand": 19.0
    },
    {
        "medicine_id": "MED063", "brand_name": "Evion 400", "generic_salt": "Vitamin E", "strength": "400mg",
        "dosage_form": "Capsule", "category": "Nutritional", "manufacturer": "Procter & Gamble Health",
        "mrp": 38.00, "cost_price": 30.40, "pack_size": "10 Capsules", "units_per_pack": 10,
        "velocity_class": "FAST", "primary_supplier_id": "SUP013", "base_daily_demand": 21.0
    },
    {
        "medicine_id": "MED064", "brand_name": "Supradyn Daily", "generic_salt": "Multivitamin Complex", "strength": "Tablet",
        "dosage_form": "Tablet", "category": "Nutritional", "manufacturer": "Bayer India",
        "mrp": 62.00, "cost_price": 49.60, "pack_size": "15 Tablets", "units_per_pack": 15,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP016", "base_daily_demand": 14.0
    },

    # === THYROID & HORMONE THERAPY (Strict daily chronic refills) ===
    {
        "medicine_id": "MED065", "brand_name": "Thyronorm 50", "generic_salt": "Thyroxine Sodium", "strength": "50mcg",
        "dosage_form": "Tablet", "category": "Endocrine", "manufacturer": "Abbott India",
        "mrp": 155.00, "cost_price": 124.00, "pack_size": "100 Tablets", "units_per_pack": 100,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP025", "base_daily_demand": 12.0
    },
    {
        "medicine_id": "MED066", "brand_name": "Thyronorm 100", "generic_salt": "Thyroxine Sodium", "strength": "100mcg",
        "dosage_form": "Tablet", "category": "Endocrine", "manufacturer": "Abbott India",
        "mrp": 185.00, "cost_price": 148.00, "pack_size": "100 Tablets", "units_per_pack": 100,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP025", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED067", "brand_name": "Eltroxin 50", "generic_salt": "Thyroxine Sodium", "strength": "50mcg",
        "dosage_form": "Tablet", "category": "Endocrine", "manufacturer": "GSK India",
        "mrp": 150.00, "cost_price": 120.00, "pack_size": "100 Tablets", "units_per_pack": 100,
        "velocity_class": "CHRONIC", "primary_supplier_id": "SUP002", "base_daily_demand": 10.0
    },

    # === TOPICALS, OINTMENTS & FIRST AID ===
    {
        "medicine_id": "MED068", "brand_name": "Betadine 10% Ointment", "generic_salt": "Povidone-Iodine", "strength": "20g",
        "dosage_form": "Ointment", "category": "Antiseptic", "manufacturer": "Win-Medicare",
        "mrp": 128.00, "cost_price": 102.40, "pack_size": "20g Tube", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP017", "base_daily_demand": 8.0
    },
    {
        "medicine_id": "MED069", "brand_name": "Soframycin Skin Cream", "generic_salt": "Framycetin Sulphate", "strength": "30g",
        "dosage_form": "Ointment", "category": "Antiseptic", "manufacturer": "Sanofi India",
        "mrp": 62.00, "cost_price": 49.60, "pack_size": "30g Tube", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP004", "base_daily_demand": 12.0
    },
    {
        "medicine_id": "MED070", "brand_name": "Volini Pain Relief Gel", "generic_salt": "Diclofenac Diethylamine", "strength": "30g",
        "dosage_form": "Gel", "category": "Analgesic", "manufacturer": "Sun Pharma",
        "mrp": 145.00, "cost_price": 116.00, "pack_size": "30g Tube", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP021", "base_daily_demand": 11.0
    },
    {
        "medicine_id": "MED071", "brand_name": "Omnigel", "generic_salt": "Diclofenac + Virgin Linseed Oil", "strength": "30g",
        "dosage_form": "Gel", "category": "Analgesic", "manufacturer": "Cipla",
        "mrp": 130.00, "cost_price": 104.00, "pack_size": "30g Tube", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP022", "base_daily_demand": 9.0
    },
    {
        "medicine_id": "MED072", "brand_name": "Candid-B Cream", "generic_salt": "Clotrimazole + Beclomethasone", "strength": "20g",
        "dosage_form": "Ointment", "category": "Antifungal", "manufacturer": "Glenmark Pharma",
        "mrp": 165.00, "cost_price": 132.00, "pack_size": "20g Tube", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP030", "base_daily_demand": 7.0
    },

    # === DERMATOLOGY & ANTIFUNGAL ORAL ===
    {
        "medicine_id": "MED073", "brand_name": "Itramac 200", "generic_salt": "Itraconazole", "strength": "200mg",
        "dosage_form": "Capsule", "category": "Antifungal", "manufacturer": "Macleods Pharma",
        "mrp": 240.00, "cost_price": 192.00, "pack_size": "10 Capsules", "units_per_pack": 10,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP018", "base_daily_demand": 6.0
    },
    {
        "medicine_id": "MED074", "brand_name": "Candiforce 200", "generic_salt": "Itraconazole", "strength": "200mg",
        "dosage_form": "Capsule", "category": "Antifungal", "manufacturer": "Mankind Pharma",
        "mrp": 210.00, "cost_price": 168.00, "pack_size": "10 Capsules", "units_per_pack": 10,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP024", "base_daily_demand": 8.0
    },
    {
        "medicine_id": "MED075", "brand_name": "Fluconazole 150 (Forcan)", "generic_salt": "Fluconazole", "strength": "150mg",
        "dosage_form": "Tablet", "category": "Antifungal", "manufacturer": "Cipla",
        "mrp": 38.00, "cost_price": 30.40, "pack_size": "3 Tablets", "units_per_pack": 3,
        "velocity_class": "SLOW", "primary_supplier_id": "SUP022", "base_daily_demand": 4.0
    },

    # === OPHTHALMIC & EAR DROPS ===
    {
        "medicine_id": "MED076", "brand_name": "Ciplox Eye/Ear Drops", "generic_salt": "Ciprofloxacin", "strength": "10ml",
        "dosage_form": "Drops", "category": "Ophthalmic", "manufacturer": "Cipla",
        "mrp": 24.00, "cost_price": 19.20, "pack_size": "10ml Bottle", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP022", "base_daily_demand": 14.0
    },
    {
        "medicine_id": "MED077", "brand_name": "Refresh Tears", "generic_salt": "Carboxymethylcellulose", "strength": "10ml",
        "dosage_form": "Drops", "category": "Ophthalmic", "manufacturer": "Allergan India",
        "mrp": 185.00, "cost_price": 148.00, "pack_size": "10ml Bottle", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP019", "base_daily_demand": 6.0
    },
    {
        "medicine_id": "MED078", "brand_name": "Otorex Ear Drops", "generic_salt": "Chlorbutol + Benzocaine", "strength": "10ml",
        "dosage_form": "Drops", "category": "Ophthalmic", "manufacturer": "Mankind Pharma",
        "mrp": 65.00, "cost_price": 52.00, "pack_size": "10ml Bottle", "units_per_pack": 1,
        "velocity_class": "MEDIUM", "primary_supplier_id": "SUP024", "base_daily_demand": 5.0
    },

    # === AYURVEDIC & LIVER PROTECTIVE (Massive OTC demand in Indian retail) ===
    {
        "medicine_id": "MED079", "brand_name": "Liv 52 DS", "generic_salt": "Herbal Liver Formulation", "strength": "Tablet",
        "dosage_form": "Tablet", "category": "Hepatoprotective", "manufacturer": "Himalaya Wellness",
        "mrp": 190.00, "cost_price": 152.00, "pack_size": "60 Tablets", "units_per_pack": 60,
        "velocity_class": "FAST", "primary_supplier_id": "SUP020", "base_daily_demand": 16.0
    },
    {
        "medicine_id": "MED080", "brand_name": "Liv 52 Syrup", "generic_salt": "Herbal Liver Formulation", "strength": "200ml",
        "dosage_form": "Syrup", "category": "Hepatoprotective", "manufacturer": "Himalaya Wellness",
        "mrp": 175.00, "cost_price": 140.00, "pack_size": "200ml Bottle", "units_per_pack": 1,
        "velocity_class": "FAST", "primary_supplier_id": "SUP020", "base_daily_demand": 12.0
    },
]

# For catalog depth, dynamically generate realistic brand & generic variations
# for remaining SKUs (MED081 to MED150) across pediatric syrups, antidiabetic strengths,
# cardiac combinations, and anti-infectives.
def _expand_catalog() -> List[Dict[str, Any]]:
    catalog = list(MEDICINES)
    existing_count = len(catalog)
    
    variations = [
        # Pediatric Syrups
        ("Calpol 120 Paediatric", "Paracetamol", "120mg/5ml", "Syrup", "Antipyretic", "GSK India", 45.0, 36.0, "60ml Bottle", 1, "FAST", "SUP002", 14.0),
        ("Calpol 250 Paediatric", "Paracetamol", "250mg/5ml", "Syrup", "Antipyretic", "GSK India", 55.0, 44.0, "60ml Bottle", 1, "FAST", "SUP002", 12.0),
        ("Augmentin Duo Oral Susp", "Amoxicillin + Clavulanate", "200mg+28.5mg", "Suspension", "Antibiotic", "GSK India", 72.0, 57.6, "30ml Bottle", 1, "MEDIUM", "SUP002", 7.0),
        ("Moxikind-CV Dry Syrup", "Amoxicillin + Clavulanate", "200mg+28.5mg", "Suspension", "Antibiotic", "Mankind Pharma", 64.0, 51.2, "30ml Bottle", 1, "MEDIUM", "SUP024", 8.0),
        ("Azithral Junior 100", "Azithromycin", "100mg/5ml", "Suspension", "Antibiotic", "Alembic Pharma", 75.0, 60.0, "15ml Bottle", 1, "MEDIUM", "SUP009", 6.0),
        ("Taxim-O Forte Dry Syrup", "Cefixime", "100mg/5ml", "Suspension", "Antibiotic", "Alkem Laboratories", 98.0, 78.4, "30ml Bottle", 1, "MEDIUM", "SUP023", 7.0),
        ("Meftal-P Suspension", "Mefenamic Acid", "100mg/5ml", "Suspension", "Analgesic", "Blue Cross Labs", 48.0, 38.4, "60ml Bottle", 1, "FAST", "SUP005", 11.0),
        ("Ibugesic Plus Syrup", "Ibuprofen + Paracetamol", "100mg+162.5mg", "Syrup", "Analgesic", "Cipla", 42.0, 33.6, "60ml Bottle", 1, "FAST", "SUP022", 13.0),
        
        # Intermediate / Additional Chronic formulations
        ("Telma-AM", "Telmisartan + Amlodipine", "40mg+5mg", "Tablet", "Cardiovascular", "Glenmark Pharma", 285.0, 228.0, "30 Tablets", 30, "CHRONIC", "SUP030", 14.0),
        ("Telmikind-AM", "Telmisartan + Amlodipine", "40mg+5mg", "Tablet", "Cardiovascular", "Mankind Pharma", 85.0, 68.0, "10 Tablets", 10, "CHRONIC", "SUP024", 15.0),
        ("Telma 80", "Telmisartan", "80mg", "Tablet", "Cardiovascular", "Glenmark Pharma", 310.0, 248.0, "30 Tablets", 30, "CHRONIC", "SUP030", 9.0),
        ("Amlong 2.5", "Amlodipine", "2.5mg", "Tablet", "Cardiovascular", "Micro Labs Ltd", 28.0, 22.4, "15 Tablets", 15, "CHRONIC", "SUP001", 8.0),
        ("Amlopres 5", "Amlodipine", "5mg", "Tablet", "Cardiovascular", "Cipla", 44.0, 35.2, "15 Tablets", 15, "CHRONIC", "SUP022", 11.0),
        ("Cilacar 10", "Cilnidipine", "10mg", "Tablet", "Cardiovascular", "J.B. Chemicals", 125.0, 100.0, "15 Tablets", 15, "CHRONIC", "SUP007", 13.0),
        ("Cilacar 20", "Cilnidipine", "20mg", "Tablet", "Cardiovascular", "J.B. Chemicals", 215.0, 172.0, "15 Tablets", 15, "CHRONIC", "SUP007", 8.0),
        ("Starpress XL 25", "Metoprolol Succinate", "25mg", "Tablet", "Cardiovascular", "Lupin Ltd", 88.0, 70.4, "10 Tablets", 10, "CHRONIC", "SUP029", 10.0),
        ("Starpress XL 50", "Metoprolol Succinate", "50mg", "Tablet", "Cardiovascular", "Lupin Ltd", 142.0, 113.6, "10 Tablets", 10, "CHRONIC", "SUP029", 12.0),
        ("Rosuvas 20", "Rosuvastatin", "20mg", "Tablet", "Cardiovascular", "Sun Pharma", 410.0, 328.0, "15 Tablets", 15, "CHRONIC", "SUP021", 6.0),
        ("Rozavel 10", "Rosuvastatin", "10mg", "Tablet", "Cardiovascular", "Sun Pharma", 225.0, 180.0, "10 Tablets", 10, "CHRONIC", "SUP021", 9.0),
        ("Deplatt 75", "Clopidogrel", "75mg", "Tablet", "Cardiovascular", "Torrent Pharma", 148.0, 118.4, "15 Tablets", 15, "CHRONIC", "SUP026", 11.0),
        ("Clopilet 75", "Clopidogrel", "75mg", "Tablet", "Cardiovascular", "Sun Pharma", 152.0, 121.6, "15 Tablets", 15, "CHRONIC", "SUP021", 10.0),
        
        # Diabetes variations
        ("Glycomet 850 SR", "Metformin", "850mg", "Tablet", "Antidiabetic", "USV Ltd", 54.0, 43.2, "10 Tablets", 10, "CHRONIC", "SUP003", 9.0),
        ("Amaryl 2mg", "Glimepiride", "2mg", "Tablet", "Antidiabetic", "Sanofi India", 158.0, 126.4, "15 Tablets", 15, "CHRONIC", "SUP004", 12.0),
        ("Glimestar 1", "Glimepiride", "1mg", "Tablet", "Antidiabetic", "Mankind Pharma", 52.0, 41.6, "10 Tablets", 10, "CHRONIC", "SUP024", 14.0),
        ("Glimestar 2", "Glimepiride", "2mg", "Tablet", "Antidiabetic", "Mankind Pharma", 78.0, 62.4, "10 Tablets", 10, "CHRONIC", "SUP024", 16.0),
        ("Glimestar-M 1", "Glimepiride + Metformin", "1mg+500mg", "Tablet", "Antidiabetic", "Mankind Pharma", 92.0, 73.6, "10 Tablets", 10, "CHRONIC", "SUP024", 17.0),
        ("Glimestar-M 2", "Glimepiride + Metformin", "2mg+500mg", "Tablet", "Antidiabetic", "Mankind Pharma", 112.0, 89.6, "10 Tablets", 10, "CHRONIC", "SUP024", 19.0),
        ("Jardiance 10", "Empagliflozin", "10mg", "Tablet", "Antidiabetic", "Boehringer Ingelheim", 680.0, 544.0, "10 Tablets", 10, "CHRONIC", "SUP014", 5.0),
        ("Jardiance 25", "Empagliflozin", "25mg", "Tablet", "Antidiabetic", "Boehringer Ingelheim", 840.0, 672.0, "10 Tablets", 10, "CHRONIC", "SUP014", 4.0),
        ("Forxiga 10", "Dapagliflozin", "10mg", "Tablet", "Antidiabetic", "AstraZeneca", 720.0, 576.0, "14 Tablets", 14, "CHRONIC", "SUP016", 5.0),
        ("Oxra 10", "Dapagliflozin", "10mg", "Tablet", "Antidiabetic", "Sun Pharma", 480.0, 384.0, "14 Tablets", 14, "CHRONIC", "SUP021", 7.0),
        ("Zomelis 50", "Vildagliptin", "50mg", "Tablet", "Antidiabetic", "Abbott India", 185.0, 148.0, "15 Tablets", 15, "CHRONIC", "SUP025", 8.0),
        
        # Chronic Thyroid & Uric Acid
        ("Thyronorm 25", "Thyroxine Sodium", "25mcg", "Tablet", "Endocrine", "Abbott India", 140.0, 112.0, "100 Tablets", 100, "CHRONIC", "SUP025", 8.0),
        ("Thyronorm 75", "Thyroxine Sodium", "75mcg", "Tablet", "Endocrine", "Abbott India", 170.0, 136.0, "100 Tablets", 100, "CHRONIC", "SUP025", 11.0),
        ("Thyronorm 125", "Thyroxine Sodium", "125mcg", "Tablet", "Endocrine", "Abbott India", 195.0, 156.0, "100 Tablets", 100, "CHRONIC", "SUP025", 6.0),
        ("Febutaz 40", "Febuxostat", "40mg", "Tablet", "Antigout", "Sun Pharma", 165.0, 132.0, "15 Tablets", 15, "CHRONIC", "SUP021", 7.0),
        ("Zyloric 100", "Allopurinol", "100mg", "Tablet", "Antigout", "GSK India", 28.0, 22.4, "10 Tablets", 10, "CHRONIC", "SUP002", 9.0),
        
        # Additional Gastrointestinal & Antibiotics
        ("Dulcoflex 5", "Bisacodyl", "5mg", "Tablet", "Laxative", "Sanofi India", 14.0, 11.2, "10 Tablets", 10, "FAST", "SUP004", 18.0),
        ("Cremaffin Mixed Fruit", "Liquid Paraffin + Milk of Magnesia", "225ml", "Syrup", "Laxative", "Abbott India", 265.0, 212.0, "225ml Bottle", 1, "MEDIUM", "SUP025", 6.0),
        ("Econorm Sachet", "Saccharomyces boulardii", "250mg", "Sachet", "Probiotic", "Dr. Reddy's", 52.0, 41.6, "1 Sachet", 1, "FAST", "SUP027", 14.0),
        ("Darolac Capsule", "Probiotics + Prebiotics", "Capsule", "Capsule", "Probiotic", "Aristo Pharma", 115.0, 92.0, "10 Capsules", 10, "MEDIUM", "SUP010", 8.0),
        ("Doxinate", "Doxylamine + Pyridoxine", "10mg+10mg", "Tablet", "Antiemetic", "Maneesh Pharma", 145.0, 116.0, "30 Tablets", 30, "MEDIUM", "SUP017", 6.0),
        ("Vomikind 4", "Ondansetron", "4mg", "Tablet", "Antiemetic", "Mankind Pharma", 44.0, 35.2, "10 Tablets", 10, "FAST", "SUP024", 15.0),
        ("Emeset 4", "Ondansetron", "4mg", "Tablet", "Antiemetic", "Cipla", 48.0, 38.4, "10 Tablets", 10, "FAST", "SUP022", 12.0),
        ("Sporidex 500", "Cephalexin", "500mg", "Capsule", "Antibiotic", "Sun Pharma", 185.0, 148.0, "10 Capsules", 10, "MEDIUM", "SUP021", 6.0),
        ("Klam 625", "Amoxicillin + Clavulanate", "625mg", "Tablet", "Antibiotic", "Alkem Laboratories", 170.0, 136.0, "10 Tablets", 10, "FAST", "SUP023", 11.0),
        ("Doxy-1 L-DR Forte", "Doxycycline + Lactic Acid Bacillus", "100mg", "Capsule", "Antibiotic", "USV Ltd", 110.0, 88.0, "10 Capsules", 10, "MEDIUM", "SUP003", 9.0),
        ("Oflox 200", "Ofloxacin", "200mg", "Tablet", "Antibiotic", "Cipla", 72.0, 57.6, "10 Tablets", 10, "MEDIUM", "SUP022", 8.0),
        ("Zenflox-OZ", "Ofloxacin + Ornidazole", "200mg+500mg", "Tablet", "Antibiotic", "Mankind Pharma", 128.0, 102.4, "10 Tablets", 10, "FAST", "SUP024", 14.0)
    ]
    
    for i, var in enumerate(variations):
        med_id = f"MED{existing_count + i + 1:03d}"
        catalog.append({
            "medicine_id": med_id,
            "brand_name": var[0],
            "generic_salt": var[1],
            "strength": var[2],
            "dosage_form": var[3],
            "category": var[4],
            "manufacturer": var[5],
            "mrp": var[6],
            "cost_price": var[7],
            "pack_size": var[8],
            "units_per_pack": var[9],
            "velocity_class": var[10],
            "primary_supplier_id": var[11],
            "base_daily_demand": var[12]
        })
        
    return catalog

MASTER_MEDICINE_CATALOG: List[Dict[str, Any]] = _expand_catalog()
