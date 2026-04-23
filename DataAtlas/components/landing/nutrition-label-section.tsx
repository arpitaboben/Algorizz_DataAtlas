'use client';

import { Activity } from 'lucide-react';

interface NutritionMetric {
  label: string;
  value: number;
  color: string;
  description: string;
}

const metrics: NutritionMetric[] = [
  { label: 'Quality Score', value: 82, color: 'from-green-500 to-emerald-500', description: 'Completeness & Accuracy' },
  { label: 'Data Freshness', value: 68, color: 'from-blue-500 to-cyan-500', description: 'Recency & Updates' },
  { label: 'Bias Risk', value: 35, color: 'from-amber-500 to-orange-500', description: 'Lower is better' },
  { label: 'Privacy Score', value: 91, color: 'from-purple-500 to-pink-500', description: 'Privacy protection' },
];

export function NutritionLabelSection() {
  return (
    <section className="relative py-20 sm:py-32 overflow-hidden">
      {/* Background elements */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-primary/10 blur-3xl opacity-40" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2 items-center">
          {/* Left side - Content */}
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 px-3 py-1.5 text-sm text-primary">
              <Activity className="h-4 w-4" />
              <span className="font-medium">Signature Feature</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground mb-6 leading-tight">
              The Data{' '}
              <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
                Nutrition Label
              </span>
            </h2>

            <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
              Just like food has a nutrition label, datasets need one too. Our AI-powered analysis gives you instant insights into dataset quality, freshness, bias, and privacy—all in one visual dashboard.
            </p>

            <div className="space-y-4">
              {metrics.map((metric) => (
                <div key={metric.label} className="rounded-lg border border-border/50 bg-card/30 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">{metric.label}</span>
                    <span className="text-sm font-bold text-primary">{metric.value}/100</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${metric.color}`}
                      style={{ width: `${metric.value}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">{metric.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right side - Radar Chart */}
          <div className="flex items-center justify-center">
            <div className="relative w-full max-w-sm">
              {/* Glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/30 to-blue-500/20 rounded-3xl blur-2xl opacity-50" />

              {/* Radar chart container */}
              <div className="relative rounded-3xl border border-primary/30 bg-card/50 backdrop-blur-xl p-12 aspect-square flex items-center justify-center">
                {/* SVG Radar Chart */}
                <svg viewBox="0 0 400 400" className="w-full h-full">
                  {/* Background circles */}
                  <circle cx="200" cy="200" r="160" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />
                  <circle cx="200" cy="200" r="120" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />
                  <circle cx="200" cy="200" r="80" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />
                  <circle cx="200" cy="200" r="40" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />

                  {/* Grid lines */}
                  <line x1="200" y1="40" x2="200" y2="360" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />
                  <line x1="40" y1="200" x2="360" y2="200" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />
                  <line x1="88" y1="88" x2="312" y2="312" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />
                  <line x1="312" y1="88" x2="88" y2="312" stroke="currentColor" strokeWidth="1" opacity="0.1" className="text-primary" />

                  {/* Data polygon */}
                  <polygon
                    points="200,71 270,97 300,200 270,303 200,329 130,303 100,200 130,97"
                    fill="url(#radarGradient)"
                    opacity="0.5"
                    className="animate-pulse"
                  />

                  {/* Data outline */}
                  <polygon
                    points="200,71 270,97 300,200 270,303 200,329 130,303 100,200 130,97"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-primary"
                  />

                  {/* Data points */}
                  {[
                    { cx: 200, cy: 71 },
                    { cx: 270, cy: 97 },
                    { cx: 300, cy: 200 },
                    { cx: 270, cy: 303 },
                    { cx: 200, cy: 329 },
                    { cx: 130, cy: 303 },
                    { cx: 100, cy: 200 },
                    { cx: 130, cy: 97 },
                  ].map((point, i) => (
                    <circle
                      key={i}
                      cx={point.cx}
                      cy={point.cy}
                      r="5"
                      fill="currentColor"
                      className="text-primary"
                    />
                  ))}

                  {/* Labels */}
                  <text x="200" y="20" textAnchor="middle" className="fill-foreground text-xs font-medium">Quality</text>
                  <text x="310" y="155" textAnchor="start" className="fill-foreground text-xs font-medium">Freshness</text>
                  <text x="310" y="250" textAnchor="start" className="fill-foreground text-xs font-medium">Privacy</text>
                  <text x="200" y="380" textAnchor="middle" className="fill-foreground text-xs font-medium">Bias</text>
                  <text x="90" y="250" textAnchor="end" className="fill-foreground text-xs font-medium">Completeness</text>
                  <text x="90" y="155" textAnchor="end" className="fill-foreground text-xs font-medium">Diversity</text>

                  {/* Gradient definition */}
                  <defs>
                    <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.5" />
                      <stop offset="100%" stopColor="rgb(147, 51, 234)" stopOpacity="0.5" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>

              {/* Info badges */}
              <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 flex gap-3">
                <div className="rounded-lg bg-card border border-border px-3 py-2 text-center shadow-lg">
                  <p className="text-xs text-muted-foreground mb-1">Overall</p>
                  <p className="text-lg font-bold text-primary">8.2/10</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
