'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Database, TrendingUp, AlertCircle, GitCompare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DashboardHeader } from '@/components/dashboard/dashboard-header';
import { SearchForm } from '@/components/dashboard/search-form';
import { DatasetCard } from '@/components/dashboard/dataset-card';
import { useAuth } from '@/lib/auth-context';
import { Dataset, SearchFilters } from '@/lib/types';

// localStorage keys for persisting search state
const STORAGE_KEYS = {
  QUERY: 'dataatlas_search_query',
  RESULTS: 'dataatlas_search_results',
  HAS_SEARCHED: 'dataatlas_has_searched',
} as const;

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [restoredQuery, setRestoredQuery] = useState('');
  const [selectedForCompare, setSelectedForCompare] = useState<Set<string>>(new Set());
  const [compareMode, setCompareMode] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Restore search state from localStorage on mount
  useEffect(() => {
    try {
      const savedResults = localStorage.getItem(STORAGE_KEYS.RESULTS);
      const savedQuery = localStorage.getItem(STORAGE_KEYS.QUERY);
      const savedHasSearched = localStorage.getItem(STORAGE_KEYS.HAS_SEARCHED);

      if (savedHasSearched === 'true' && savedResults) {
        const parsed = JSON.parse(savedResults) as Dataset[];
        setDatasets(parsed);
        setHasSearched(true);
        setRestoredQuery(savedQuery || '');
      }
    } catch {
      // Corrupted localStorage — ignore silently
    }
  }, []);

  const handleSearch = useCallback(async (query: string, description: string, filters: SearchFilters) => {
    setIsSearching(true);
    setHasSearched(true);
    setSearchError(null);
    setSelectedForCompare(new Set());
    setCompareMode(false);

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          description: description || undefined,
          filters: {
            format: filters.format?.length ? filters.format : undefined,
            size: filters.size !== 'all' ? filters.size : undefined,
            freshness: filters.freshness !== 'all' ? filters.freshness : undefined,
            source: filters.source?.length ? filters.source : undefined,
            quality: filters.quality?.length ? filters.quality : undefined,
          },
          page: 1,
          limit: 20,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ message: 'Search failed' }));
        throw new Error(err.message || 'Search failed');
      }

      const data = await response.json();
      const results = data.datasets || [];
      setDatasets(results);

      // Persist to localStorage so results survive navigation
      try {
        localStorage.setItem(STORAGE_KEYS.QUERY, query);
        localStorage.setItem(STORAGE_KEYS.RESULTS, JSON.stringify(results));
        localStorage.setItem(STORAGE_KEYS.HAS_SEARCHED, 'true');
      } catch {
        // localStorage full or disabled — degrade gracefully
      }
    } catch (error) {
      console.error('Search error:', error);
      const message = error instanceof Error ? error.message : 'Search failed';
      setSearchError(message);
      setDatasets([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleSelectForCompare = (id: string, selected: boolean) => {
    setSelectedForCompare((prev) => {
      const next = new Set(prev);
      if (selected) {
        if (next.size < 2) next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const handleCompare = () => {
    const ids = Array.from(selectedForCompare);
    if (ids.length === 2) {
      // Store the dataset info for the datasets that need analysis
      ids.forEach((id) => {
        const ds = datasets.find((d) => d.id === id);
        if (ds) sessionStorage.setItem(`dataset-${id}`, JSON.stringify(ds));
      });
      sessionStorage.setItem('compare_dataset_ids', JSON.stringify(ids));
      router.push('/compare');
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Dataset Search</h1>
          <p className="mt-2 text-muted-foreground">
            Find the perfect dataset for your machine learning project — powered by AI semantic search
          </p>
        </div>

        <SearchForm onSearch={handleSearch} isLoading={isSearching} initialQuery={restoredQuery} />

        <div className="mt-8">
          {isSearching ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="mt-4 text-muted-foreground">
                Searching across Kaggle, HuggingFace, and GitHub...
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                First search may take a moment while the AI model loads
              </p>
            </div>
          ) : searchError ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <AlertCircle className="h-12 w-12 text-destructive" />
              <h3 className="mt-4 text-lg font-semibold text-foreground">Search Error</h3>
              <p className="mt-2 max-w-sm text-muted-foreground">{searchError}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Make sure the FastAPI backend is running on port 8000
              </p>
            </div>
          ) : hasSearched ? (
            datasets.length > 0 ? (
              <>
                <div className="mb-4 flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-3">
                    <p className="text-sm text-muted-foreground">
                      Found <span className="font-medium text-foreground">{datasets.length}</span> datasets
                    </p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      Sorted by AI relevance
                    </div>
                  </div>

                  {/* Compare controls */}
                  <div className="flex items-center gap-3">
                    <Button
                      variant={compareMode ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => {
                        setCompareMode(!compareMode);
                        if (compareMode) setSelectedForCompare(new Set());
                      }}
                      className="gap-2"
                    >
                      <GitCompare className="h-4 w-4" />
                      {compareMode ? 'Cancel Compare' : 'Compare Datasets'}
                    </Button>

                    {compareMode && selectedForCompare.size === 2 && (
                      <Button size="sm" onClick={handleCompare} className="gap-2 animate-in fade-in">
                        <GitCompare className="h-4 w-4" />
                        Compare {selectedForCompare.size} Datasets
                      </Button>
                    )}

                    {compareMode && selectedForCompare.size < 2 && (
                      <span className="text-xs text-muted-foreground">
                        Select {2 - selectedForCompare.size} more dataset{2 - selectedForCompare.size > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                </div>

                {compareMode && (
                  <div className="mb-4 rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-muted-foreground">
                    💡 Select exactly 2 datasets to compare. Both must be analyzed first (click &quot;View &amp; Analyze&quot; on each).
                  </div>
                )}

                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {datasets.map((dataset) => (
                    <DatasetCard
                      key={dataset.id}
                      dataset={dataset}
                      showCheckbox={compareMode}
                      isSelected={selectedForCompare.has(dataset.id)}
                      onSelect={handleSelectForCompare}
                    />
                  ))}
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Database className="h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-semibold text-foreground">No datasets found</h3>
                <p className="mt-2 max-w-sm text-muted-foreground">
                  Try adjusting your search query or filters to find what you're looking for.
                </p>
              </div>
            )
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="rounded-full bg-primary/10 p-4">
                <Database className="h-8 w-8 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-foreground">Start your search</h3>
              <p className="mt-2 max-w-sm text-muted-foreground">
                Enter a dataset name or description above to discover datasets from Kaggle, GitHub,
                and HuggingFace — ranked by AI semantic relevance.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
