'use client';

import { useState, useEffect, useMemo } from 'react';
import { Loader2, BarChart3, ChevronDown, Sparkles, PieChart, LineChart, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ColumnType } from '@/lib/types';

interface VisualizationPanelProps {
  datasetId: string;
  columnTypes: ColumnType[];
}

interface ChartDataItem {
  label?: string;
  count?: number;
  x?: number;
  y?: number;
  value?: number;
  density?: number;
  density_pct?: number;
  cumulative_pct?: number;
  percentage?: number;
  column?: string;
  row?: string;
  col?: string;
  min?: number;
  q1?: number;
  median?: number;
  q3?: number;
  max?: number;
  outlier_count?: number;
}

interface ChartResult {
  chart_type: string;
  columns: string[];
  data: ChartDataItem[];
  stats: Record<string, unknown>;
  error?: string;
}

interface ChartSuggestion {
  chart_type: string;
  columns: string[];
  reason: string;
  priority: number;
}

const CHART_TYPES = [
  { id: 'histogram', label: 'Histogram', icon: '📊', description: '1 column', maxCols: 1 },
  { id: 'scatter', label: 'Scatter', icon: '⚬', description: '2 numeric', maxCols: 2 },
  { id: 'boxplot', label: 'Box Plot', icon: '📦', description: '1-5 numeric', maxCols: 5 },
  { id: 'violin', label: 'Violin', icon: '🎻', description: '1 numeric', maxCols: 1 },
  { id: 'pie', label: 'Pie', icon: '🥧', description: '1 categorical', maxCols: 1 },
  { id: 'area', label: 'CDF Area', icon: '📈', description: '1 numeric', maxCols: 1 },
  { id: 'heatmap', label: 'Heatmap', icon: '🔥', description: '2+ numeric', maxCols: 12 },
  { id: 'line', label: 'Line', icon: '📉', description: '2 columns', maxCols: 2 },
];

const PIE_COLORS = [
  'hsl(221 83% 53%)', 'hsl(142 71% 45%)', 'hsl(38 92% 50%)',
  'hsl(0 84% 60%)', 'hsl(262 83% 58%)', 'hsl(199 89% 48%)',
  'hsl(43 96% 56%)', 'hsl(346 77% 49%)', 'hsl(168 76% 42%)',
  'hsl(25 95% 53%)', 'hsl(210 40% 60%)',
];

