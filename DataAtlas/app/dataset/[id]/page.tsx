'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Code,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  Loader2,
  FileText,
  Calendar,
  User,
  Scale,
  Lightbulb,
  BarChart3,
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { DashboardHeader } from '@/components/dashboard/dashboard-header';
import { MetricsCards } from '@/components/dataset/metrics-cards';
import { DataPreviewTable } from '@/components/dataset/data-preview-table';
import { DistributionChart } from '@/components/dataset/distribution-chart';
import { CorrelationChart } from '@/components/dataset/correlation-chart';
import { MLRecommendation } from '@/components/dataset/ml-recommendation';
import { HealthBreakdown } from '@/components/dataset/health-breakdown';
import { PreprocessingPanel } from '@/components/dataset/preprocessing-panel';
import { NextStepsPanel } from '@/components/dataset/next-steps-panel';
import { BiasWarnings } from '@/components/dataset/bias-warnings';
import { PipelineTracker } from '@/components/dataset/pipeline-tracker';
import { MissingHeatmap } from '@/components/dataset/missing-heatmap';
import { TargetFeatureChart } from '@/components/dataset/target-feature-chart';
import { AugmentationPanel } from '@/components/dataset/augmentation-panel';
import { VisualizationPanel } from '@/components/dataset/visualization-panel';
import { useAuth } from '@/lib/auth-context';
import { DatasetDetails, Dataset, InsightItem } from '@/lib/types';
import { cn } from '@/lib/utils';

const sourceColors: Record<string, string> = {
  kaggle: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  github: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  huggingface: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  government: 'bg-green-500/10 text-green-500 border-green-500/20',
  upload: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
};

const qualityColors: Record<string, string> = {
  high: 'bg-success/10 text-success border-success/20',
  medium: 'bg-warning/10 text-warning border-warning/20',
  low: 'bg-destructive/10 text-destructive border-destructive/20',
};

const insightSeverityStyles: Record<string, { border: string; bg: string; icon: string }> = {
  critical: { border: 'border-red-500/30', bg: 'bg-red-500/5', icon: '🔴' },
  warning: { border: 'border-yellow-500/30', bg: 'bg-yellow-500/5', icon: '⚠️' },
  info: { border: 'border-blue-500/30', bg: 'bg-blue-500/5', icon: '✅' },
};

