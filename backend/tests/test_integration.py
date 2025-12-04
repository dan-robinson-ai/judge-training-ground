"""Integration tests that hit the actual running API.

These tests require:
1. The backend server to be running on localhost:8000
2. Valid API keys for LLM providers (OPENAI_API_KEY, etc.)

Run with: pytest tests/test_integration.py -v -m integration
Skip with: pytest -m "not integration"

To run these tests:
1. Start the backend: cd backend && uv run uvicorn app.main:app --reload
2. Run tests: cd backend && uv run pytest tests/test_integration.py -v -m integration
"""

import os

import pytest
import requests

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Base URL for the API
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")


def is_server_running() -> bool:
    """Check if the server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="module", autouse=True)
def check_server():
    """Skip all tests if server is not running."""
    if not is_server_running():
        pytest.skip("Backend server is not running. Start it with: uv run uvicorn app.main:app")


class TestHealthEndpointIntegration:
    """Integration tests for health endpoint."""

    def test_health_check(self):
        """Test health check returns healthy status."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestGenerateEndpointIntegration:
    """Integration tests for the generate endpoint.

    Note: These tests make actual LLM calls and require API keys.
    """

    @pytest.mark.slow
    def test_generate_test_cases_real_llm(self):
        """Test generating test cases with actual LLM call."""
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "intent": "Detect spam messages",
                "count": 3,  # Small count for faster test
                "model": "gpt-4o-mini",  # Cheaper model for tests
            },
            timeout=120,  # LLM calls can take time
        )

        assert response.status_code == 200
        data = response.json()

        assert "test_cases" in data
        assert "system_prompt" in data
        assert len(data["test_cases"]) == 3

        # Verify test case structure
        for tc in data["test_cases"]:
            assert "id" in tc
            assert "input_text" in tc
            assert tc["expected_verdict"] in ["PASS", "FAIL"]
            assert "reasoning" in tc

        # Verify system prompt is non-empty
        assert len(data["system_prompt"]) > 0


