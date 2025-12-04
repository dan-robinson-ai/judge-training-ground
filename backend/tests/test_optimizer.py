"""Tests for the DSPy-based optimizer module."""

import pytest
from unittest.mock import patch, MagicMock

from app.schemas import TestCase, EvaluationResult, OptimizeResponse
from app.services.optimizer import (
    split_test_cases,
    create_metric,
    create_optimizer,
    extract_optimized_prompt,
    optimize_prompt,
    get_dspy_model_name,
    MODEL_PROVIDER_MAP,
    JudgeModule,
    JudgeSignature,
)


class TestSplitTestCases:
    """Tests for the split_test_cases function."""

    def test_split_default_ratio(self):
        """Test splitting with default 70/30 ratio."""
        test_cases = [
            TestCase(
                id=f"test-{i}",
                input_text=f"Input {i}",
                expected_verdict="PASS" if i % 2 == 0 else "FAIL",
                reasoning=f"Reasoning {i}",
            )
            for i in range(10)
        ]

        train, test = split_test_cases(test_cases)

        assert len(train) == 7
        assert len(test) == 3
        assert all(tc.split == "train" for tc in train)
        assert all(tc.split == "test" for tc in test)

    def test_split_custom_ratio(self):
        """Test splitting with custom ratio."""
        test_cases = [
            TestCase(
                id=f"test-{i}",
                input_text=f"Input {i}",
                expected_verdict="PASS",
                reasoning=f"Reasoning {i}",
            )
            for i in range(10)
        ]

        train, test = split_test_cases(test_cases, train_ratio=0.8)

        assert len(train) == 8
        assert len(test) == 2

    def test_split_preserves_data(self):
        """Test that splitting preserves all original data."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Hello",
                expected_verdict="PASS",
                reasoning="Friendly",
                verified=True,
            ),
            TestCase(
                id="test-2",
                input_text="Bad",
                expected_verdict="FAIL",
                reasoning="Hostile",
                verified=False,
            ),
        ]

        train, test = split_test_cases(test_cases, train_ratio=0.5)

        all_cases = train + test
        assert len(all_cases) == 2

        # Check that original data is preserved (except split field)
        for tc in all_cases:
            assert tc.id in ["test-1", "test-2"]
            assert tc.split in ["train", "test"]

    def test_split_empty_list(self):
        """Test splitting an empty list."""
        train, test = split_test_cases([])

        assert train == []
        assert test == []

    def test_split_single_item(self):
        """Test splitting a single item."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Hello",
                expected_verdict="PASS",
                reasoning="Friendly",
            )
        ]

        train, test = split_test_cases(test_cases)

        # With one item, it should go to train (70% of 1 = 0.7, int = 0, but we have 1 item)
        assert len(train) + len(test) == 1


class TestCreateMetric:
    """Tests for the create_metric function."""

    def test_metric_correct_verdict(self):
        """Test metric returns 1.0 for correct verdict."""
        metric = create_metric(with_feedback=False)

        example = MagicMock()
        example.expected_verdict = "PASS"

        pred = MagicMock()
        pred.verdict = "PASS"

        score = metric(example, pred)
        assert score == 1.0

    def test_metric_incorrect_verdict(self):
        """Test metric returns 0.0 for incorrect verdict."""
        metric = create_metric(with_feedback=False)

        example = MagicMock()
        example.expected_verdict = "PASS"

        pred = MagicMock()
        pred.verdict = "FAIL"

        score = metric(example, pred)
        assert score == 0.0

    def test_metric_with_feedback_correct(self):
        """Test metric with feedback returns correct Prediction for correct verdict."""
        metric = create_metric(with_feedback=True)

        example = MagicMock()
        example.expected_verdict = "PASS"

        pred = MagicMock()
        pred.verdict = "PASS"

        result = metric(example, pred)
        assert result.score == 1.0
        assert "Correct" in result.feedback

    def test_metric_with_feedback_incorrect(self):
        """Test metric with feedback returns detailed feedback for incorrect verdict."""
        metric = create_metric(with_feedback=True)

        example = MagicMock()
        example.expected_verdict = "PASS"
        example.input_text = "Test input text"
        example.reasoning = "Test reasoning"

        pred = MagicMock()
        pred.verdict = "FAIL"

        result = metric(example, pred)
        assert result.score == 0.0
        assert "Expected PASS but got FAIL" in result.feedback


