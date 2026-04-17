'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ColumnType } from '@/lib/types';
import { Grid3X3 } from 'lucide-react';

interface MissingHeatmapProps {
  columnTypes: ColumnType[];
  totalRows: number;
}

function getPctColor(pct: number): string {
  if (pct === 0) return 'bg-emerald-500/20 text-emerald-500';
  if (pct < 5) return 'bg-emerald-500/30 text-emerald-600';
  if (pct < 15) return 'bg-yellow-500/30 text-yellow-600';
  if (pct < 30) return 'bg-orange-500/30 text-orange-600';
  if (pct < 50) return 'bg-red-500/30 text-red-600';
  return 'bg-red-500/50 text-red-700';
}

function getBarWidth(pct: number): string {
  return `${Math.max(2, Math.min(100, pct))}%`;
}

export function MissingHeatmap({ columnTypes, totalRows }: MissingHeatmapProps) {
  if (!columnTypes || totalRows === 0) return null;

  const columnsWithMissing = columnTypes
    .map((col) => ({
      name: col.name,
      type: col.type,
      nullCount: col.nullCount,
      pct: totalRows > 0 ? Math.round((col.nullCount / totalRows) * 1000) / 10 : 0,
    }))
    .sort((a, b) => b.pct - a.pct);

  const totalMissing = columnsWithMissing.reduce((sum, c) => sum + c.nullCount, 0);
  if (totalMissing === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Grid3X3 className="h-5 w-5 text-primary" />
          Missing Values Map
        </CardTitle>
        <CardDescription>
          Per-column breakdown of missing values ({totalMissing.toLocaleString()} total across {totalRows.toLocaleString()} rows)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {columnsWithMissing.map((col) => (
            <div key={col.name} className="flex items-center gap-3">
              <div className="w-32 shrink-0 truncate text-right">
                <span className="font-mono text-xs text-foreground">{col.name}</span>
              </div>
              <div className="flex-1 h-6 rounded bg-muted/50 relative overflow-hidden">
                {col.pct > 0 && (
                  <div
                    className={`absolute inset-y-0 left-0 rounded ${col.pct > 50 ? 'bg-red-500/40' : col.pct > 15 ? 'bg-orange-500/30' : col.pct > 5 ? 'bg-yellow-500/30' : 'bg-emerald-500/20'}`}
                    style={{ width: getBarWidth(col.pct), transition: 'width 0.5s ease' }}
                  />
                )}
                <div className="absolute inset-0 flex items-center px-2">
                  <span className={`text-xs font-medium ${col.pct === 0 ? 'text-emerald-500' : 'text-foreground'}`}>
                    {col.pct === 0 ? '✓ Complete' : `${col.pct}% missing (${col.nullCount.toLocaleString()})`}
                  </span>
                </div>
              </div>
              <div className="w-16 shrink-0">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${getPctColor(col.pct)}`}>
                  {col.type}
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
