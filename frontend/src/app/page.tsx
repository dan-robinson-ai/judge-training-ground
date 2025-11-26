"use client";

import { useTrainingStore } from "@/lib/store";
import { PromptEditor } from "@/components/training-ground/PromptEditor";
import { DataGrid } from "@/components/training-ground/DataGrid";
import { ResultsView } from "@/components/training-ground/ResultsView";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Database, LineChart, AlertCircle, X } from "lucide-react";

export default function Home() {
  const { activeTab, setActiveTab, error, clearError } = useTrainingStore();

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-primary-foreground">JT</span>
          </div>
          <h1 className="text-lg font-semibold text-foreground">
            Judge Training Ground
          </h1>
        </div>
        <div className="text-sm text-muted-foreground">
          Train and optimize LLM judges
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 bg-[#e5484d]/10 border-b border-[#e5484d]/20 px-6 py-3">
          <AlertCircle className="h-4 w-4 text-[#e5484d]" />
          <span className="flex-1 text-sm text-[#e5484d]">{error}</span>
          <button
            onClick={clearError}
            className="text-[#e5484d] hover:text-[#e5484d]/80"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex flex-1 min-h-0">
        {/* Left Panel - Engineer View */}
        <div className="w-1/2 border-r border-border">
          <PromptEditor />
        </div>

        {/* Right Panel - Data View */}
        <div className="w-1/2 flex flex-col">
          <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as "dataset" | "results")}
            className="flex flex-1 flex-col"
          >
            <div className="border-b border-border px-4">
              <TabsList className="h-12 bg-transparent">
                <TabsTrigger
                  value="dataset"
                  className="gap-2 data-[state=active]:bg-secondary"
                >
                  <Database className="h-4 w-4" />
                  Dataset
                </TabsTrigger>
                <TabsTrigger
                  value="results"
                  className="gap-2 data-[state=active]:bg-secondary"
                >
                  <LineChart className="h-4 w-4" />
                  Results
                </TabsTrigger>
              </TabsList>
            </div>
            <TabsContent value="dataset" className="flex-1 m-0 min-h-0">
              <DataGrid />
            </TabsContent>
            <TabsContent value="results" className="flex-1 m-0 min-h-0">
              <ResultsView />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
