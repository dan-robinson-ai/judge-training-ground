"""Tests for API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas import (
    GeneratedSystemPrompt,
    GeneratedTestCase,
    GeneratedTestCaseList,
    JudgeVerdict,
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
        """Test successful prompt optimization with DSPy."""
        with patch("app.services.optimizer.dspy") as mock_dspy:
            # Mock DSPy components
            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.configure = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()

            # Mock the optimized module
            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Improved prompt"
            optimized.judge.demos = []

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
                        },
                        {
                            "id": "test-2",
                            "input_text": "Bad",
                            "expected_verdict": "FAIL",
                            "reasoning": "Hostile",
                            "verified": True,
                        },
                    ],
                    "results": [
                        {
                            "test_case_id": "test-1",
                            "actual_verdict": "FAIL",
                            "reasoning": "Incorrectly flagged",
                            "correct": False,
                        },
                        {
                            "test_case_id": "test-2",
                            "actual_verdict": "FAIL",
                            "reasoning": "Correct",
                            "correct": True,
                        },
                    ],
                    "optimizer_type": "bootstrap_fewshot",
                    "model": "gpt-4o",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "optimized_prompt" in data
            assert "modification_notes" in data
            assert "train_cases" in data
            assert "test_cases" in data
            # Auto-split should have occurred
            assert len(data["train_cases"]) + len(data["test_cases"]) == 2

    @pytest.mark.asyncio
    async def test_optimize_with_different_optimizer_types(self, async_client):
        """Test optimization with different optimizer types."""
        for optimizer_type in ["bootstrap_fewshot", "miprov2", "copro"]:
            with patch("app.services.optimizer.dspy") as mock_dspy:
                mock_dspy.LM.return_value = MagicMock()
                mock_dspy.configure = MagicMock()
                mock_dspy.Example = MagicMock(return_value=MagicMock())

                # Mock all optimizer types
                for opt_name in ["BootstrapFewShot", "MIPROv2", "COPRO"]:
                    mock_opt = MagicMock()
                    mock_opt.compile.return_value = MagicMock()
                    mock_opt.compile.return_value.judge = MagicMock()
                    mock_opt.compile.return_value.judge.signature = MagicMock()
                    mock_opt.compile.return_value.judge.signature.instructions = "Optimized"
                    mock_opt.compile.return_value.judge.demos = []
                    setattr(mock_dspy, opt_name, MagicMock(return_value=mock_opt))

                response = await async_client.post(
                    "/api/optimize",
                    json={
                        "current_prompt": "Original",
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
                                "reasoning": "Wrong",
                                "correct": False,
                            }
                        ],
                        "optimizer_type": optimizer_type,
                    },
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_optimize_preserves_existing_split(self, async_client):
        """Test that optimization preserves existing train/test split."""
        with patch("app.services.optimizer.dspy") as mock_dspy:
            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.configure = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()

            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Optimized"
            optimized.judge.demos = []

            response = await async_client.post(
                "/api/optimize",
                json={
                    "current_prompt": "Original",
                    "test_cases": [
                        {
                            "id": "train-1",
                            "input_text": "Train input",
                            "expected_verdict": "PASS",
                            "reasoning": "Train reasoning",
                            "verified": True,
                            "split": "train",
                        },
                        {
                            "id": "test-1",
                            "input_text": "Test input",
                            "expected_verdict": "FAIL",
                            "reasoning": "Test reasoning",
                            "verified": True,
                            "split": "test",
                        },
                    ],
                    "results": [
                        {
                            "test_case_id": "train-1",
                            "actual_verdict": "FAIL",
                            "reasoning": "Wrong",
                            "correct": False,
                        },
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["train_cases"]) == 1
            assert len(data["test_cases"]) == 1
            assert data["train_cases"][0]["id"] == "train-1"
            assert data["test_cases"][0]["id"] == "test-1"

    @pytest.mark.asyncio
    async def test_optimize_no_train_cases_returns_original(self, async_client):
        """Test optimization returns original prompt when no training data."""
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
                        "split": "test",  # All test, no train
                    }
                ],
                "results": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["optimized_prompt"] == "Original prompt"
        assert "No training cases" in data["modification_notes"]
