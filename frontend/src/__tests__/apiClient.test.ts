import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient, RemediSyncApiError } from "@/services/apiClient";

describe("Typed FastAPI client & uniform error envelope parser", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("fetches network analytics overview with optional branch_id and days", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        network_daily_revenue_inr: 226534.59,
        target_daily_revenue_inr: 220000,
        performance_ratio: 1.029,
        network_stockout_rate: 0.018,
        active_branches_count: 4,
        total_skus_tracked: 129,
        critical_stockouts_count: 3,
        near_expiry_batches_count: 12,
        estimated_near_expiry_value_inr: 48200,
      }),
    });

    const res = await apiClient.getAnalyticsOverview({ branchId: "BR001", days: 30 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = String(fetchMock.mock.calls[0]?.[0]);
    expect(calledUrl).toContain("/api/v1/analytics/overview");
    expect(calledUrl).toContain("branch_id=BR001");
    expect(calledUrl).toContain("days=30");
    expect(res.network_daily_revenue_inr).toBe(226534.59);
  });

  it("parses FastAPI uniform error envelope into RemediSyncApiError with correlationId", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({
        success: false,
        error: {
          code: "BRANCH_NOT_FOUND",
          message: "Branch 'BR999' does not exist in master records.",
          timestamp: "2026-11-25T15:00:00Z",
          correlation_id: "req-98fbc12e",
        },
      }),
    });

    await expect(apiClient.getBranchInventory({ branchId: "BR999" })).rejects.toMatchObject({
      name: "RemediSyncApiError",
      statusCode: 404,
      code: "BRANCH_NOT_FOUND",
      correlationId: "req-98fbc12e",
    });
  });

  it("posts approved purchase orders and returns created PO records", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({
        success: true,
        orders_created: [
          {
            order_id: "PO-BR001-20261125-001",
            medicine_id: "MED002",
            approved_units: 60,
            estimated_cost_inr: 9600,
            status: "APPROVED",
            created_at: "2026-11-25T15:05:00Z",
          },
        ],
      }),
    });

    const out = await apiClient.approveOrders({
      branch_id: "BR001",
      orders: [
        {
          medicine_id: "MED002",
          supplier_id: "SUP001",
          approved_quantity_units: 60,
          notes: "Urgent restock",
        },
      ],
    });

    expect(out.success).toBe(true);
    expect(out.orders_created[0]?.order_id).toBe("PO-BR001-20261125-001");
    expect(RemediSyncApiError).toBeDefined();
  });
});
