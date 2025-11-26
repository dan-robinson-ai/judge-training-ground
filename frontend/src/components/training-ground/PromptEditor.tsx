"use client";

import { useTrainingStore } from "@/lib/store";
import { AVAILABLE_MODELS } from "@/lib/types";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sparkles, Play, Wand2, Loader2 } from "lucide-react";

export function PromptEditor() {
  const {
    intent,
    setIntent,
    systemPrompt,
    setSystemPrompt,
    selectedModel,
    setSelectedModel,
    testCases,
    runStats,
    isGenerating,
    isRunning,
    isOptimizing,
    generateTestCases,
    runEvaluation,
    optimizePrompt,
  } = useTrainingStore();

  const canOptimize = runStats && runStats.accuracy < 100;

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
        <div className="flex gap-2">
          <Input
            id="intent"
            placeholder="e.g., Detect toxic messages, Identify spam content..."
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            className="flex-1 bg-secondary/50 border-border"
          />
          <Button
            onClick={() => generateTestCases(10)}
            disabled={isGenerating || !intent.trim()}
            className="shrink-0"
          >
            {isGenerating ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            Generate
          </Button>
        </div>
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

      {/* System Prompt */}
      <div className="flex flex-1 flex-col space-y-2 min-h-0">
        <Label htmlFor="prompt" className="text-sm font-medium">
          System Prompt
        </Label>
        <Textarea
          id="prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="Enter your system prompt for the judge..."
          className="flex-1 resize-none bg-secondary/50 border-border font-mono text-sm"
        />
      </div>

      {/* Action Buttons */}
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
          Auto-Optimize
        </Button>
      </div>
    </div>
  );
}
