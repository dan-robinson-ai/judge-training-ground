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

// Framework type
export type OptimizerFramework = "dspy" | "opik";

// DSPy optimizer types
export type DSPyOptimizerType = "bootstrap_fewshot" | "miprov2" | "copro";

// Opik optimizer types
export type OpikOptimizerType =
  | "evolutionary"
  | "fewshot_bayesian"
  | "metaprompt"
  | "hierarchical_reflective"
  | "gepa"
  | "parameter";

// Combined type
export type OptimizerType = DSPyOptimizerType | OpikOptimizerType;

// Framework option for UI
export type FrameworkOption = {
  value: OptimizerFramework;
  label: string;
  description: string;
};

export const FRAMEWORK_OPTIONS: FrameworkOption[] = [
  {
    value: "dspy",
    label: "DSPy",
    description: "Stanford NLP's declarative prompt optimization",
  },
  {
    value: "opik",
    label: "Opik",
    description: "Comet ML's agent optimization framework",
  },
];

// Optimizer option with framework association
export type OptimizerOption = {
  value: OptimizerType;
  label: string;
  description: string;
  framework: OptimizerFramework;
};

export const OPTIMIZER_OPTIONS: OptimizerOption[] = [
  // DSPy optimizers
  {
    value: "bootstrap_fewshot",
    label: "BootstrapFewShot",
    description: "Adds fewshot examples to improve accuracy",
    framework: "dspy",
  },
  {
    value: "miprov2",
    label: "MIPROv2",
    description: "Bayesian optimization for prompts",
    framework: "dspy",
  },
  {
    value: "copro",
    label: "COPRO",
    description: "Cooperative prompt optimization",
    framework: "dspy",
  },
  // Opik optimizers
  {
    value: "evolutionary",
    label: "Evolutionary",
    description: "Genetic algorithm-based prompt evolution",
    framework: "opik",
  },
  {
    value: "fewshot_bayesian",
    label: "Few-Shot Bayesian",
    description: "Few-shot learning with Bayesian optimization",
    framework: "opik",
  },
  {
    value: "metaprompt",
    label: "MetaPrompt",
    description: "Meta-reasoning prompt enhancement",
    framework: "opik",
  },
  {
    value: "hierarchical_reflective",
    label: "Hierarchical Reflective",
    description: "Hierarchical reflective prompt optimization",
    framework: "opik",
  },
  {
    value: "gepa",
    label: "GEPA",
    description: "Genetic-Pareto optimization approach",
    framework: "opik",
  },
  {
    value: "parameter",
    label: "Parameter",
    description: "LLM parameter tuning (temperature, top_p)",
    framework: "opik",
  },
];

// Helper function to filter optimizers by framework
export function getOptimizersForFramework(
  framework: OptimizerFramework
): OptimizerOption[] {
  return OPTIMIZER_OPTIONS.filter((opt) => opt.framework === framework);
}

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
  framework?: OptimizerFramework;
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
