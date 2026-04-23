'use client';

import { ArrowRight, Check, Zap, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DatasetDetailModal } from './dataset-detail-modal';
import { Dataset } from '@/lib/types';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';

const sampleDatasets: Dataset[] = [
  {
    id: 'house-prices',
    title: 'House Prices Dataset',
    description: 'Real estate price prediction · 14.6K houses · 80 features',
    source: 'kaggle',
    format: 'csv',
    size: '12MB',
    sizeBytes: 12000000,
    relevanceScore: 92,
    qualityScore: 'high',
    downloadUrl: '#',
    tags: ['Regression', 'Tabular Data', 'Real Estate'],
    lastUpdated: new Date().toISOString(),
    author: 'Kaggle',
    license: 'CC0 Public',
  },
  {
    id: 'titanic-clean',
    title: 'Titanic Dataset (Cleaned)',
    description: 'Passenger survival prediction · 891 records · 12 features',
    source: 'kaggle',
    format: 'csv',
    size: '61KB',
    sizeBytes: 61000,
    relevanceScore: 88,
    qualityScore: 'high',
    downloadUrl: '#',
    tags: ['Classification', 'Structured Data', 'Popular'],
    lastUpdated: new Date().toISOString(),
    author: 'Kaggle',
    license: 'CC0 Public',
  },
];

export function DemoSection() {
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const handleDatasetClick = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setIsDetailModalOpen(true);
  };

  return (
    <section className="relative py-12 sm:py-16 overflow-hidden">
      {/* Background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute bottom-0 right-0 h-80 w-96 rounded-full bg-blue-500/10 blur-3xl opacity-40" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-16 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground mb-4">
            From Chaos to Clarity
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            See how DataAtlas transforms your dataset discovery workflow.
          </p>
        </div>

        {/* Before / After comparison */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* BEFORE */}
          <div className="rounded-2xl border border-destructive/30 bg-destructive/5 backdrop-blur-lg overflow-hidden">
            <div className="p-8 border-b border-destructive/20 bg-destructive/10">
              <h3 className="text-lg font-bold text-foreground">Without DataAtlas</h3>
              <p className="text-sm text-muted-foreground mt-1">Hours of manual work</p>
            </div>

            <div className="p-8 space-y-4">
              {[
                'Search Kaggle manually for hours',
                'Jump between GitHub and HuggingFace',
                'Download datasets to evaluate locally',
                'Spend days on exploratory analysis',
                'Manually check for bias and quality',
                'Guess which ML models fit best',
                'Write preprocessing code from scratch',
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="mt-1 h-1.5 w-1.5 rounded-full bg-destructive flex-shrink-0" />
                  <span className="text-sm text-muted-foreground">{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AFTER */}
          <div className="rounded-2xl border border-green-500/30 bg-green-500/5 backdrop-blur-lg overflow-hidden">
            <div className="p-8 border-b border-green-500/20 bg-green-500/10">
              <h3 className="text-lg font-bold text-foreground">With DataAtlas</h3>
              <p className="text-sm text-muted-foreground mt-1">Minutes to actionable insights</p>
            </div>

            <div className="p-8 space-y-4">
              {[
                'Search all sources with semantic understanding',
                'View quality metrics instantly',
                'Analyze datasets without downloading',
                'Auto-generated EDA in seconds',
                'AI-detected bias and quality scores',
                'ML task recommendations built-in',
                'Generated starter code ready to use',
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <Check className="mt-0.5 h-4 w-4 text-green-500 flex-shrink-0" />
                  <span className="text-sm text-muted-foreground">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sample datasets - Interactive section */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-foreground mb-6">Try Clicking on Datasets</h3>
          <div className="grid md:grid-cols-2 gap-4 mb-12">
            {sampleDatasets.map((dataset) => (
              <div
                key={dataset.id}
                onClick={() => handleDatasetClick(dataset)}
                className="group cursor-pointer rounded-xl border border-primary/20 bg-card/40 backdrop-blur-lg p-6 transition-all hover:border-primary/50 hover:shadow-lg hover:scale-102 active:scale-98"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                        {dataset.title}
                      </h4>
                      <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/30">
                        Supported
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{dataset.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground mb-1">Quality</p>
                    <p className="text-2xl font-bold text-primary">
                      {dataset.qualityScore === 'high' ? '87' : '75'}/100
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 mb-3">
                  <Badge variant="secondary" className="text-xs">{dataset.format.toUpperCase()}</Badge>
                  <Badge variant="secondary" className="text-xs">{dataset.size}</Badge>
                  <Badge variant="secondary" className="text-xs">Relevance {Math.round(dataset.relevanceScore)}%</Badge>
                </div>

                {/* Hover indicator */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground group-hover:text-primary transition-colors pt-2 border-t border-border/30">
                  <Zap className="h-3.5 w-3.5" />
                  <span>Click to analyze</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sample output */}
        <div className="mt-16">
          <div className="rounded-2xl border border-primary/30 bg-card/40 backdrop-blur-lg overflow-hidden">
            <div className="p-8 sm:p-12">
              <h3 className="text-2xl font-bold text-foreground mb-8">Sample Analysis Output</h3>

              {/* Dataset result card */}
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Main info */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="rounded-xl bg-secondary/40 border border-border/50 p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-lg font-bold text-foreground">House Prices Dataset</h4>
                        <p className="text-sm text-muted-foreground mt-1">Real estate price prediction · 14.6K records · 80 features</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground mb-1">Quality Score</p>
                        <p className="text-2xl font-bold text-primary">92/100</p>
                      </div>
                    </div>
                  </div>

                  {/* Metrics breakdown */}
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { label: 'Total Rows', value: '14.6K', icon: '✓' },
                      { label: 'Features', value: '80', icon: '📊' },
                      { label: 'Missing Data', value: '8%', icon: '⚖️' },
                      { label: 'Data Freshness', value: 'Recent', icon: '📅' },
                    ].map((metric) => (
                      <div key={metric.label} className="rounded-lg bg-muted/50 p-4">
                        <p className="text-xs text-muted-foreground mb-2">{metric.label}</p>
                        <p className="text-lg font-bold text-foreground">{metric.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Recommended tasks */}
                  <div className="rounded-lg border border-border/50 bg-muted/30 p-6">
                    <h5 className="font-semibold text-foreground mb-3">Recommended ML Tasks</h5>
                    <div className="space-y-2">
                      {['Price Regression', 'Feature Engineering', 'Outlier Detection', 'Model Ensemble'].map((task) => (
                        <div key={task} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <ArrowRight className="h-4 w-4 text-primary" />
                          {task}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Quick stats sidebar */}
                <div className="space-y-4">
                  <div className="rounded-lg border border-primary/30 bg-primary/10 p-6">
                    <p className="text-xs text-primary font-medium mb-4">QUICK INSIGHTS</p>
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Size</p>
                        <p className="font-semibold text-foreground">12MB</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Format</p>
                        <p className="font-semibold text-foreground">CSV</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">License</p>
                        <p className="font-semibold text-foreground">CC0 Public</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Task Type</p>
                        <p className="font-semibold text-foreground">Regression</p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-6">
                    <p className="text-sm font-semibold text-foreground mb-3">Why This Dataset?</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      Clean tabular data with excellent quality scores, minimal missing values, and ideal for regression modeling.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <DatasetDetailModal
          dataset={selectedDataset}
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
        />
      </div>
    </section>
  );
}
