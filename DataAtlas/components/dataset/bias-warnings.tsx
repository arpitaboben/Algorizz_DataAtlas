'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BiasWarning } from '@/lib/types';
import { ShieldAlert, AlertTriangle, Info } from 'lucide-react';

interface BiasWarningsProps {
  warnings: BiasWarning[];
}

const severityStyles: Record<string, { border: string; bg: string; icon: string; badge: string }> = {
  high: {
    border: 'border-red-500/30',
    bg: 'bg-red-500/5',
    icon: 'text-red-500',
    badge: 'border-red-500/30 bg-red-500/10 text-red-500',
  },
  medium: {
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/5',
    icon: 'text-yellow-500',
    badge: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-500',
  },
  low: {
    border: 'border-blue-500/30',
    bg: 'bg-blue-500/5',
    icon: 'text-blue-500',
    badge: 'border-blue-500/30 bg-blue-500/10 text-blue-500',
  },
};

const typeLabels: Record<string, string> = {
  class_imbalance: 'Class Imbalance',
  feature_skewness: 'Feature Skewness',
  feature_dominance: 'Feature Dominance',
  low_variance: 'Low Variance',
  outlier_heavy: 'Outlier Heavy',
  proxy_variable: 'Sensitive Data',
};

export function BiasWarnings({ warnings }: BiasWarningsProps) {
  if (!warnings || warnings.length === 0) return null;

  // Sort: high severity first
  const sorted = [...warnings].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return (order[a.severity] ?? 2) - (order[b.severity] ?? 2);
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-yellow-500" />
          Bias & Fairness Warnings
          <Badge variant="secondary">{warnings.length}</Badge>
        </CardTitle>
        <CardDescription>Potential data bias issues that may affect model fairness</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {sorted.map((warning, index) => {
          const style = severityStyles[warning.severity] || severityStyles.low;
          const SeverityIcon = warning.severity === 'high' ? AlertTriangle : warning.severity === 'medium' ? AlertTriangle : Info;

          return (
            <div
              key={`${warning.type}-${index}`}
              className={`rounded-lg border p-4 ${style.border} ${style.bg}`}
            >
              <div className="flex items-start gap-3">
                <SeverityIcon className={`mt-0.5 h-5 w-5 shrink-0 ${style.icon}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-sm font-medium text-foreground">{warning.title}</span>
                    <Badge variant="outline" className={`text-xs ${style.badge}`}>
                      {warning.severity}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      {typeLabels[warning.type] || warning.type}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-2">{warning.description}</p>

                  {warning.affected_columns.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {warning.affected_columns.slice(0, 6).map((col) => (
                        <Badge key={col} variant="outline" className="text-xs font-mono">
                          {col}
                        </Badge>
                      ))}
                      {warning.affected_columns.length > 6 && (
                        <Badge variant="outline" className="text-xs">
                          +{warning.affected_columns.length - 6} more
                        </Badge>
                      )}
                    </div>
                  )}

                  {warning.suggestion && (
                    <div className="rounded bg-muted/50 p-2 mt-2">
                      <p className="text-xs text-muted-foreground">
                        <span className="font-medium text-foreground">💡 Suggestion:</span> {warning.suggestion}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
