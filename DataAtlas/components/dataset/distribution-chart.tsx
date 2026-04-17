'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Distribution } from '@/lib/types';

interface DistributionChartProps {
  distributions: Distribution[];
}

export function DistributionChart({ distributions }: DistributionChartProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  if (!distributions || distributions.length === 0) {
    return null;
  }

  const distribution = distributions[activeIndex] || distributions[0];
  const maxCount = Math.max(...distribution.bins.map((b) => b.count || 0), 1);
  const totalCount = distribution.bins.reduce((sum, b) => sum + (b.count || 0), 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Value Distributions</CardTitle>
        <CardDescription>
          Distribution of values in &quot;{distribution.column}&quot; column
          {totalCount > 0 && (
            <span className="ml-2 text-xs text-muted-foreground/70">
              ({totalCount.toLocaleString()} values)
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Column Tabs */}
        {distributions.length > 1 && (
          <div className="flex flex-wrap gap-1">
            {distributions.map((d, i) => (
              <Button
                key={d.column}
                variant={i === activeIndex ? 'default' : 'outline'}
                size="sm"
                className="text-xs h-7 px-2.5 font-mono"
                onClick={() => setActiveIndex(i)}
              >
                {d.column}
              </Button>
            ))}
          </div>
        )}

        {/* Chart */}
        <div className="space-y-2">
          {/* Bars */}
          <div className="flex items-end gap-[2px] h-52">
            {distribution.bins.map((bin, i) => {
              const pct = ((bin.count || 0) / maxCount) * 100;
              const barPct = ((bin.count || 0) / totalCount * 100).toFixed(1);
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-0.5 group relative">
                  {/* Hover tooltip */}
                  <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-popover border border-border rounded-md px-2 py-1 text-[10px] shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-nowrap">
                    <p className="font-medium text-foreground">{bin.label}</p>
                    <p className="text-muted-foreground">{(bin.count || 0).toLocaleString()} ({barPct}%)</p>
                  </div>
                  <div
                    className="w-full rounded-t transition-all min-h-[2px]"
                    style={{
                      height: `${pct}%`,
                      backgroundColor: `hsl(221 83% ${65 - (pct / 100) * 25}%)`,
                    }}
                  />
                </div>
              );
            })}
          </div>

          {/* X-axis labels */}
          <div className="flex gap-[2px]">
            {distribution.bins.map((bin, i) => {
              // Only show every Nth label to prevent overlap
              const showEvery = Math.max(1, Math.ceil(distribution.bins.length / 8));
              return (
                <div
                  key={i}
                  className="flex-1 text-center text-[8px] text-muted-foreground truncate"
                  title={String(bin.label)}
                >
                  {i % showEvery === 0 ? bin.label : ''}
                </div>
              );
            })}
          </div>
        </div>

        {/* Quick Stats */}
        {distribution.bins.length > 0 && (
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border">
            <div className="text-center">
              <p className="text-[10px] text-muted-foreground">Mode bin</p>
              <p className="text-xs font-medium text-foreground truncate">
                {distribution.bins.reduce((max, b) =>
                  (b.count || 0) > (max.count || 0) ? b : max, distribution.bins[0]
                ).label}
              </p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-muted-foreground">Bins</p>
              <p className="text-xs font-medium text-foreground">{distribution.bins.length}</p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-muted-foreground">Max count</p>
              <p className="text-xs font-medium text-foreground">{maxCount.toLocaleString()}</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
