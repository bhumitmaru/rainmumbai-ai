export interface User {
  id: number
  full_name: string
  email: string
  contact_number: string
  role: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface RegisterInput {
  full_name: string
  email: string
  contact_number: string
  password: string
  confirm_password: string
}

export interface DirectionProbabilities {
  increase: number
  no_change: number
  decrease: number
}

export interface ConfidenceBreakdown {
  overall: number
  data_quality: number
  model_performance: number
  stability: number
}

export interface Prediction {
  id: number
  generated_at: string
  target_timestamp: string
  current_index: number
  predicted_index: number
  expected_deviation: number
  direction: string
  probabilities: DirectionProbabilities
  category_current: string
  category_predicted: string
  confidence: ConfidenceBreakdown
  model_version: string
  disclaimer: string
}

export interface HistoryItem {
  id: number
  generated_at: string
  target_timestamp: string
  current_index: number
  predicted_index: number
  actual_index: number | null
  expected_deviation: number
  direction: string
  actual_direction: string | null
  confidence_overall: number
  model_version: string
  source: 'live' | 'backfill'
}

export interface PredictionHistory {
  items: HistoryItem[]
  total: number
  limit: number
  offset: number
}

export interface WeatherCurrent {
  station: string
  observed_at: string | null
  rainfall_mm: number | null
  temperature_c: number | null
  humidity_pct: number | null
  pressure_hpa: number | null
  wind_kmh: number | null
  source: string
  degraded: boolean
  warning: string | null
}

export interface RainfallPoint {
  time: string
  rainfall_mm: number | null
}

export interface WeatherForecast {
  current: WeatherCurrent
  hourly_rainfall_24h: RainfallPoint[]
  hourly: Array<{
    time: string
    rainfall_mm: number | null
    temperature_c: number | null
    humidity_pct: number | null
    pressure_hpa: number | null
    wind_kmh: number | null
  }>
  generated_at: string
  source: string
  degraded: boolean
  warning: string | null
}

export interface EvaluationSnapshot {
  id: number
  finished_at: string | null
  status: string
  mae: number | null
  rmse: number | null
  direction_accuracy: number | null
  direction_f1: number | null
  sample_count: number | null
  promoted: boolean
  notes: string | null
}

export interface PerformanceSample {
  prediction_id: number
  target_timestamp: string
  predicted_index: number
  actual_index: number
  error: number
  abs_error: number
  direction: string
  actual_direction: string
  direction_correct: boolean
  source: 'live' | 'backfill'
}

export interface PerformanceSeriesPoint {
  target_timestamp: string
  value: number
}

export interface BaselineMetrics {
  label: string
  mae: number | null
  direction_accuracy: number | null
}

export interface Performance {
  mae: number | null
  rmse: number | null
  direction_accuracy: number | null
  direction_f1: number | null
  sample_count: number
  sample_total: number
  last_evaluated_at: string | null
  model_version: string | null
  disclaimer: string
  baseline: BaselineMetrics
  evaluated_from: string | null
  evaluated_to: string | null
  error_series: PerformanceSeriesPoint[]
  cumulative_accuracy_series: PerformanceSeriesPoint[]
  limit: number
  offset: number
  evaluation_runs: EvaluationSnapshot[]
  samples: PerformanceSample[]
}

export interface Trade {
  target_timestamp: string
  direction: string
  current_index: number
  actual_index: number
  realized_delta: number
  pnl_inr: number
  source: 'live' | 'backfill'
}

export interface Profitability {
  decision_rule: string
  lots: number
  inr_per_mm: number
  trades: Trade[]
  total_pnl_inr: number
  trade_count: number
  win_rate_pct: number
  disclaimer: string
}
