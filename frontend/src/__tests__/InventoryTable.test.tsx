import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { InventoryTable } from "@/components/features/inventory/InventoryTable";
import type { InventoryItem } from "@/types/api";

const SAMPLE_ITEMS: InventoryItem[] = [
  {
    medicine_id: "MED001",
    brand_name: "Dolo 650",
    generic_salt: "Paracetamol",
    category: "Analgesic",
    dosage_form: "TABLET",
    current_stock_units: 120,
    pending_order_units: 0,
    predicted_7d_demand: 70,
    days_of_cover: 12.0,
    reorder_point: 28,
    is_below_rop: false,
    abc_class: "A",
    demand_pattern: "Smooth",
  },
  {
    medicine_id: "MED002",
    brand_name: "Telma 40",
    generic_salt: "Telmisartan",
    category: "Cardiovascular",
    dosage_form: "TABLET",
    current_stock_units: 15,
    pending_order_units: 0,
    predicted_7d_demand: 70,
    days_of_cover: 1.5,
    reorder_point: 34,
    is_below_rop: true,
    abc_class: "A",
    demand_pattern: "Smooth",
  },
];

describe("InventoryTable clinical shelf view", () => {
  it("renders medicine metadata, days of cover, ROP status, and triggers SKU drawer selection", () => {
    const onSelectItem = vi.fn();
    render(
      <InventoryTable
        items={SAMPLE_ITEMS}
        isLoading={false}
        onSelectItem={onSelectItem}
      />
    );

    expect(screen.getByText("Dolo 650")).toBeInTheDocument();
    expect(screen.getByText("Telma 40")).toBeInTheDocument();
    expect(screen.getByText("Below ROP")).toBeInTheDocument();
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("1.5d")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Telma 40"));
    expect(onSelectItem).toHaveBeenCalledWith(SAMPLE_ITEMS[1]);
  });
});
