"use client";

import * as React from "react";
import { RationaleProofBox } from "@/components/features/replenishment/RationaleProofBox";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  SegmentedControl,
  type SegmentedOption,
} from "@/components/ui/SegmentedControl";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatINR } from "@/lib/format";
import type { OrderItemRequest, RecommendationItem } from "@/types/api";
import { cn } from "@/lib/cn";

export type UrgencyFilter = "ALL" | "CRITICAL" | "REORDER";

export interface ReplenishmentWorkbenchProps {
  recommendations: readonly RecommendationItem[];
  isLoading: boolean;
  isSubmitting: boolean;
  onApprove: (orders: OrderItemRequest[]) => Promise<void> | void;
}

function getUrgencyBadgeTone(
  urgency: string
): "critical" | "warning" | "healthy" | "neutral" {
  if (urgency === "CRITICAL") return "critical";
  if (urgency === "REORDER") return "warning";
  if (urgency === "HEALTHY") return "healthy";
  return "neutral";
}

export function ReplenishmentWorkbench({
  recommendations,
  isLoading,
  isSubmitting,
  onApprove,
}: ReplenishmentWorkbenchProps): React.ReactElement {
  const [urgencyFilter, setUrgencyFilter] =
    React.useState<UrgencyFilter>("ALL");
  const [selectedIds, setSelectedIds] = React.useState<Record<string, boolean>>(
    {}
  );
  const [quantities, setQuantities] = React.useState<Record<string, string>>(
    {}
  );
  const [notesMap, setNotesMap] = React.useState<Record<string, string>>({});

  React.useEffect(() => {
    const initialSelected: Record<string, boolean> = {};
    const initialQty: Record<string, string> = {};
    for (const rec of recommendations) {
      const actionable =
        (rec.urgency === "CRITICAL" || rec.urgency === "REORDER") &&
        rec.recommended_order_units > 0;
      initialSelected[rec.medicine_id] = actionable;
      initialQty[rec.medicine_id] = String(rec.recommended_order_units);
    }
    setSelectedIds(initialSelected);
    setQuantities(initialQty);
  }, [recommendations]);

  const criticalCount = recommendations.filter(
    (r) => r.urgency === "CRITICAL"
  ).length;
  const reorderCount = recommendations.filter(
    (r) => r.urgency === "REORDER"
  ).length;

  const filterOptions = React.useMemo<SegmentedOption<UrgencyFilter>[]>(
    () => [
      { value: "ALL", label: "All", count: recommendations.length },
      { value: "CRITICAL", label: "Critical", count: criticalCount },
      { value: "REORDER", label: "Reorder", count: reorderCount },
    ],
    [recommendations.length, criticalCount, reorderCount]
  );

  const visibleItems = React.useMemo(() => {
    if (urgencyFilter === "ALL") {
      return recommendations;
    }
    return recommendations.filter((r) => r.urgency === urgencyFilter);
  }, [recommendations, urgencyFilter]);

  const selectedItems = recommendations.filter(
    (r) => selectedIds[r.medicine_id]
  );

  const hasInvalidSelectedQuantity = selectedItems.some((r) => {
    const raw = Number(quantities[r.medicine_id]);
    return !Number.isFinite(raw) || raw <= 0;
  });

  const selectedTotalInr = selectedItems.reduce((sum, r) => {
    const parsed = Number(quantities[r.medicine_id]);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      return sum;
    }
    return sum + parsed * r.unit_cost_price;
  }, 0);

  const toggleAllVisible = (checked: boolean): void => {
    setSelectedIds((prev) => {
      const next = { ...prev };
      for (const item of visibleItems) {
        next[item.medicine_id] = checked;
      }
      return next;
    });
  };

  const allVisibleChecked =
    visibleItems.length > 0 &&
    visibleItems.every((item) => Boolean(selectedIds[item.medicine_id]));

  const handleSubmit = (): void => {
    if (selectedItems.length === 0 || hasInvalidSelectedQuantity) {
      return;
    }
    const orders: OrderItemRequest[] = selectedItems.map((r) => {
      const qty = Number(quantities[r.medicine_id]);
      const note = notesMap[r.medicine_id]?.trim();
      return {
        medicine_id: r.medicine_id,
        supplier_id: r.primary_supplier_id,
        approved_quantity_units: qty,
        notes: note && note.length > 0 ? note : undefined,
      };
    });
    void onApprove(orders);
  };

  const selectedCount = selectedItems.length;
  const approveLabel =
    selectedCount === 1
      ? "Approve 1 selected order"
      : `Approve ${selectedCount} selected orders`;

  return (
    <div className="space-y-4">
      {/* Control & Approval Strip */}
      <div className="flex flex-col gap-3 rounded-panel border border-hairline bg-surface p-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <SegmentedControl
          ariaLabel="Filter recommendations by urgency"
          options={filterOptions}
          value={urgencyFilter}
          onChange={setUrgencyFilter}
        />

        <div className="flex flex-wrap items-center gap-4">
          <div className="text-right">
            <p className="text-[12px] text-ink-muted">Selected expenditure</p>
            <p className="font-mono-tabular text-[16px] font-semibold text-ink-primary">
              {formatINR(selectedTotalInr, 2)}
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            loading={isSubmitting}
            disabled={selectedCount === 0 || hasInvalidSelectedQuantity}
            onClick={handleSubmit}
          >
            {approveLabel}
          </Button>
        </div>
      </div>

      {/* Recommendations Queue Table */}
      <div className="overflow-x-auto rounded-panel border border-hairline bg-surface">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-hairline bg-subtle">
              <th scope="col" className="h-9 w-10 px-4">
                <input
                  type="checkbox"
                  aria-label="Select all visible recommendations"
                  checked={allVisibleChecked}
                  onChange={(e) => toggleAllVisible(e.target.checked)}
                  className="h-4 w-4 rounded border-hairline accent-accent cursor-pointer"
                />
              </th>
              <th
                scope="col"
                className="h-9 px-4 text-[12px] font-medium text-ink-muted"
              >
                Medicine, supplier & calculation rationale
              </th>
              <th
                scope="col"
                className="h-9 px-4 text-right text-[12px] font-medium text-ink-muted whitespace-nowrap"
              >
                Stock / ROP
              </th>
              <th
                scope="col"
                className="h-9 px-4 text-right text-[12px] font-medium text-ink-muted whitespace-nowrap"
              >
                7d forecast
              </th>
              <th
                scope="col"
                className="h-9 px-4 text-[12px] font-medium text-ink-muted whitespace-nowrap"
              >
                Order quantity (units)
              </th>
              <th
                scope="col"
                className="h-9 px-4 text-right text-[12px] font-medium text-ink-muted whitespace-nowrap"
              >
                Estimated cost
              </th>
              <th
                scope="col"
                className="h-9 px-4 text-right text-[12px] font-medium text-ink-muted whitespace-nowrap"
              >
                Urgency
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, idx) => (
                <tr key={`rec-skel-${idx}`} className="h-16">
                  <td colSpan={7} className="px-4 py-3">
                    <Skeleton className="h-10 w-full" />
                  </td>
                </tr>
              ))
            ) : visibleItems.length === 0 ? (
              <tr>
                <td colSpan={7}>
                  <EmptyState
                    title="All SKUs are above reorder thresholds"
                    description="No replenishment orders match the current urgency filter for this branch."
                  />
                </td>
              </tr>
            ) : (
              visibleItems.map((rec) => {
                const isSelected = Boolean(selectedIds[rec.medicine_id]);
                const rawVal =
                  quantities[rec.medicine_id] ??
                  String(rec.recommended_order_units);
                const parsedQty = Number(rawVal);
                const invalidQty =
                  rawVal.trim() === "" ||
                  !Number.isFinite(parsedQty) ||
                  parsedQty <= 0;
                const lineCost = invalidQty
                  ? 0
                  : parsedQty * rec.unit_cost_price;

                return (
                  <tr
                    key={rec.medicine_id}
                    className={cn(
                      "align-top transition-colors duration-150",
                      isSelected ? "bg-surface" : "bg-canvas/50"
                    )}
                  >
                    <td className="px-4 py-3.5">
                      <input
                        type="checkbox"
                        aria-label={`Select ${rec.brand_name}`}
                        checked={isSelected}
                        onChange={(e) =>
                          setSelectedIds((prev) => ({
                            ...prev,
                            [rec.medicine_id]: e.target.checked,
                          }))
                        }
                        className="mt-1 h-4 w-4 rounded border-hairline accent-accent cursor-pointer"
                      />
                    </td>
                    <td className="min-w-[300px] px-4 py-3.5">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="text-[14px] font-medium text-ink-primary">
                          {rec.brand_name}
                        </span>
                        <span className="font-mono-tabular text-[12px] text-ink-muted">
                          {rec.medicine_id}
                        </span>
                      </div>
                      <p className="mt-0.5 text-[12.5px] text-ink-secondary">
                        {rec.primary_supplier_name} ·{" "}
                        <span className="font-mono-tabular">
                          {rec.lead_time_days.toFixed(1)}d
                        </span>{" "}
                        lead · {rec.supplier_fulfillment_tier.replace(/_/g, " ").toLowerCase()}
                      </p>
                      <RationaleProofBox
                        rationale={rec.calculation_rationale}
                        roundingNote={rec.pack_size_rounding}
                      />
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono-tabular text-[13.5px] whitespace-nowrap">
                      <span className="font-medium text-ink-primary">
                        {rec.current_stock_units.toFixed(0)}
                      </span>{" "}
                      <span className="text-ink-muted">
                        / {rec.reorder_point.toFixed(0)}
                      </span>
                      {rec.pending_order_units > 0 ? (
                        <p className="mt-0.5 text-[12px] text-accent">
                          +{rec.pending_order_units.toFixed(0)} pending
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono-tabular text-[13.5px] text-ink-primary whitespace-nowrap">
                      {rec.predicted_7d_demand.toFixed(1)}
                    </td>
                    <td className="w-52 px-4 py-3.5">
                      <input
                        type="number"
                        min={1}
                        step={1}
                        aria-label={`Order quantity for ${rec.brand_name}`}
                        value={rawVal}
                        onChange={(e) =>
                          setQuantities((prev) => ({
                            ...prev,
                            [rec.medicine_id]: e.target.value,
                          }))
                        }
                        className={cn(
                          "h-8 w-28 rounded-control border bg-surface px-2.5 font-mono-tabular text-[13.5px] text-ink-primary",
                          invalidQty
                            ? "border-status-critical-ink"
                            : "border-hairline hover:border-strong"
                        )}
                      />
                      {invalidQty ? (
                        <p
                          role="alert"
                          className="mt-1 text-[12px] text-status-critical-ink"
                        >
                          Quantity must be greater than zero
                        </p>
                      ) : null}
                      <input
                        type="text"
                        aria-label={`Pharmacist note for ${rec.brand_name}`}
                        placeholder="Optional dispatch note"
                        value={notesMap[rec.medicine_id] ?? ""}
                        onChange={(e) =>
                          setNotesMap((prev) => ({
                            ...prev,
                            [rec.medicine_id]: e.target.value,
                          }))
                        }
                        className="mt-1.5 h-7 w-44 rounded-badge border border-hairline bg-surface px-2 text-[12px] text-ink-secondary placeholder:text-ink-muted"
                      />
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono-tabular text-[13.5px] font-medium text-ink-primary whitespace-nowrap">
                      {formatINR(lineCost, 2)}
                      <p className="mt-0.5 text-[12px] font-normal text-ink-muted">
                        {formatINR(rec.unit_cost_price, 2)} / unit
                      </p>
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      <Badge tone={getUrgencyBadgeTone(rec.urgency)}>
                        {rec.urgency === "CRITICAL"
                          ? "Critical"
                          : rec.urgency === "REORDER"
                            ? "Reorder"
                            : rec.urgency}
                      </Badge>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
