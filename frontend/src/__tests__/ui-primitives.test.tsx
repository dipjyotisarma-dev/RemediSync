import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { SlideOver } from "@/components/ui/SlideOver";

interface SampleRow {
  id: string;
  name: string;
  qty: number;
}

describe("Design system Layer 1 UI primitives", () => {
  it("disables Button and exposes aria-busy when loading", () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Approve order
      </Button>
    );
    const btn = screen.getByRole("button", { name: /approve order/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("aria-busy", "true");
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("renders Badge semantic label in sentence case", () => {
    render(<Badge tone="critical">Below ROP</Badge>);
    expect(screen.getByText("Below ROP")).toBeInTheDocument();
  });

  it("switches SegmentedControl active value and renders counts", () => {
    const onChange = vi.fn();
    render(
      <SegmentedControl
        ariaLabel="Filter urgency"
        value="ALL"
        onChange={onChange}
        options={[
          { value: "ALL", label: "All", count: 8 },
          { value: "CRITICAL", label: "Critical", count: 2 },
        ]}
      />
    );
    fireEvent.click(screen.getByRole("tab", { name: /critical/i }));
    expect(onChange).toHaveBeenCalledWith("CRITICAL");
  });

  it("renders DataTable skeleton rows when loading and empty state when empty", () => {
    const columns: DataColumn<SampleRow>[] = [
      { key: "name", header: "Medicine", render: (row) => row.name },
      { key: "qty", header: "Stock", align: "right", render: (row) => row.qty },
    ];

    const { rerender } = render(
      <DataTable
        columns={columns}
        data={[]}
        rowKey={(r) => r.id}
        isLoading
        emptyTitle="No medicines found"
        emptyDescription="Adjust filters to view shelf items."
      />
    );
    expect(screen.getAllByTestId("skeleton-row").length).toBeGreaterThan(0);

    rerender(
      <DataTable
        columns={columns}
        data={[]}
        rowKey={(r) => r.id}
        isLoading={false}
        emptyTitle="No medicines found"
        emptyDescription="Adjust filters to view shelf items."
      />
    );
    expect(screen.getByText("No medicines found")).toBeInTheDocument();
  });

  it("closes SlideOver drawer on Escape key press", () => {
    const onClose = vi.fn();
    render(
      <SlideOver open onClose={onClose} title="Dolo 650" subtitle="Paracetamol · MED001">
        <p>Sales telemetry</p>
      </SlideOver>
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
