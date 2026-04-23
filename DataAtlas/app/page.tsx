import { LandingHeader } from '@/components/landing/header';
import { HeroSection } from '@/components/landing/hero-section';
import { StorySection } from '@/components/landing/story-section';
import { NutritionLabelSection } from '@/components/landing/nutrition-label-section';
import { FeaturesSection } from '@/components/landing/features-section';
import { DemoSection } from '@/components/landing/demo-section';
import { ArchitectureSection } from '@/components/landing/architecture-section';
import { CTASection } from '@/components/landing/cta-section';
import { Footer } from '@/components/landing/footer';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingHeader />
      <main>
        <HeroSection />
        <StorySection />
        <NutritionLabelSection />
        <FeaturesSection />
        <DemoSection />
        <ArchitectureSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
