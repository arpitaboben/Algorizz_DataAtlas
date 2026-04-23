'use client';

import Link from 'next/link';
import { ArrowRight, Sparkles, TrendingUp, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function HeroSection() {
  return (
    <section className="relative overflow-hidden pt-20 pb-20 sm:pt-32 sm:pb-32 lg:pt-40 lg:pb-40">
      {/* Animated background elements */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {/* Gradient orb 1 */}
        <div className="absolute -top-1/4 -right-1/4 h-96 w-96 rounded-full bg-gradient-to-br from-primary/40 to-blue-500/20 blur-3xl opacity-40 animate-pulse" />
        {/* Gradient orb 2 */}
        <div className="absolute top-1/3 -left-1/4 h-80 w-80 rounded-full bg-gradient-to-tr from-purple-500/20 to-primary/30 blur-3xl opacity-30" style={{ animation: 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite 2s' }} />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2 items-center">
          {/* LEFT SIDE */}
          <div className="flex flex-col justify-center">
            <div className="mb-8 inline-flex w-fit items-center gap-2 rounded-full border border-primary/30 bg-primary/5 backdrop-blur-sm px-4 py-1.5 text-sm text-primary">
              <Sparkles className="h-4 w-4" />
              <span className="font-medium">AI-Powered Dataset Discovery</span>
            </div>

            <h1 className="text-balance text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-foreground mb-6 leading-tight">
              Find the perfect dataset for your{' '}
              <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
                ML project
              </span>
            </h1>

            <p className="text-lg leading-relaxed text-muted-foreground mb-8 max-w-lg">
              Stop wasting hours searching across scattered platforms. DataAtlas intelligently aggregates and ranks datasets from Kaggle, GitHub, HuggingFace, and more—all in one place.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Link href="/signup">
                <Button size="lg" className="gap-2 w-full sm:w-auto">
                  Get Started Free
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  View Demo
                </Button>
              </Link>
            </div>

            <div className="flex flex-wrap gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-muted-foreground">10K+ Datasets</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-muted-foreground">4 Data Sources</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-muted-foreground">Instant EDA</span>
              </div>
            </div>
          </div>

          {/* RIGHT SIDE - Product UI Mock */}
          <div className="relative hidden lg:flex items-center justify-center">
            {/* Product card container with glassmorphism */}
            <div className="relative w-full max-w-sm">
              {/* Glow effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-blue-500/20 rounded-2xl blur-2xl opacity-60" />
              
              {/* Main card */}
              <div className="relative rounded-2xl border border-primary/30 bg-card/40 backdrop-blur-xl p-6 space-y-6 shadow-2xl">
                {/* Card header */}
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                      <h3 className="font-semibold text-foreground text-sm">ImageNet Subset</h3>
                      <p className="text-xs text-muted-foreground">Computer Vision Dataset</p>
                    </div>
                    <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/30">
                      Premium
                    </Badge>
                  </div>
                </div>

                {/* Quality Score */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground font-medium">Quality Score</span>
                    <span className="text-lg font-bold text-primary">82/100</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                    <div className="h-full w-4/5 bg-gradient-to-r from-primary to-blue-500" />
                  </div>
                </div>

                {/* Metrics grid */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-lg bg-secondary/50 p-3 text-center">
                    <div className="text-xs text-muted-foreground mb-1">Bias</div>
                    <div className="font-semibold text-sm text-foreground">Low</div>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-3 text-center">
                    <div className="text-xs text-muted-foreground mb-1">Missing</div>
                    <div className="font-semibold text-sm text-foreground">12%</div>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-3 text-center">
                    <div className="text-xs text-muted-foreground mb-1">Size</div>
                    <div className="font-semibold text-sm text-foreground">450MB</div>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-xs">Image Classification</Badge>
                  <Badge variant="secondary" className="text-xs">10k Images</Badge>
                  <Badge variant="secondary" className="text-xs">1000 Classes</Badge>
                </div>

                {/* Mini chart visualization */}
                <div className="pt-4 border-t border-border/50">
                  <div className="flex items-end justify-between gap-1 h-12">
                    {[40, 65, 35, 80, 55, 72, 48].map((value, i) => (
                      <div
                        key={i}
                        className="flex-1 rounded-sm bg-gradient-to-t from-primary to-blue-400 opacity-70 hover:opacity-100 transition-opacity"
                        style={{ height: `${value}%` }}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Sample Distribution</p>
                </div>
              </div>

              {/* Floating detail cards */}
              <div className="absolute -bottom-4 -left-6 rounded-xl border border-primary/20 bg-card/60 backdrop-blur-lg p-4 shadow-lg max-w-xs">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-xs font-medium text-muted-foreground">Trending</span>
                </div>
                <p className="text-xs text-foreground">Up 24% this month</p>
              </div>

              <div className="absolute top-6 -right-8 rounded-xl border border-primary/20 bg-card/60 backdrop-blur-lg p-4 shadow-lg max-w-xs">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="h-4 w-4 text-amber-500" />
                  <span className="text-xs font-medium text-muted-foreground">Note</span>
                </div>
                <p className="text-xs text-foreground">Perfect for CV models</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
