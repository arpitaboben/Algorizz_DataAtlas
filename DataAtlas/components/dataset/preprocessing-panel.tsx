'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Wrench, Download, ArrowRight, Check, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { PreprocessStep, PreprocessResponse, DatasetMetrics } from '@/lib/types';

interface PreprocessingPanelProps {
  datasetId: string;
  metrics: DatasetMetrics;
  onPreprocessComplete?: (response: PreprocessResponse) => void;
}

interface StepConfig {
  action: string;
  label: string;
  description: string;
  icon: string;
  paramOptions?: {
    key: string;
    label: string;
    options: { value: string; label: string }[];
    default: string;
  };
}

const AVAILABLE_STEPS: StepConfig[] = [
  {
    action: 'handle_missing',
    label: 'Handle Missing Values',
    description: 'Fill or remove missing data using advanced imputation techniques.',
    icon: '🔧',
    paramOptions: {
      key: 'strategy',
      label: 'Strategy',
      options: [
        { value: 'smart', label: 'Smart (Auto-select best per column)' },
        { value: 'knn', label: 'KNN Imputation (Advanced)' },
        { value: 'iterative', label: 'Iterative/MICE (Most Advanced)' },
        { value: 'median', label: 'Median / Mode Fill' },
        { value: 'mean', label: 'Mean / Mode Fill' },
        { value: 'drop_rows', label: 'Drop Rows with Missing' },
        { value: 'drop_cols', label: 'Drop Columns >50% Missing' },
      ],
      default: 'smart',
    },
  },
  {
    action: 'remove_duplicates',
    label: 'Remove Duplicates',
    description: 'Remove exact duplicate rows from the dataset.',
    icon: '🗑️',
  },
  {
    action: 'remove_outliers',
    label: 'Remove Outliers',
    description: 'Remove statistical outliers using IQR or Z-score method.',
    icon: '📊',
    paramOptions: {
      key: 'method',
      label: 'Method',
      options: [
        { value: 'iqr', label: 'IQR Method (Recommended)' },
        { value: 'zscore', label: 'Z-Score Method' },
      ],
      default: 'iqr',
    },
  },
  {
    action: 'handle_skewness',
    label: 'Fix Skewed Distributions',
    description: 'Apply power transforms to normalize skewed features.',
    icon: '📈',
    paramOptions: {
      key: 'method',
      label: 'Transform',
      options: [
        { value: 'yeo_johnson', label: 'Yeo-Johnson (Works for all values)' },
        { value: 'log', label: 'Log Transform (Positive values only)' },
        { value: 'sqrt', label: 'Square Root Transform' },
        { value: 'box_cox', label: 'Box-Cox (Positive values only)' },
      ],
      default: 'yeo_johnson',
    },
  },
  {
    action: 'normalize',
    label: 'Normalize Features',
    description: 'Scale numeric features to a standard range.',
    icon: '⚖️',
    paramOptions: {
      key: 'method',
      label: 'Method',
      options: [
        { value: 'robust', label: 'Robust Scaling (Outlier-resistant)' },
        { value: 'minmax', label: 'Min-Max Scaling [0, 1]' },
        { value: 'zscore', label: 'Z-Score Standardization' },
      ],
      default: 'robust',
    },
  },
  {
    action: 'remove_correlated',
    label: 'Remove Correlated Features',
    description: 'Drop one feature from pairs with very high correlation.',
    icon: '🔗',
    paramOptions: {
      key: 'threshold',
      label: 'Threshold',
      options: [
        { value: '0.95', label: '0.95 (Very strict)' },
        { value: '0.9', label: '0.90 (Recommended)' },
        { value: '0.8', label: '0.80 (Aggressive)' },
      ],
      default: '0.9',
    },
  },
  {
    action: 'encode_categorical',
    label: 'Encode Categorical Features',
    description: 'Convert text/categorical columns to numeric format.',
    icon: '🔢',
    paramOptions: {
      key: 'method',
      label: 'Encoding',
      options: [
        { value: 'onehot', label: 'One-Hot (Low cardinality) + Label (High cardinality)' },
        { value: 'label', label: 'Label Encoding (All columns)' },
      ],
      default: 'onehot',
    },
  },
  {
    action: 'drop_low_variance',
    label: 'Drop Low-Variance Features',
    description: 'Remove near-constant columns that provide no information.',
    icon: '✂️',
  },
];

