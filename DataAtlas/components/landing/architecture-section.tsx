'use client';

import { useState } from 'react';
import { ArrowRight, Database, Globe, Cpu, Server, BarChart3, ChevronDown } from 'lucide-react';
import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';

const architectureFlow = [
  {
    id: 'sources',
    icon: Globe,
    title: 'Data Sources',
    items: ['Kaggle API', 'GitHub API', 'HuggingFace Hub', 'Data.gov'],
    details: 'Data Sources layer aggregates datasets from multiple platforms using official APIs and web scraping techniques to create a unified data lake.',
    technologies: ['Kaggle API', 'GitHub GraphQL', 'HuggingFace Hub API', 'Requests/Selenium'],
  },
  {
    id: 'processing',
    icon: Cpu,
    title: 'AI Processing',
    items: ['Semantic Embeddings', 'Quality Analysis', 'ML Task Detection'],
    details: 'The AI Processing layer analyzes dataset characteristics, generates embeddings for semantic search, detects quality issues, and recommends suitable ML tasks.',
    technologies: ['OpenAI Embeddings', 'Pandas Profiling', 'scikit-learn', 'LLMs for Analysis'],
  },
  {
    id: 'storage',
    icon: Database,
    title: 'Storage',
    items: ['PostgreSQL', 'Pinecone Vectors', 'Redis Cache'],
    details: 'Storage layer persists structured dataset metadata, vector embeddings for fast semantic search, and caches frequently accessed data for performance.',
    technologies: ['PostgreSQL', 'Pinecone DB', 'Redis', 'S3 (metadata backups)'],
  },
  {
    id: 'backend',
    icon: Server,
    title: 'Backend',
    items: ['FastAPI', 'REST + GraphQL', 'Auth & Rate Limiting'],
    details: 'Backend API handles authentication, request routing, rate limiting, and coordinates between frontend and data processing services.',
    technologies: ['FastAPI', 'GraphQL (Strawberry)', 'JWT Auth', 'Kubernetes'],
  },
  {
    id: 'frontend',
    icon: BarChart3,
    title: 'Frontend',
    items: ['Next.js App', 'Real-time Updates', 'Interactive EDA'],
    details: 'The frontend delivers an intuitive dashboard for searching, analyzing, and previewing datasets with real-time updates and interactive visualizations.',
    technologies: ['Next.js 16', 'React 19', 'WebSockets', 'TailwindCSS'],
  },
];

export function ArchitectureSection() {
  const [selectedArchitecture, setSelectedArchitecture] = useState<string | null>(null);

  return (
    <section id="architecture" className="py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Architecture Overview
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            A scalable, production-ready system for intelligent dataset discovery.
          </p>
        </div>

        <div className="mt-12">
          <div className="flex flex-col items-center gap-3 lg:flex-row lg:justify-center lg:gap-0">
            {architectureFlow.map((stage, index) => (
              <div key={stage.id} className="flex items-center w-full lg:w-auto">
                <Dialog open={selectedArchitecture === stage.id} onOpenChange={(open) => setSelectedArchitecture(open ? stage.id : null)}>
                  <DialogTrigger asChild>
                    <button className="w-full lg:w-auto group rounded-xl border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-lg cursor-pointer active:scale-95">
                      <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                        <stage.icon className="h-5 w-5 text-primary" />
                      </div>
                      <h3 className="mb-2 font-semibold text-card-foreground text-left">{stage.title}</h3>
                      <ul className="space-y-1 text-left">
                        {stage.items.slice(0, 2).map((item) => (
                          <li key={item} className="text-xs text-muted-foreground">
                            {item}
                          </li>
                        ))}
                      </ul>
                      <div className="mt-3 flex items-center gap-1 text-xs text-primary font-medium group-hover:gap-2 transition-all">
                        <span>Details</span>
                        <ChevronDown className="h-3 w-3" />
                      </div>
                    </button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogTitle className="flex items-center gap-2">
                      <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <stage.icon className="h-5 w-5 text-primary" />
                      </div>
                      {stage.title}
                    </DialogTitle>
                    <DialogDescription asChild>
                      <div className="space-y-4">
                        <p>{stage.details}</p>
                        <div className="space-y-2">
                          <p className="text-sm font-semibold text-foreground">Key Technologies:</p>
                          <div className="flex flex-wrap gap-2">
                            {stage.technologies.map((tech) => (
                              <span key={tech} className="inline-block bg-secondary/80 text-foreground text-xs px-2.5 py-1 rounded-md">
                                {tech}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </DialogDescription>
                  </DialogContent>
                </Dialog>
                {index < architectureFlow.length - 1 && (
                  <ArrowRight className="mx-2 hidden h-5 w-5 text-muted-foreground lg:block flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
