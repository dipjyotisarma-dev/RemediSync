import type {
  AbcClass,
  AnalyticsOverviewResponse,
  ApiErrorEnvelope,
  BatchExpiryResponse,
  BranchInventoryResponse,
  HealthResponse,
  OrderApproveRequest,
  OrderApproveResponse,
  ReplenishmentRecommendationsResponse,
  SalesHistoryResponse,
  UrgencyTier,
} from "@/types/api";

export class RemediSyncApiError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly correlationId: string;
  public readonly timestamp: string;

  constructor(params: {
    statusCode: number;
    code: string;
    message: string;
    correlationId: string;
    timestamp: string;
  }) {
    super(params.message);
    this.name = "RemediSyncApiError";
    this.statusCode = params.statusCode;
    this.code = params.code;
    this.correlationId = params.correlationId;
    this.timestamp = params.timestamp;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!isRecord(value) || value.success !== false || !isRecord(value.error)) {
    return false;
  }
  const err = value.error;
  return (
    typeof err.code === "string" &&
    typeof err.message === "string" &&
    typeof err.correlation_id === "string"
  );
}

function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured && configured.trim().length > 0) {
    return configured.replace(/\/+$/, "");
  }
  return "/api/v1";
}

function buildUrl(
  path: string,
  params?: Record<string, string | number | undefined>
): string {
  const base = `${getApiBaseUrl()}${path}`;
  if (!params) {
    return base;
  }
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query.length > 0 ? `${base}?${query}` : base;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new RemediSyncApiError({
      statusCode: 0,
      code: "NETWORK_UNREACHABLE",
      message:
        "Cannot reach RemediSync API at localhost:8000. Verify the FastAPI server is running.",
      correlationId: "offline",
      timestamp: new Date().toISOString(),
    });
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    if (isApiErrorEnvelope(payload)) {
      throw new RemediSyncApiError({
        statusCode: response.status,
        code: payload.error.code,
        message: payload.error.message,
        correlationId: payload.error.correlation_id,
        timestamp: payload.error.timestamp,
      });
    }
    throw new RemediSyncApiError({
      statusCode: response.status,
      code: `HTTP_${response.status}`,
      message: `Request failed with status ${response.status}.`,
      correlationId: "unknown",
      timestamp: new Date().toISOString(),
    });
  }

  return payload as T;
}

export const apiClient = {
  getHealth(): Promise<HealthResponse> {
    return requestJson<HealthResponse>(buildUrl("/health"));
  },

  getAnalyticsOverview(options?: {
    branchId?: string;
    days?: number;
  }): Promise<AnalyticsOverviewResponse> {
    return requestJson<AnalyticsOverviewResponse>(
      buildUrl("/analytics/overview", {
        branch_id:
          options?.branchId && options.branchId !== "ALL"
            ? options.branchId
            : undefined,
        days: options?.days,
      })
    );
  },

  getBranchInventory(options: {
    branchId: string;
    category?: string;
    abcClass?: AbcClass | string;
    limit?: number;
    offset?: number;
  }): Promise<BranchInventoryResponse> {
    return requestJson<BranchInventoryResponse>(
      buildUrl(
        `/inventory/branches/${encodeURIComponent(options.branchId)}`,
        {
          category: options.category,
          abc_class: options.abcClass,
          limit: options.limit,
          offset: options.offset,
        }
      )
    );
  },

  getExpiringBatches(options?: {
    branchId?: string;
    maxDaysToExpiry?: number;
  }): Promise<BatchExpiryResponse> {
    return requestJson<BatchExpiryResponse>(
      buildUrl("/inventory/batches/expiry-risk", {
        branch_id:
          options?.branchId && options.branchId !== "ALL"
            ? options.branchId
            : undefined,
        max_days_to_expiry: options?.maxDaysToExpiry,
      })
    );
  },

  getReplenishmentRecommendations(options: {
    branchId: string;
    urgency?: UrgencyTier | string;
    supplierId?: string;
  }): Promise<ReplenishmentRecommendationsResponse> {
    return requestJson<ReplenishmentRecommendationsResponse>(
      buildUrl("/recommendations/replenish", {
        branch_id: options.branchId,
        urgency: options.urgency,
        supplier_id: options.supplierId,
      })
    );
  },

  approveOrders(request: OrderApproveRequest): Promise<OrderApproveResponse> {
    return requestJson<OrderApproveResponse>(buildUrl("/orders/approve"), {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  getSalesHistory(options: {
    branchId: string;
    medicineId: string;
    days?: number;
  }): Promise<SalesHistoryResponse> {
    return requestJson<SalesHistoryResponse>(
      buildUrl("/sales/history", {
        branch_id: options.branchId,
        medicine_id: options.medicineId,
        days: options.days,
      })
    );
  },
};