export function VisualizationPanel({ datasetId, columnTypes }: VisualizationPanelProps) {
  const [selectedCols, setSelectedCols] = useState<string[]>([]);
  const [chartType, setChartType] = useState('histogram');
  const [bins, setBins] = useState(0); // 0 = auto
  const [chart, setChart] = useState<ChartResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showColPicker, setShowColPicker] = useState(false);
  const [suggestions, setSuggestions] = useState<ChartSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const numericCols = useMemo(() => columnTypes.filter((c) => c.type === 'number'), [columnTypes]);
  const categoricalCols = useMemo(() => columnTypes.filter((c) => c.type === 'string'), [columnTypes]);
  const allCols = columnTypes;

  const currentChartInfo = CHART_TYPES.find((c) => c.id === chartType)!;

  // Which columns to show in the picker
  const pickerCols = useMemo(() => {
    if (['scatter', 'boxplot', 'violin', 'area', 'heatmap'].includes(chartType)) return numericCols;
    if (chartType === 'pie') return categoricalCols.length > 0 ? categoricalCols : allCols;
    if (chartType === 'line') return allCols;
    return allCols; // histogram
  }, [chartType, numericCols, categoricalCols, allCols]);

  // Load suggestions
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const resp = await fetch('/api/visualize/suggest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dataset_id: datasetId }),
        });
        if (resp.ok) {
          const data = await resp.json();
          setSuggestions(data.suggestions || []);
        }
      } catch { /* ignore — suggestions are non-critical */ }
    };
    loadSuggestions();
  }, [datasetId]);

  const handleGenerate = async (overrideCols?: string[], overrideType?: string) => {
    const cols = overrideCols || selectedCols;
    const type = overrideType || chartType;
    if (cols.length === 0) return;

    setIsLoading(true);
    setError(null);
    setChart(null);

    try {
      const resp = await fetch('/api/visualize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          columns: cols,
          chart_type: type,
          bins: type === 'histogram' || type === 'violin' ? bins : 0,
        }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ message: 'Visualization failed' }));
        throw new Error(err.message || 'Visualization failed');
      }

      const data: ChartResult = await resp.json();
      if (data.error) {
        setError(data.error);
      } else {
        setChart(data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (s: ChartSuggestion) => {
    setChartType(s.chart_type);
    setSelectedCols(s.columns);
    setShowSuggestions(false);
    handleGenerate(s.columns, s.chart_type);
  };

  const toggleColumn = (colName: string) => {
    const maxCols = currentChartInfo.maxCols;
    setSelectedCols((prev) => {
      if (prev.includes(colName)) return prev.filter((c) => c !== colName);
      if (prev.length >= maxCols) return [...prev.slice(1), colName];
      return [...prev, colName];
    });
  };

  const maxBarHeight = chart?.data
    ? Math.max(...chart.data.map((d) => d.count || 0), 1)
    : 1;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-500" />
              Custom Visualization
            </CardTitle>
            <CardDescription>
              8 chart types • configurable bins • smart suggestions
            </CardDescription>
          </div>
          {suggestions.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-xs"
              onClick={() => setShowSuggestions(!showSuggestions)}
            >
              <Sparkles className="h-3.5 w-3.5 text-yellow-500" />
              {showSuggestions ? 'Hide' : 'Suggest Charts'}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="space-y-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-3">
            <p className="text-xs font-medium text-yellow-600 dark:text-yellow-400">
              <Sparkles className="inline h-3 w-3 mr-1" />
              Recommended visualizations for this dataset
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {suggestions.map((s, i) => {
                const info = CHART_TYPES.find((t) => t.id === s.chart_type);
                return (
                  <button
                    key={i}
                    className="flex items-start gap-2 rounded-md border border-border p-2 text-left text-xs transition-all hover:border-primary/40 hover:bg-primary/5"
                    onClick={() => handleSuggestionClick(s)}
                  >
                    <span className="text-base shrink-0">{info?.icon || '📊'}</span>
                    <div className="min-w-0">
                      <p className="font-medium text-foreground capitalize">{s.chart_type}</p>
                      <p className="text-muted-foreground truncate">{s.reason}</p>
                      <p className="font-mono text-[10px] text-muted-foreground/60 truncate mt-0.5">
                        {s.columns.join(', ')}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-wrap gap-3 items-end">
          {/* Chart Type */}
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Chart Type</label>
            <div className="flex flex-wrap gap-1">
              {CHART_TYPES.map((t) => (
                <Button
                  key={t.id}
                  variant={chartType === t.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setChartType(t.id);
                    setSelectedCols([]);
                    setChart(null);
                    setBins(0);
                  }}
                  className="text-xs gap-1 h-7 px-2"
                  title={t.description}
                >
                  <span className="text-xs">{t.icon}</span>
                  <span className="hidden sm:inline">{t.label}</span>
                </Button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          {/* Column Selector */}
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs font-medium text-muted-foreground mb-1 block">
              {currentChartInfo.description} — {selectedCols.length > 0 ? selectedCols.length : 'none'} selected
            </label>
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between text-xs"
                onClick={() => setShowColPicker(!showColPicker)}
              >
                {selectedCols.length > 0 ? selectedCols.join(', ') : 'Choose columns...'}
                <ChevronDown className="h-3 w-3 ml-2" />
              </Button>

              {showColPicker && (
                <div className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-lg border border-border bg-popover shadow-lg">
                  {pickerCols.map((col) => (
                    <button
                      key={col.name}
                      className={`w-full px-3 py-1.5 text-left text-xs hover:bg-muted/50 flex items-center justify-between ${
                        selectedCols.includes(col.name) ? 'bg-primary/10 text-primary' : 'text-foreground'
                      }`}
                      onClick={() => toggleColumn(col.name)}
                    >
                      <span className="font-mono">{col.name}</span>
                      <Badge variant="secondary" className="text-[10px]">{col.type}</Badge>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Bins Control — only for histogram, violin */}
          {(chartType === 'histogram' || chartType === 'violin') && (
            <div className="w-36">
              <label className="text-xs font-medium text-muted-foreground mb-1 block">
                Bins: {bins === 0 ? 'Auto' : bins}
              </label>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={bins}
                onChange={(e) => setBins(Number(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-muted accent-primary"
              />
              <div className="flex justify-between text-[9px] text-muted-foreground mt-0.5">
                <span>Auto</span>
                <span>100</span>
              </div>
            </div>
          )}

          <Button
            onClick={() => handleGenerate()}
            disabled={selectedCols.length === 0 || isLoading}
            size="sm"
            className="gap-2"
          >
            {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <BarChart3 className="h-3 w-3" />}
            Generate
          </Button>
        </div>

        {/* Error */}
        {error && (
          <div className="text-sm text-destructive bg-destructive/5 border border-destructive/20 rounded-lg p-3">
            {error}
          </div>
        )}

        {/* ── Chart Renderers ── */}

        {/* Histogram */}
        {chart && chart.chart_type === 'histogram' && (
          <div className="space-y-3">
            <StatsBar stats={chart.stats} />
            <div className="flex items-end gap-[2px] h-52">
              {chart.data.map((d, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[9px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                    {typeof d.count === 'number' ? (d.count > 999 ? `${(d.count/1000).toFixed(1)}k` : d.count) : ''}
                  </span>
                  <div
                    className="w-full bg-primary/70 hover:bg-primary rounded-t transition-all min-h-[2px]"
                    style={{ height: `${((d.count || 0) / maxBarHeight) * 100}%` }}
                    title={`${d.label}: ${typeof d.count === 'number' ? d.count.toLocaleString() : d.count}`}
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-[2px]">
              {chart.data.map((d, i) => (
                <div key={i} className="flex-1 text-center text-[8px] text-muted-foreground truncate" title={String(d.label)}>
                  {i % Math.max(1, Math.floor(chart.data.length / 10)) === 0 ? d.label : ''}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Scatter */}
        {chart && chart.chart_type === 'scatter' && (
          <div className="space-y-3">
            <StatsBar stats={chart.stats} />
            <div className="relative h-72 border border-border rounded-lg bg-muted/10 overflow-hidden">
              {chart.data.map((d, i) => {
                const xRange = chart.stats.x_range as number[] | undefined;
                const yRange = chart.stats.y_range as number[] | undefined;
                if (!xRange || !yRange || d.x === undefined || d.y === undefined) return null;
                const xPct = ((d.x - xRange[0]) / (xRange[1] - xRange[0])) * 100;
                const yPct = 100 - ((d.y - yRange[0]) / (yRange[1] - yRange[0])) * 100;
                return (
                  <div
                    key={i}
                    className="absolute w-1.5 h-1.5 rounded-full bg-primary/50 hover:bg-primary hover:scale-[2.5] hover:z-10 transition-all"
                    style={{ left: `${Math.max(2, Math.min(97, xPct))}%`, top: `${Math.max(2, Math.min(97, yPct))}%` }}
                    title={`(${d.x}, ${d.y})`}
                  />
                );
              })}
              <div className="absolute bottom-1 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground font-mono bg-background/80 px-1 rounded">{chart.columns[0]}</div>
              <div className="absolute left-1 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] text-muted-foreground font-mono bg-background/80 px-1 rounded">{chart.columns[1]}</div>
            </div>
          </div>
        )}

        {/* Boxplot */}
        {chart && chart.chart_type === 'boxplot' && (
          <div className="space-y-3">
            {chart.data.map((d) => (
              <div key={d.column} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-foreground">{d.column}</span>
                  <span className="text-muted-foreground">
                    median: {d.median} | Q1: {d.q1} | Q3: {d.q3} | outliers: {d.outlier_count}
                  </span>
                </div>
                <div className="relative h-8 bg-muted/20 rounded border border-border">
                  {d.min !== undefined && d.max !== undefined && d.q1 !== undefined && d.q3 !== undefined && d.median !== undefined && (d.max - d.min) > 0 && (
                    <>
                      <div className="absolute top-1/2 h-[1px] w-full bg-muted-foreground/20" />
                      {/* Whisker lines */}
                      <div className="absolute top-1/4 h-1/2 w-[1px] bg-muted-foreground/50" style={{ left: `${((d.min - d.min) / (d.max - d.min)) * 100}%` }} />
                      <div className="absolute top-1/4 h-1/2 w-[1px] bg-muted-foreground/50" style={{ left: `${100}%` }} />
                      {/* IQR box */}
                      <div
                        className="absolute top-1 bottom-1 bg-primary/20 border border-primary/40 rounded"
                        style={{
                          left: `${((d.q1 - d.min) / (d.max - d.min)) * 100}%`,
                          width: `${Math.max(2, ((d.q3 - d.q1) / (d.max - d.min)) * 100)}%`,
                        }}
                      />
                      {/* Median line */}
                      <div className="absolute top-0.5 bottom-0.5 w-[2px] bg-primary rounded" style={{ left: `${((d.median - d.min) / (d.max - d.min)) * 100}%` }} />
                    </>
                  )}
                </div>
                <div className="flex justify-between text-[9px] text-muted-foreground">
                  <span>{d.min}</span>
                  <span>{d.max}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Violin */}
        {chart && chart.chart_type === 'violin' && (
          <div className="space-y-3">
            <StatsBar stats={chart.stats} />
            <div className="relative h-56 flex items-center justify-center">
              <div className="relative w-full h-full flex items-center">
                {/* Mirror density shape */}
                <svg viewBox={`0 0 ${chart.data.length} 100`} className="w-full h-full" preserveAspectRatio="none">
                  {/* Top half */}
                  <polygon
                    points={chart.data.map((d, i) => `${i},${50 - (d.density_pct || 0) / 2}`).join(' ') + ` ${chart.data.length - 1},50 0,50`}
                    fill="hsl(var(--primary) / 0.3)"
                    stroke="hsl(var(--primary))"
                    strokeWidth="0.5"
                  />
                  {/* Bottom half (mirror) */}
                  <polygon
                    points={chart.data.map((d, i) => `${i},${50 + (d.density_pct || 0) / 2}`).join(' ') + ` ${chart.data.length - 1},50 0,50`}
                    fill="hsl(var(--primary) / 0.3)"
                    stroke="hsl(var(--primary))"
                    strokeWidth="0.5"
                  />
                  {/* Center line */}
                  <line x1="0" y1="50" x2={chart.data.length} y2="50" stroke="hsl(var(--muted-foreground) / 0.3)" strokeWidth="0.5" />
                </svg>
              </div>
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>{chart.data[0]?.value}</span>
              <span className="text-foreground">{chart.columns[0]}</span>
              <span>{chart.data[chart.data.length - 1]?.value}</span>
            </div>
          </div>
        )}

        {/* Pie */}
        {chart && chart.chart_type === 'pie' && (
          <div className="space-y-3">
            <StatsBar stats={chart.stats} />
            <div className="flex items-center gap-6">
              {/* SVG Pie */}
              <div className="relative w-44 h-44 shrink-0">
                <svg viewBox="-1 -1 2 2" className="w-full h-full -rotate-90">
                  {(() => {
                    let cumAngle = 0;
                    return chart.data.map((d, i) => {
                      const pct = (d.percentage || 0) / 100;
                      const startAngle = cumAngle * 2 * Math.PI;
                      cumAngle += pct;
                      const endAngle = cumAngle * 2 * Math.PI;
                      const largeArc = pct > 0.5 ? 1 : 0;
                      const x1 = Math.cos(startAngle);
                      const y1 = Math.sin(startAngle);
                      const x2 = Math.cos(endAngle);
                      const y2 = Math.sin(endAngle);
                      const pathD = pct >= 1
                        ? `M 1 0 A 1 1 0 1 1 -1 0 A 1 1 0 1 1 1 0`
                        : `M 0 0 L ${x1} ${y1} A 1 1 0 ${largeArc} 1 ${x2} ${y2} Z`;
                      return (
                        <path
                          key={i}
                          d={pathD}
                          fill={PIE_COLORS[i % PIE_COLORS.length]}
                          stroke="hsl(var(--background))"
                          strokeWidth="0.02"
                          className="hover:opacity-80 transition-opacity"
                        >
                          <title>{`${d.label}: ${d.percentage}%`}</title>
                        </path>
                      );
                    });
                  })()}
                </svg>
              </div>
              {/* Legend */}
              <div className="flex-1 space-y-1.5">
                {chart.data.map((d, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <div className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                    <span className="text-foreground truncate flex-1">{d.label}</span>
                    <span className="font-mono text-muted-foreground">{d.percentage}%</span>
                    <span className="text-muted-foreground/60">({d.count?.toLocaleString()})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Area / CDF */}
        {chart && chart.chart_type === 'area' && (
          <div className="space-y-3">
            <StatsBar stats={chart.stats} />
            <div className="relative h-56 border border-border rounded-lg bg-muted/10 overflow-hidden">
              <svg viewBox={`0 0 ${chart.data.length} 100`} className="w-full h-full" preserveAspectRatio="none">
                {/* Fill area */}
                <polygon
                  points={`0,100 ${chart.data.map((d, i) => `${i},${100 - (d.cumulative_pct || 0)}`).join(' ')} ${chart.data.length - 1},100`}
                  fill="hsl(var(--primary) / 0.15)"
                />
                {/* Line */}
                <polyline
                  points={chart.data.map((d, i) => `${i},${100 - (d.cumulative_pct || 0)}`).join(' ')}
                  fill="none"
                  stroke="hsl(var(--primary))"
                  strokeWidth="1"
                />
                {/* Guide lines for percentiles */}
                {[25, 50, 75].map((p) => (
                  <line key={p} x1="0" y1={100 - p} x2={chart.data.length} y2={100 - p} stroke="hsl(var(--muted-foreground) / 0.15)" strokeWidth="0.5" strokeDasharray="2,2" />
                ))}
              </svg>
              {/* Y axis labels */}
              <div className="absolute right-1 top-0 bottom-0 flex flex-col justify-between text-[9px] text-muted-foreground py-1">
                <span>100%</span>
                <span>75%</span>
                <span>50%</span>
                <span>25%</span>
                <span>0%</span>
              </div>
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>{chart.data[0]?.value}</span>
              <span className="text-foreground">Cumulative Distribution — {chart.columns[0]}</span>
              <span>{chart.data[chart.data.length - 1]?.value}</span>
            </div>
          </div>
        )}

        {/* Heatmap */}
        {chart && chart.chart_type === 'heatmap' && <HeatmapChart chart={chart} />}

        {/* Line Chart */}
        {chart && chart.chart_type === 'line' && (
          <div className="space-y-3">
            <StatsBar stats={chart.stats} />
            <div className="relative h-56 border border-border rounded-lg bg-muted/10 overflow-hidden p-2">
              {chart.data.length > 0 && (() => {
                const yVals = chart.data.map((d) => d.y || 0);
                const yMin = Math.min(...yVals);
                const yMax = Math.max(...yVals);
                const yRange = yMax - yMin || 1;
                return (
                  <svg viewBox={`0 0 ${chart.data.length} 100`} className="w-full h-full" preserveAspectRatio="none">
                    <polyline
                      points={chart.data.map((d, i) => `${i},${100 - ((d.y || 0) - yMin) / yRange * 100}`).join(' ')}
                      fill="none"
                      stroke="hsl(var(--primary))"
                      strokeWidth="1"
                    />
                  </svg>
                );
              })()}
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>{typeof chart.data[0]?.x === 'number' ? chart.data[0].x : chart.data[0]?.x}</span>
              <span className="text-foreground">{chart.columns[0]} → {chart.columns[1]}</span>
              <span>{typeof chart.data[chart.data.length-1]?.x === 'number' ? chart.data[chart.data.length-1].x : chart.data[chart.data.length-1]?.x}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}


// ── Sub-components ──

function StatsBar({ stats }: { stats: Record<string, unknown> }) {
  const entries = Object.entries(stats).filter(([k]) => !['columns', 'x_range', 'y_range'].includes(k));
  if (entries.length === 0) return null;

  return (
    <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap bg-muted/30 rounded-lg px-3 py-2">
      {entries.slice(0, 8).map(([key, val]) => (
        <span key={key}>
          <span className="font-medium text-foreground">{key.replace(/_/g, ' ')}:</span>{' '}
          {typeof val === 'number' ? val.toLocaleString() : Array.isArray(val) ? val.join(' – ') : String(val ?? '')}
        </span>
      ))}
    </div>
  );
}


function HeatmapChart({ chart }: { chart: ChartResult }) {
  const columns = (chart.stats.columns as string[]) || [];
  const n = columns.length;
  if (n < 2) return null;

  const cellSize = Math.max(28, Math.min(56, 400 / n));

  const getColor = (value: number) => {
    const abs = Math.abs(value);
    if (value > 0) {
      const intensity = Math.round(abs * 255);
      return `rgba(59, 130, 246, ${abs * 0.85 + 0.15})`; // Blue
    } else {
      return `rgba(239, 68, 68, ${abs * 0.85 + 0.15})`; // Red
    }
  };

  const getTextColor = (value: number) => {
    return Math.abs(value) > 0.5 ? 'white' : 'currentColor';
  };

  return (
    <div className="space-y-3">
      {chart.stats.strongest_positive && (
        <div className="flex items-center gap-4 text-xs">
          <span>
            <span className="font-medium text-blue-500">Strongest +:</span>{' '}
            <span className="text-muted-foreground">{chart.stats.strongest_positive as string}</span>
          </span>
          {chart.stats.strongest_negative && (
            <span>
              <span className="font-medium text-red-500">Strongest −:</span>{' '}
              <span className="text-muted-foreground">{chart.stats.strongest_negative as string}</span>
            </span>
          )}
        </div>
      )}

      <div className="overflow-x-auto">
        <div className="inline-block">
          {/* Header row */}
          <div className="flex" style={{ marginLeft: cellSize * 2.5 }}>
            {columns.map((col) => (
              <div
                key={col}
                className="text-[9px] text-muted-foreground font-mono truncate text-center"
                style={{ width: cellSize }}
                title={col}
              >
                {col.length > 6 ? col.slice(0, 5) + '…' : col}
              </div>
            ))}
          </div>

          {/* Grid */}
          {columns.map((rowCol) => (
            <div key={rowCol} className="flex items-center">
              <div
                className="text-[9px] text-muted-foreground font-mono truncate text-right pr-2 shrink-0"
                style={{ width: cellSize * 2.5 }}
                title={rowCol}
              >
                {rowCol}
              </div>
              {columns.map((colCol) => {
                const cell = chart.data.find((d) => d.row === rowCol && d.col === colCol);
                const value = cell?.value ?? 0;
                const isDiagonal = rowCol === colCol;

                return (
                  <div
                    key={colCol}
                    className="border border-background/50 flex items-center justify-center transition-all hover:ring-1 hover:ring-foreground/20 hover:z-10"
                    style={{
                      width: cellSize,
                      height: cellSize,
                      backgroundColor: isDiagonal ? 'hsl(var(--muted))' : getColor(value),
                      color: isDiagonal ? 'hsl(var(--muted-foreground))' : getTextColor(value),
                    }}
                    title={`${rowCol} × ${colCol}: ${value.toFixed(3)}`}
                  >
                    <span className="text-[9px] font-mono font-bold">
                      {isDiagonal ? '1' : value.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          ))}

          {/* Color scale legend */}
          <div className="flex items-center gap-2 mt-3 ml-auto justify-end text-[9px] text-muted-foreground">
            <span className="font-medium">−1</span>
            <div className="flex h-3 w-32 rounded overflow-hidden">
              {Array.from({ length: 20 }).map((_, i) => {
                const val = -1 + (i / 19) * 2;
                return <div key={i} className="flex-1" style={{ backgroundColor: getColor(val) }} />;
              })}
            </div>
            <span className="font-medium">+1</span>
          </div>
        </div>
      </div>
    </div>
  );
}
