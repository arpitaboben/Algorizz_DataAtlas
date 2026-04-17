'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ScoreBreakdown } from '@/lib/types';
import { Shield, AlertCircle, Database, Columns3 } from 'lucide-react';

interface HealthBreakdownProps {
  score: number;
  breakdown: ScoreBreakdown;
}

const componentIcons: Record<string, typeof Shield> = {
  completeness: AlertCircle,
  uniqueness: Database,
  size: Database,
  diversity: Columns3,
};

const componentLabels: Record<string, string> = {
  completeness: 'Data Completeness',
  uniqueness: 'Data Uniqueness',
  size: 'Dataset Size',
  diversity: 'Feature Diversity',
};

function getScoreColor(score: number, max: number): string {
  const pct = (score / max) * 100;
  if (pct >= 80) return 'text-emerald-500';
  if (pct >= 60) return 'text-yellow-500';
  if (pct >= 40) return 'text-orange-500';
  return 'text-red-500';
}

function getProgressColor(score: number, max: number): string {
  const pct = (score / max) * 100;
  if (pct >= 80) return '[&>div]:bg-emerald-500';
  if (pct >= 60) return '[&>div]:bg-yellow-500';
  if (pct >= 40) return '[&>div]:bg-orange-500';
  return '[&>div]:bg-red-500';
}

function getLabelColor(label: string): string {
  if (label === 'Excellent') return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
  if (label === 'Good') return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
  if (label === 'Fair') return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
  if (label === 'Poor') return 'bg-red-500/10 text-red-500 border-red-500/20';
  return 'bg-muted text-muted-foreground';
}

export function HealthBreakdown({ score, breakdown }: HealthBreakdownProps) {
  const overallColor = score >= 70 ? 'text-emerald-500' : score >= 40 ? 'text-yellow-500' : 'text-red-500';
  const overallRingColor = score >= 70 ? 'stroke-emerald-500' : score >= 40 ? 'stroke-yellow-500' : 'stroke-red-500';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Dataset Health Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center gap-8 md:flex-row">
          {/* Circular Score */}
          <div className="flex flex-col items-center">
            <div className="relative h-36 w-36">
              <svg className="h-36 w-36 -rotate-90" viewBox="0 0 120 120">
                <circle
                  cx="60" cy="60" r="52"
                  fill="none"
                  className="stroke-muted"
                  strokeWidth="8"
                />
                <circle
                  cx="60" cy="60" r="52"
                  fill="none"
                  className={overallRingColor}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${(score / 100) * 327} 327`}
                  style={{ transition: 'stroke-dasharray 1s ease' }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-3xl font-bold ${overallColor}`}>{score}</span>
                <span className="text-xs text-muted-foreground">/100</span>
              </div>
            </div>
            <span className="mt-2 text-sm font-medium text-muted-foreground">
              {score >= 70 ? 'High Quality' : score >= 40 ? 'Medium Quality' : 'Low Quality'}
            </span>
          </div>

          {/* Sub-scores */}
          <div className="flex-1 space-y-4 w-full">
            {breakdown.components.map((comp) => {
              const Icon = componentIcons[comp.name] || Shield;
              const pct = Math.round((comp.score / comp.maxScore) * 100);

              return (
                <div key={comp.name} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className={`h-4 w-4 ${getScoreColor(comp.score, comp.maxScore)}`} />
                      <span className="text-sm font-medium text-foreground">
                        {componentLabels[comp.name] || comp.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${getLabelColor(comp.label)}`}>
                        {comp.label}
                      </span>
                      <span className={`text-sm font-bold ${getScoreColor(comp.score, comp.maxScore)}`}>
                        {comp.score}/{comp.maxScore}
                      </span>
                    </div>
                  </div>
                  <Progress value={pct} className={`h-2 ${getProgressColor(comp.score, comp.maxScore)}`} />
                  <p className="text-xs text-muted-foreground">{comp.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
