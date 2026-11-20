"""High-performance database seeder for RemediSync.

Loads master telemetry CSV files from data/raw/ into relational database tables:
1. branches.csv (4 branches)
2. suppliers.csv (30 stockists)
3. medicines.csv (129 SKUs)
4. batches.csv (808 physical lots)
5. inventory_snapshot.csv (516 active inventory states)
6. daily_sales.csv (329,208 records ingested in high-speed chunks)
"""

import argparse
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import (
    Base,
    Batch,
    Branch,
    DailySale,
    InventorySnapshot,
    Medicine,
    Supplier,
)
from src.database.session import DATABASE_URL, get_engine


def seed_database(
    data_dir: str = "data/raw",
    database_url: str = DATABASE_URL,
    reset_tables: bool = True,
    include_sales: bool = True,
    sales_chunk_size: int = 15000,
    sales_days_limit: Optional[int] = None,
) -> Dict[str, int]:
    """Execute relational database seeding from raw CSV files.

    Args:
        data_dir: Path to directory containing raw CSV datasets.
        database_url: Target database connection URL.
        reset_tables: Whether to drop and recreate tables before seeding.
        include_sales: Whether to seed daily_sales.csv.
        sales_chunk_size: Batch size for bulk sales insertion.
        sales_days_limit: If specified, only seed the last N days of sales.

    Returns:
        Dictionary containing counts of ingested records per entity.
    """
    raw_path = Path(data_dir)
    engine = get_engine(database_url)
    SessionClass = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if reset_tables:
        print(f"Resetting schema on: {engine.url.render_as_string(hide_password=True)}...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    record_counts: Dict[str, int] = {}

    with SessionClass() as session:
        # 1. Seed Branches
        branches_csv = raw_path / "branches.csv"
        if branches_csv.exists():
            df_b = pd.read_csv(branches_csv)
            branch_objects = [
                Branch(
                    branch_id=str(row["branch_id"]),
                    branch_name=str(row["branch_name"]),
                    location_type=str(row["location_type"]),
                    daily_target_revenue=Decimal(str(row["daily_target_revenue"])),
                    is_active=bool(row["is_active"]),
                )
                for _, row in df_b.iterrows()
            ]
            session.add_all(branch_objects)
            session.commit()
            record_counts["branches"] = len(branch_objects)
            print(f" -> Ingested {len(branch_objects)} branches.")

        # 2. Seed Suppliers
        suppliers_csv = raw_path / "suppliers.csv"
        if suppliers_csv.exists():
            df_s = pd.read_csv(suppliers_csv)
            supplier_objects = [
                Supplier(
                    supplier_id=str(row["supplier_id"]),
                    supplier_name=str(row["supplier_name"]),
                    contact_phone="+91-361-2540001",
                    city_hub=str(row.get("city", "GUWAHATI")),
                    lead_time_days=Decimal(str(row["lead_time_days"])),
                    fulfillment_tier=str(row.get("fulfillment_type", "EXPRESS_PICKUP")),
                    is_active=bool(row["is_active"]),
                )
                for _, row in df_s.iterrows()
            ]
            session.add_all(supplier_objects)
            session.commit()
            record_counts["suppliers"] = len(supplier_objects)
            print(f" -> Ingested {len(supplier_objects)} suppliers.")

        # 3. Seed Medicines
        medicines_csv = raw_path / "medicines.csv"
        if medicines_csv.exists():
            df_m = pd.read_csv(medicines_csv)
            medicine_objects = [
                Medicine(
                    medicine_id=str(row["medicine_id"]),
                    brand_name=str(row["brand_name"]),
                    generic_salt=str(row["generic_salt"]),
                    strength=str(row["strength"]),
                    dosage_form=str(row["dosage_form"]),
                    category=str(row["category"]),
                    manufacturer=str(row["manufacturer"]),
                    mrp=Decimal(str(row["mrp"])),
                    cost_price=Decimal(str(row["cost_price"])),
                    pack_size=str(row["pack_size"]),
                    units_per_pack=int(row["units_per_pack"]),
                    primary_supplier_id=str(row["primary_supplier_id"]),
                    is_cold_chain=False,
                    schedule_type="SCHEDULE_H",
                )
                for _, row in df_m.iterrows()
            ]
            session.add_all(medicine_objects)
            session.commit()
            record_counts["medicines"] = len(medicine_objects)
            print(f" -> Ingested {len(medicine_objects)} medicines.")

        # 4. Seed Batches
        batches_csv = raw_path / "batches.csv"
        if batches_csv.exists():
            df_bat = pd.read_csv(batches_csv)
            batch_objects = [
                Batch(
                    batch_id=str(row["batch_id"]),
                    medicine_id=str(row["medicine_id"]),
                    branch_id=str(row["branch_id"]),
                    batch_number=str(row["batch_number"]),
                    mfg_date=datetime.strptime(str(row["mfg_date"]), "%Y-%m-%d").date(),
                    expiry_date=datetime.strptime(str(row["expiry_date"]), "%Y-%m-%d").date(),
                    initial_quantity=int(row["initial_quantity"]),
                    current_quantity=int(row["current_quantity"]),
                    unit_cost_price=Decimal(str(row["unit_cost_price"])),
                )
                for _, row in df_bat.iterrows()
            ]
            session.add_all(batch_objects)
            session.commit()
            record_counts["batches"] = len(batch_objects)
            print(f" -> Ingested {len(batch_objects)} physical batches.")

        # 5. Seed Inventory Snapshots
        snapshots_csv = raw_path / "inventory_snapshot.csv"
        if snapshots_csv.exists():
            df_snap = pd.read_csv(snapshots_csv)
            snapshot_objects = [
                InventorySnapshot(
                    branch_id=str(row["branch_id"]),
                    medicine_id=str(row["medicine_id"]),
                    current_stock=Decimal(str(row["current_stock"])),
                    last_replenished_date=datetime.strptime(
                        str(row["last_replenished_date"]), "%Y-%m-%d"
                    ).date()
                    if pd.notna(row.get("last_replenished_date"))
                    else None,
                    pending_order_quantity=Decimal(str(row["pending_order_quantity"])),
                )
                for _, row in df_snap.iterrows()
            ]
            session.add_all(snapshot_objects)
            session.commit()
            record_counts["inventory_snapshots"] = len(snapshot_objects)
            print(f" -> Ingested {len(snapshot_objects)} inventory snapshots.")

        # 6. Seed Daily Sales (Chunked Bulk Insert)
        sales_csv = raw_path / "daily_sales.csv"
        if include_sales and sales_csv.exists():
            print(f"Reading {sales_csv} for bulk ingestion...")
            df_sales = pd.read_csv(sales_csv)

            if sales_days_limit:
                max_dt = df_sales["date"].max()
                min_dt = pd.to_datetime(max_dt) - pd.Timedelta(days=sales_days_limit)
                df_sales = df_sales[df_sales["date"] >= min_dt.strftime("%Y-%m-%d")].copy()
                print(f"Filtered to recent {sales_days_limit} days ({len(df_sales):,} rows)...")

            total_sales_rows = len(df_sales)
            print(f"Ingesting {total_sales_rows:,} sales records in chunks of {sales_chunk_size:,}...")

            inserted_count = 0
            # Pre-parse dates for performance
            df_sales["date_obj"] = pd.to_datetime(df_sales["date"]).dt.date

            for start_idx in range(0, total_sales_rows, sales_chunk_size):
                chunk = df_sales.iloc[start_idx : start_idx + sales_chunk_size]
                sales_batch = [
                    DailySale(
                        date=row["date_obj"],
                        branch_id=str(row["branch_id"]),
                        medicine_id=str(row["medicine_id"]),
                        units_sold=Decimal(str(round(row["units_sold"], 2))),
                        unit_price=Decimal(str(round(row["unit_price"], 2))),
                        total_revenue=Decimal(str(round(row["total_revenue"], 2))),
                        is_stockout=bool(row["is_stockout"]),
                    )
                    for _, row in chunk.iterrows()
                ]
                session.add_all(sales_batch)
                session.commit()
                inserted_count += len(sales_batch)
                print(f"   [{inserted_count:,}/{total_sales_rows:,}] sales rows inserted...")

            record_counts["daily_sales"] = inserted_count
            print(f" -> Ingested {inserted_count:,} total daily sales records.")

    return record_counts


def main() -> None:
    """CLI entrypoint for database seeder."""
    parser = argparse.ArgumentParser(description="RemediSync Relational Database Seeder")
    parser.add_argument("--data-dir", default="data/raw", help="Path to raw CSV directory")
    parser.add_argument(
        "--db-url",
        default=DATABASE_URL,
        help="Target database connection URL (PostgreSQL or SQLite)",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not drop existing tables before seeding",
    )
    parser.add_argument(
        "--no-sales",
        action="store_true",
        help="Skip ingesting the 329,208 daily sales records (dimensions and state only)",
    )
    parser.add_argument(
        "--sales-days",
        type=int,
        default=None,
        help="Seed only the last N days of sales (e.g. 90 days)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("                 REMEDISYNC: DATABASE SEEDER")
    print("=" * 70)
    print(f" Target Database: {args.db_url}")
    print(f" Source CSVs    : {args.data_dir}")
    print("-" * 70)

    t0 = datetime.now()
    counts = seed_database(
        data_dir=args.data_dir,
        database_url=args.db_url,
        reset_tables=not args.no_reset,
        include_sales=not args.no_sales,
        sales_days_limit=args.sales_days,
    )
    elapsed = (datetime.now() - t0).total_seconds()

    print("=" * 70)
    print(f"[SUCCESS] Database seeding complete in {elapsed:.2f} seconds!")
    print(f" Total Records Seeded: {sum(counts.values()):,}")
    for entity, count in counts.items():
        print(f"   * {entity:<22}: {count:,} records")
    print("=" * 70)


if __name__ == "__main__":
    main()
