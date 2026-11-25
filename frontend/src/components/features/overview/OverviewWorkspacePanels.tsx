"use client";

import * as React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { DataTable, type DataColumn } from "@/components/ui/DataTable";
import { useBranchContext } from "@/context/BranchContext";
import { ASSAM_BRANCHES, type BranchDefinition } from "@/lib/constants";
import { formatINR } from "@/lib/format";
import type { AnalyticsOverviewResponse } from "@/types/api";

export interface OverviewWorkspacePanelsProps {
  overview: AnalyticsOverviewResponse | null;
  isLoading: boolean;
}

export function OverviewWorkspacePanels({
  overview,
  isLoading,
}: OverviewWorkspacePanelsProps): React.ReactElement {
  const { selectedBranchId, setSelectedBranchId } = useBranchContext();

  const columns = React.useMemo<DataColumn<BranchDefinition>[]>(
    () => [
      {
        key: "name",
        header: "Branch location",
        render: (b) => (
          <div>
            <p className="font-medium text-ink-primary">{b.name}</p>
            <p className="font-mono-tabular text-[12px] text-ink-muted">
              {b.id}
            </p>
          </div>
        ),
      },
      {
        key: "type",
        header: "Catchment profile",
        render: (b) => <Badge tone="neutral">{b.locationType}</Badge>,
      },
      {
        key: "target",
        header: "Daily target",
        align: "right",
        mono: true,
        render: (b) => formatINR(b.dailyTargetInr, 0),
      },
      {
        key: "actions",
        header: "Store workbench",
        align: "right",
        render: (b) => (
          <div className="inline-flex items-center justify-end gap-2">
            <Link
              href="/inventory"
              onClick={() => setSelectedBranchId(b.id)}
              className="rounded-control border border-hairline bg-surface px-2.5 py-1 text-[12.5px] font-medium text-ink-primary transition-colors duration-150 hover:bg-subtle"
            >
              Inspect shelf
            </Link>
            <Link
              href="/replenishment"
              onClick={() => setSelectedBranchId(b.id)}
              className="rounded-control bg-accent px-2.5 py-1 text-[12.5px] font-medium text-ink-inverse transition-colors duration-150 hover:bg-accent-hover"
            >
              Order queue
            </Link>
          </div>
        ),
      },
    ],
    [setSelectedBranchId]
  );

  const filteredBranches =
    selectedBranchId === "ALL"
      ? ASSAM_BRANCHES
      : ASSAM_BRANCHES.filter((b) => b.id === selectedBranchId);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <div className="lg:col-span-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[15px] leading-[22px] font-medium text-ink-primary">
            Assam branch network & daily revenue targets
          </h2>
          {selectedBranchId !== "ALL" ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedBranchId("ALL")}
            >
              Show all 4 branches
            </Button>
          ) : null}
        </div>
        <DataTable
          columns={columns}
          data={filteredBranches}
          rowKey={(b) => b.id}
          isLoading={isLoading}
          skeletonRowCount={4}
        />
      </div>

      <div className="lg:col-span-4">
        <div className="mb-3">
          <h2 className="text-[15px] leading-[22px] font-medium text-ink-primary">
            Immediate operational priorities
          </h2>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Dispensary action queue</CardTitle>
            <Badge
              tone={
                (overview?.critical_stockouts_count ?? 0) > 0
                  ? "critical"
                  : "healthy"
              }
            >
              {(overview?.critical_stockouts_count ?? 0) > 0
                ? "Action required"
                : "Nominal"}
            </Badge>
          </CardHeader>
          <CardContent className="divide-y divide-hairline p-0">
            <div className="flex items-start justify-between gap-4 px-5 py-4">
              <div>
                <p className="text-[13.5px] font-medium text-ink-primary">
                  Critical stockout protection
                </p>
                <p className="mt-1 text-[12.5px] text-ink-secondary">
                  <span className="font-mono-tabular font-medium text-ink-primary">
                    {overview?.critical_stockouts_count ?? 0}
                  </span>{" "}
                  SKUs have 5 or fewer physical units on shelf. Review
                  pack-rounded purchase recommendations.
                </p>
              </div>
              <Link
                href="/replenishment"
                className="shrink-0 rounded-control border border-hairline bg-surface px-3 py-1.5 text-[12.5px] font-medium text-ink-primary transition-colors duration-150 hover:bg-subtle"
              >
                Open POs
              </Link>
            </div>

            <div className="flex items-start justify-between gap-4 px-5 py-4">
              <div>
                <p className="text-[13.5px] font-medium text-ink-primary">
                  90-day distributor credit returns
                </p>
                <p className="mt-1 text-[12.5px] text-ink-secondary">
                  <span className="font-mono-tabular font-medium text-ink-primary">
                    {overview?.near_expiry_batches_count ?? 0}
                  </span>{" "}
                  physical lots approach statutory expiry cutoff with{" "}
                  <span className="font-mono-tabular font-medium text-ink-primary">
                    {formatINR(
                      overview?.estimated_near_expiry_value_inr ?? 0,
                      0
                    )}
                  </span>{" "}
                  capital exposure.
                </p>
              </div>
              <Link
                href="/expiry"
                className="shrink-0 rounded-control border border-hairline bg-surface px-3 py-1.5 text-[12.5px] font-medium text-ink-primary transition-colors duration-150 hover:bg-subtle"
              >
                Audit lots
              </Link>
            </div>

            <div className="px-5 py-4">
              <p className="text-[12.5px] font-medium text-ink-secondary">
                Forecasting governance
              </p>
              <p className="mt-1 text-[12.5px] text-ink-muted">
                Safety stock buffers are calibrated dynamically from 7-day
                HistGradientBoosting demand forecasts (15.72% out-of-time WAPE)
                and therapeutic service-level Z-scores (98% chronic, 95% acute,
                90% OTC).
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
