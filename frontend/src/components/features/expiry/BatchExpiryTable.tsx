"use client";

import * as React from "react";
import { Badge } from "@/components/ui/Badge";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { formatINR } from "@/lib/format";
import type { BatchExpiryItem } from "@/types/api";

export interface BatchExpiryTableProps {
  batches: readonly BatchExpiryItem[];
  isLoading: boolean;
}

export function BatchExpiryTable({
  batches,
  isLoading,
}: BatchExpiryTableProps): React.ReactElement {
  const columns = React.useMemo<DataColumn<BatchExpiryItem>[]>(
    () => [
      {
        key: "batch",
        header: "Batch & medicine",
        render: (b) => (
          <div className="min-w-[220px]">
            <div className="flex items-baseline gap-2">
              <span className="font-medium text-ink-primary">
                {b.brand_name}
              </span>
              <span className="font-mono-tabular text-[12px] text-ink-muted">
                {b.batch_number}
              </span>
            </div>
            <p className="mt-1 text-[12px] text-ink-secondary">
              {b.action_rationale}
            </p>
          </div>
        ),
      },
      {
        key: "branch",
        header: "Branch",
        mono: true,
        render: (b) => b.branch_id,
      },
      {
        key: "expiry",
        header: "Expiry date",
        mono: true,
        render: (b) => b.expiry_date,
      },
      {
        key: "days",
        header: "Days left",
        align: "right",
        render: (b) => (
          <Badge
            mono
            tone={
              b.days_to_expiry <= 30
                ? "critical"
                : b.days_to_expiry <= 90
                  ? "warning"
                  : "neutral"
            }
          >
            {b.days_to_expiry}d
          </Badge>
        ),
      },
      {
        key: "qty",
        header: "Qty / projected sold",
        align: "right",
        mono: true,
        render: (b) => (
          <span>
            {b.current_quantity_units.toFixed(0)}{" "}
            <span className="text-ink-muted">
              / {b.predicted_demand_before_expiry.toFixed(0)}
            </span>
          </span>
        ),
      },
      {
        key: "unsold",
        header: "Unsold risk",
        align: "right",
        mono: true,
        render: (b) => `${b.projected_unsold_units.toFixed(0)} units`,
      },
      {
        key: "loss",
        header: "Projected loss",
        align: "right",
        mono: true,
        render: (b) => formatINR(b.projected_loss_inr, 2),
      },
      {
        key: "action",
        header: "Protocol",
        align: "right",
        render: (b) =>
          b.recommended_action === "IMMEDIATE_DISTRIBUTOR_RETURN" ? (
            <Badge tone="warning">Distributor return</Badge>
          ) : (
            <Badge tone="neutral">FEFO front-row</Badge>
          ),
      },
    ],
    []
  );

  return (
    <DataTable
      columns={columns}
      data={batches}
      rowKey={(b) => b.batch_id}
      isLoading={isLoading}
      skeletonRowCount={6}
      emptyTitle="Zero batches at risk within this horizon"
      emptyDescription="All physical lots in scope are projected to sell through prior to expiration."
    />
  );
}
