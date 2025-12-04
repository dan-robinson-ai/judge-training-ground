"use client";

import { Scale, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface WelcomeViewProps {
  onCreateDataset: () => void;
}

export function WelcomeView({ onCreateDataset }: WelcomeViewProps) {
  return (
    <div className="flex flex-1 items-center justify-center bg-background">
      <div className="text-center max-w-md px-6">
        <div className="flex justify-center mb-6">
          <div className="h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Scale className="h-10 w-10 text-primary" />
          </div>
        </div>
        <h2 className="text-2xl font-semibold text-foreground mb-3">
          Welcome to Judge Training Ground
        </h2>
        <p className="text-muted-foreground mb-8">
          Create your first dataset to start training and optimizing LLM-based
          evaluation systems. Each dataset can have multiple prompt versions
          and evaluation runs.
        </p>
        <Button size="lg" onClick={onCreateDataset} className="gap-2">
          <Plus className="h-5 w-5" />
          Create Your First Dataset
        </Button>
      </div>
    </div>
  );
}
