"use client";

import * as React from "react";
import { DaysOfCoverBar } from "@/components/features/inventory/DaysOfCoverBar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import type { InventoryItem } from "@/types/api";

export interface InventoryTableProps {
  items: readonly InventoryItem[];
  isLoading: boolean;
  onSelectItem: (item: InventoryItem) => void;
  onClearFilters?: () => void;
}

export function InventoryTable({
  items,
  isLoading,
  onSelectItem,
  onClearFilters,
}: InventoryTableProps): React.ReactElement {
  const columns = React.useMemo<DataColumn<InventoryItem>[]>(
    () => [
      {
        key: "medicine",
        header: "Medicine & salt",
        render: (item) => (
          <div className="min-w-[180px]">
            <p className="font-medium text-ink-primary">{item.brand_name}</p>
            <p className="text-[12px] text-ink-secondary">
              {item.generic_salt}{" "}
              <span className="font-mono-tabular text-ink-muted">
                ({item.medicine_id})
              </span>
            </p>
          </div>
        ),
      },
      {
        key: "category",
        header: "Category",
        render: (item) => (
          <span className="text-ink-secondary">{item.category}</span>
        ),
      },
      {
        key: "abc",
        header: "Pareto",
        render: (item) => (
          <Badge
            mono
            tone={item.abc_class === "A" ? "accent" : "neutral"}
          >
            Class {item.abc_class}
          </Badge>
        ),
      },
      {
        key: "stock",
        header: "On hand",
        align: "right",
        mono: true,
        render: (item) => item.current_stock_units.toFixed(1),
      },
      {
        key: "pending",
        header: "In transit",
        align: "right",
        mono: true,
        render: (item) => item.pending_order_units.toFixed(1),
      },
      {
        key: "forecast",
        header: "7d forecast",
        align: "right",
        mono: true,
        render: (item) => item.predicted_7d_demand.toFixed(1),
      },
      {
        key: "rop",
        header: "Reorder point",
        align: "right",
        mono: true,
        render: (item) => item.reorder_point.toFixed(1),
      },
      {
        key: "cover",
        header: "Days of cover",
        align: "right",
        render: (item) => <DaysOfCoverBar days={item.days_of_cover} />,
      },
      {
        key: "status",
        header: "Shelf status",
        align: "right",
        render: (item) =>
          item.is_below_rop ? (
            <Badge tone={item.days_of_cover <= 2 ? "critical" : "warning"}>
              Below ROP
            </Badge>
          ) : (
            <Badge tone="healthy">Healthy</Badge>
          ),
      },
    ],
    []
  );

  return (
    <DataTable
      columns={columns}
      data={items}
      rowKey={(item) => item.medicine_id}
      isLoading={isLoading}
      skeletonRowCount={8}
      onRowClick={onSelectItem}
      emptyTitle="No shelf items match the active filters"
      emptyDescription="Try clearing the search query or switching therapeutic categories."
      emptyAction={
        onClearFilters ? (
          <Button variant="secondary" size="sm" onClick={onClearFilters}>
            Clear filters
          </Button>
        ) : undefined
      }
    />
  );
}
