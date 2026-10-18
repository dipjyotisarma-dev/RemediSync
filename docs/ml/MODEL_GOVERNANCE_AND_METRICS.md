# Machine Learning Model Governance & Evaluation Protocol

## 1. Machine Learning Model Card

### 1.1 Objective & Target Definition
The forecasting subsystem acts as a probabilistic estimator of customer demand over a 7-day forward rolling replenishment window.
- **Granularity:** `[branch_id, medicine_id, date]`
- **Mathematical Target ($y$):**
  $$y_{m, b, t} = \sum_{k=1}^{7} \text{units\_sold}_{m, b, t+k}$$
- **Objective:** Minimize forecast discrepancy on forward consumer demand across all 516 active pharmacy series without temporal data leakage.

### 1.2 Model Input Feature Contract (31 Columns)
The feature matrix is populated strictly through the [`FeaturePipeline`](file:///D:/RemediSync/src/features/feature_pipeline.py) under the `.shift(1)` rule:

| Feature Group | Column Names | Data Type | Leakage Guard |
| :--- | :--- | :--- | :--- |
| **Identifiers** | `date`, `branch_id`, `medicine_id` | `date`, `string` | Categorical keys |
| **Categorical Metadata** | `category`, `dosage_form`, `location_type`, `demand_pattern`, `abc_class` | `string` / `category` | Static / historical profile |
| **Numerical Metadata** | `mrp`, `cost_price`, `adi`, `cv2` | `float64` | Pricing & historic volatility |
| **Calendar Signals** | `day_of_week`, `day_of_month`, `month`, `quarter`, `is_payday_week` | `int8` / `int16` | Deterministic calendar math |
| **Cyclical Trigonometric** | `sin_dow`, `cos_dow`, `sin_month`, `cos_month` | `float64` | Smooth cyclical wrap |
| **Historical Lags** | `sales_lag_7`, `sales_lag_14`, `sales_lag_21`, `sales_lag_28` | `float64` | Derived strictly from $t-7, t-14, t-21, t-28$ |
| **Rolling Demand Statistics** | `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`, `rolling_std_7`, `rolling_std_28` | `float64` | Rolling windows applied to `units_sold.shift(1)` |
| **Label** | `target_7d` | `float64` | Forward sum $t+1 \to t+7$ |

---

## 2. Validation Protocol: Strict Walk-Forward Chronological Splitting

### 2.1 The "No Lookahead Bias" Rule
Standard random cross-validation ($K$-Fold) randomly samples rows from the entire timeline. In retail demand forecasting, this leaks future trend and promotional information backward into past observations, producing artificially low errors that fail completely in production.

RemediSync enforces a **Chronological Walk-Forward Backtest**:
```
Total Timeline: 2025-01-29  ───────────────────────────────>  2026-09-23 (603 Days)

[  Training Set: 2025-01-29 to 2026-06-30 (518 Days)  ] │ [  Test Set: 2026-07-01 to 2026-09-23 (85 Days)  ]
```
- **Training Window:** Historical data up to June 30, 2026.
- **Unseen Test Window:** Final ~3 months (85 days) of telemetry, covering summer peak demand, monsoon disease surges, and multiple monthly payday refill cycles.
- **Zero Overlap:** The model never trains on any observation within or after the test horizon.

---

## 3. Evaluation Metrics

Model performance is evaluated across four complementary quantitative metrics:

### 3.1 Primary Metric: Weighted Absolute Percentage Error (WAPE)
$$\text{WAPE} = \frac{\sum_{i=1}^N |y_i - \hat{y}_i|}{\sum_{i=1}^N y_i}$$
- **Why WAPE:** Standard MAPE divides each error by $y_i$, which blows up to infinity on low-demand or zero-demand days ($y_i = 0$ or $1$). WAPE weights the error by the volume of the product, accurately reflecting the financial impact on working capital.
- **Production Target:** $\text{WAPE} \le 22.0\%$.

### 3.2 Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
- **Interpretation:** The average unit error per series over a 7-day window.

### 3.3 Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- **Interpretation:** Heavily penalizes large forecasting misses, alerting engineers to volatile erratic SKUs.

### 3.4 Aggregate Bias (Tracking Signal)
$$\text{Bias} = \frac{\sum_{i=1}^N (\hat{y}_i - y_i)}{\sum_{i=1}^N y_i}$$
- **Interpretation:** 
  - $\text{Bias} > +0.05$ indicates systematic over-forecasting (risks dead stock and expiry write-offs).
  - $\text{Bias} < -0.05$ indicates systematic under-forecasting (risks customer prescription stockouts).
- **Target:** $-0.03 \le \text{Bias} \le +0.03$.

---

## 4. Model Promotion & Deployment Gates

To promote any machine learning model (e.g. HistGradientBoosting, LightGBM, Random Forest) to production, it must pass three mandatory release gates:

1. **The Heuristic Benchmark Gate:**
   $$\text{WAPE}_{\text{candidate}} \le 0.80 \times \text{WAPE}_{\text{7d\_moving\_average}}$$
   The candidate ML model must demonstrate at least a **20% relative error reduction** over the naive 7-day moving average benchmark.
2. **The Pareto Class A Safety Gate:**
   On the top 70 revenue drivers (Class A SKUs), the candidate model's WAPE must not exceed **18.0%**.
3. **The Bias Guardrail:**
   Aggregate model bias on the test set must remain within $[-3\%, +3\%]$.

---

## 5. Drift Monitoring & Automated Retraining Triggers

In production, models degrade over time due to seasonal disease shifts, inflation, or competitor store openings:
- **Population Stability Index (PSI):** Feature distributions are evaluated weekly against baseline distributions. A $\text{PSI} > 0.20$ triggers an engineering alert.
- **Rolling WAPE Degradation:** If the 14-day rolling WAPE rises above $28.0\%$ in production, an automated model retraining pipeline is triggered.
- **Scheduled Retraining:** Models are retrained bi-weekly on the latest 12 months of transactional telemetry.
