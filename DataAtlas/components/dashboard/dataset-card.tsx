'use client';

import Link from 'next/link';
import { ExternalLink, FileText, Calendar, User, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { Dataset } from '@/lib/types';
import { cn } from '@/lib/utils';

interface DatasetCardProps {
  dataset: Dataset;
  isSelected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  showCheckbox?: boolean;
  isSupported?: boolean;
  onCardClick?: (dataset: Dataset) => void;
}

const isImageDataset = (format: string): boolean => {
  return ['image', 'jpeg', 'jpg', 'png', 'gif', 'bmp'].includes(format.toLowerCase());
};

const sourceColors: Record<string, string> = {
  kaggle: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  github: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  huggingface: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  government: 'bg-green-500/10 text-green-500 border-green-500/20',
  upload: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
};

const sourceIcons: Record<string, string> = {
  kaggle: '🏷️',
  github: '🐙',
  huggingface: '🤗',
  government: '🏛️',
  upload: '📁',
};

const qualityColors: Record<string, string> = {
  high: 'bg-success/10 text-success border-success/20',
  medium: 'bg-warning/10 text-warning border-warning/20',
  low: 'bg-destructive/10 text-destructive border-destructive/20',
};

export function DatasetCard({
  dataset,
  isSelected = false,
  onSelect,
  showCheckbox = false,
  isSupported = true,
  onCardClick,
}: DatasetCardProps) {
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

  const isImage = isImageDataset(dataset.format);

  const handleCardClick = () => {
    if (onCardClick) {
      onCardClick(dataset);
    } else {
      // Store dataset info so the detail page can access it for analysis
      sessionStorage.setItem(`dataset-${dataset.id}`, JSON.stringify(dataset));
    }
  };

  const buttonLabel = dataset.source === 'kaggle'
    ? 'View & Analyze'
    : dataset.source === 'upload'
    ? 'View Analysis'
    : 'View & Analyze';

  return (
    <div
      onClick={handleCardClick}
      className={cn(
        'group rounded-xl border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] cursor-pointer',
        isSelected ? 'border-primary ring-2 ring-primary/20' : 'border-border',
        isImage && !isSupported && 'opacity-90',
      )}
    >
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
            {sourceIcons[dataset.source] || ''} {dataset.source}
          </Badge>
          <Badge variant="outline" className={cn('capitalize', qualityColors[dataset.qualityScore])}>
            {dataset.qualityScore} quality
          </Badge>
          {isImage && !isSupported && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/30">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Limited Support
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                Analysis currently available for tabular datasets only
              </TooltipContent>
            </Tooltip>
          )}
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

      <div className={isImage && !isSupported ? 'opacity-60' : ''}>
        <Link href={`/dataset/${dataset.id}`} onClick={handleCardClick}>
          <Button
            className="w-full gap-2"
            size="sm"
            disabled={isImage && !isSupported}
            title={isImage && !isSupported ? 'Image dataset analysis coming soon' : undefined}
          >
            {isImage && !isSupported ? 'Analyze (Coming Soon)' : buttonLabel}
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </Link>
      </div>
    </div>
  );
}

