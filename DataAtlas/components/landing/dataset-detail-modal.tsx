'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Zap } from 'lucide-react';
import { Dataset } from '@/lib/types';

interface DatasetDetailModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
}

export function DatasetDetailModal({ dataset, isOpen, onClose }: DatasetDetailModalProps) {
  if (!dataset) return null;

  const formattedDate = new Date(dataset.lastUpdated).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl">{dataset.title}</DialogTitle>
          <DialogDescription>{dataset.source.charAt(0).toUpperCase() + dataset.source.slice(1)} Dataset</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Description */}
          <div>
            <p className="text-sm text-muted-foreground leading-relaxed">{dataset.description}</p>
          </div>

          {/* Quality Score */}
          <div className="rounded-lg bg-primary/10 border border-primary/20 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Quality Score</span>
              <span className="text-2xl font-bold text-primary">
                {dataset.qualityScore === 'high' ? '85' : dataset.qualityScore === 'medium' ? '65' : '45'}
                <span className="text-sm text-muted-foreground">/100</span>
              </span>
            </div>
            <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary"
                style={{
                  width: dataset.qualityScore === 'high' ? '85%' : dataset.qualityScore === 'medium' ? '65%' : '45%',
                }}
              />
            </div>
          </div>

          {/* Basic Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-secondary/50 p-3">
              <p className="text-xs text-muted-foreground mb-1">Format</p>
              <p className="font-semibold text-sm text-foreground uppercase">{dataset.format}</p>
            </div>
            <div className="rounded-lg bg-secondary/50 p-3">
              <p className="text-xs text-muted-foreground mb-1">Size</p>
              <p className="font-semibold text-sm text-foreground">{dataset.size}</p>
            </div>
            <div className="rounded-lg bg-secondary/50 p-3">
              <p className="text-xs text-muted-foreground mb-1">Updated</p>
              <p className="font-semibold text-sm text-foreground">{formattedDate}</p>
            </div>
            <div className="rounded-lg bg-secondary/50 p-3">
              <p className="text-xs text-muted-foreground mb-1">Relevance</p>
              <p className="font-semibold text-sm text-foreground">{Math.round(dataset.relevanceScore)}%</p>
            </div>
          </div>

          {/* Tags */}
          {dataset.tags && dataset.tags.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-2">TAGS</p>
              <div className="flex flex-wrap gap-2">
                {dataset.tags.slice(0, 5).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer with CTA */}
        <div className="border-t border-border pt-4 flex gap-2">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            Cancel
          </Button>
          <Button className="flex-1 gap-2">
            Analyze Dataset
            <Zap className="h-4 w-4" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
