import { 
  Search, 
  BarChart2, 
  Shield, 
  Layers, 
  GitBranch, 
  Download,
  Sparkles,
  Zap
} from 'lucide-react';

const primaryFeature = {
  icon: Sparkles,
  title: 'AI Dataset Analysis',
  description: 'Our proprietary AI analyzes every dataset across 50+ dimensions including completeness, bias, privacy risk, and ML suitability. Get comprehensive insights in seconds.',
  points: [
    'Automated bias detection',
    'Statistical quality assessment',
    'Privacy risk evaluation',
    'ML task recommendations'
  ]
};

const secondaryFeatures = [
  {
    icon: Search,
    title: 'Semantic Search',
    description: 'Natural language queries that understand context and intent.',
  },
  {
    icon: BarChart2,
    title: 'Auto EDA',
    description: 'Instant visualizations and statistical insights.',
  },
  {
    icon: Shield,
    title: 'Quality Scoring',
    description: 'Comprehensive reliability metrics.',
  },
];

const otherFeatures = [
  {
    icon: Layers,
    title: 'Multi-Source',
    description: 'Kaggle, GitHub, HuggingFace, Government data—all in one place.',
  },
  {
    icon: GitBranch,
    title: 'ML Recommendations',
    description: 'Suggested models and pipelines based on dataset characteristics.',
  },
  {
    icon: Download,
    title: 'Starter Code',
    description: 'Generate boilerplate for TensorFlow, PyTorch, and Scikit-learn.',
  },
  {
    icon: Zap,
    title: 'One-Click Integration',
    description: 'Seamlessly import datasets to your ML environment.',
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="relative py-20 sm:py-32 overflow-hidden">
      {/* Background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 h-96 w-96 rounded-full bg-primary/10 blur-3xl opacity-40" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-16 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground mb-4">
            Powerful Features for Smarter Discovery
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything you need to find, evaluate, and integrate the perfect dataset.
          </p>
        </div>

        {/* Primary Feature - Large block */}
        <div className="mb-16 rounded-2xl border border-primary/30 bg-card/40 backdrop-blur-lg overflow-hidden">
          <div className="grid lg:grid-cols-2 gap-0">
            <div className="p-8 sm:p-12 flex flex-col justify-center">
              <div className="mb-6 inline-flex w-fit items-center gap-2 rounded-lg bg-primary/10 border border-primary/20 px-3 py-1.5 text-sm text-primary">
                <primaryFeature.icon className="h-4 w-4" />
                <span className="font-medium">Featured</span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-bold text-foreground mb-4">
                {primaryFeature.title}
              </h3>
              <p className="text-muted-foreground mb-8 leading-relaxed">
                {primaryFeature.description}
              </p>

              <div className="space-y-3">
                {primaryFeature.points.map((point) => (
                  <div key={point} className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-primary flex-shrink-0" />
                    <span className="text-sm text-muted-foreground">{point}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Visual representation */}
            <div className="p-8 sm:p-12 bg-gradient-to-br from-primary/10 to-blue-500/10 flex items-center justify-center min-h-80">
              <div className="relative w-full h-full flex items-center justify-center">
                {/* Metric cards layout */}
                <div className="grid grid-cols-2 gap-4 w-full">
                  {[
                    { label: 'Quality', value: '82%', color: 'from-green-500/20 to-emerald-500/10' },
                    { label: 'Bias Risk', value: 'Low', color: 'from-blue-500/20 to-cyan-500/10' },
                    { label: 'Privacy', value: '91%', color: 'from-purple-500/20 to-pink-500/10' },
                    { label: 'Freshness', value: '68%', color: 'from-amber-500/20 to-orange-500/10' },
                  ].map((metric) => (
                    <div key={metric.label} className={`rounded-lg bg-gradient-to-br ${metric.color} border border-primary/20 p-4 text-center`}>
                      <p className="text-xs text-muted-foreground mb-2">{metric.label}</p>
                      <p className="text-lg font-bold text-foreground">{metric.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Secondary Features - 3 cards */}
        <div className="mb-16">
          <div className="grid gap-6 md:grid-cols-3">
            {secondaryFeatures.map((feature) => (
              <div
                key={feature.title}
                className="group rounded-xl border border-primary/20 bg-card/40 backdrop-blur-lg p-6 hover:border-primary/40 transition-all hover:shadow-lg hover:bg-card/60"
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mb-2 font-semibold text-foreground">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Features - 4 cards grid */}
        <div>
          <h3 className="text-lg font-semibold text-foreground mb-6">Additional Capabilities</h3>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {otherFeatures.map((feature) => (
              <div
                key={feature.title}
                className="rounded-lg border border-border/50 bg-card/30 backdrop-blur-sm p-5 hover:border-primary/30 transition-all"
              >
                <div className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/70">
                  <feature.icon className="h-4 w-4 text-foreground" />
                </div>
                <h4 className="mb-1 text-sm font-semibold text-foreground">{feature.title}</h4>
                <p className="text-xs leading-relaxed text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
