'use client';

import React from "react"

import { useState, useEffect } from 'react';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SearchFilters } from '@/lib/types';

interface SearchFormProps {
  onSearch: (query: string, description: string, filters: SearchFilters) => void;
  isLoading?: boolean;
  initialQuery?: string;
}

export function SearchForm({ onSearch, isLoading, initialQuery }: SearchFormProps) {
  const [query, setQuery] = useState(initialQuery || '');

  // Restore query when navigating back with cached results
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);
  const [description, setDescription] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    format: [],
    size: 'all',
    freshness: 'all',
    source: [],
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query, description, filters);
  };

  const clearFilters = () => {
    setFilters({
      format: [],
      size: 'all',
      freshness: 'all',
      source: [],
    });
  };

  const hasActiveFilters =
    filters.format?.length ||
    (filters.size && filters.size !== 'all') ||
    (filters.freshness && filters.freshness !== 'all') ||
    filters.source?.length;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search datasets (e.g., COVID-19, housing prices, sentiment analysis)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-12 pl-10 text-base"
          />
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="h-12 gap-2"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {hasActiveFilters && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
              {(filters.format?.length || 0) +
                (filters.source?.length || 0) +
                (filters.size !== 'all' ? 1 : 0) +
                (filters.freshness !== 'all' ? 1 : 0)}
            </span>
          )}
        </Button>
        <Button type="submit" className="h-12 px-8" disabled={isLoading}>
          {isLoading ? 'Searching...' : 'Search'}
        </Button>
      </div>

      <Textarea
        placeholder="Describe what you're looking for in more detail (optional). E.g., 'I need a dataset with customer purchase history for building a recommendation system'"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="min-h-[80px] resize-none"
      />

      {showFilters && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-medium text-card-foreground">Filters</h3>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="h-8 gap-1 text-xs">
                <X className="h-3 w-3" />
                Clear all
              </Button>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label>Format</Label>
              <Select
                value={filters.format?.[0] || 'all'}
                onValueChange={(value) =>
                  setFilters({ ...filters, format: value === 'all' ? [] : [value] })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All formats" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All formats</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="parquet">Parquet</SelectItem>
                  <SelectItem value="excel">Excel</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Size</Label>
              <Select
                value={filters.size || 'all'}
                onValueChange={(value) =>
                  setFilters({ ...filters, size: value as SearchFilters['size'] })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Any size" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Any size</SelectItem>
                  <SelectItem value="small">Small ({'<'} 10MB)</SelectItem>
                  <SelectItem value="medium">Medium (10MB - 1GB)</SelectItem>
                  <SelectItem value="large">Large ({'>'} 1GB)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Freshness</Label>
              <Select
                value={filters.freshness || 'all'}
                onValueChange={(value) =>
                  setFilters({ ...filters, freshness: value as SearchFilters['freshness'] })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Any time" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Any time</SelectItem>
                  <SelectItem value="day">Last 24 hours</SelectItem>
                  <SelectItem value="week">Last week</SelectItem>
                  <SelectItem value="month">Last month</SelectItem>
                  <SelectItem value="year">Last year</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Source</Label>
              <Select
                value={filters.source?.[0] || 'all'}
                onValueChange={(value) =>
                  setFilters({ ...filters, source: value === 'all' ? [] : [value] })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All sources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All sources</SelectItem>
                  <SelectItem value="kaggle">Kaggle</SelectItem>
                  <SelectItem value="github">GitHub</SelectItem>
                  <SelectItem value="huggingface">HuggingFace</SelectItem>
                  <SelectItem value="government">Government</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}
    </form>
  );
}
