"""
Automated Pytest Validation Suite for Data Health & Schema Audit.

Validates that the DataHealthAuditor passes with zero critical errors,
100% time-series grid continuity, and zero foreign key violations.
"""

from pathlib import Path
import pytest
from src.features.data_audit import DataHealthAuditor


@pytest.fixture(scope="module")
def audit_report():
    """Runs the DataHealthAuditor once and caches the report for assertions."""
    auditor = DataHealthAuditor(raw_dir="data/raw", processed_dir="data/processed")
    return auditor.run_full_audit()


def test_audit_overall_status(audit_report):
    """Asserts that the full data health audit passed with zero errors."""
    assert audit_report["audit_status"] == "PASSED", f"Audit failed: {audit_report['critical_errors']}"
    assert audit_report["critical_errors_count"] == 0


def test_date_grid_completeness(audit_report):
    """Asserts that all 329,208 dates in the grid exist with zero duplicates."""
    grid_audit = audit_report["date_grid_audit"]
    assert bool(grid_audit["grid_continuity_valid"]) is True
    assert grid_audit["missing_records"] == 0
    assert grid_audit["duplicate_records"] == 0
    assert grid_audit["actual_records"] == 329208


def test_null_rates(audit_report):
    """Asserts that all 6 tables have 0.0% null values."""
    null_rates = audit_report["null_rates_pct"]
    for table_name, null_pct in null_rates.items():
        assert null_pct == 0.0, f"Table {table_name} has non-zero null rate: {null_pct}%"


def test_referential_integrity(audit_report):
    """Asserts that foreign key links across suppliers, branches, and meds are valid."""
    ref_audit = audit_report["referential_integrity"]
    assert ref_audit["medicines_to_suppliers"] is True
    assert ref_audit["batches_foreign_keys"] is True
    assert ref_audit["sales_foreign_keys"] is True


def test_domain_invariants(audit_report):
    """Asserts that pricing margins, lead times, and near-term batches are valid."""
    invariants = audit_report["domain_invariants"]
    assert invariants["pricing_and_margins_valid"] is True
    assert invariants["lead_times_valid"] is True
    assert invariants["near_term_expiries_present"] is True
    assert invariants["near_term_expiries_count"] >= 30
    assert invariants["sales_quantities_valid"] is True


def test_health_report_exported():
    """Asserts that data/processed/data_health_report.json was exported cleanly."""
    report_file = Path("data/processed/data_health_report.json")
    assert report_file.exists()
    assert report_file.stat().st_size > 0
