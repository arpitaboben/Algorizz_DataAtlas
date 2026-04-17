'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { NextStep } from '@/lib/types';
import { ListChecks, AlertCircle, Wrench, Brain, Info } from 'lucide-react';

interface NextStepsPanelProps {
  steps: NextStep[];
  onStepClick?: (actionKey: string) => void;
}

const actionIcons: Record<string, typeof Wrench> = {
  preprocess: Wrench,
  model: Brain,
  analyze: ListChecks,
  info: Info,
};

export function NextStepsPanel({ steps, onStepClick }: NextStepsPanelProps) {
  if (!steps || steps.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ListChecks className="h-5 w-5 text-primary" />
          What To Do Next
        </CardTitle>
        <CardDescription>Priority-ordered steps to prepare your dataset for ML</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative space-y-0">
          {steps.map((step, index) => {
            const Icon = actionIcons[step.action_type] || Info;
            const isLast = index === steps.length - 1;

            return (
              <div
                key={step.order}
                className={`relative flex gap-4 pb-6 ${!isLast ? '' : ''}`}
              >
                {/* Timeline line */}
                {!isLast && (
                  <div className="absolute left-[17px] top-10 h-[calc(100%-24px)] w-[2px] bg-border" />
                )}

                {/* Step number circle */}
                <div
                  className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold transition-all ${
                    step.is_critical
                      ? 'border-red-500 bg-red-500/10 text-red-500'
                      : step.action_type === 'preprocess'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-muted text-muted-foreground'
                  }`}
                >
                  {step.order}
                </div>

                {/* Content */}
                <div
                  className={`flex-1 rounded-lg border p-3 transition-all ${
                    step.is_critical
                      ? 'border-red-500/30 bg-red-500/5'
                      : step.action_type === 'preprocess' && step.action_key
                      ? 'cursor-pointer border-border hover:border-primary/50 hover:bg-primary/5'
                      : 'border-border'
                  }`}
                  onClick={() => {
                    if (step.action_key && onStepClick) onStepClick(step.action_key);
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className={`h-4 w-4 ${step.is_critical ? 'text-red-500' : 'text-muted-foreground'}`} />
                    <span className="text-sm font-medium text-foreground">{step.title}</span>
                    {step.is_critical && (
                      <Badge variant="outline" className="border-red-500/30 bg-red-500/10 text-red-500 text-xs">
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Critical
                      </Badge>
                    )}
                    {step.action_type === 'preprocess' && step.action_key && (
                      <Badge variant="outline" className="text-xs">Auto-fix available</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