class TestCreateOptimizer:
    """Tests for the create_optimizer function."""

    def test_create_bootstrap_fewshot(self):
        """Test creating BootstrapFewShot optimizer."""
        metric = lambda e, p, t=None: 1.0

        with patch("dspy.BootstrapFewShot") as mock_optimizer:
            mock_optimizer.return_value = MagicMock()
            optimizer = create_optimizer("bootstrap_fewshot", metric)

            mock_optimizer.assert_called_once()
            call_kwargs = mock_optimizer.call_args[1]
            assert call_kwargs["metric"] == metric
            assert call_kwargs["max_bootstrapped_demos"] == 4

    def test_create_miprov2(self):
        """Test creating MIPROv2 optimizer."""
        metric = lambda e, p, t=None: 1.0

        with patch("dspy.MIPROv2") as mock_optimizer:
            mock_optimizer.return_value = MagicMock()
            optimizer = create_optimizer("miprov2", metric)

            mock_optimizer.assert_called_once()
            call_kwargs = mock_optimizer.call_args[1]
            assert call_kwargs["metric"] == metric
            assert call_kwargs["auto"] == "light"

    def test_create_copro(self):
        """Test creating COPRO optimizer."""
        metric = lambda e, p, t=None: 1.0

        with patch("dspy.COPRO") as mock_optimizer:
            mock_optimizer.return_value = MagicMock()
            optimizer = create_optimizer("copro", metric)

            mock_optimizer.assert_called_once()
            call_kwargs = mock_optimizer.call_args[1]
            assert call_kwargs["metric"] == metric

    def test_create_unknown_optimizer(self):
        """Test creating unknown optimizer raises error."""
        metric = lambda e, p, t=None: 1.0

        with pytest.raises(ValueError, match="Unknown optimizer type"):
            create_optimizer("unknown_type", metric)


class TestExtractOptimizedPrompt:
    """Tests for the extract_optimized_prompt function."""

    def test_extract_with_instructions(self):
        """Test extracting prompt when optimizer updated instructions."""
        module = MagicMock()
        module.judge = MagicMock()
        module.judge.signature = MagicMock()
        module.judge.signature.instructions = "Updated instructions from optimizer"
        module.judge.demos = None

        prompt, notes = extract_optimized_prompt(module, "Original prompt", "bootstrap_fewshot")

        assert "Updated instructions" in prompt
        assert "Updated instructions from optimizer" in notes

    def test_extract_with_demos(self):
        """Test extracting prompt when optimizer added demos."""
        demo1 = MagicMock()
        demo1.input_text = "Example input 1"
        demo1.verdict = "PASS"
        demo1.reasoning = "Example reasoning 1"

        demo2 = MagicMock()
        demo2.input_text = "Example input 2"
        demo2.verdict = "FAIL"
        demo2.reasoning = "Example reasoning 2"

        module = MagicMock()
        module.judge = MagicMock()
        module.judge.signature = MagicMock()
        module.judge.signature.instructions = None
        module.judge.demos = [demo1, demo2]

        prompt, notes = extract_optimized_prompt(module, "Original prompt", "bootstrap_fewshot")

        assert "Original prompt" in prompt
        assert "Examples:" in prompt
        assert "Example 1:" in prompt
        assert "Example input 1" in prompt
        assert "2 fewshot examples" in notes

    def test_extract_no_changes(self):
        """Test extracting prompt when optimizer made no changes."""
        module = MagicMock()
        module.judge = MagicMock()
        module.judge.signature = MagicMock()
        module.judge.signature.instructions = None
        module.judge.demos = []

        prompt, notes = extract_optimized_prompt(module, "Original prompt", "bootstrap_fewshot")

        assert prompt == "Original prompt"
        assert "no changes" in notes.lower()


