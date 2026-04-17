// User Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  createdAt: string;
  connectedAccounts: ConnectedAccount[];
  savedDatasets: string[];
}

export interface ConnectedAccount {
  provider: 'kaggle' | 'github' | 'huggingface';
  username?: string;
  connected: boolean;
  connectedAt?: string;
}

// Dataset Types
export interface Dataset {
  id: string;
  title: string;
  description: string;
  source: 'kaggle' | 'github' | 'huggingface' | 'government' | 'upload';
  format: 'csv' | 'json' | 'parquet' | 'excel';
  size: string;
  sizeBytes: number;
  relevanceScore: number;
  qualityScore: 'high' | 'medium' | 'low';
  downloadUrl: string;
  previewUrl?: string;
  tags: string[];
  lastUpdated: string;
  author: string;
  license: string;
}

export interface DatasetMetrics {
  rows: number;
  columns: number;
  missingPercent: number;
  duplicatePercent: number;
  columnTypes: ColumnType[];
  sampleData: Record<string, unknown>[];
}

export interface ColumnType {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'object';
  nullCount: number;
  uniqueCount: number;
}

// Enhanced Insight (Feature 2)
export interface InsightItem {
  title: string;
  description: string;
  why_it_matters: string;
  suggested_action: string;
  severity: 'info' | 'warning' | 'critical';
  category: 'missing' | 'duplicates' | 'correlation' | 'distribution' | 'size' | 'column' | 'general';
}

// Score Breakdown (Feature 3)
export interface ScoreComponent {
  name: string;
  score: number;
  maxScore: number;
  label: string;
  description: string;
}

export interface ScoreBreakdown {
  overall: number;
  components: ScoreComponent[];
}

// Bias Detection (Feature 7)
export interface BiasWarning {
  type: 'class_imbalance' | 'feature_skewness' | 'feature_dominance' | 'low_variance' | 'outlier_heavy' | 'proxy_variable';
  severity: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  affected_columns: string[];
  suggestion: string;
}

// Next Steps (Feature 5)
export interface NextStep {
  order: number;
  title: string;
  description: string;
  action_type: 'preprocess' | 'analyze' | 'model' | 'info';
  action_key?: string;
  is_critical: boolean;
}

export interface DatasetDetails extends Dataset {
  metrics: DatasetMetrics;
  correlations: Correlation[];
  distributions: Distribution[];
  mlRecommendation: MLRecommendation;
  insights?: InsightItem[];
  score?: number;
  scoreExplanation?: string;
  scoreBreakdown?: ScoreBreakdown;
  biasWarnings?: BiasWarning[];
  nextSteps?: NextStep[];
  warnings?: string[];
}

export interface Correlation {
  column1: string;
  column2: string;
  value: number;
}

export interface Distribution {
  column: string;
  bins: { label: string; count: number }[];
}

export interface MLRecommendation {
  task: 'classification' | 'regression' | 'clustering' | 'time-series';
  confidence: number;
  suggestedModels: string[];
  targetColumn?: string;
  reasoning: string;
  useCases?: string[];
}

// Search Types
export interface SearchFilters {
  format?: string[];
  size?: 'small' | 'medium' | 'large' | 'all';
  freshness?: 'day' | 'week' | 'month' | 'year' | 'all';
  source?: string[];
  quality?: string[];
}

export interface SearchRequest {
  query: string;
  description?: string;
  filters?: SearchFilters;
  page?: number;
  limit?: number;
}

export interface SearchResponse {
  datasets: Dataset[];
  total: number;
  page: number;
  totalPages: number;
}

// Comparison Types (Feature 1)
export interface DatasetSummary {
  id: string;
  title: string;
  source: string;
  rows: number;
  columns: number;
  missingPercent: number;
  duplicatePercent: number;
  qualityScore: number;
  qualityLabel: string;
  mlTask: string;
  targetColumn?: string;
  numericColumnCount: number;
  categoricalColumnCount: number;
  avgNullsPerColumn: number;
  correlationStrength: string;
  sizeBytes: number;
}

export interface ComparisonResult {
  datasets: DatasetSummary[];
  bestDatasetId: string;
  explanation: string;
  metricComparisons: {
    metric: string;
    dataset1_value: string;
    dataset2_value: string;
    winner: string;
    explanation: string;
  }[];
}

// Preprocessing Types (Feature 4)
export interface PreprocessStep {
  action: string;
  params?: Record<string, unknown>;
}

export interface PreprocessResponse {
  dataset_id: string;
  success: boolean;
  original_metrics: DatasetMetrics;
  updated_metrics: DatasetMetrics;
  applied_steps: string[];
  rows_removed: number;
  columns_removed: number;
  columns_added: number;
  download_filename: string;
  summary: string;
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}
