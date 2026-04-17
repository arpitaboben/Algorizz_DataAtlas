'use client';

import { Search, GitCompare, BarChart3, Wrench, CheckCircle } from 'lucide-react';

interface PipelineTrackerProps {
  currentStep: 'search' | 'compare' | 'analyze' | 'fix' | 'ready';
  completedSteps?: string[];
}

const pipelineSteps = [
  { key: 'search', label: 'Search', icon: Search, description: 'Find datasets' },
  { key: 'compare', label: 'Compare', icon: GitCompare, description: 'Compare options' },
  { key: 'analyze', label: 'Analyze', icon: BarChart3, description: 'Run EDA' },
  { key: 'fix', label: 'Fix', icon: Wrench, description: 'Clean data' },
  { key: 'ready', label: 'Ready', icon: CheckCircle, description: 'ML-ready' },
];

export function PipelineTracker({ currentStep, completedSteps = [] }: PipelineTrackerProps) {
  const currentIndex = pipelineSteps.findIndex((s) => s.key === currentStep);

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {pipelineSteps.map((step, index) => {
          const isCompleted = completedSteps.includes(step.key) || index < currentIndex;
          const isCurrent = step.key === currentStep;
          const isFuture = index > currentIndex && !completedSteps.includes(step.key);
          const Icon = step.icon;

          return (
            <div key={step.key} className="flex items-center flex-1">
              {/* Step */}
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all ${
                    isCompleted
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : isCurrent
                      ? 'border-primary bg-primary/10 text-primary scale-110 shadow-lg shadow-primary/20'
                      : 'border-border bg-muted text-muted-foreground'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </div>
                <span
                  className={`mt-1.5 text-xs font-medium ${
                    isCurrent ? 'text-primary' : isCompleted ? 'text-emerald-500' : 'text-muted-foreground'
                  }`}
                >
                  {step.label}
                </span>
                <span className="text-[10px] text-muted-foreground">{step.description}</span>
              </div>

              {/* Connector line */}
              {index < pipelineSteps.length - 1 && (
                <div
                  className={`mx-2 h-0.5 flex-1 rounded-full transition-all ${
                    isCompleted ? 'bg-emerald-500' : 'bg-border'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
