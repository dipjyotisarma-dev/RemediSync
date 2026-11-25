"use client";

import * as React from "react";
import { ReplenishmentWorkbench } from "@/components/features/replenishment/ReplenishmentWorkbench";
import { Badge } from "@/components/ui/Badge";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useBranchContext } from "@/context/BranchContext";
import { useToast } from "@/context/ToastContext";
import { getBranchLabel } from "@/lib/constants";
import { formatINR } from "@/lib/format";
import { apiClient, RemediSyncApiError } from "@/services/apiClient";
import type {
  OrderCreatedItem,
  OrderItemRequest,
  RecommendationItem,
} from "@/types/api";

export default function ReplenishmentPage(): React.ReactElement {
  const { activeStoreBranchId, refreshNonce, triggerRefresh } =
    useBranchContext();
  const { pushToast } = useToast();

  const [recommendations, setRecommendations] = React.useState<
    RecommendationItem[]
  >([]);
  const [recentOrders, setRecentOrders] = React.useState<OrderCreatedItem[]>(
    []
  );
  const [loading, setLoading] = React.useState<boolean>(true);
  const [submitting, setSubmitting] = React.useState<boolean>(false);
  const [error, setError] = React.useState<unknown>(null);

  const loadRecommendations = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getReplenishmentRecommendations({
        branchId: activeStoreBranchId,
      });
      setRecommendations(res.recommendations);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [activeStoreBranchId, refreshNonce]);

  React.useEffect(() => {
    void loadRecommendations();
  }, [loadRecommendations]);

  const handleApprove = async (orders: OrderItemRequest[]): Promise<void> => {
    setSubmitting(true);
    try {
      const res = await apiClient.approveOrders({
        branch_id: activeStoreBranchId,
        orders,
      });
      setRecentOrders(res.orders_created);
      const totalValue = res.orders_created.reduce(
        (sum, o) => sum + o.estimated_cost_inr,
        0
      );
      pushToast({
        title: "Order approved",
        description: `Created ${res.orders_created.length} PO record(s) totaling ${formatINR(totalValue, 2)}.`,
        tone: "healthy",
      });
      triggerRefresh();
    } catch (err) {
      const msg =
        err instanceof RemediSyncApiError
          ? err.message
          : "Purchase order approval failed.";
      pushToast({
        title: "Approval failed",
        description: msg,
        tone: "critical",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <p className="text-[13.5px] text-ink-secondary">
          Pack-rounded purchase recommendations for{" "}
          <span className="font-medium text-ink-primary">
            {getBranchLabel(activeStoreBranchId)}
          </span>
          , calibrated from 7-day demand velocity, supplier lead times, and
          therapeutic safety stock targets.
        </p>
      </div>

      {error ? (
        <ErrorBanner error={error} onRetry={loadRecommendations} />
      ) : null}

      {recentOrders.length > 0 ? (
        <div className="rounded-panel border border-status-healthy-border bg-status-healthy-bg px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-[13.5px] font-medium text-status-healthy-ink">
              Dispatched purchase orders recorded in database
            </p>
            <Badge tone="healthy" mono>
              {recentOrders.length} approved
            </Badge>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {recentOrders.map((po) => (
              <span
                key={po.order_id}
                className="rounded-badge border border-status-healthy-border bg-surface px-2.5 py-1 font-mono-tabular text-[12px] text-ink-primary"
              >
                {po.order_id} · {po.medicine_id} ({po.approved_units} units)
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <ReplenishmentWorkbench
        recommendations={recommendations}
        isLoading={loading}
        isSubmitting={submitting}
        onApprove={handleApprove}
      />
    </div>
  );
}
