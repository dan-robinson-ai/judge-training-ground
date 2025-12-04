"""Shared test fixtures and configuration."""

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas import EvaluationResult, TestCase


@pytest.fixture
def sample_test_cases() -> list[TestCase]:
    """Sample test cases for testing."""
    return [
        TestCase(
            id="test-1",
            input_text="This is a friendly message",
            expected_verdict="PASS",
            reasoning="Positive and appropriate content",
            verified=True,
        ),
        TestCase(
            id="test-2",
            input_text="You are terrible and I hate you",
            expected_verdict="FAIL",
            reasoning="Contains hostile language",
            verified=True,
        ),
        TestCase(
            id="test-3",
            input_text="Could you help me with my homework?",
            expected_verdict="PASS",
            reasoning="Polite request for assistance",
            verified=False,
        ),
    ]


@pytest.fixture
def sample_evaluation_results() -> list[EvaluationResult]:
    """Sample evaluation results for testing."""
    return [
        EvaluationResult(
            test_case_id="test-1",
            actual_verdict="PASS",
            reasoning="Content is friendly and appropriate",
            correct=True,
        ),
        EvaluationResult(
            test_case_id="test-2",
            actual_verdict="FAIL",
            reasoning="Contains hostile language targeting the user",
            correct=True,
        ),
        EvaluationResult(
            test_case_id="test-3",
            actual_verdict="FAIL",
            reasoning="Incorrectly flagged as suspicious",
            correct=False,
        ),
    ]


@pytest.fixture
def mock_llm_response():
    """Factory fixture to create mock LLM responses."""

    def _create_mock(response_content: str):
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = response_content
        return mock_response

    return _create_mock


@pytest.fixture
def mock_call_llm():
    """Fixture to mock the call_llm utility function."""
    with patch("app.services.llm.call_llm") as mock:
        yield mock
