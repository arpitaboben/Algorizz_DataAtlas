'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CTASection() {
  return (
    <section className="relative py-20 sm:py-32 overflow-hidden">
      {/* Animated background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-blue-500/5" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-primary/10 blur-3xl opacity-50" />
      </div>

      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-primary/30 bg-card/40 backdrop-blur-xl overflow-hidden">
          <div className="px-6 py-16 sm:px-12 sm:py-24 text-center">
            {/* Heading */}
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-foreground mb-6 max-w-2xl mx-auto">
              Stop guessing.{' '}
              <span className="bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
                Start building
              </span>{' '}
              with better data.
            </h2>

            {/* Subheading */}
            <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
              Join thousands of data scientists and ML engineers who&apos;ve found the perfect datasets in minutes, not days.
            </p>

            {/* Stats */}
            <div className="grid sm:grid-cols-3 gap-8 my-12 py-8 border-y border-border/50">
              {[
                { number: '10K+', label: 'Datasets Analyzed' },
                { number: '50+', label: 'Quality Metrics' },
                { number: '4', label: 'Data Sources' },
              ].map((stat) => (
                <div key={stat.label}>
                  <p className="text-3xl sm:text-4xl font-bold text-primary mb-2">{stat.number}</p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <Link href="/signup">
                <Button size="lg" className="gap-2 w-full sm:w-auto text-base">
                  Get Started Free
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="w-full sm:w-auto text-base">
                  Schedule Demo
                </Button>
              </Link>
            </div>

            {/* Trust line */}
            <p className="text-sm text-muted-foreground">
              No credit card required. Start discovering better datasets in minutes.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
