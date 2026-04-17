'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, Loader2, GitCompare, Trophy, Crown, AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { DashboardHeader } from '@/components/dashboard/dashboard-header';
import { useAuth } from '@/lib/auth-context';
import { ComparisonResult } from '@/lib/types';

export default function ComparePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [isComparing, setIsComparing] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [datasetIds, setDatasetIds] = useState<string[]>([]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    try {
      const ids = JSON.parse(sessionStorage.getItem('compare_dataset_ids') || '[]');
      setDatasetIds(ids);
      if (ids.length === 2) {
        runComparison(ids);
      }
    } catch {
      setError('No datasets selected for comparison.');
    }
  }, []);

  const runComparison = async (ids: string[]) => {
    setIsComparing(true);
    setError(null);

    try {
      const response = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_ids: ids }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ message: 'Comparison failed' }));
        throw new Error(err.message || 'Comparison failed');
      }

      const data: ComparisonResult = await response.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comparison failed');
    } finally {
      setIsComparing(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Link
          href="/dashboard"
          className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to search
        </Link>

        <div className="mb-8">
          <h1 className="flex items-center gap-3 text-3xl font-bold text-foreground">
            <GitCompare className="h-8 w-8 text-primary" />
            Dataset Comparison
          </h1>
          <p className="mt-2 text-muted-foreground">
            Side-by-side comparison of two analyzed datasets
          </p>
        </div>

        {isComparing && (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <h3 className="mt-6 text-lg font-semibold text-foreground">Comparing Datasets</h3>
            <p className="mt-2 text-muted-foreground">Analyzing metrics side-by-side...</p>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <h3 className="mt-4 text-lg font-semibold text-foreground">Comparison Failed</h3>
            <p className="mt-2 max-w-md text-muted-foreground">{error}</p>
            <Link href="/dashboard">
              <Button className="mt-4">Back to Dashboard</Button>
            </Link>
          </div>
        )}

        {result && (
          <>
            {/* Winner Banner */}
            <Card className="mb-8 border-primary/30 bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5">
              <CardContent className="py-6">
                <div className="flex items-center gap-3 mb-3">
                  <Crown className="h-6 w-6 text-yellow-500" />
                  <h2 className="text-xl font-bold text-foreground">
                    Recommended: {result.datasets.find((d) => d.id === result.bestDatasetId)?.title || 'Unknown'}
                  </h2>
                  <Trophy className="h-5 w-5 text-yellow-500" />
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{result.explanation}</p>
              </CardContent>
            </Card>

            {/* Comparison Table */}
            <Card>
              <CardHeader>
                <CardTitle>Metric-by-Metric Comparison</CardTitle>
                <CardDescription>Green highlights indicate the better value for each metric</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="py-3 px-4 text-left text-sm font-medium text-muted-foreground">Metric</th>
                        <th className="py-3 px-4 text-center text-sm font-medium text-foreground">
                          <div className="flex items-center justify-center gap-2">
                            {result.datasets[0]?.id === result.bestDatasetId && (
                              <Crown className="h-4 w-4 text-yellow-500" />
                            )}
                            <span className="truncate max-w-[200px]">{result.datasets[0]?.title}</span>
                          </div>
                        </th>
                        <th className="py-3 px-4 text-center text-sm font-medium text-foreground">
                          <div className="flex items-center justify-center gap-2">
                            {result.datasets[1]?.id === result.bestDatasetId && (
                              <Crown className="h-4 w-4 text-yellow-500" />
                            )}
                            <span className="truncate max-w-[200px]">{result.datasets[1]?.title}</span>
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.metricComparisons.map((comp, index) => {
                        const ds1Wins = comp.winner === result.datasets[0]?.id;
                        const ds2Wins = comp.winner === result.datasets[1]?.id;

                        return (
                          <tr key={comp.metric} className={`border-b border-border/50 ${index % 2 === 0 ? '' : 'bg-muted/20'}`}>
                            <td className="py-3 px-4">
                              <p className="text-sm font-medium text-foreground">{comp.metric}</p>
                              <p className="text-xs text-muted-foreground">{comp.explanation}</p>
                            </td>
                            <td className={`py-3 px-4 text-center ${ds1Wins ? 'bg-emerald-500/10' : ''}`}>
                              <span className={`text-sm font-bold ${ds1Wins ? 'text-emerald-500' : 'text-foreground'}`}>
                                {comp.dataset1_value}
                              </span>
                              {ds1Wins && <Badge className="ml-2 bg-emerald-500/20 text-emerald-500 text-xs border-0">Better</Badge>}
                            </td>
                            <td className={`py-3 px-4 text-center ${ds2Wins ? 'bg-emerald-500/10' : ''}`}>
                              <span className={`text-sm font-bold ${ds2Wins ? 'text-emerald-500' : 'text-foreground'}`}>
                                {comp.dataset2_value}
                              </span>
                              {ds2Wins && <Badge className="ml-2 bg-emerald-500/20 text-emerald-500 text-xs border-0">Better</Badge>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <div className="mt-6 flex gap-3">
              <Link href={`/dataset/${result.bestDatasetId}`}>
                <Button className="gap-2">
                  <Trophy className="h-4 w-4" />
                  View Recommended Dataset
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="outline">Back to Search</Button>
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
