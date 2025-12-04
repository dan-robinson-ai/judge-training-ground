"use client";

import { useState } from "react";
import { useTrainingStore } from "@/lib/store";
import { PromptVersion } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  GitBranch,
  Sparkles,
  Wand2,
  Edit3,
  ChevronDown,
  ChevronRight,
  Check,
} from "lucide-react";

function getSourceIcon(source: PromptVersion["source"]) {
  switch (source) {
    case "generated":
      return <Sparkles className="h-4 w-4 text-blue-500" />;
    case "optimized":
      return <Wand2 className="h-4 w-4 text-purple-500" />;
    case "manual":
      return <Edit3 className="h-4 w-4 text-gray-500" />;
  }
}

function getSourceLabel(source: PromptVersion["source"]) {
  switch (source) {
    case "generated":
      return "Generated";
    case "optimized":
      return "Optimized";
    case "manual":
      return "Manual";
  }
}

export function PromptVersionsView() {
  const {
    promptVersions,
    runs,
    activePromptVersionId,
    selectPromptVersion,
  } = useTrainingStore();

  const [expandedVersionId, setExpandedVersionId] = useState<string | null>(
    null
  );

  if (promptVersions.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center p-8">
        <div className="rounded-full bg-secondary p-4">
          <GitBranch className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <h3 className="font-medium text-foreground">No prompt versions yet</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Generate test cases or save a prompt manually to create a version
          </p>
        </div>
      </div>
    );
  }

  // Get best accuracy for each version from runs
  const versionMetrics = promptVersions.map((version) => {
    const versionRuns = runs.filter((r) => r.promptVersionId === version.id);
    const bestRun =
      versionRuns.length > 0
        ? versionRuns.reduce((best, run) =>
            run.stats.accuracy > best.stats.accuracy ? run : best
          )
        : null;
    return {
      version,
      runCount: versionRuns.length,
      bestAccuracy: bestRun?.stats.accuracy ?? null,
      bestKappa: bestRun?.stats.cohen_kappa ?? null,
    };
  });

  // Sort by version number descending (newest first)
  const sortedVersionMetrics = [...versionMetrics].sort(
    (a, b) => b.version.version - a.version.version
  );

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="text-sm text-muted-foreground">
          {promptVersions.length} version
          {promptVersions.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Version List */}
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {sortedVersionMetrics.map(
          ({ version, runCount, bestAccuracy, bestKappa }) => {
            const isActive = version.id === activePromptVersionId;
            const isExpanded = expandedVersionId === version.id;

            return (
              <Card
                key={version.id}
                className={`cursor-pointer transition-colors ${
                  isActive
                    ? "border-primary bg-primary/5"
                    : "hover:border-muted-foreground/50"
                }`}
                onClick={() => selectPromptVersion(version.id)}
              >
                <CardHeader className="py-3 px-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedVersionId(isExpanded ? null : version.id);
                        }}
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </Button>

                      <div className="flex items-center gap-2">
                        {getSourceIcon(version.source)}
                        <span className="font-medium">
                          Version {version.version}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {getSourceLabel(version.source)}
                        </Badge>
                        {isActive && (
                          <Badge className="bg-primary text-xs">
                            <Check className="h-3 w-3 mr-1" />
                            Active
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm">
                      {bestAccuracy !== null && (
                        <div className="text-center">
                          <div
                            className={`font-medium ${
                              bestAccuracy >= 90
                                ? "text-[#30a46c]"
                                : bestAccuracy >= 70
                                ? "text-[#f5a623]"
                                : "text-[#e5484d]"
                            }`}
                          >
                            {bestAccuracy.toFixed(1)}%
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Best Acc.
                          </div>
                        </div>
                      )}
                      {bestKappa !== null && (
                        <div className="text-center">
                          <div className="font-medium">
                            {bestKappa.toFixed(2)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Best k
                          </div>
                        </div>
                      )}
                      <div className="text-center">
                        <div className="font-medium">{runCount}</div>
                        <div className="text-xs text-muted-foreground">
                          Runs
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                {isExpanded && (
                  <CardContent className="pt-0 px-4 pb-4">
                    <div className="space-y-3">
                      <div className="text-xs text-muted-foreground">
                        Created:{" "}
                        {new Date(version.createdAt).toLocaleString()}
                        {version.optimizerType && (
                          <span className="ml-2">
                            | Optimizer: {version.optimizerType}
                          </span>
                        )}
                      </div>
                      {version.notes && (
                        <div className="text-sm bg-secondary/50 rounded p-2">
                          <div className="text-xs text-muted-foreground mb-1">
                            Notes:
                          </div>
                          {version.notes}
                        </div>
                      )}
                      <div className="bg-secondary/50 rounded p-3 font-mono text-xs max-h-40 overflow-auto whitespace-pre-wrap">
                        {version.systemPrompt}
                      </div>
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          }
        )}
      </div>
    </div>
  );
}
