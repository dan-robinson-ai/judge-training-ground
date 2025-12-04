"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    EvaluationResult,
    GeneratedSystemPrompt,
    GeneratedTestCase,
    GeneratedTestCaseList,
    GenerateRequest,
    GenerateResponse,
    JudgeVerdict,
    OptimizedPromptResponse,
    RunRequest,
    RunStats,
    TestCase,
)


class TestTestCase:
    def test_create_test_case(self):
        tc = TestCase(
            input_text="Hello world",
            expected_verdict="PASS",
            reasoning="Friendly greeting",
        )
        assert tc.input_text == "Hello world"
        assert tc.expected_verdict == "PASS"
        assert tc.reasoning == "Friendly greeting"
        assert tc.verified is False
        assert tc.id is not None

    def test_test_case_with_custom_id(self):
        tc = TestCase(
            id="custom-id",
            input_text="Test",
            expected_verdict="FAIL",
            reasoning="Test reasoning",
        )
        assert tc.id == "custom-id"

    def test_invalid_verdict(self):
        with pytest.raises(ValidationError):
            TestCase(
                input_text="Test",
                expected_verdict="INVALID",
                reasoning="Test",
            )


class TestEvaluationResult:
    def test_create_evaluation_result(self):
        result = EvaluationResult(
            test_case_id="test-1",
            actual_verdict="PASS",
            reasoning="Looks good",
            correct=True,
        )
        assert result.test_case_id == "test-1"
        assert result.actual_verdict == "PASS"
        assert result.correct is True

    def test_error_verdict(self):
        result = EvaluationResult(
            test_case_id="test-1",
            actual_verdict="ERROR",
            reasoning="Failed to evaluate",
            correct=False,
        )
        assert result.actual_verdict == "ERROR"


class TestGenerateRequest:
    def test_default_values(self):
        req = GenerateRequest(intent="Detect spam")
        assert req.intent == "Detect spam"
        assert req.count == 50
        assert req.model == "gpt-4o"

    def test_custom_values(self):
        req = GenerateRequest(intent="Detect spam", count=25, model="claude-3-5-sonnet-20241022")
        assert req.count == 25
        assert req.model == "claude-3-5-sonnet-20241022"

    def test_count_validation(self):
        with pytest.raises(ValidationError):
            GenerateRequest(intent="Test", count=0)

        with pytest.raises(ValidationError):
            GenerateRequest(intent="Test", count=101)


class TestGenerateResponse:
    def test_create_response(self):
        tc = TestCase(
            input_text="Test",
            expected_verdict="PASS",
            reasoning="Test",
        )
        resp = GenerateResponse(test_cases=[tc], system_prompt="You are a judge...")
        assert len(resp.test_cases) == 1
        assert resp.system_prompt == "You are a judge..."


class TestRunRequest:
    def test_create_run_request(self):
        tc = TestCase(
            input_text="Test",
            expected_verdict="PASS",
            reasoning="Test",
        )
        req = RunRequest(
            system_prompt="You are a judge",
            test_cases=[tc],
        )
        assert req.system_prompt == "You are a judge"
        assert req.model_name == "gpt-4o"


class TestRunStats:
    def test_create_run_stats(self):
        result = EvaluationResult(
            test_case_id="test-1",
            actual_verdict="PASS",
            reasoning="Good",
            correct=True,
        )
        stats = RunStats(
            total=10,
            passed=8,
            failed=1,
            errors=1,
            accuracy=80.0,
            results=[result],
        )
        assert stats.total == 10
        assert stats.accuracy == 80.0


class TestLLMResponseSchemas:
    def test_generated_test_case(self):
        gtc = GeneratedTestCase(
            input_text="Test input",
            expected_verdict="PASS",
            difficulty="clear_pass",
            reasoning="This is clearly appropriate",
        )
        assert gtc.difficulty == "clear_pass"

    def test_generated_test_case_list(self):
        gtc = GeneratedTestCase(
            input_text="Test",
            expected_verdict="FAIL",
            difficulty="tricky_negative",
            reasoning="Tricky case",
        )
        gtcl = GeneratedTestCaseList(test_cases=[gtc])
        assert len(gtcl.test_cases) == 1

    def test_judge_verdict(self):
        verdict = JudgeVerdict(verdict="PASS", reasoning="Appropriate content")
        assert verdict.verdict == "PASS"

    def test_optimized_prompt_response(self):
        resp = OptimizedPromptResponse(
            optimized_prompt="Improved prompt",
            modification_notes="Added more clarity",
        )
        assert resp.optimized_prompt == "Improved prompt"

    def test_generated_system_prompt(self):
        gsp = GeneratedSystemPrompt(system_prompt="You are a helpful judge...")
        assert gsp.system_prompt == "You are a helpful judge..."
