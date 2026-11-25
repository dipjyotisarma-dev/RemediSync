export type AbcClass = "A" | "B" | "C";

export type UrgencyTier = "CRITICAL" | "REORDER" | "HEALTHY" | "OVERSTOCKED";

export interface ApiErrorDetail {
  code: string;
  message: string;
  timestamp: string;
  correlation_id: string;
}

export interface ApiErrorEnvelope {
  success: false;
  error: ApiErrorDetail;
}

export interface ModelMetadata {
  name: string;
  version: string;
  trained_date?: string | null;
  model_type?: string | null;
}

export interface HealthResponse {
  status: "HEALTHY" | "DEGRADED" | string;
  version: string;
  uptime_seconds: number;
  database: "CONNECTED" | "DISCONNECTED" | string;
  active_model: ModelMetadata;
}

export interface AnalyticsOverviewResponse {
  network_daily_revenue_inr: number;
  target_daily_revenue_inr: number;
  performance_ratio: number;
  network_stockout_rate: number;
  active_branches_count: number;
  total_skus_tracked: number;
  critical_stockouts_count: number;
  near_expiry_batches_count: number;
  estimated_near_expiry_value_inr: number;
}

export interface InventoryItem {
  medicine_id: string;
  brand_name: string;
  generic_salt: string;
  category: string;
  dosage_form: string;
  current_stock_units: number;
  pending_order_units: number;
  predicted_7d_demand: number;
  days_of_cover: number;
  reorder_point: number;
  is_below_rop: boolean;
  abc_class: AbcClass | string;
  demand_pattern: string;
}

export interface BranchInventoryResponse {
  branch_id: string;
  branch_name: string;
  total_records: number;
  items: InventoryItem[];
}

export interface BatchExpiryItem {
  batch_id: string;
  branch_id: string;
  medicine_id: string;
  brand_name: string;
  batch_number: string;
  expiry_date: string;
  days_to_expiry: number;
  current_quantity_units: number;
  predicted_demand_before_expiry: number;
  projected_unsold_units: number;
  projected_loss_inr: number;
  recommended_action: string;
  action_rationale: string;
}

export interface BatchExpiryResponse {
  total_at_risk_batches: number;
  total_write_off_exposure_inr: number;
  batches: BatchExpiryItem[];
}

export interface RecommendationItem {
  medicine_id: string;
  brand_name: string;
  primary_supplier_id: string;
  primary_supplier_name: string;
  supplier_fulfillment_tier: string;
  lead_time_days: number;
  current_stock_units: number;
  pending_order_units: number;
  predicted_7d_demand: number;
  safety_stock_units: number;
  reorder_point: number;
  recommended_order_units: number;
  unit_cost_price: number;
  estimated_cost_inr: number;
  pack_size_rounding: string;
  urgency: UrgencyTier | string;
  calculation_rationale: string;
}

export interface ReplenishmentRecommendationsResponse {
  branch_id: string;
  generated_at: string;
  total_recommended_orders: number;
  total_estimated_expenditure_inr: number;
  recommendations: RecommendationItem[];
}

export interface OrderItemRequest {
  medicine_id: string;
  supplier_id: string;
  approved_quantity_units: number;
  notes?: string;
}

export interface OrderApproveRequest {
  branch_id: string;
  orders: OrderItemRequest[];
}

export interface OrderCreatedItem {
  order_id: string;
  medicine_id: string;
  approved_units: number;
  estimated_cost_inr: number;
  status: string;
  created_at: string;
}

export interface OrderApproveResponse {
  success: boolean;
  orders_created: OrderCreatedItem[];
}

export interface DailySaleItem {
  date: string;
  units_sold: number;
  unit_selling_price: number;
  total_revenue: number;
  is_stockout_flag: boolean;
}

export interface SalesHistoryResponse {
  branch_id: string;
  medicine_id: string;
  total_days: number;
  sales: DailySaleItem[];
}
