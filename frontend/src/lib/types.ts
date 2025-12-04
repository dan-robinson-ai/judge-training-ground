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

export interface SplitResponse {
  train_cases: TestCase[];
  test_cases: TestCase[];
}

// Multi-judge support types
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
