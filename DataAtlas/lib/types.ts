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
  source: 'kaggle' | 'github' | 'huggingface' | 'government';
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

export interface DatasetDetails extends Dataset {
  metrics: DatasetMetrics;
  correlations: Correlation[];
  distributions: Distribution[];
  mlRecommendation: MLRecommendation;
  insights?: string[];
  score?: number;
  scoreExplanation?: string;
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
