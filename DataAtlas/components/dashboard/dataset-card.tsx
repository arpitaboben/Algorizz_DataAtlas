'use client';

import Link from 'next/link';
import { ExternalLink, FileText, Calendar, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Dataset } from '@/lib/types';
import { cn } from '@/lib/utils';

interface DatasetCardProps {
  dataset: Dataset;
  isSelected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  showCheckbox?: boolean;
}

const sourceColors: Record<string, string> = {
  kaggle: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  github: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  huggingface: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  government: 'bg-green-500/10 text-green-500 border-green-500/20',
};

const qualityColors: Record<string, string> = {
  high: 'bg-success/10 text-success border-success/20',
  medium: 'bg-warning/10 text-warning border-warning/20',
  low: 'bg-destructive/10 text-destructive border-destructive/20',
};

export function DatasetCard({ dataset, isSelected = false, onSelect, showCheckbox = false }: DatasetCardProps) {
  let formattedDate = 'Unknown';
  try {
    if (dataset.lastUpdated) {
      formattedDate = new Date(dataset.lastUpdated).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    }
  } catch {
    formattedDate = 'Unknown';
  }

  const handleClick = () => {
    // Store dataset info so the detail page can access it for analysis
    sessionStorage.setItem(`dataset-${dataset.id}`, JSON.stringify(dataset));
  };

  return (
    <div className={cn(
      'group rounded-xl border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-lg',
      isSelected ? 'border-primary ring-2 ring-primary/20' : 'border-border',
    )}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {showCheckbox && (
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => onSelect?.(dataset.id, !!checked)}
              className="mr-1"
              aria-label={`Select ${dataset.title} for comparison`}
            />
          )}
          <Badge variant="outline" className={cn('capitalize', sourceColors[dataset.source])}>
            {dataset.source}
          </Badge>
          <Badge variant="outline" className={cn('capitalize', qualityColors[dataset.qualityScore])}>
            {dataset.qualityScore} quality
          </Badge>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <span className="text-sm font-bold text-primary">{Math.round(dataset.relevanceScore)}%</span>
        </div>
      </div>

      <h3 className="mb-2 line-clamp-1 text-lg font-semibold text-card-foreground group-hover:text-primary">
        {dataset.title}
      </h3>

      <p className="mb-4 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
        {dataset.description || 'No description available'}
      </p>

      <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <FileText className="h-3.5 w-3.5" />
          <span className="uppercase">{dataset.format}</span>
          <span className="text-border">|</span>
          <span>{dataset.size}</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="h-3.5 w-3.5" />
          <span>{formattedDate}</span>
        </div>
        <div className="flex items-center gap-1">
          <User className="h-3.5 w-3.5" />
          <span className="max-w-[120px] truncate">{dataset.author}</span>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-1.5">
        {(dataset.tags || []).slice(0, 4).map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
          >
            {tag}
          </span>
        ))}
        {(dataset.tags || []).length > 4 && (
          <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-muted-foreground">
            +{dataset.tags.length - 4}
          </span>
        )}
      </div>

      <Link href={`/dataset/${dataset.id}`} onClick={handleClick}>
        <Button className="w-full gap-2" size="sm">
          View & Analyze Dataset
          <ExternalLink className="h-3.5 w-3.5" />
        </Button>
      </Link>
    </div>
  );
}
