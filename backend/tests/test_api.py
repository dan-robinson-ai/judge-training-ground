"""Tests for API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas import (
    TestCase,
    EvaluationResult,
    GeneratedTestCaseList,
    GeneratedTestCase,
    GeneratedSystemPrompt,
    JudgeVerdict,
    OptimizedPromptResponse,
)


@pytest.fixture
def client():
    """Sync test client for simple tests."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for async tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestGenerateEndpoint:
    @pytest.mark.asyncio
    async def test_generate_success(self, async_client):
        """Test successful test case generation."""
        mock_test_cases = GeneratedTestCaseList(
            test_cases=[
                GeneratedTestCase(
                    input_text="Hello friend",
                    expected_verdict="PASS",
                    difficulty="clear_pass",
                    reasoning="Friendly greeting",
                ),
            ]
        )
        mock_system_prompt = GeneratedSystemPrompt(
            system_prompt="You are a content moderation judge..."
        )

        with patch("app.services.generator.call_llm") as mock_llm:
            mock_llm.side_effect = [mock_test_cases, mock_system_prompt]

            response = await async_client.post(
                "/api/generate",
                json={"intent": "Detect toxic messages", "count": 1},
            )

            assert response.status_code == 200
            data = response.json()
            assert "test_cases" in data
            assert "system_prompt" in data
            assert len(data["test_cases"]) == 1
            assert data["test_cases"][0]["input_text"] == "Hello friend"
            assert data["system_prompt"] == "You are a content moderation judge..."

    @pytest.mark.asyncio
    async def test_generate_with_model(self, async_client):
        """Test generation with specific model."""
        mock_test_cases = GeneratedTestCaseList(
            test_cases=[
                GeneratedTestCase(
                    input_text="Test",
                    expected_verdict="PASS",
                    difficulty="clear_pass",
                    reasoning="Test",
                ),
            ]
        )
        mock_system_prompt = GeneratedSystemPrompt(system_prompt="Prompt")

        with patch("app.services.generator.call_llm") as mock_llm:
            mock_llm.side_effect = [mock_test_cases, mock_system_prompt]

            response = await async_client.post(
                "/api/generate",
                json={
                    "intent": "Test",
                    "count": 1,
                    "model": "claude-3-5-sonnet-20241022",
                },
            )

            assert response.status_code == 200
            # Verify the model was passed to call_llm
            assert mock_llm.call_args_list[0][1]["model"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_generate_validation_error(self, async_client):
        """Test validation error for invalid count."""
        response = await async_client.post(
            "/api/generate",
            json={"intent": "Test", "count": 0},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_missing_intent(self, async_client):
        """Test validation error for missing intent."""
        response = await async_client.post(
            "/api/generate",
            json={"count": 10},
        )
        assert response.status_code == 422


class TestRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_success(self, async_client):
        """Test successful evaluation run."""
        mock_verdict = JudgeVerdict(verdict="PASS", reasoning="Appropriate content")

        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.return_value = mock_verdict

            response = await async_client.post(
                "/api/run",
                json={
                    "system_prompt": "You are a judge",
                    "test_cases": [
                        {
                            "id": "test-1",
                            "input_text": "Hello",
                            "expected_verdict": "PASS",
                            "reasoning": "Friendly",
                            "verified": True,
                        }
                    ],
                    "model_name": "gpt-4o",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["passed"] == 1
            assert data["accuracy"] == 100.0
            assert len(data["results"]) == 1

    @pytest.mark.asyncio
    async def test_run_with_errors(self, async_client):
        """Test run with evaluation errors."""
        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.side_effect = Exception("API error")

            response = await async_client.post(
                "/api/run",
                json={
                    "system_prompt": "You are a judge",
                    "test_cases": [
                        {
                            "id": "test-1",
                            "input_text": "Hello",
                            "expected_verdict": "PASS",
                            "reasoning": "Friendly",
                            "verified": True,
                        }
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["errors"] == 1
            assert data["results"][0]["actual_verdict"] == "ERROR"

    @pytest.mark.asyncio
    async def test_run_multiple_test_cases(self, async_client):
        """Test run with multiple test cases."""
        mock_verdicts = [
            JudgeVerdict(verdict="PASS", reasoning="Good"),
            JudgeVerdict(verdict="FAIL", reasoning="Bad"),
        ]

        with patch("app.services.judge.call_llm") as mock_llm:
            mock_llm.side_effect = mock_verdicts

            response = await async_client.post(
                "/api/run",
                json={
                    "system_prompt": "You are a judge",
                    "test_cases": [
                        {
                            "id": "test-1",
                            "input_text": "Hello",
                            "expected_verdict": "PASS",
                            "reasoning": "Friendly",
                            "verified": True,
                        },
                        {
                            "id": "test-2",
                            "input_text": "Bad message",
                            "expected_verdict": "FAIL",
                            "reasoning": "Hostile",
                            "verified": True,
                        },
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["passed"] == 2  # Both verdicts match expected
            assert data["accuracy"] == 100.0


class TestOptimizeEndpoint:
    @pytest.mark.asyncio
    async def test_optimize_success(self, async_client):
        """Test successful prompt optimization."""
        mock_response = OptimizedPromptResponse(
            optimized_prompt="Improved prompt",
            modification_notes="Better edge case handling",
        )

        with patch("app.services.optimizer.call_llm") as mock_llm:
            mock_llm.return_value = mock_response

            response = await async_client.post(
                "/api/optimize",
                json={
                    "current_prompt": "Original prompt",
                    "test_cases": [
                        {
                            "id": "test-1",
                            "input_text": "Hello",
                            "expected_verdict": "PASS",
                            "reasoning": "Friendly",
                            "verified": True,
                        }
                    ],
                    "results": [
                        {
                            "test_case_id": "test-1",
                            "actual_verdict": "FAIL",
                            "reasoning": "Incorrectly flagged",
                            "correct": False,
                        }
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["optimized_prompt"] == "Improved prompt"
            assert data["modification_notes"] == "Better edge case handling"

    @pytest.mark.asyncio
    async def test_optimize_no_failures(self, async_client):
        """Test optimization when all tests pass."""
        response = await async_client.post(
            "/api/optimize",
            json={
                "current_prompt": "Original prompt",
                "test_cases": [
                    {
                        "id": "test-1",
                        "input_text": "Hello",
                        "expected_verdict": "PASS",
                        "reasoning": "Friendly",
                        "verified": True,
                    }
                ],
                "results": [
                    {
                        "test_case_id": "test-1",
                        "actual_verdict": "PASS",
                        "reasoning": "Correct",
                        "correct": True,
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["optimized_prompt"] == "Original prompt"
        assert "No optimization needed" in data["modification_notes"]
