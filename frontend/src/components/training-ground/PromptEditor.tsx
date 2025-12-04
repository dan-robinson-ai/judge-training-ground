"use client";

import { useTrainingStore } from "@/lib/store";
import { AVAILABLE_MODELS, FRAMEWORK_OPTIONS, getOptimizersForFramework } from "@/lib/types";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sparkles, Play, Wand2, Loader2, Split, Save } from "lucide-react";

export function PromptEditor() {
  const {
    intent,
    setIntent,
    currentSystemPrompt,
    setCurrentSystemPrompt,
    selectedModel,
    setSelectedModel,
    generateCount,
    setGenerateCount,
    optimizerFramework,
    setOptimizerFramework,
    optimizerType,
    setOptimizerType,
    hasGenerated,
    testCases,
    runs,
    promptVersions,
    activePromptVersionId,
    isGenerating,
    isRunning,
    isOptimizing,
    isSplit,
    generateTestCases,
    runEvaluation,
    optimizePrompt,
    savePromptVersion,
  } = useTrainingStore();

  // Get optimizers available for the selected framework
  const availableOptimizers = getOptimizersForFramework(optimizerFramework);

  // Find active version
  const activeVersion = promptVersions.find(
    (v) => v.id === activePromptVersionId
  );

  // Check if we can optimize (need runs for current version)
  const versionRuns = runs.filter(
    (r) => r.promptVersionId === activePromptVersionId
  );
  const latestRun = versionRuns.length > 0 ? versionRuns[versionRuns.length - 1] : null;
  const canOptimize = latestRun && latestRun.stats.accuracy < 100;

  return (
    <div className="flex h-full flex-col gap-6 p-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-foreground">Engineer View</h2>
        <p className="text-sm text-muted-foreground">
          Define your intent and system prompt
        </p>
      </div>

      {/* Intent Input */}
      <div className="space-y-2">
        <Label htmlFor="intent" className="text-sm font-medium">
          Judge Intent
        </Label>
        <Input
          id="intent"
          placeholder="e.g., Detect toxic messages, Identify spam content..."
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          className="bg-secondary/50 border-border"
        />
      </div>

      {/* Number to Generate */}
      <div className="space-y-2">
        <Label htmlFor="count" className="text-sm font-medium">
          Number to Generate
        </Label>
        <Input
          id="count"
          type="number"
          min={1}
          max={100}
          value={generateCount}
          onChange={(e) => setGenerateCount(Math.max(1, Math.min(100, parseInt(e.target.value) || 50)))}
          className="bg-secondary/50 border-border"
        />
      </div>

      {/* Model Selector */}
      <div className="space-y-2">
        <Label htmlFor="model" className="text-sm font-medium">
          Model
        </Label>
        <Select value={selectedModel} onValueChange={setSelectedModel}>
          <SelectTrigger className="bg-secondary/50 border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {AVAILABLE_MODELS.map((model) => (
              <SelectItem key={model.value} value={model.value}>
                <div className="flex items-center gap-2">
                  <span>{model.label}</span>
                  <span className="text-xs text-muted-foreground">
                    ({model.provider})
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Generate Button */}
      <Button
        onClick={() => generateTestCases()}
        disabled={isGenerating || !intent.trim()}
        className="w-full"
      >
        {isGenerating ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="mr-2 h-4 w-4" />
        )}
        Generate Test Cases
      </Button>

      {/* System Prompt - Only shown after generation */}
      {hasGenerated && (
        <div className="flex flex-1 flex-col space-y-2 min-h-0">
          <div className="flex items-center justify-between">
            <Label htmlFor="prompt" className="text-sm font-medium">
              System Prompt
            </Label>
            {activeVersion && (
              <Badge variant="outline" className="text-xs">
                v{activeVersion.version} ({activeVersion.source})
              </Badge>
            )}
          </div>
          <Textarea
            id="prompt"
            value={currentSystemPrompt}
            onChange={(e) => setCurrentSystemPrompt(e.target.value)}
            placeholder="System prompt will be generated..."
            className="flex-1 resize-none bg-secondary/50 border-border font-mono text-sm"
          />
          {/* Save Version Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => savePromptVersion()}
            disabled={!currentSystemPrompt.trim()}
            className="w-fit"
          >
            <Save className="mr-2 h-4 w-4" />
            Save as New Version
          </Button>
        </div>
      )}

      {/* Framework Selector - Only shown after generation */}
      {hasGenerated && (
        <div className="space-y-2">
          <Label htmlFor="framework" className="text-sm font-medium">
            Optimization Framework
          </Label>
          <Select value={optimizerFramework} onValueChange={setOptimizerFramework}>
            <SelectTrigger className="bg-secondary/50 border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FRAMEWORK_OPTIONS.map((fw) => (
                <SelectItem key={fw.value} value={fw.value}>
                  <div className="flex flex-col">
                    <span>{fw.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {fw.description}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Optimizer Selector - Only shown after generation */}
      {hasGenerated && (
        <div className="space-y-2">
          <Label htmlFor="optimizer" className="text-sm font-medium">
            Optimizer
          </Label>
          <Select value={optimizerType} onValueChange={setOptimizerType}>
            <SelectTrigger className="bg-secondary/50 border-border">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {availableOptimizers.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  <div className="flex flex-col">
                    <span>{opt.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {opt.description}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Split Status - shown after optimization splits the data */}
      {isSplit && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground bg-secondary/50 rounded-md px-3 py-2">
          <Split className="h-4 w-4" />
          <span>
            Auto-split: {testCases.filter(tc => tc.split === "train").length} train / {testCases.filter(tc => tc.split === "test").length} test
          </span>
        </div>
      )}

      {/* Action Buttons - Only shown after generation */}
      {hasGenerated && (
        <div className="flex gap-2">
          <Button
            onClick={runEvaluation}
            disabled={isRunning || testCases.length === 0}
            className="flex-1"
            variant="default"
          >
            {isRunning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Run Evaluation
          </Button>
          <Button
            onClick={optimizePrompt}
            disabled={isOptimizing || !canOptimize}
            variant="secondary"
            className="flex-1"
          >
            {isOptimizing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Wand2 className="mr-2 h-4 w-4" />
            )}
            Optimize
          </Button>
        </div>
      )}
    </div>
  );
}