export default function DatasetDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, user, updateUser } = useAuth();
  const [dataset, setDataset] = useState<DatasetDetails | null>(null);
  const [basicInfo, setBasicInfo] = useState<Dataset | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<InsightItem | null>(null);
  const [hasPreprocessed, setHasPreprocessed] = useState(false);
  const [showAllInsights, setShowAllInsights] = useState(false);
  const [showDetailedEDA, setShowDetailedEDA] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    const fetchDataset = async () => {
      setIsLoading(true);

      // Load basic dataset info from sessionStorage (set by DatasetCard click)
      const stored = sessionStorage.getItem(`dataset-${resolvedParams.id}`);
      if (stored) {
        const info = JSON.parse(stored) as Dataset;
        setBasicInfo(info);
      }

      // Try to get cached analysis from backend
      try {
        const response = await fetch(`/api/dataset/${resolvedParams.id}`);
        if (response.ok) {
          const data = await response.json();
          setDataset(data);
          setIsSaved(user?.savedDatasets?.includes(resolvedParams.id) || false);
          setIsLoading(false);
          return;
        }
      } catch {
        // Not cached yet — will trigger analysis
      }

      setIsLoading(false);

      // Auto-trigger analysis if we have basic info
      if (stored) {
        const info = JSON.parse(stored) as Dataset;
        triggerAnalysis(info);
      }
    };

    if (isAuthenticated) {
      fetchDataset();
    }
  }, [resolvedParams.id, isAuthenticated]);

  const triggerAnalysis = async (info: Dataset) => {
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const response = await fetch(`/api/dataset/${resolvedParams.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          download_url: info.downloadUrl,
          title: info.title,
          source: info.source,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ message: 'Analysis failed' }));
        throw new Error(err.message || 'Analysis failed');
      }

      const data = await response.json();
      setDataset(data);
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSave = () => {
    if (!user) return;
    const newSaved = isSaved
      ? user.savedDatasets.filter((id) => id !== resolvedParams.id)
      : [...user.savedDatasets, resolvedParams.id];
    updateUser({ savedDatasets: newSaved });
    setIsSaved(!isSaved);
  };

  const handleGenerateCode = () => {
    const title = dataset?.title || basicInfo?.title || 'dataset';
    const targetCol = dataset?.mlRecommendation?.targetColumn || 'target';
    const task = dataset?.mlRecommendation?.task || 'classification';

    const code = `# Auto-generated starter code for ${title}
import pandas as pd
from sklearn.model_selection import train_test_split
${task === 'regression' ? 'from sklearn.ensemble import RandomForestRegressor' : 'from sklearn.ensemble import RandomForestClassifier'}

# Load the dataset
df = pd.read_csv('${title.toLowerCase().replace(/\\s+/g, '_')}.csv')

# Basic preprocessing
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(df.head())
print(df.describe())

# Handle missing values
df = df.dropna()

# Suggested target column: ${targetCol}
# Suggested task: ${task}

# Split data
X = df.drop('${targetCol}', axis=1)
y = df['${targetCol}']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = ${task === 'regression' ? 'RandomForestRegressor' : 'RandomForestClassifier'}(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
print(f"Score: {model.score(X_test, y_test):.4f}")
`;
    navigator.clipboard.writeText(code);
    alert('Starter code copied to clipboard!');
  };

  // Determine pipeline step
  const getPipelineStep = () => {
    if (hasPreprocessed) return 'fix';
    if (dataset) return 'analyze';
    return 'search';
  };

  const getCompletedSteps = () => {
    const steps = ['search'];
    if (dataset) steps.push('analyze');
    if (hasPreprocessed) steps.push('fix');
    return steps;
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Show analysis in progress
  if (isAnalyzing) {
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

          {basicInfo && (
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground">{basicInfo.title}</h1>
              <p className="mt-3 max-w-3xl text-muted-foreground">{basicInfo.description}</p>
            </div>
          )}

          <div className="flex flex-col items-center justify-center py-16">
            <div className="relative">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <BarChart3 className="absolute inset-0 m-auto h-5 w-5 text-primary/60" />
            </div>
            <h3 className="mt-6 text-lg font-semibold text-foreground">Analyzing Dataset</h3>
            <p className="mt-2 max-w-md text-center text-muted-foreground">
              Downloading CSV, running comprehensive EDA, quality scoring,
              bias detection, and generating ML recommendations...
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <Badge variant="outline">📥 Downloading CSV</Badge>
              <Badge variant="outline">📊 Running EDA</Badge>
              <Badge variant="outline">🧮 Scoring Quality</Badge>
              <Badge variant="outline">💡 Generating Insights</Badge>
              <Badge variant="outline">🤖 ML Recommendations</Badge>
              <Badge variant="outline">⚖️ Bias Detection</Badge>
              <Badge variant="outline">📋 Next Steps</Badge>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Show error state
  if (analysisError) {
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

          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <h3 className="mt-4 text-lg font-semibold text-foreground">Analysis Failed</h3>
            <p className="mt-2 max-w-md text-muted-foreground">{analysisError}</p>
            {basicInfo && (
              <Button
                className="mt-4"
                onClick={() => triggerAnalysis(basicInfo)}
              >
                Retry Analysis
              </Button>
            )}
          </div>
        </main>
      </div>
    );
  }

  // No dataset loaded
  if (!dataset && !basicInfo) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader />
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-foreground">Dataset not found</h1>
            <p className="mt-2 text-muted-foreground">
              The dataset you&apos;re looking for doesn&apos;t exist or has been removed.
            </p>
            <Link href="/dashboard">
              <Button className="mt-4">Back to Dashboard</Button>
            </Link>
          </div>
        </main>
      </div>
    );
  }

  // Use dataset if analyzed, fall back to basicInfo
  const displayData = dataset || (basicInfo as any as DatasetDetails);
  if (!displayData) return null;

  const formattedDate = displayData.lastUpdated
    ? new Date(displayData.lastUpdated).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Unknown';

  const insights = dataset?.insights || [];
  const visibleInsights = showAllInsights ? insights : insights.slice(0, 4);

  // Detect if dataset is small or imbalanced (for augmentation panel)
  const isSmallDataset = (dataset?.metrics?.rows || 0) < 1000;
  const isImbalanced = (dataset?.biasWarnings || []).some(
    (w) => w.type === 'class_imbalance'
  );

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Back button */}
        <Link
          href="/dashboard"
          className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to search
        </Link>

        {/* Pipeline Tracker (Feature 8) */}
        {dataset && (
          <PipelineTracker
            currentStep={getPipelineStep()}
            completedSteps={getCompletedSteps()}
          />
        )}

        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex-1">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={cn('capitalize', sourceColors[displayData.source] || '')}>
                  {displayData.source}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn('capitalize', qualityColors[displayData.qualityScore] || '')}
                >
                  {displayData.qualityScore} quality
                </Badge>
                <div className="flex h-7 items-center justify-center rounded-full bg-primary/10 px-3">
                  <span className="text-sm font-bold text-primary">{displayData.relevanceScore}% match</span>
                </div>
                {dataset?.score !== undefined && (
                  <div className="flex h-7 items-center justify-center rounded-full bg-green-500/10 px-3">
                    <span className="text-sm font-bold text-green-500">Score: {dataset.score}/100</span>
                  </div>
                )}
              </div>
              <h1 className="text-3xl font-bold text-foreground">{displayData.title}</h1>
              <p className="mt-3 max-w-3xl text-muted-foreground">{displayData.description}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleSave}>
                {isSaved ? (
                  <>
                    <BookmarkCheck className="mr-2 h-4 w-4" />
                    Saved
                  </>
                ) : (
                  <>
                    <Bookmark className="mr-2 h-4 w-4" />
                    Save
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Meta info */}
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="uppercase">{displayData.format}</span>
              <span className="text-border">|</span>
              <span>{displayData.size}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span>Updated {formattedDate}</span>
            </div>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4" />
              <span>{displayData.author}</span>
            </div>
            <div className="flex items-center gap-2">
              <Scale className="h-4 w-4" />
              <span>{displayData.license}</span>
            </div>
          </div>

          {/* Tags */}
          <div className="mt-4 flex flex-wrap gap-2">
            {displayData.tags?.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        </div>

        {/* EDA Warnings */}
        {dataset?.warnings && dataset.warnings.length > 0 && (
          <section className="mb-8">
            <Card className="border-warning/20 bg-warning/5">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm font-medium">
                  <AlertTriangle className="h-4 w-4 text-warning" />
                  Data Processing Notes
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <ul className="space-y-1">
                  {dataset.warnings.map((warning, i) => (
                    <li key={i} className="text-sm text-muted-foreground">
                      ⚠️ {warning}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </section>
        )}

        {/* Action buttons */}
        <div className="mb-8 flex flex-wrap gap-3">
          {dataset && (
            <Button variant="outline" onClick={handleGenerateCode} className="gap-2 bg-transparent">
              <Code className="h-4 w-4" />
              Generate Starter Code
            </Button>
          )}
          {(displayData.source !== 'upload') && (
            <Button variant="outline" asChild className="gap-2 bg-transparent">
              <a
                href={
                  dataset?.downloadUrl?.startsWith('http')
                    ? dataset.downloadUrl
                    : basicInfo?.downloadUrl?.startsWith('http')
                    ? basicInfo.downloadUrl
                    : `https://www.kaggle.com/datasets/${basicInfo?.downloadUrl || dataset?.downloadUrl || ''}`
                }
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-4 w-4" />
                {displayData.source === 'github' ? 'View on GitHub'
                  : displayData.source === 'huggingface' ? 'View on HuggingFace'
                  : 'View on Kaggle'}
              </a>
            </Button>
          )}
          {!dataset && basicInfo && (
            <Button onClick={() => triggerAnalysis(basicInfo)} className="gap-2">
              <BarChart3 className="h-4 w-4" />
              Analyze Dataset
            </Button>
          )}
        </div>

        {/* Analysis results — only shown when dataset is analyzed */}
        {dataset?.metrics && (
          <>
            {/* Health Score Breakdown (Feature 3) */}
            {dataset.scoreBreakdown && (
              <section className="mb-8">
                <HealthBreakdown
                  score={dataset.score || 0}
                  breakdown={dataset.scoreBreakdown}
                />
              </section>
            )}

            {/* Metrics */}
            <section className="mb-8">
              <h2 className="mb-4 text-xl font-semibold text-foreground">Dataset Metrics</h2>
              <MetricsCards metrics={dataset.metrics} />
            </section>

            {/* Interactive Insights (Feature 2) */}
            {insights.length > 0 && (
              <section className="mb-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      AI-Generated Insights
                      <Badge variant="secondary">{insights.length}</Badge>
                    </CardTitle>
                    <CardDescription>Click any insight for detailed analysis and recommendations</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {visibleInsights.map((insight, i) => {
                        const style = insightSeverityStyles[insight.severity] || insightSeverityStyles.info;

                        return (
                          <div
                            key={i}
                            className={`rounded-lg border p-3 cursor-pointer transition-all hover:shadow-md ${style.border} ${style.bg}`}
                            onClick={() => setSelectedInsight(insight)}
                          >
                            <div className="flex items-start gap-2">
                              <span className="text-sm shrink-0">{style.icon}</span>
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-foreground line-clamp-1">{insight.title}</p>
                                <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{insight.description}</p>
                                <div className="flex items-center gap-2 mt-1.5">
                                  <Badge variant="secondary" className="text-[10px]">{insight.category}</Badge>
                                  <span className="text-[10px] text-primary cursor-pointer hover:underline">View details →</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {insights.length > 6 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-3 w-full gap-2"
                        onClick={() => setShowAllInsights(!showAllInsights)}
                      >
                        {showAllInsights ? (
                          <>
                            <ChevronUp className="h-4 w-4" />
                            Show fewer insights
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-4 w-4" />
                            Show all {insights.length} insights
                          </>
                        )}
                      </Button>
                    )}
                  </CardContent>
                </Card>

                {/* Insight Detail Dialog */}
                <Dialog open={!!selectedInsight} onOpenChange={() => setSelectedInsight(null)}>
                  <DialogContent className="max-w-lg">
                    {selectedInsight && (
                      <>
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-2">
                            <span>{insightSeverityStyles[selectedInsight.severity]?.icon}</span>
                            {selectedInsight.title}
                          </DialogTitle>
                          <DialogDescription>{selectedInsight.description}</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div>
                            <h4 className="text-sm font-semibold text-foreground mb-1">Why It Matters</h4>
                            <p className="text-sm text-muted-foreground leading-relaxed">{selectedInsight.why_it_matters}</p>
                          </div>
                          <div className="rounded-lg bg-primary/5 border border-primary/20 p-3">
                            <h4 className="text-sm font-semibold text-foreground mb-1">💡 Suggested Action</h4>
                            <p className="text-sm text-muted-foreground leading-relaxed">{selectedInsight.suggested_action}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">{selectedInsight.category}</Badge>
                            <Badge
                              variant="outline"
                              className={
                                selectedInsight.severity === 'critical'
                                  ? 'border-red-500/30 text-red-500'
                                  : selectedInsight.severity === 'warning'
                                  ? 'border-yellow-500/30 text-yellow-500'
                                  : 'border-blue-500/30 text-blue-500'
                              }
                            >
                              {selectedInsight.severity}
                            </Badge>
                          </div>
                        </div>
                      </>
                    )}
                  </DialogContent>
                </Dialog>
              </section>
            )}

            {/* Bias Detection (Feature 7) */}
            {dataset.biasWarnings && dataset.biasWarnings.length > 0 && (
              <section className="mb-8">
                <BiasWarnings warnings={dataset.biasWarnings} />
              </section>
            )}

            {/* Missing Values Map (Feature 9) */}
            {dataset.metrics.columnTypes.some((c) => c.nullCount > 0) && (
              <section className="mb-8">
                <MissingHeatmap
                  columnTypes={dataset.metrics.columnTypes}
                  totalRows={dataset.metrics.rows}
                />
              </section>
            )}


            {/* What To Do Next (Feature 5) */}
            {dataset.nextSteps && dataset.nextSteps.length > 0 && (
              <section className="mb-8">
                <NextStepsPanel steps={dataset.nextSteps} />
              </section>
            )}

            {/* ── Action Section: Quick Actions ── */}
            <section className="mb-8">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    🎯 What do you want to do next?
                  </CardTitle>
                  <CardDescription>Choose an action to continue your analysis workflow</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <button
                      className="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-all hover:border-primary/40 hover:bg-primary/5"
                      onClick={() => document.getElementById('data-preview')?.scrollIntoView({ behavior: 'smooth' })}
                    >
                      <span className="text-xl">🔍</span>
                      <div>
                        <p className="text-sm font-medium text-foreground">Explore Data</p>
                        <p className="text-xs text-muted-foreground">View sample data and column info</p>
                      </div>
                    </button>
                    <button
                      className="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-all hover:border-primary/40 hover:bg-primary/5"
                      onClick={() => document.getElementById('preprocessing')?.scrollIntoView({ behavior: 'smooth' })}
                    >
                      <span className="text-xl">🧹</span>
                      <div>
                        <p className="text-sm font-medium text-foreground">Clean Dataset</p>
                        <p className="text-xs text-muted-foreground">Handle missing values, duplicates & more</p>
                      </div>
                    </button>
                    <button
                      className="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-all hover:border-primary/40 hover:bg-primary/5"
                      onClick={() => document.getElementById('visualization')?.scrollIntoView({ behavior: 'smooth' })}
                    >
                      <span className="text-xl">📊</span>
                      <div>
                        <p className="text-sm font-medium text-foreground">Visualize</p>
                        <p className="text-xs text-muted-foreground">Create custom charts on demand</p>
                      </div>
                    </button>
                    {(isSmallDataset || isImbalanced) && (
                      <button
                        className="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-all hover:border-primary/40 hover:bg-primary/5"
                        onClick={() => document.getElementById('augmentation')?.scrollIntoView({ behavior: 'smooth' })}
                      >
                        <span className="text-xl">📈</span>
                        <div>
                          <p className="text-sm font-medium text-foreground">Augment Data</p>
                          <p className="text-xs text-muted-foreground">Generate synthetic samples</p>
                        </div>
                      </button>
                    )}
                    <button
                      className="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-all hover:border-primary/40 hover:bg-primary/5"
                      onClick={handleGenerateCode}
                    >
                      <span className="text-xl">💻</span>
                      <div>
                        <p className="text-sm font-medium text-foreground">Get Starter Code</p>
                        <p className="text-xs text-muted-foreground">Copy Python code to clipboard</p>
                      </div>
                    </button>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* Column Info */}
            <section className="mb-8">
              <Card>
                <CardHeader>
                  <CardTitle>Column Information</CardTitle>
                  <CardDescription>Overview of dataset columns and their types</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {dataset.metrics.columnTypes.map((col) => (
                      <div
                        key={col.name}
                        className="flex items-center justify-between rounded-lg border border-border p-3"
                      >
                        <div>
                          <p className="font-mono text-sm font-medium text-foreground">{col.name}</p>
                          <p className="text-xs text-muted-foreground capitalize">{col.type}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">
                            {col.uniqueCount.toLocaleString()} unique
                          </p>
                          {col.nullCount > 0 && (
                            <p className="text-xs text-warning">{col.nullCount.toLocaleString()} nulls</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* Data Preview */}
            {dataset.metrics.sampleData.length > 0 && (
              <section id="data-preview" className="mb-8">
                <DataPreviewTable data={dataset.metrics.sampleData} />
              </section>
            )}

            {/* On-Demand Visualization (Phase 6) */}
            <section id="visualization" className="mb-8">
              <VisualizationPanel
                datasetId={dataset.id}
                columnTypes={dataset.metrics.columnTypes}
              />
            </section>

            {/* Augmentation Panel (Phase 5) */}
            {(isSmallDataset || isImbalanced) && (
              <section id="augmentation" className="mb-8">
                <AugmentationPanel
                  datasetId={dataset.id}
                  targetColumn={dataset.mlRecommendation?.targetColumn}
                  taskType={dataset.mlRecommendation?.task || 'classification'}
                  isSmallDataset={isSmallDataset}
                  isImbalanced={isImbalanced}
                />
              </section>
            )}

            {/* No-Code Preprocessing (Feature 4) */}
            <section id="preprocessing" className="mb-8">
              <PreprocessingPanel
                datasetId={dataset.id}
                metrics={dataset.metrics}
                onPreprocessComplete={() => setHasPreprocessed(true)}
              />
            </section>

            {/* Detailed EDA — Collapsible */}
            {(dataset.distributions.length > 0 || dataset.correlations.length > 0) && (
              <section className="mb-8">
                <Button
                  variant="ghost"
                  className="mb-4 w-full justify-between text-xl font-semibold text-foreground"
                  onClick={() => setShowDetailedEDA(!showDetailedEDA)}
                >
                  <span>Detailed EDA</span>
                  {showDetailedEDA ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </Button>

                {showDetailedEDA && (
                  <div className="space-y-8 animate-in slide-in-from-top-2">
                    {/* Target vs Feature Correlations */}
                    {dataset.correlations.length > 0 && (
                      <TargetFeatureChart
                        correlations={dataset.correlations}
                        targetColumn={dataset.mlRecommendation?.targetColumn}
                      />
                    )}

                    {/* Distribution + Correlation Heatmap */}
                    <div className="grid gap-6 lg:grid-cols-2">
                      {dataset.distributions.length > 0 && (
                        <DistributionChart distributions={dataset.distributions} />
                      )}
                      {dataset.correlations.length > 0 && (
                        <CorrelationChart correlations={dataset.correlations} />
                      )}
                    </div>

                    {/* Missing Value Heatmap */}
                    {dataset.metrics.missingPercent > 0 && (
                      <MissingHeatmap
                        columnTypes={dataset.metrics.columnTypes}
                        totalRows={dataset.metrics.rows}
                      />
                    )}

                    {/* Column Statistics Summary */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          📋 Column Statistics
                        </CardTitle>
                        <CardDescription>
                          Detailed statistics for each column in the dataset
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b border-border">
                                <th className="text-left py-2 px-2 font-medium text-muted-foreground">Column</th>
                                <th className="text-left py-2 px-2 font-medium text-muted-foreground">Type</th>
                                <th className="text-right py-2 px-2 font-medium text-muted-foreground">Unique</th>
                                <th className="text-right py-2 px-2 font-medium text-muted-foreground">Nulls</th>
                                <th className="text-right py-2 px-2 font-medium text-muted-foreground">Null %</th>
                                <th className="text-left py-2 px-2 font-medium text-muted-foreground">Completeness</th>
                              </tr>
                            </thead>
                            <tbody>
                              {dataset.metrics.columnTypes.map((col) => {
                                const nullPct = dataset.metrics.rows > 0
                                  ? (col.nullCount / dataset.metrics.rows * 100)
                                  : 0;
                                const completeness = 100 - nullPct;
                                return (
                                  <tr key={col.name} className="border-b border-border/50 hover:bg-muted/30">
                                    <td className="py-1.5 px-2 font-mono text-foreground">{col.name}</td>
                                    <td className="py-1.5 px-2">
                                      <Badge variant="secondary" className="text-[10px] capitalize">
                                        {col.type}
                                      </Badge>
                                    </td>
                                    <td className="py-1.5 px-2 text-right text-muted-foreground">
                                      {col.uniqueCount.toLocaleString()}
                                    </td>
                                    <td className="py-1.5 px-2 text-right">
                                      <span className={col.nullCount > 0 ? 'text-warning' : 'text-muted-foreground'}>
                                        {col.nullCount.toLocaleString()}
                                      </span>
                                    </td>
                                    <td className="py-1.5 px-2 text-right">
                                      <span className={nullPct > 20 ? 'text-destructive' : nullPct > 5 ? 'text-warning' : 'text-muted-foreground'}>
                                        {nullPct.toFixed(1)}%
                                      </span>
                                    </td>
                                    <td className="py-1.5 px-2 w-32">
                                      <div className="flex items-center gap-2">
                                        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                                          <div
                                            className={`h-full rounded-full transition-all ${
                                              completeness >= 95 ? 'bg-green-500'
                                              : completeness >= 80 ? 'bg-yellow-500'
                                              : 'bg-red-500'
                                            }`}
                                            style={{ width: `${completeness}%` }}
                                          />
                                        </div>
                                        <span className="text-[10px] text-muted-foreground w-8 text-right">{completeness.toFixed(0)}%</span>
                                      </div>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Outlier Detection Overview */}
                    {dataset.biasWarnings && dataset.biasWarnings.some((w) => w.type === 'outlier_heavy') && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            ⚡ Outlier Detection
                          </CardTitle>
                          <CardDescription>
                            Columns flagged with significant outlier presence
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="grid gap-3 sm:grid-cols-2">
                            {dataset.biasWarnings
                              .filter((w) => w.type === 'outlier_heavy')
                              .map((warning, i) => (
                                <div
                                  key={i}
                                  className="flex items-start gap-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-3"
                                >
                                  <span className="text-lg shrink-0">⚠️</span>
                                  <div>
                                    <p className="text-sm font-medium text-foreground">{warning.title}</p>
                                    <p className="text-xs text-muted-foreground mt-1">{warning.description}</p>
                                    {warning.affected_columns.length > 0 && (
                                      <div className="flex flex-wrap gap-1 mt-2">
                                        {warning.affected_columns.map((col) => (
                                          <Badge key={col} variant="secondary" className="text-[10px] font-mono">{col}</Badge>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </section>
            )}

            {/* ML Recommendation */}
            {dataset.mlRecommendation && (
              <section className="mb-8">
                <MLRecommendation recommendation={dataset.mlRecommendation} />
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
