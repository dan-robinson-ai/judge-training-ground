from pydantic import BaseModel, Field
from typing import Literal
from uuid import uuid4


class TestCase(BaseModel):
    """A single test case for evaluating the judge."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    input_text: str
    expected_verdict: Literal["PASS", "FAIL"]
    reasoning: str
    verified: bool = False


class EvaluationResult(BaseModel):
    """Result of evaluating a single test case."""
    test_case_id: str
    actual_verdict: Literal["PASS", "FAIL", "ERROR"]
    reasoning: str
    correct: bool


class GenerateRequest(BaseModel):
    """Request to generate synthetic test cases."""
    intent: str = Field(..., description="The intent to generate test cases for")
    count: int = Field(default=10, ge=1, le=50, description="Number of test cases to generate")


class GenerateResponse(BaseModel):
    """Response containing generated test cases."""
    test_cases: list[TestCase]


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
    results: list[EvaluationResult]


class OptimizeRequest(BaseModel):
    """Request to optimize the system prompt."""
    current_prompt: str
    test_cases: list[TestCase]
    results: list[EvaluationResult]


class OptimizeResponse(BaseModel):
    """Response containing the optimized prompt."""
    optimized_prompt: str
    modification_notes: str