class TestRunEndpointIntegration:
    """Integration tests for the run endpoint."""

    @pytest.mark.slow
    def test_run_evaluation_real_llm(self):
        """Test running evaluation with actual LLM call."""
        response = requests.post(
            f"{BASE_URL}/api/run",
            json={
                "system_prompt": "You are a content moderation judge. Evaluate if the message is spam. Reply with PASS if not spam, FAIL if spam.",
                "test_cases": [
                    {
                        "id": "test-1",
                        "input_text": "Hello, how are you today?",
                        "expected_verdict": "PASS",
                        "reasoning": "Normal greeting",
                        "verified": True,
                    },
                    {
                        "id": "test-2",
                        "input_text": "BUY NOW!!! CHEAP VIAGRA!!! CLICK HERE!!!",
                        "expected_verdict": "FAIL",
                        "reasoning": "Obvious spam with all caps and suspicious content",
                        "verified": True,
                    },
                ],
                "model_name": "gpt-4o-mini",
            },
            timeout=120,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert "passed" in data
        assert "failed" in data
        assert "accuracy" in data
        assert "cohen_kappa" in data
        assert len(data["results"]) == 2


class TestOptimizeEndpointIntegration:
    """Integration tests for the optimize endpoint."""

    def test_optimize_no_failures(self):
        """Test optimization when all tests pass (no LLM call needed)."""
        response = requests.post(
            f"{BASE_URL}/api/optimize",
            json={
                "current_prompt": "Original prompt",
                "test_cases": [
                    {
                        "id": "test-1",
                        "input_text": "Hello",
                        "expected_verdict": "PASS",
                        "reasoning": "Friendly",
                        "verified": True,
                        "split": "train",
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
                "optimizer_type": "bootstrap_fewshot",
            },
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()

        # When all pass, should return original prompt
        assert "optimized_prompt" in data
        assert "modification_notes" in data
        assert "train_cases" in data
        assert "test_cases" in data

    def test_optimize_auto_splits_data(self):
        """Test that optimization auto-splits unsplit data."""
        response = requests.post(
            f"{BASE_URL}/api/optimize",
            json={
                "current_prompt": "Original prompt",
                "test_cases": [
                    {
                        "id": f"test-{i}",
                        "input_text": f"Input {i}",
                        "expected_verdict": "PASS" if i % 2 == 0 else "FAIL",
                        "reasoning": f"Reasoning {i}",
                        "verified": True,
                        # No split field - should be auto-split
                    }
                    for i in range(10)
                ],
                "results": [
                    {
                        "test_case_id": f"test-{i}",
                        "actual_verdict": "PASS",
                        "reasoning": "Correct",
                        "correct": i % 2 == 0,
                    }
                    for i in range(10)
                ],
                "optimizer_type": "bootstrap_fewshot",
            },
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have auto-split: 70% train, 30% test
        assert len(data["train_cases"]) == 7
        assert len(data["test_cases"]) == 3
        assert all(tc["split"] == "train" for tc in data["train_cases"])
        assert all(tc["split"] == "test" for tc in data["test_cases"])

    def test_optimize_preserves_existing_split(self):
        """Test that optimization preserves existing splits."""
        response = requests.post(
            f"{BASE_URL}/api/optimize",
            json={
                "current_prompt": "Original prompt",
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
                        "actual_verdict": "PASS",
                        "reasoning": "Correct",
                        "correct": True,
                    },
                ],
                "optimizer_type": "bootstrap_fewshot",
            },
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["train_cases"]) == 1
        assert len(data["test_cases"]) == 1
        assert data["train_cases"][0]["id"] == "train-1"
        assert data["test_cases"][0]["id"] == "test-1"

    @pytest.mark.slow
    def test_optimize_with_failures_real_llm(self):
        """Test optimization with actual failures using real LLM.

        This test makes actual DSPy optimizer calls which can be slow.
        """
        response = requests.post(
            f"{BASE_URL}/api/optimize",
            json={
                "current_prompt": "You are a judge. Reply PASS or FAIL.",
                "test_cases": [
                    {
                        "id": "test-1",
                        "input_text": "Hello friend!",
                        "expected_verdict": "PASS",
                        "reasoning": "Friendly greeting",
                        "verified": True,
                    },
                    {
                        "id": "test-2",
                        "input_text": "I hate you",
                        "expected_verdict": "FAIL",
                        "reasoning": "Hostile message",
                        "verified": True,
                    },
                ],
                "results": [
                    {
                        "test_case_id": "test-1",
                        "actual_verdict": "FAIL",  # Wrong!
                        "reasoning": "Incorrectly flagged",
                        "correct": False,
                    },
                    {
                        "test_case_id": "test-2",
                        "actual_verdict": "FAIL",
                        "reasoning": "Correctly flagged",
                        "correct": True,
                    },
                ],
                "optimizer_type": "bootstrap_fewshot",
                "model": "gpt-4o-mini",
            },
            timeout=300,  # DSPy optimization can take a while
        )

        assert response.status_code == 200
        data = response.json()

        assert "optimized_prompt" in data
        assert "modification_notes" in data
        assert "train_cases" in data
        assert "test_cases" in data


class TestFullWorkflowIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.slow
    def test_full_generate_run_workflow(self):
        """Test the complete workflow: generate -> run."""
        # Step 1: Generate test cases
        gen_response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "intent": "Detect rude or offensive messages",
                "count": 5,
                "model": "gpt-4o-mini",
            },
            timeout=120,
        )

        assert gen_response.status_code == 200
        gen_data = gen_response.json()

        test_cases = gen_data["test_cases"]
        system_prompt = gen_data["system_prompt"]

        assert len(test_cases) == 5
        assert len(system_prompt) > 0

        # Step 2: Run evaluation
        run_response = requests.post(
            f"{BASE_URL}/api/run",
            json={
                "system_prompt": system_prompt,
                "test_cases": test_cases,
                "model_name": "gpt-4o-mini",
            },
            timeout=120,
        )

        assert run_response.status_code == 200
        run_data = run_response.json()

        assert run_data["total"] == 5
        assert "accuracy" in run_data
        assert len(run_data["results"]) == 5

        # Verify results structure
        for result in run_data["results"]:
            assert result["actual_verdict"] in ["PASS", "FAIL", "ERROR"]
            assert "reasoning" in result


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_generate_missing_intent(self):
        """Test generate endpoint with missing intent."""
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={"count": 10},
        )
        assert response.status_code == 422

    def test_generate_invalid_count(self):
        """Test generate endpoint with invalid count."""
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={"intent": "Test", "count": 0},
        )
        assert response.status_code == 422

    def test_run_empty_test_cases(self):
        """Test run endpoint with empty test cases."""
        response = requests.post(
            f"{BASE_URL}/api/run",
            json={
                "system_prompt": "You are a judge",
                "test_cases": [],
            },
        )
        # Should succeed but with 0 results
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_optimize_invalid_optimizer_type(self):
        """Test optimize endpoint with invalid optimizer type."""
        response = requests.post(
            f"{BASE_URL}/api/optimize",
            json={
                "current_prompt": "Test",
                "test_cases": [
                    {
                        "id": "test-1",
                        "input_text": "Hello",
                        "expected_verdict": "PASS",
                        "reasoning": "Friendly",
                        "verified": True,
                    }
                ],
                "results": [],
                "optimizer_type": "invalid_type",
            },
        )
        assert response.status_code == 422
