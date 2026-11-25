"use client";

import * as React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/Badge";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Skeleton } from "@/components/ui/Skeleton";
import { SlideOver } from "@/components/ui/SlideOver";
import { formatDaysOfCover, formatINR, formatShortDate } from "@/lib/format";
import { apiClient } from "@/services/apiClient";
import type { DailySaleItem, InventoryItem } from "@/types/api";

export interface SkuSalesDrawerProps {
  branchId: string;
  item: InventoryItem | null;
  onClose: () => void;
}

export function SkuSalesDrawer({
  branchId,
  item,
  onClose,
}: SkuSalesDrawerProps): React.ReactElement {
  const [sales, setSales] = React.useState<DailySaleItem[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<unknown>(null);

  const loadSales = React.useCallback(async () => {
    if (!item) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getSalesHistory({
        branchId,
        medicineId: item.medicine_id,
        days: 30,
      });
      setSales(res.sales);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [branchId, item]);

  React.useEffect(() => {
    void loadSales();
  }, [loadSales]);

  const totalUnits30d = sales.reduce((acc, s) => acc + s.units_sold, 0);
  const totalRevenue30d = sales.reduce((acc, s) => acc + s.total_revenue, 0);
  const stockoutDays = sales.filter((s) => s.is_stockout_flag);

  return (
    <SlideOver
      open={Boolean(item)}
      onClose={onClose}
      title={item?.brand_name ?? "SKU telemetry"}
      subtitle={
        item
          ? `${item.generic_salt} · ${item.dosage_form} · ${item.medicine_id}`
          : undefined
      }
    >
      {item ? (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-control border border-hairline bg-canvas p-3">
              <p className="text-[12px] text-ink-muted">On hand</p>
              <p className="mt-1 font-mono-tabular text-[18px] font-semibold text-ink-primary">
                {item.current_stock_units.toFixed(1)}
              </p>
              <p className="mt-0.5 text-[12px] text-ink-secondary">
                Cover: {formatDaysOfCover(item.days_of_cover)}
              </p>
            </div>
            <div className="rounded-control border border-hairline bg-canvas p-3">
              <p className="text-[12px] text-ink-muted">Reorder point</p>
              <p className="mt-1 font-mono-tabular text-[18px] font-semibold text-ink-primary">
                {item.reorder_point.toFixed(1)}
              </p>
              <p className="mt-0.5 text-[12px] text-ink-secondary">
                Class {item.abc_class} · {item.demand_pattern}
              </p>
            </div>
            <div className="rounded-control border border-hairline bg-canvas p-3">
              <p className="text-[12px] text-ink-muted">7d forecast</p>
              <p className="mt-1 font-mono-tabular text-[18px] font-semibold text-ink-primary">
                {item.predicted_7d_demand.toFixed(1)}
              </p>
              <p className="mt-0.5 text-[12px] text-ink-secondary">
                {(item.predicted_7d_demand / 7).toFixed(1)} / day
              </p>
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-[14px] font-medium text-ink-primary">
                  30-day dispensing velocity
                </h3>
                <p className="text-[12px] text-ink-secondary">
                  Daily units sold at {branchId}
                </p>
              </div>
              {stockoutDays.length > 0 ? (
                <Badge tone="critical">
                  {stockoutDays.length} stockout{" "}
                  {stockoutDays.length === 1 ? "day" : "days"}
                </Badge>
              ) : (
                <Badge tone="healthy">Zero stockouts</Badge>
              )}
            </div>

            {error ? (
              <ErrorBanner error={error} onRetry={loadSales} />
            ) : loading ? (
              <Skeleton className="h-56 w-full" />
            ) : sales.length === 0 ? (
              <div className="rounded-control border border-hairline bg-canvas px-4 py-10 text-center text-[13px] text-ink-secondary">
                No historical sales recorded in the past 30 days for this SKU.
              </div>
            ) : (
              <div className="h-60 w-full rounded-control border border-hairline bg-surface p-3">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={sales}
                    margin={{ top: 8, right: 8, left: -18, bottom: 0 }}
                  >
                    <CartesianGrid
                      stroke="var(--border-hairline)"
                      strokeDasharray="3 3"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="date"
                      tickFormatter={formatShortDate}
                      tick={{ fontSize: 12, fill: "var(--ink-muted)" }}
                      axisLine={{ stroke: "var(--border-hairline)" }}
                      tickLine={false}
                      minTickGap={24}
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: "var(--ink-muted)" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      formatter={(val: number) => [
                        `${val.toFixed(1)} units`,
                        "Dispensed",
                      ]}
                      labelFormatter={(label: string) =>
                        `Date: ${formatShortDate(String(label))}`
                      }
                      contentStyle={{
                        backgroundColor: "var(--bg-surface)",
                        borderColor: "var(--border-hairline)",
                        borderRadius: "8px",
                        fontSize: "12px",
                        color: "var(--ink-primary)",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="units_sold"
                      stroke="var(--accent-primary)"
                      strokeWidth={1.75}
                      fill="var(--accent-subtle)"
                      isAnimationActive={false}
                    />
                    {stockoutDays.map((sd) => (
                      <ReferenceDot
                        key={sd.date}
                        x={sd.date}
                        y={sd.units_sold}
                        r={4}
                        fill="var(--status-critical-ink)"
                        stroke="var(--bg-surface)"
                        strokeWidth={1.5}
                      />
                    ))}
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="rounded-control border border-hairline bg-canvas px-4 py-3">
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-ink-secondary">30-day cumulative volume</span>
              <span className="font-mono-tabular font-medium text-ink-primary">
                {totalUnits30d.toFixed(1)} units
              </span>
            </div>
            <div className="mt-1.5 flex items-center justify-between text-[13px]">
              <span className="text-ink-secondary">30-day gross revenue</span>
              <span className="font-mono-tabular font-medium text-ink-primary">
                {formatINR(totalRevenue30d, 2)}
              </span>
            </div>
          </div>
        </div>
      ) : null}
    </SlideOver>
  );
}