class TestOptimizePrompt:
    """Tests for the main optimize_prompt function."""

    @pytest.mark.asyncio
    async def test_optimize_auto_splits_data(self):
        """Test that optimize_prompt auto-splits data if not already split."""
        test_cases = [
            TestCase(
                id=f"test-{i}",
                input_text=f"Input {i}",
                expected_verdict="PASS" if i % 2 == 0 else "FAIL",
                reasoning=f"Reasoning {i}",
            )
            for i in range(10)
        ]
        results = [
            EvaluationResult(
                test_case_id=f"test-{i}",
                actual_verdict="FAIL",
                reasoning="Wrong",
                correct=False,
            )
            for i in range(10)
        ]

        with patch("app.services.optimizer.dspy") as mock_dspy:
            # Mock DSPy components with context manager
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_dspy.context.return_value = mock_context

            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()
            mock_dspy.BootstrapFewShot.return_value.compile.return_value = MagicMock()

            # Mock the optimized module
            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Optimized prompt"
            optimized.judge.demos = []

            response = await optimize_prompt(
                current_prompt="Original prompt",
                test_cases=test_cases,
                results=results,
                optimizer_type="bootstrap_fewshot",
                model="gpt-4o",
            )

            # Verify response includes split data
            assert len(response.train_cases) == 7
            assert len(response.test_cases) == 3
            assert all(tc.split == "train" for tc in response.train_cases)
            assert all(tc.split == "test" for tc in response.test_cases)

    @pytest.mark.asyncio
    async def test_optimize_uses_existing_split(self):
        """Test that optimize_prompt uses existing split if already split."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input 1",
                expected_verdict="PASS",
                reasoning="Reasoning 1",
                split="train",
            ),
            TestCase(
                id="test-2",
                input_text="Input 2",
                expected_verdict="FAIL",
                reasoning="Reasoning 2",
                split="test",
            ),
        ]
        results = [
            EvaluationResult(
                test_case_id="test-1",
                actual_verdict="FAIL",
                reasoning="Wrong",
                correct=False,
            ),
        ]

        with patch("app.services.optimizer.dspy") as mock_dspy:
            # Mock context manager
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_dspy.context.return_value = mock_context

            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()
            mock_dspy.BootstrapFewShot.return_value.compile.return_value = MagicMock()

            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Optimized"
            optimized.judge.demos = []

            response = await optimize_prompt(
                current_prompt="Original",
                test_cases=test_cases,
                results=results,
            )

            # Should preserve existing split
            assert len(response.train_cases) == 1
            assert len(response.test_cases) == 1
            assert response.train_cases[0].id == "test-1"
            assert response.test_cases[0].id == "test-2"

    @pytest.mark.asyncio
    async def test_optimize_no_train_cases(self):
        """Test optimize_prompt handles case with no training data."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input",
                expected_verdict="PASS",
                reasoning="Reasoning",
                split="test",  # All test, no train
            ),
        ]
        results = []

        response = await optimize_prompt(
            current_prompt="Original",
            test_cases=test_cases,
            results=results,
        )

        assert response.optimized_prompt == "Original"
        assert "No training cases" in response.modification_notes

    @pytest.mark.asyncio
    async def test_optimize_handles_error(self):
        """Test optimize_prompt handles optimization errors gracefully."""
        # Use split="train" to ensure there's training data and optimization runs
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input",
                expected_verdict="PASS",
                reasoning="Reasoning",
                split="train",  # Explicitly mark as train to ensure optimization runs
            ),
        ]
        results = [
            EvaluationResult(
                test_case_id="test-1",
                actual_verdict="FAIL",
                reasoning="Wrong",
                correct=False,
            ),
        ]

        with patch("app.services.optimizer.dspy") as mock_dspy:
            # Mock context manager
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_dspy.context.return_value = mock_context

            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()
            mock_dspy.BootstrapFewShot.return_value.compile.side_effect = Exception(
                "DSPy error"
            )

            response = await optimize_prompt(
                current_prompt="Original",
                test_cases=test_cases,
                results=results,
            )

            assert response.optimized_prompt == "Original"
            assert "failed" in response.modification_notes.lower()
            assert "DSPy error" in response.modification_notes

    @pytest.mark.asyncio
    async def test_optimize_different_optimizer_types(self):
        """Test optimize_prompt with different optimizer types."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input",
                expected_verdict="PASS",
                reasoning="Reasoning",
            ),
        ]
        results = [
            EvaluationResult(
                test_case_id="test-1",
                actual_verdict="FAIL",
                reasoning="Wrong",
                correct=False,
            ),
        ]

        for optimizer_type in ["bootstrap_fewshot", "miprov2", "copro"]:
            with patch("app.services.optimizer.dspy") as mock_dspy:
                # Mock context manager
                mock_context = MagicMock()
                mock_context.__enter__ = MagicMock(return_value=None)
                mock_context.__exit__ = MagicMock(return_value=None)
                mock_dspy.context.return_value = mock_context

                mock_dspy.LM.return_value = MagicMock()
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

                response = await optimize_prompt(
                    current_prompt="Original",
                    test_cases=test_cases,
                    results=results,
                    optimizer_type=optimizer_type,
                )

                assert isinstance(response, OptimizeResponse)


class TestGetDspyModelName:
    """Tests for the model name conversion function."""

    def test_openai_models(self):
        """Test OpenAI models get correct prefix."""
        assert get_dspy_model_name("gpt-4o") == "openai/gpt-4o"
        assert get_dspy_model_name("gpt-4o-mini") == "openai/gpt-4o-mini"

    def test_anthropic_models(self):
        """Test Anthropic models get correct prefix."""
        assert get_dspy_model_name("claude-3-5-sonnet-20241022") == "anthropic/claude-3-5-sonnet-20241022"
        assert get_dspy_model_name("claude-3-5-haiku-20241022") == "anthropic/claude-3-5-haiku-20241022"

    def test_already_prefixed(self):
        """Test models with existing prefix are unchanged."""
        assert get_dspy_model_name("openai/gpt-4o") == "openai/gpt-4o"
        assert get_dspy_model_name("anthropic/claude-3") == "anthropic/claude-3"
        assert get_dspy_model_name("custom/my-model") == "custom/my-model"

    def test_unknown_model_defaults_to_openai(self):
        """Test unknown models default to openai provider."""
        assert get_dspy_model_name("some-new-model") == "openai/some-new-model"
        assert get_dspy_model_name("unknown-provider-model") == "openai/unknown-provider-model"

    def test_model_provider_map_contents(self):
        """Test that MODEL_PROVIDER_MAP contains expected models."""
        assert "gpt-4o" in MODEL_PROVIDER_MAP
        assert "gpt-4o-mini" in MODEL_PROVIDER_MAP
        assert "claude-3-5-sonnet-20241022" in MODEL_PROVIDER_MAP
        assert "claude-3-5-haiku-20241022" in MODEL_PROVIDER_MAP
        assert MODEL_PROVIDER_MAP["gpt-4o"] == "openai"
        assert MODEL_PROVIDER_MAP["claude-3-5-sonnet-20241022"] == "anthropic"


class TestOptimizePromptAsyncContext:
    """Tests for async context handling in optimize_prompt."""

    @pytest.mark.asyncio
    async def test_uses_context_not_configure(self):
        """Test that optimize_prompt uses dspy.context() instead of dspy.configure()."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input",
                expected_verdict="PASS",
                reasoning="Reasoning",
                split="train",
            ),
        ]
        results = []

        with patch("app.services.optimizer.dspy") as mock_dspy:
            # Setup context manager mock
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_dspy.context.return_value = mock_context

            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()

            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Optimized"
            optimized.judge.demos = []

            await optimize_prompt(
                current_prompt="Original",
                test_cases=test_cases,
                results=results,
            )

            # Verify context() was called, not configure()
            mock_dspy.context.assert_called_once()
            # configure should never be called
            assert not hasattr(mock_dspy, 'configure') or not mock_dspy.configure.called

    @pytest.mark.asyncio
    async def test_multiple_sequential_calls_no_error(self):
        """Test that calling optimize_prompt multiple times works without errors."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input",
                expected_verdict="PASS",
                reasoning="Reasoning",
                split="train",
            ),
        ]
        results = []

        with patch("app.services.optimizer.dspy") as mock_dspy:
            # Setup context manager mock
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_dspy.context.return_value = mock_context

            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()

            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Optimized"
            optimized.judge.demos = []

            # First call
            response1 = await optimize_prompt(
                current_prompt="Original",
                test_cases=test_cases,
                results=results,
            )
            assert isinstance(response1, OptimizeResponse)

            # Second call should also succeed (no async context error)
            response2 = await optimize_prompt(
                current_prompt="Original 2",
                test_cases=test_cases,
                results=results,
            )
            assert isinstance(response2, OptimizeResponse)

            # context() should have been called twice
            assert mock_dspy.context.call_count == 2

    @pytest.mark.asyncio
    async def test_correct_model_format_passed_to_dspy_lm(self):
        """Test that the correct model format is passed to dspy.LM."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input",
                expected_verdict="PASS",
                reasoning="Reasoning",
                split="train",
            ),
        ]
        results = []

        with patch("app.services.optimizer.dspy") as mock_dspy:
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            mock_dspy.context.return_value = mock_context

            mock_dspy.LM.return_value = MagicMock()
            mock_dspy.Example = MagicMock(return_value=MagicMock())
            mock_dspy.BootstrapFewShot.return_value = MagicMock()

            optimized = mock_dspy.BootstrapFewShot.return_value.compile.return_value
            optimized.judge = MagicMock()
            optimized.judge.signature = MagicMock()
            optimized.judge.signature.instructions = "Optimized"
            optimized.judge.demos = []

            # Test with gpt-4o (should become openai/gpt-4o)
            await optimize_prompt(
                current_prompt="Original",
                test_cases=test_cases,
                results=results,
                model="gpt-4o",
            )

            # Verify LM was called with correct format
            mock_dspy.LM.assert_called_with("openai/gpt-4o")
