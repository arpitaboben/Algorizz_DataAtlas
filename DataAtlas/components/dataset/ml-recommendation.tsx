'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MLRecommendation as MLRecommendationType } from '@/lib/types';
import { Brain, Target, Sparkles, Lightbulb } from 'lucide-react';

interface MLRecommendationProps {
  recommendation: MLRecommendationType;
}

const taskIcons: Record<string, typeof Brain> = {
  classification: Target,
  regression: Sparkles,
  clustering: Brain,
  'time-series': Sparkles,
};

const taskColors: Record<string, string> = {
  classification: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  regression: 'bg-green-500/10 text-green-500 border-green-500/20',
  clustering: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  'time-series': 'bg-orange-500/10 text-orange-500 border-orange-500/20',
};

export function MLRecommendation({ recommendation }: MLRecommendationProps) {
  const Icon = taskIcons[recommendation.task] || Brain;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          ML Task Recommendation
        </CardTitle>
        <CardDescription>AI-suggested machine learning approach for this dataset</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10">
            <Icon className="h-7 w-7 text-primary" />
          </div>
          <div>
            <Badge variant="outline" className={`mb-1 capitalize ${taskColors[recommendation.task]}`}>
              {recommendation.task.replace('-', ' ')}
            </Badge>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Confidence:</span>
              <span className="font-semibold text-foreground">{recommendation.confidence}%</span>
            </div>
          </div>
        </div>

        {recommendation.targetColumn && (
          <div className="rounded-lg bg-muted/50 p-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">Suggested Target</p>
            <p className="mt-1 font-mono text-sm text-foreground">{recommendation.targetColumn}</p>
          </div>
        )}

        <div>
          <p className="mb-2 text-sm font-medium text-foreground">Reasoning</p>
          <p className="text-sm leading-relaxed text-muted-foreground">{recommendation.reasoning}</p>
        </div>

        <div>
          <p className="mb-3 text-sm font-medium text-foreground">Suggested Models</p>
          <div className="flex flex-wrap gap-2">
            {recommendation.suggestedModels.map((model) => (
              <Badge key={model} variant="secondary">
                {model}
              </Badge>
            ))}
          </div>
        </div>

        {/* Use Cases (Feature 6) */}
        {recommendation.useCases && recommendation.useCases.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="h-4 w-4 text-yellow-500" />
              <p className="text-sm font-medium text-foreground">Potential Use Cases</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {recommendation.useCases.map((useCase) => (
                <Badge
                  key={useCase}
                  variant="outline"
                  className="bg-yellow-500/5 text-yellow-600 dark:text-yellow-400 border-yellow-500/20 capitalize"
                >
                  {useCase}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
