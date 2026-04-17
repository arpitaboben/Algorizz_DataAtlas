'use client';

import { useState } from 'react';
import { Loader2, Download, Beaker, BarChart3, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

interface AugmentationPanelProps {
  datasetId: string;
  targetColumn?: string;
  taskType: string;
  isSmallDataset: boolean;
  isImbalanced: boolean;
}

interface AugmentResult {
  success: boolean;
  method_used: string;
  before: { rows: number; class_distribution?: Record<string, number> | null };
  after: { rows: number; class_distribution?: Record<string, number> | null };
  rows_added: number;
  download_filename: string;
  summary: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export function AugmentationPanel({
  datasetId,
  targetColumn,
  taskType,
  isSmallDataset,
  isImbalanced,
}: AugmentationPanelProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AugmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isSmallDataset && !isImbalanced) return null;
  if (!targetColumn) return null;

  const handleAugment = async (method: string) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/augment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          target_column: targetColumn,
          task_type: taskType,
          method,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ message: 'Augmentation failed' }));
        throw new Error(err.message || 'Augmentation failed');
      }

      const data: AugmentResult = await response.json();
      setResult(data);

      if (!data.success) {
        setError(data.summary);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Augmentation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (result?.download_filename) {
      window.open(`${BACKEND_URL}/api/augment/download/${result.download_filename}`, '_blank');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Beaker className="h-5 w-5 text-purple-500" />
          Data Augmentation
          {isImbalanced && <Badge variant="outline" className="text-xs border-yellow-500/30 text-yellow-500">Imbalanced</Badge>}
          {isSmallDataset && <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-500">Small Dataset</Badge>}
        </CardTitle>
        <CardDescription>
          {isImbalanced
            ? 'Your dataset has class imbalance. Augmentation can create synthetic samples to balance classes.'
            : 'Your dataset is small. Bootstrap augmentation can generate more training samples.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!result && !isLoading && (
          <div className="flex flex-wrap gap-3">
            {isImbalanced && (
              <Button onClick={() => handleAugment('smote')} className="gap-2">
                <Beaker className="h-4 w-4" />
                Apply SMOTE
              </Button>
            )}
            <Button
              variant={isImbalanced ? 'outline' : 'default'}
              onClick={() => handleAugment('bootstrap')}
              className="gap-2"
            >
              <BarChart3 className="h-4 w-4" />
              Bootstrap + Noise
            </Button>
            <Button variant="outline" onClick={() => handleAugment('auto')} className="gap-2">
              Auto-Detect Best Method
            </Button>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center gap-3 py-4">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Augmenting dataset...</span>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        )}

        {result && result.success && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-green-500">
              <CheckCircle2 className="h-4 w-4" />
              {result.summary}
            </div>

            {/* Before vs After comparison */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border border-border p-3">
                <p className="text-xs font-medium text-muted-foreground mb-2">Before</p>
                <p className="text-lg font-bold text-foreground">{result.before.rows?.toLocaleString()} rows</p>
                {result.before.class_distribution && (
                  <div className="mt-2 space-y-1">
                    {Object.entries(result.before.class_distribution).map(([cls, count]) => (
                      <div key={cls} className="flex justify-between text-xs text-muted-foreground">
                        <span>{cls}</span>
                        <span>{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-3">
                <p className="text-xs font-medium text-green-500 mb-2">After</p>
                <p className="text-lg font-bold text-foreground">{result.after.rows?.toLocaleString()} rows</p>
                {result.after.class_distribution && (
                  <div className="mt-2 space-y-1">
                    {Object.entries(result.after.class_distribution).map(([cls, count]) => (
                      <div key={cls} className="flex justify-between text-xs text-muted-foreground">
                        <span>{cls}</span>
                        <span>{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleDownload} className="gap-2">
                <Download className="h-4 w-4" />
                Download Augmented Dataset
              </Button>
              <Badge variant="secondary" className="self-center">
                +{result.rows_added.toLocaleString()} rows • {result.method_used}
              </Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
