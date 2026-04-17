'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Correlation } from '@/lib/types';

interface CorrelationChartProps {
  correlations: Correlation[];
}

export function CorrelationChart({ correlations }: CorrelationChartProps) {
  if (!correlations || correlations.length === 0) {
    return null;
  }

  // Extract unique column names from correlation pairs
  const columnSet = new Set<string>();
  correlations.forEach((c) => {
    columnSet.add(c.column1);
    columnSet.add(c.column2);
  });
  const columns = Array.from(columnSet).slice(0, 12); // Max 12 for readability

  // Build correlation matrix lookup
  const corrMap = new Map<string, number>();
  correlations.forEach((c) => {
    corrMap.set(`${c.column1}|${c.column2}`, c.value);
    corrMap.set(`${c.column2}|${c.column1}`, c.value);
  });

  const getCorr = (row: string, col: string) => {
    if (row === col) return 1.0;
    return corrMap.get(`${row}|${col}`) ?? 0;
  };

  const getColor = (value: number) => {
    if (value === 1.0) return 'hsl(var(--muted))';
    const abs = Math.abs(value);
    if (value > 0) {
      // Blue gradient: light for weak, strong for high
      return `rgba(59, 130, 246, ${abs * 0.85 + 0.1})`;
    } else {
      // Red gradient: light for weak, strong for high
      return `rgba(239, 68, 68, ${abs * 0.85 + 0.1})`;
    }
  };

  const getTextColor = (value: number) => {
    if (value === 1.0) return 'hsl(var(--muted-foreground))';
    return Math.abs(value) > 0.5 ? 'white' : 'currentColor';
  };

  // Find strongest correlations (non-diagonal)
  const allPairs = correlations
    .filter((c) => Math.abs(c.value) > 0.3)
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  const cellSize = Math.max(32, Math.min(52, 420 / columns.length));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Correlation Heatmap</CardTitle>
        <CardDescription>
          Pairwise correlation coefficients between numeric features
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Highlights */}
        {allPairs.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {allPairs.slice(0, 3).map((c, i) => (
              <div
                key={i}
                className={`flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-medium ${
                  c.value > 0
                    ? 'bg-blue-500/10 text-blue-500'
                    : 'bg-red-500/10 text-red-500'
                }`}
              >
                <span>{c.column1} ↔ {c.column2}</span>
                <span className="font-mono font-bold">{c.value > 0 ? '+' : ''}{c.value.toFixed(3)}</span>
              </div>
            ))}
          </div>
        )}

        <div className="overflow-x-auto">
          <div className="inline-block">
            {/* Header row */}
            <div className="flex" style={{ marginLeft: cellSize * 2.2 }}>
              {columns.map((col) => (
                <div
                  key={col}
                  className="text-[8px] text-muted-foreground font-mono truncate text-center"
                  style={{ width: cellSize }}
                  title={col}
                >
                  {col.length > 5 ? col.slice(0, 4) + '…' : col}
                </div>
              ))}
            </div>

            {/* Heatmap grid */}
            {columns.map((rowCol) => (
              <div key={rowCol} className="flex items-center">
                <div
                  className="text-[9px] text-muted-foreground font-mono truncate text-right pr-2 shrink-0"
                  style={{ width: cellSize * 2.2 }}
                  title={rowCol}
                >
                  {rowCol}
                </div>
                {columns.map((colCol) => {
                  const value = getCorr(rowCol, colCol);
                  const isDiagonal = rowCol === colCol;

                  return (
                    <div
                      key={colCol}
                      className="border border-background/60 flex items-center justify-center transition-all hover:ring-1 hover:ring-foreground/30 hover:z-10 cursor-default"
                      style={{
                        width: cellSize,
                        height: cellSize,
                        backgroundColor: getColor(value),
                        color: getTextColor(value),
                      }}
                      title={`${rowCol} × ${colCol}: ${value.toFixed(3)}`}
                    >
                      <span className="text-[8px] font-mono font-bold leading-none">
                        {isDiagonal ? '' : value.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
              </div>
            ))}

            {/* Color scale legend */}
            <div className="flex items-center gap-2 mt-3 justify-center text-[9px] text-muted-foreground">
              <span className="font-medium text-red-500">−1</span>
              <div className="flex h-2.5 w-36 rounded overflow-hidden">
                {Array.from({ length: 20 }).map((_, i) => {
                  const val = -1 + (i / 19) * 2;
                  return <div key={i} className="flex-1" style={{ backgroundColor: getColor(val) }} />;
                })}
              </div>
              <span className="font-medium text-blue-500">+1</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
