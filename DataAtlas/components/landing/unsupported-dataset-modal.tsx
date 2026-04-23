'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertCircle, Mail } from 'lucide-react';
import { Dataset } from '@/lib/types';
import { useState } from 'react';

interface UnsupportedDatasetModalProps {
  dataset: Dataset | null;
  isOpen: boolean;
  onClose: () => void;
}

export function UnsupportedDatasetModal({ dataset, isOpen, onClose }: UnsupportedDatasetModalProps) {
  const [notifyEmail, setNotifyEmail] = useState('');
  const [notifySubmitted, setNotifySubmitted] = useState(false);

  if (!dataset) return null;

  const handleNotifySubmit = () => {
    if (notifyEmail) {
      setNotifySubmitted(true);
      setTimeout(() => {
        setNotifyEmail('');
        setNotifySubmitted(false);
        onClose();
      }, 1500);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="h-10 w-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-amber-500" />
            </div>
            <DialogTitle className="text-xl">Coming Soon</DialogTitle>
          </div>
          <DialogDescription>Image dataset analysis is under development</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Dataset info */}
          <div className="rounded-lg bg-secondary/40 border border-border/50 p-4">
            <p className="text-sm font-semibold text-foreground mb-1">{dataset.title}</p>
            <p className="text-xs text-muted-foreground">{dataset.description}</p>
          </div>

          {/* Message */}
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground leading-relaxed">
              DataAtlas currently supports <span className="font-semibold text-foreground">tabular datasets (CSV, JSON, Parquet, Excel)</span>.
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Support for <span className="font-semibold text-foreground">image datasets and Computer Vision</span> tasks is under active development and will be available soon.
            </p>
          </div>

          {/* Notify section */}
          <div className="rounded-lg bg-primary/5 border border-primary/20 p-4 space-y-3">
            <p className="text-sm font-medium text-foreground">Get notified when available</p>
            <div className="flex gap-2">
              <input
                type="email"
                placeholder="your@email.com"
                value={notifyEmail}
                onChange={(e) => setNotifyEmail(e.target.value)}
                className="flex-1 px-3 py-2 rounded-md bg-background border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
                disabled={notifySubmitted}
              />
              <Button
                size="sm"
                variant="default"
                onClick={handleNotifySubmit}
                disabled={!notifyEmail || notifySubmitted}
                className="gap-1"
              >
                {notifySubmitted ? '✓' : <Mail className="h-4 w-4" />}
              </Button>
            </div>
            {notifySubmitted && (
              <p className="text-xs text-green-600">Thanks! We&apos;ll notify you soon.</p>
            )}
          </div>

          {/* Disabled analyze button */}
          <div>
            <Button className="w-full" disabled>
              Analyze Dataset (Unavailable)
            </Button>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-border pt-4">
          <Button variant="outline" className="w-full" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
