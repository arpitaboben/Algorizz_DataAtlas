'use client';

import { Search, HelpCircle, Zap, ArrowRight } from 'lucide-react';

const storySteps = [
  {
    number: '01',
    icon: Search,
    title: 'The Hunt',
    description: 'Searching across Kaggle, GitHub, HuggingFace... jumping between tabs.',
  },
  {
    number: '02',
    icon: HelpCircle,
    title: 'The Confusion',
    description: 'Messy metadata, unknown quality, missing documentation. Which dataset is right?',
  },
  {
    number: '03',
    icon: Zap,
    title: 'The Solution',
    description: 'DataAtlas brings clarity. Find, evaluate, and choose the perfect dataset in minutes.',
  },
];

export function StorySection() {
  return (
    <section className="relative py-12 sm:py-16 overflow-hidden">
      {/* Background element */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-16 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground mb-4">
            The Journey from Chaos to Clarity
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            We understand the frustration of finding the right dataset. Here&apos;s how DataAtlas changes that.
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Connecting line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-primary/30 to-transparent -translate-y-1/2" />

          {/* Steps */}
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-3">
            {storySteps.map((step, index) => (
              <div key={step.number} className="relative group">
                {/* Step card */}
                <div className="rounded-2xl border border-primary/20 bg-card/40 backdrop-blur-lg p-8 h-full hover:border-primary/40 transition-all hover:shadow-lg">
                  {/* Step number */}
                  <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-blue-500/20 border border-primary/30">
                    <span className="text-2xl font-bold text-primary">{step.number}</span>
                  </div>

                  {/* Icon and title */}
                  <div className="mb-4 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <step.icon className="h-5 w-5 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground">{step.title}</h3>
                  </div>

                  <p className="text-muted-foreground text-sm leading-relaxed mb-6">
                    {step.description}
                  </p>

                  {/* Arrow indicator */}
                  {index < storySteps.length - 1 && (
                    <div className="flex lg:justify-end">
                      <ArrowRight className="h-5 w-5 text-primary/50 group-hover:text-primary transition-colors lg:rotate-90" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
