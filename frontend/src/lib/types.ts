export interface TestCase {
  id: string;
  input_text: string;
  expected_verdict: "PASS" | "FAIL";
  reasoning: string;
  verified: boolean;
  split?: "train" | "test" | null;
}

export interface EvaluationResult {
  test_case_id: string;
  actual_verdict: "PASS" | "FAIL" | "ERROR";
  reasoning: string;
  correct: boolean;
}

export interface RunStats {
  total: number;
  passed: number;
  failed: number;
  errors: number;
  accuracy: number;
  cohen_kappa: number;
  results: EvaluationResult[];
}

export interface GenerateResponse {
  test_cases: TestCase[];
  system_prompt: string;
}

export interface OptimizeResponse {
  optimized_prompt: string;
  modification_notes: string;
  train_cases: TestCase[];
  test_cases: TestCase[];
}

export type OptimizerType = "bootstrap_fewshot" | "miprov2" | "copro";

export type OptimizerOption = {
  value: OptimizerType;
  label: string;
  description: string;
};

export const OPTIMIZER_OPTIONS: OptimizerOption[] = [
  { value: "bootstrap_fewshot", label: "BootstrapFewShot", description: "Adds fewshot examples to improve accuracy" },
  { value: "miprov2", label: "MIPROv2", description: "Bayesian optimization for prompts" },
  { value: "copro", label: "COPRO", description: "Cooperative prompt optimization" },
];

export type ModelOption = {
  value: string;
  label: string;
  provider: string;
};

export const AVAILABLE_MODELS: ModelOption[] = [
  { value: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
  { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { value: "claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku", provider: "Anthropic" },
];

// Legacy types - kept for migration
export interface Judge {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  intent: string;
  systemPrompt: string;
  testCases: TestCase[];
  runStats: RunStats | null;
  selectedModel: string;
  generateCount: number;
  hasGenerated: boolean;
  isSplit: boolean;
}

export interface JudgeListItem {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  testCaseCount: number;
  accuracy: number | null;
}

// New dataset-centric types with prompt versioning

export interface PromptVersion {
  id: string;
  version: number;
  systemPrompt: string;
  source: "manual" | "generated" | "optimized";
  createdAt: string;
  parentVersionId: string | null;
  notes?: string;
  optimizerType?: OptimizerType;
}

export interface Run {
  id: string;
  promptVersionId: string;
  modelName: string;
  createdAt: string;
  stats: RunStats;
}

export interface Dataset {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  intent: string;
  testCases: TestCase[];
  promptVersions: PromptVersion[];
  runs: Run[];
  activePromptVersionId: string | null;
  generateCount: number;
  hasGenerated: boolean;
  isSplit: boolean;
}

export interface DatasetListItem {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  testCaseCount: number;
  promptVersionCount: number;
  bestAccuracy: number | null;
}
