'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Correlation } from '@/lib/types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TargetFeatureChartProps {
  correlations: Correlation[];
  targetColumn?: string;
}

function getCorrelationColor(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 0.7) return value > 0 ? 'text-emerald-500' : 'text-red-500';
  if (abs >= 0.4) return value > 0 ? 'text-blue-500' : 'text-orange-500';
  return 'text-muted-foreground';
}

function getBarColor(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 0.7) return value > 0 ? 'bg-emerald-500' : 'bg-red-500';
  if (abs >= 0.4) return value > 0 ? 'bg-blue-500' : 'bg-orange-500';
  return 'bg-muted-foreground/30';
}

function getStrengthLabel(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 0.9) return 'Very Strong';
  if (abs >= 0.7) return 'Strong';
  if (abs >= 0.5) return 'Moderate';
  if (abs >= 0.3) return 'Weak';
  return 'Very Weak';
}

export function TargetFeatureChart({ correlations, targetColumn }: TargetFeatureChartProps) {
  if (!correlations || correlations.length === 0) return null;

  // If target column specified, show only correlations involving it
  let relevantCorrelations = correlations;
  if (targetColumn) {
    relevantCorrelations = correlations.filter(
      (c) => c.column1 === targetColumn || c.column2 === targetColumn
    );
  }

  // Sort by absolute correlation
  const sorted = [...relevantCorrelations]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 12);

  if (sorted.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          {targetColumn ? `Feature Correlations with '${targetColumn}'` : 'Top Feature Correlations'}
        </CardTitle>
        <CardDescription>
          {targetColumn
            ? 'How strongly each feature relates to the target variable'
            : 'Strongest correlations between feature pairs'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sorted.map((corr, index) => {
            const featureName = targetColumn
              ? (corr.column1 === targetColumn ? corr.column2 : corr.column1)
              : `${corr.column1} ↔ ${corr.column2}`;
            const absVal = Math.abs(corr.value);
            const TrendIcon = corr.value > 0 ? TrendingUp : corr.value < 0 ? TrendingDown : Minus;

            return (
              <div key={`${corr.column1}-${corr.column2}`} className="flex items-center gap-3">
                <div className="w-40 shrink-0 truncate text-right">
                  <span className="font-mono text-xs text-foreground">{featureName}</span>
                </div>

                {/* Bar chart */}
                <div className="flex-1 flex items-center gap-2">
                  {/* Negative side */}
                  <div className="flex-1 h-5 flex justify-end">
                    {corr.value < 0 && (
                      <div
                        className={`h-full rounded-l ${getBarColor(corr.value)}`}
                        style={{ width: `${absVal * 100}%`, transition: 'width 0.5s ease', minWidth: '4px' }}
                      />
                    )}
                  </div>
                  {/* Center line */}
                  <div className="w-px h-5 bg-border shrink-0" />
                  {/* Positive side */}
                  <div className="flex-1 h-5">
                    {corr.value > 0 && (
                      <div
                        className={`h-full rounded-r ${getBarColor(corr.value)}`}
                        style={{ width: `${absVal * 100}%`, transition: 'width 0.5s ease', minWidth: '4px' }}
                      />
                    )}
                  </div>
                </div>

                {/* Value */}
                <div className="w-24 shrink-0 flex items-center gap-1">
                  <TrendIcon className={`h-3 w-3 ${getCorrelationColor(corr.value)}`} />
                  <span className={`text-xs font-bold ${getCorrelationColor(corr.value)}`}>
                    {corr.value > 0 ? '+' : ''}{corr.value.toFixed(3)}
                  </span>
                </div>

                <Badge
                  variant="secondary"
                  className={`text-[10px] shrink-0 ${
                    absVal >= 0.7 ? 'bg-primary/10 text-primary' : ''
                  }`}
                >
                  {getStrengthLabel(corr.value)}
                </Badge>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center justify-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <TrendingDown className="h-3 w-3 text-red-500" />
            <span>Negative</span>
          </div>
          <div className="flex items-center gap-1">
            <Minus className="h-3 w-3" />
            <span>None</span>
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-emerald-500" />
            <span>Positive</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
