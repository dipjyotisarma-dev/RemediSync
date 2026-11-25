import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ReplenishmentWorkbench } from "@/components/features/replenishment/ReplenishmentWorkbench";
import type { RecommendationItem } from "@/types/api";

const SAMPLE_RECOMMENDATIONS: RecommendationItem[] = [
  {
    medicine_id: "MED002",
    brand_name: "Telma 40",
    primary_supplier_id: "SUP001",
    primary_supplier_name: "Assam Drug Distributors",
    supplier_fulfillment_tier: "STANDARD",
    lead_time_days: 1.5,
    current_stock_units: 15,
    pending_order_units: 0,
    predicted_7d_demand: 70,
    safety_stock_units: 19.2,
    reorder_point: 34.2,
    recommended_order_units: 90,
    unit_cost_price: 160,
    estimated_cost_inr: 14400,
    pack_size_rounding: "Rounded to 3 packs of 30 (90 units)",
    urgency: "CRITICAL",
    calculation_rationale:
      "Telma 40: Current stock (15 units) covers only 1.5 days; supplier takes 1.5 days to deliver. Reorder 3 packs (90 units) immediately.",
  },
];

describe("ReplenishmentWorkbench PO approval & validation", () => {
  it("displays calculation rationale, blocks non-positive quantities, and submits valid PO lines", async () => {
    const onApprove = vi.fn().mockResolvedValue(undefined);

    render(
      <ReplenishmentWorkbench
        recommendations={SAMPLE_RECOMMENDATIONS}
        isLoading={false}
        isSubmitting={false}
        onApprove={onApprove}
      />
    );

    expect(
      screen.getByText(/Current stock \(15 units\) covers only 1\.5 days/i)
    ).toBeInTheDocument();

    const qtyInput = screen.getByLabelText(/Order quantity for Telma 40/i);
    expect(qtyInput).toHaveValue(90);

    // Invalid zero quantity must disable approval and show inline error
    fireEvent.change(qtyInput, { target: { value: "0" } });
    expect(
      screen.getByText(/Quantity must be greater than zero/i)
    ).toBeInTheDocument();

    const approveBtn = screen.getByRole("button", {
      name: /Approve 1 selected order/i,
    });
    expect(approveBtn).toBeDisabled();

    // Restore valid edited quantity and approve
    fireEvent.change(qtyInput, { target: { value: "120" } });
    expect(approveBtn).not.toBeDisabled();

    fireEvent.click(approveBtn);
    expect(onApprove).toHaveBeenCalledWith([
      {
        medicine_id: "MED002",
        supplier_id: "SUP001",
        approved_quantity_units: 120,
        notes: undefined,
      },
    ]);
  });
});
