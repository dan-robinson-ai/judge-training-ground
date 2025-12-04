from pydantic import BaseModel, Field
from typing import Literal
from uuid import uuid4


# LLM Response Schemas (for structured output)
class GeneratedTestCase(BaseModel):
    """Schema for a single test case from LLM generation."""
    input_text: str
    expected_verdict: Literal["PASS", "FAIL"]
    difficulty: Literal["clear_pass", "clear_fail", "tricky_negative", "tricky_positive"]
    reasoning: str


class GeneratedTestCaseList(BaseModel):
    """Schema for LLM response containing generated test cases."""
    test_cases: list[GeneratedTestCase]


class JudgeVerdict(BaseModel):
    """Schema for LLM judge evaluation response."""
    verdict: Literal["PASS", "FAIL"]
    reasoning: str


class OptimizedPromptResponse(BaseModel):
    """Schema for LLM prompt optimization response."""
    optimized_prompt: str
    modification_notes: str


class GeneratedSystemPrompt(BaseModel):
    """Schema for LLM-generated initial system prompt."""
    system_prompt: str


class TestCase(BaseModel):
    """A single test case for evaluating the judge."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    input_text: str
    expected_verdict: Literal["PASS", "FAIL"]
    reasoning: str
    verified: bool = False
    split: Literal["train", "test"] | None = None  # None = not yet split


class EvaluationResult(BaseModel):
    """Result of evaluating a single test case."""
    test_case_id: str
    actual_verdict: Literal["PASS", "FAIL", "ERROR"]
    reasoning: str
    correct: bool


class GenerateRequest(BaseModel):
    """Request to generate synthetic test cases."""
    intent: str = Field(..., description="The intent to generate test cases for")
    count: int = Field(default=50, ge=1, le=100, description="Number of test cases to generate")
    model: str = Field(default="gpt-4o", description="LiteLLM model name for generation")


class GenerateResponse(BaseModel):
    """Response containing generated test cases and initial system prompt."""
    test_cases: list[TestCase]
    system_prompt: str = Field(..., description="Generated initial system prompt based on intent")


class RunRequest(BaseModel):
    """Request to run the judge on test cases."""
    system_prompt: str
    test_cases: list[TestCase]
    model_name: str = Field(default="gpt-4o", description="LiteLLM model name")


class RunStats(BaseModel):
    """Statistics from running the judge."""
    total: int
    passed: int
    failed: int
    errors: int
    accuracy: float
    cohen_kappa: float = 0.0  # Inter-rater agreement metric
    results: list[EvaluationResult]


OptimizerType = Literal["bootstrap_fewshot", "miprov2", "copro"]


class OptimizeRequest(BaseModel):
    """Request to optimize the system prompt."""
    current_prompt: str
    test_cases: list[TestCase]
    results: list[EvaluationResult]
    optimizer_type: OptimizerType = "bootstrap_fewshot"
    model: str = Field(default="gpt-4o", description="LiteLLM model name")


class OptimizeResponse(BaseModel):
    """Response containing the optimized prompt."""
    optimized_prompt: str
    modification_notes: str
    train_cases: list[TestCase]
    test_cases: list[TestCase]


class SplitRequest(BaseModel):
    """Request to split test cases into train/test sets."""
    test_cases: list[TestCase]
    train_ratio: float = Field(default=0.7, ge=0.1, le=0.9, description="Ratio of cases for training")


class SplitResponse(BaseModel):
    """Response containing split test cases."""
    train_cases: list[TestCase]
    test_cases: list[TestCase]