export function PreprocessingPanel({ datasetId, metrics, onPreprocessComplete }: PreprocessingPanelProps) {
  const [enabledSteps, setEnabledSteps] = useState<Record<string, boolean>>({});
  const [stepParams, setStepParams] = useState<Record<string, Record<string, string>>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<PreprocessResponse | null>(null);
  const [expanded, setExpanded] = useState(true);

  const toggleStep = (action: string) => {
    setEnabledSteps((prev) => ({ ...prev, [action]: !prev[action] }));
  };

  const setParam = (action: string, key: string, value: string) => {
    setStepParams((prev) => ({
      ...prev,
      [action]: { ...prev[action], [key]: value },
    }));
  };

  const enabledCount = Object.values(enabledSteps).filter(Boolean).length;

  const handleApply = async () => {
    const steps: PreprocessStep[] = AVAILABLE_STEPS
      .filter((s) => enabledSteps[s.action])
      .map((s) => {
        const params: Record<string, unknown> = {};
        if (s.paramOptions) {
          const paramVal = stepParams[s.action]?.[s.paramOptions.key] || s.paramOptions.default;
          // Handle numeric params
          if (s.action === 'remove_correlated') {
            params[s.paramOptions.key] = parseFloat(paramVal);
          } else {
            params[s.paramOptions.key] = paramVal;
          }
        }
        return { action: s.action, params };
      });

    if (steps.length === 0) return;

    setIsProcessing(true);
    setResult(null);

    try {
      const response = await fetch('/api/preprocess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId, steps }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ message: 'Preprocessing failed' }));
        throw new Error(err.message || 'Preprocessing failed');
      }

      const data: PreprocessResponse = await response.json();
      setResult(data);
      if (onPreprocessComplete) onPreprocessComplete(data);
    } catch (error) {
      console.error('Preprocessing error:', error);
      setResult({
        dataset_id: datasetId,
        success: false,
        original_metrics: metrics,
        updated_metrics: metrics,
        applied_steps: [],
        rows_removed: 0,
        columns_removed: 0,
        columns_added: 0,
        download_filename: '',
        summary: error instanceof Error ? error.message : 'Preprocessing failed',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (result?.download_filename) {
      window.open(`/backend-api/preprocess/download/${result.download_filename}`, '_blank');
    }
  };

  return (
    <Card className="border-primary/20">
      <CardHeader className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-primary" />
            No-Code Preprocessing Engine
            {enabledCount > 0 && (
              <Badge variant="secondary" className="ml-2">{enabledCount} selected</Badge>
            )}
          </CardTitle>
          {expanded ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
        </div>
        <CardDescription>Clean and transform your dataset without writing code</CardDescription>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-6">
          {/* Step toggles */}
          <div className="space-y-3">
            {AVAILABLE_STEPS.map((step) => {
              const isEnabled = enabledSteps[step.action] || false;

              return (
                <div
                  key={step.action}
                  className={`rounded-lg border p-4 transition-all ${
                    isEnabled ? 'border-primary/50 bg-primary/5' : 'border-border'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{step.icon}</span>
                      <div>
                        <p className="text-sm font-medium text-foreground">{step.label}</p>
                        <p className="text-xs text-muted-foreground">{step.description}</p>
                      </div>
                    </div>
                    <Switch
                      checked={isEnabled}
                      onCheckedChange={() => toggleStep(step.action)}
                    />
                  </div>

                  {/* Param selector */}
                  {isEnabled && step.paramOptions && (
                    <div className="mt-3 ml-10">
                      <label className="mb-1 text-xs font-medium text-muted-foreground">
                        {step.paramOptions.label}
                      </label>
                      <Select
                        value={stepParams[step.action]?.[step.paramOptions.key] || step.paramOptions.default}
                        onValueChange={(val) => setParam(step.action, step.paramOptions!.key, val)}
                      >
                        <SelectTrigger className="h-8 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {step.paramOptions.options.map((opt) => (
                            <SelectItem key={opt.value} value={opt.value} className="text-xs">
                              {opt.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Apply button */}
          <div className="flex items-center gap-3">
            <Button
              onClick={handleApply}
              disabled={enabledCount === 0 || isProcessing}
              className="gap-2"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Apply {enabledCount} Step{enabledCount !== 1 ? 's' : ''}
                </>
              )}
            </Button>
            {enabledCount === 0 && (
              <span className="text-xs text-muted-foreground">Toggle at least one step to proceed</span>
            )}
          </div>

          {/* Results */}
          {result && (
            <div className={`rounded-lg border p-4 ${result.success ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
              <div className="flex items-center gap-2 mb-3">
                {result.success ? (
                  <Check className="h-5 w-5 text-emerald-500" />
                ) : (
                  <span className="text-red-500">✗</span>
                )}
                <span className="font-medium text-foreground">
                  {result.success ? 'Preprocessing Complete' : 'Preprocessing Failed'}
                </span>
              </div>

              <p className="text-sm text-muted-foreground mb-3">{result.summary}</p>

              {result.success && (
                <>
                  {/* Before vs After */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="rounded-lg bg-muted/50 p-3">
                      <p className="text-xs font-medium text-muted-foreground uppercase mb-2">Before</p>
                      <div className="space-y-1 text-sm">
                        <p><span className="text-muted-foreground">Rows:</span> <span className="font-medium">{result.original_metrics.rows?.toLocaleString()}</span></p>
                        <p><span className="text-muted-foreground">Columns:</span> <span className="font-medium">{result.original_metrics.columns}</span></p>
                        <p><span className="text-muted-foreground">Missing:</span> <span className="font-medium">{result.original_metrics.missingPercent}%</span></p>
                        <p><span className="text-muted-foreground">Duplicates:</span> <span className="font-medium">{result.original_metrics.duplicatePercent}%</span></p>
                      </div>
                    </div>
                    <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-3">
                      <p className="text-xs font-medium text-emerald-500 uppercase mb-2">After</p>
                      <div className="space-y-1 text-sm">
                        <p><span className="text-muted-foreground">Rows:</span> <span className="font-medium">{result.updated_metrics.rows?.toLocaleString()}</span></p>
                        <p><span className="text-muted-foreground">Columns:</span> <span className="font-medium">{result.updated_metrics.columns}</span></p>
                        <p><span className="text-muted-foreground">Missing:</span> <span className="font-medium text-emerald-500">{result.updated_metrics.missingPercent}%</span></p>
                        <p><span className="text-muted-foreground">Duplicates:</span> <span className="font-medium text-emerald-500">{result.updated_metrics.duplicatePercent}%</span></p>
                      </div>
                    </div>
                  </div>

                  {/* Changes summary */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {result.rows_removed > 0 && (
                      <Badge variant="secondary">{result.rows_removed.toLocaleString()} rows removed</Badge>
                    )}
                    {result.columns_removed > 0 && (
                      <Badge variant="secondary">{result.columns_removed} columns removed</Badge>
                    )}
                    {result.columns_added > 0 && (
                      <Badge variant="secondary">{result.columns_added} columns added</Badge>
                    )}
                    {result.applied_steps.map((s) => (
                      <Badge key={s} variant="outline" className="bg-primary/5"><Check className="h-3 w-3 mr-1" />{s}</Badge>
                    ))}
                  </div>

                  {/* Download button */}
                  {result.download_filename && (
                    <Button variant="outline" onClick={handleDownload} className="gap-2">
                      <Download className="h-4 w-4" />
                      Download Cleaned Dataset
                    </Button>
                  )}
                </>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
