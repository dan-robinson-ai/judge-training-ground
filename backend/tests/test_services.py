"""Tests for service modules (generator and judge).

Note: Optimizer tests are in test_optimizer.py
"""

from unittest.mock import patch

import pytest

from app.schemas import (
    GeneratedSystemPrompt,
    GeneratedTestCase,
    GeneratedTestCaseList,
    JudgeVerdict,
    TestCase,
)
from app.services.generator import generate_test_cases
from app.services.judge import LLMJudge


class TestGenerateTestCases:
    @pytest.mark.asyncio
    async def test_generate_test_cases_success(self):
        """Test successful test case generation."""
        mock_test_cases = GeneratedTestCaseList(
            test_cases=[
                GeneratedTestCase(
                    input_text="Hello friend",
                    expected_verdict="PASS",
                    difficulty="clear_pass",
                    reasoning="Friendly greeting",
                ),
                GeneratedTestCase(
                    input_text="I hate you",
                    expected_verdict="FAIL",
                    difficulty="clear_fail",
                    reasoning="Hostile message",
                ),
            ]
        )
        mock_system_prompt = GeneratedSystemPrompt(
            system_prompt="You are a content moderation judge..."
        )

        with patch("app.services.generator.call_llm") as mock_llm:
            mock_llm.side_effect = [mock_test_cases, mock_system_prompt]

            test_cases, system_prompt = await generate_test_cases(
                intent="Detect toxic messages",
                count=2,
                model="gpt-4o",
            )

            assert len(test_cases) == 2
            assert test_cases[0].input_text == "Hello friend"
            assert test_cases[0].expected_verdict == "PASS"
            assert test_cases[1].expected_verdict == "FAIL"
            assert system_prompt == "You are a content moderation judge..."
            assert mock_llm.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_test_cases_llm_error(self):
        """Test handling of LLM errors during generation."""
        with patch("app.services.generator.call_llm") as mock_llm:
            mock_llm.side_effect = ValueError("LLM API error")

            with pytest.raises(ValueError, match="LLM API error"):
                await generate_test_cases(intent="Test", count=5)


class TestLLMJudge:
    @pytest.mark.asyncio
    async def test_evaluate_single_success(self):
        """Test successful single evaluation."""
        mock_verdict = JudgeVerdict(
            verdict="PASS",
            reasoning="Content is appropriate and friendly",
        )

        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.return_value = mock_verdict

            judge = LLMJudge(system_prompt="You are a judge", model="gpt-4o")
            test_case = TestCase(
                id="test-1",
                input_text="Hello!",
                expected_verdict="PASS",
                reasoning="Friendly greeting",
            )

            result = await judge.evaluate_single(test_case)

            assert result.test_case_id == "test-1"
            assert result.actual_verdict == "PASS"
            assert result.correct is True
            assert "appropriate" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_single_incorrect(self):
        """Test evaluation where judge gives incorrect verdict."""
        mock_verdict = JudgeVerdict(
            verdict="FAIL",
            reasoning="Flagged incorrectly",
        )

        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.return_value = mock_verdict

            judge = LLMJudge(system_prompt="You are a judge", model="gpt-4o")
            test_case = TestCase(
                id="test-1",
                input_text="Hello!",
                expected_verdict="PASS",
                reasoning="Friendly greeting",
            )

            result = await judge.evaluate_single(test_case)

            assert result.actual_verdict == "FAIL"
            assert result.correct is False

    @pytest.mark.asyncio
    async def test_evaluate_single_error(self):
        """Test handling of errors during evaluation."""
        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.side_effect = Exception("API error")

            judge = LLMJudge(system_prompt="You are a judge", model="gpt-4o")
            test_case = TestCase(
                id="test-1",
                input_text="Hello!",
                expected_verdict="PASS",
                reasoning="Friendly greeting",
            )

            result = await judge.evaluate_single(test_case)

            assert result.actual_verdict == "ERROR"
            assert result.correct is False
            assert "API error" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_batch(self):
        """Test batch evaluation."""
        mock_verdicts = [
            JudgeVerdict(verdict="PASS", reasoning="Good"),
            JudgeVerdict(verdict="FAIL", reasoning="Bad"),
        ]

        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.side_effect = mock_verdicts

            judge = LLMJudge(system_prompt="You are a judge", model="gpt-4o")
            test_cases = [
                TestCase(
                    id="test-1",
                    input_text="Hello!",
                    expected_verdict="PASS",
                    reasoning="Friendly",
                ),
                TestCase(
                    id="test-2",
                    input_text="I hate you",
                    expected_verdict="FAIL",
                    reasoning="Hostile",
                ),
            ]

            results = await judge.evaluate_batch(test_cases)

            assert len(results) == 2
            assert results[0].actual_verdict == "PASS"
            assert results[1].actual_verdict == "FAIL"


