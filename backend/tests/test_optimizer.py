"""Tests for the optimizer module with factory pattern."""

from unittest.mock import MagicMock, patch

import pytest

from app.schemas import EvaluationResult, OptimizeResponse, TestCase
from app.services.optimizer import optimize_prompt
from app.services.optimizer.dspy.adapters import (
    MODEL_PROVIDER_MAP,
    create_metric,
    get_dspy_model_name,
)
from app.services.optimizer.dspy.factory import DSPyOptimizerFactory
from app.services.optimizer.registry import split_test_cases


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


class TestDSPyOptimizerFactory:
    """Tests for the DSPy optimizer factory."""

    def test_get_optimizer_types(self):
        """Test getting available optimizer types."""
        factory = DSPyOptimizerFactory()
        types = factory.get_optimizer_types()

        assert "bootstrap_fewshot" in types
        assert "miprov2" in types
        assert "copro" in types

    def test_create_bootstrap_fewshot_adapter(self):
        """Test creating BootstrapFewShot adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.dspy.adapters import BootstrapFewShotAdapter

        factory = DSPyOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("bootstrap_fewshot", config)

        assert isinstance(adapter, BootstrapFewShotAdapter)
        assert adapter.name == "bootstrap_fewshot"
        assert adapter.framework == "dspy"

    def test_create_miprov2_adapter(self):
        """Test creating MIPROv2 adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.dspy.adapters import MIPROv2Adapter

        factory = DSPyOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("miprov2", config)

        assert isinstance(adapter, MIPROv2Adapter)
        assert adapter.name == "miprov2"

    def test_create_copro_adapter(self):
        """Test creating COPRO adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.dspy.adapters import COPROAdapter

        factory = DSPyOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("copro", config)

        assert isinstance(adapter, COPROAdapter)
        assert adapter.name == "copro"

    def test_create_unknown_optimizer_raises_error(self):
        """Test creating unknown optimizer raises error."""
        from app.services.optimizer.base import OptimizationConfig

        factory = DSPyOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        with pytest.raises(ValueError, match="Unknown DSPy optimizer"):
            factory.create_adapter("unknown_type", config)


class TestExtractOptimizedPrompt:
    """Tests for the extract_optimized_prompt function via adapter."""

    def test_extract_with_instructions(self):
        """Test extracting prompt when optimizer updated instructions."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.dspy.adapters import BootstrapFewShotAdapter

        adapter = BootstrapFewShotAdapter(OptimizationConfig(model="gpt-4o"))

        module = MagicMock()
        module.judge = MagicMock()
        module.judge.signature = MagicMock()
        module.judge.signature.instructions = "Updated instructions from optimizer"
        module.judge.demos = None

        prompt, notes = adapter._extract_optimized_prompt(module, "Original prompt")

        assert "Updated instructions" in prompt
        assert "Updated instructions from optimizer" in notes

    def test_extract_with_demos(self):
        """Test extracting prompt when optimizer added demos."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.dspy.adapters import BootstrapFewShotAdapter

        adapter = BootstrapFewShotAdapter(OptimizationConfig(model="gpt-4o"))

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

        prompt, notes = adapter._extract_optimized_prompt(module, "Original prompt")

        assert "Original prompt" in prompt
        assert "Examples:" in prompt
        assert "Example 1:" in prompt
        assert "Example input 1" in prompt
        assert "2 fewshot examples" in notes

    def test_extract_no_changes(self):
        """Test extracting prompt when optimizer made no changes."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.dspy.adapters import BootstrapFewShotAdapter

        adapter = BootstrapFewShotAdapter(OptimizationConfig(model="gpt-4o"))

        module = MagicMock()
        module.judge = MagicMock()
        module.judge.signature = MagicMock()
        module.judge.signature.instructions = None
        module.judge.demos = []

        prompt, notes = adapter._extract_optimized_prompt(module, "Original prompt")

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

        with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                framework="dspy",
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

        with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                framework="dspy",
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
            framework="dspy",
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

        with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                framework="dspy",
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
            with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                    framework="dspy",
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

        with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                framework="dspy",
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

        with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                framework="dspy",
            )
            assert isinstance(response1, OptimizeResponse)

            # Second call should also succeed (no async context error)
            response2 = await optimize_prompt(
                current_prompt="Original 2",
                test_cases=test_cases,
                results=results,
                framework="dspy",
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

        with patch("app.services.optimizer.dspy.adapters.dspy") as mock_dspy:
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
                framework="dspy",
                model="gpt-4o",
            )

            # Verify LM was called with correct format
            mock_dspy.LM.assert_called_with("openai/gpt-4o")


class TestOptimizerRegistry:
    """Tests for the optimizer registry."""

    def test_get_frameworks(self):
        """Test getting available frameworks."""
        from app.services.optimizer.registry import get_registry

        registry = get_registry()
        frameworks = registry.get_frameworks()

        assert "dspy" in frameworks
        assert "opik" in frameworks

    def test_validate_valid_dspy_optimizer(self):
        """Test validating a valid DSPy optimizer."""
        from app.services.optimizer.registry import get_registry

        registry = get_registry()
        # Should not raise
        registry.validate_optimizer("dspy", "bootstrap_fewshot")
        registry.validate_optimizer("dspy", "miprov2")
        registry.validate_optimizer("dspy", "copro")

    def test_validate_invalid_optimizer_for_framework(self):
        """Test validating an invalid optimizer for a framework."""
        from app.services.optimizer.registry import get_registry

        registry = get_registry()
        with pytest.raises(ValueError, match="not available"):
            registry.validate_optimizer("dspy", "evolutionary")

    def test_validate_invalid_framework(self):
        """Test validating an invalid framework."""
        from app.services.optimizer.registry import get_registry

        registry = get_registry()
        with pytest.raises(ValueError, match="Unknown framework"):
            registry.validate_optimizer("unknown", "bootstrap_fewshot")

    def test_validate_valid_opik_optimizers(self):
        """Test validating all valid Opik optimizers."""
        from app.services.optimizer.registry import get_registry

        registry = get_registry()
        # All Opik optimizer types should validate without error
        opik_optimizers = [
            "evolutionary",
            "fewshot_bayesian",
            "metaprompt",
            "hierarchical_reflective",
            "gepa",
            "parameter",
        ]
        for opt_type in opik_optimizers:
            registry.validate_optimizer("opik", opt_type)

    def test_validate_dspy_optimizer_not_valid_for_opik(self):
        """Test that DSPy optimizers are not valid for Opik framework."""
        from app.services.optimizer.registry import get_registry

        registry = get_registry()
        with pytest.raises(ValueError, match="not available"):
            registry.validate_optimizer("opik", "bootstrap_fewshot")


class TestOpikOptimizerFactory:
    """Tests for the Opik optimizer factory."""

    def test_get_optimizer_types(self):
        """Test getting available Opik optimizer types."""
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        types = factory.get_optimizer_types()

        assert "evolutionary" in types
        assert "fewshot_bayesian" in types
        assert "metaprompt" in types
        assert "hierarchical_reflective" in types
        assert "gepa" in types
        assert "parameter" in types
        assert len(types) == 6

    def test_create_evolutionary_adapter(self):
        """Test creating Evolutionary adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.adapters import EvolutionaryOptimizerAdapter
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("evolutionary", config)

        assert isinstance(adapter, EvolutionaryOptimizerAdapter)
        assert adapter.name == "evolutionary"
        assert adapter.framework == "opik"

    def test_create_fewshot_bayesian_adapter(self):
        """Test creating FewShotBayesian adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.adapters import FewShotBayesianAdapter
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("fewshot_bayesian", config)

        assert isinstance(adapter, FewShotBayesianAdapter)
        assert adapter.name == "fewshot_bayesian"

    def test_create_metaprompt_adapter(self):
        """Test creating MetaPrompt adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.adapters import MetaPromptAdapter
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("metaprompt", config)

        assert isinstance(adapter, MetaPromptAdapter)
        assert adapter.name == "metaprompt"

    def test_create_hierarchical_reflective_adapter(self):
        """Test creating HierarchicalReflective adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.adapters import HierarchicalReflectiveAdapter
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("hierarchical_reflective", config)

        assert isinstance(adapter, HierarchicalReflectiveAdapter)
        assert adapter.name == "hierarchical_reflective"

    def test_create_gepa_adapter(self):
        """Test creating GEPA adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.adapters import GepaAdapter
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("gepa", config)

        assert isinstance(adapter, GepaAdapter)
        assert adapter.name == "gepa"

    def test_create_parameter_adapter(self):
        """Test creating Parameter adapter."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.adapters import ParameterAdapter
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        adapter = factory.create_adapter("parameter", config)

        assert isinstance(adapter, ParameterAdapter)
        assert adapter.name == "parameter"

    def test_create_unknown_optimizer_raises_error(self):
        """Test creating unknown optimizer raises error."""
        from app.services.optimizer.base import OptimizationConfig
        from app.services.optimizer.opik.factory import OpikOptimizerFactory

        factory = OpikOptimizerFactory()
        config = OptimizationConfig(model="gpt-4o")

        with pytest.raises(ValueError, match="Unknown Opik optimizer"):
            factory.create_adapter("unknown_type", config)


class TestOpikMetricFunction:
    """Tests for the Opik metric function."""

    def test_metric_correct_pass_verdict(self):
        """Test metric returns 1.0 for correct PASS verdict."""
        from app.services.optimizer.opik.adapters import create_opik_metric

        metric = create_opik_metric()

        dataset_item = {"expected_verdict": "PASS"}
        llm_output = "The input should PASS because it meets the criteria."

        score = metric(dataset_item, llm_output)
        assert score == 1.0

    def test_metric_correct_fail_verdict(self):
        """Test metric returns 1.0 for correct FAIL verdict."""
        from app.services.optimizer.opik.adapters import create_opik_metric

        metric = create_opik_metric()

        dataset_item = {"expected_verdict": "FAIL"}
        llm_output = "This should FAIL as it doesn't meet requirements."

        score = metric(dataset_item, llm_output)
        assert score == 1.0

    def test_metric_incorrect_verdict(self):
        """Test metric returns 0.0 for incorrect verdict."""
        from app.services.optimizer.opik.adapters import create_opik_metric

        metric = create_opik_metric()

        dataset_item = {"expected_verdict": "PASS"}
        llm_output = "This should FAIL because of issues."

        score = metric(dataset_item, llm_output)
        assert score == 0.0

    def test_metric_case_insensitive(self):
        """Test metric handles case-insensitive verdict matching."""
        from app.services.optimizer.opik.adapters import create_opik_metric

        metric = create_opik_metric()

        dataset_item = {"expected_verdict": "pass"}
        llm_output = "PASS - this meets all criteria"

        score = metric(dataset_item, llm_output)
        assert score == 1.0

    def test_metric_no_verdict_in_output(self):
        """Test metric returns 0.0 when no verdict found in output."""
        from app.services.optimizer.opik.adapters import create_opik_metric

        metric = create_opik_metric()

        dataset_item = {"expected_verdict": "PASS"}
        llm_output = "I don't know what to decide here."

        score = metric(dataset_item, llm_output)
        assert score == 0.0


class TestOpikDatasetConversion:
    """Tests for converting test cases to Opik dataset format."""

    def test_convert_single_test_case(self):
        """Test converting a single test case."""
        from app.services.optimizer.opik.adapters import convert_test_cases_to_dataset

        test_cases = [
            TestCase(
                id="test-1",
                input_text="Hello world",
                expected_verdict="PASS",
                reasoning="Friendly greeting",
            )
        ]

        dataset = convert_test_cases_to_dataset(test_cases)

        assert len(dataset) == 1
        assert dataset[0]["input_text"] == "Hello world"
        assert dataset[0]["expected_verdict"] == "PASS"
        assert dataset[0]["reasoning"] == "Friendly greeting"

    def test_convert_multiple_test_cases(self):
        """Test converting multiple test cases."""
        from app.services.optimizer.opik.adapters import convert_test_cases_to_dataset

        test_cases = [
            TestCase(
                id=f"test-{i}",
                input_text=f"Input {i}",
                expected_verdict="PASS" if i % 2 == 0 else "FAIL",
                reasoning=f"Reasoning {i}",
            )
            for i in range(5)
        ]

        dataset = convert_test_cases_to_dataset(test_cases)

        assert len(dataset) == 5
        for i, item in enumerate(dataset):
            assert item["input_text"] == f"Input {i}"
            assert item["expected_verdict"] == ("PASS" if i % 2 == 0 else "FAIL")
            assert item["reasoning"] == f"Reasoning {i}"

    def test_convert_empty_list(self):
        """Test converting an empty list."""
        from app.services.optimizer.opik.adapters import convert_test_cases_to_dataset

        dataset = convert_test_cases_to_dataset([])
        assert dataset == []


class TestOpikOptimizePrompt:
    """Tests for optimize_prompt with Opik framework."""

    @pytest.mark.asyncio
    async def test_optimize_with_opik_framework(self):
        """Test that optimize_prompt works with Opik framework."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input 1",
                expected_verdict="PASS",
                reasoning="Reasoning 1",
                split="train",
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

        with patch("app.services.optimizer.opik.adapters.EvolutionaryOptimizer") as mock_optimizer:
            # Mock the optimizer instance
            mock_instance = MagicMock()
            mock_optimizer.return_value = mock_instance

            # Mock the optimization result
            mock_result = MagicMock()
            mock_result.prompt = MagicMock()
            mock_result.prompt.messages = [{"role": "system", "content": "Optimized system prompt"}]
            mock_instance.optimize_prompt.return_value = mock_result

            response = await optimize_prompt(
                current_prompt="Original prompt",
                test_cases=test_cases,
                results=results,
                framework="opik",
                optimizer_type="evolutionary",
                model="gpt-4o",
            )

            assert response.optimized_prompt == "Optimized system prompt"
            assert "evolutionary" in response.modification_notes.lower()

    @pytest.mark.asyncio
    async def test_optimize_opik_no_changes(self):
        """Test Opik optimize_prompt when optimizer makes no changes."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input 1",
                expected_verdict="PASS",
                reasoning="Reasoning 1",
                split="train",
            ),
        ]
        results = []

        with patch("app.services.optimizer.opik.adapters.MetaPromptOptimizer") as mock_optimizer:
            # Mock optimizer returning result with empty/no prompt
            mock_instance = MagicMock()
            mock_optimizer.return_value = mock_instance

            mock_result = MagicMock()
            mock_result.prompt = None  # No optimized prompt
            mock_instance.optimize_prompt.return_value = mock_result

            response = await optimize_prompt(
                current_prompt="Original prompt",
                test_cases=test_cases,
                results=results,
                framework="opik",
                optimizer_type="metaprompt",
                model="gpt-4o",
            )

            # Should return original prompt when no changes made
            assert response.optimized_prompt == "Original prompt"
            assert "no changes" in response.modification_notes.lower()

    @pytest.mark.asyncio
    async def test_optimize_opik_handles_error(self):
        """Test that Opik optimize_prompt handles errors gracefully."""
        test_cases = [
            TestCase(
                id="test-1",
                input_text="Input 1",
                expected_verdict="PASS",
                reasoning="Reasoning 1",
                split="train",
            ),
        ]
        results = []

        with patch("app.services.optimizer.opik.adapters.GepaOptimizer") as mock_optimizer:
            mock_instance = MagicMock()
            mock_optimizer.return_value = mock_instance
            mock_instance.optimize_prompt.side_effect = Exception("Opik optimization error")

            response = await optimize_prompt(
                current_prompt="Original prompt",
                test_cases=test_cases,
                results=results,
                framework="opik",
                optimizer_type="gepa",
                model="gpt-4o",
            )

            assert response.optimized_prompt == "Original prompt"
            assert "failed" in response.modification_notes.lower()
            assert "Opik optimization error" in response.modification_notes

    @pytest.mark.asyncio
    async def test_optimize_opik_different_optimizer_types(self):
        """Test optimize_prompt with different Opik optimizer types."""
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

        opik_optimizers = [
            ("evolutionary", "EvolutionaryOptimizer"),
            ("fewshot_bayesian", "FewShotBayesianOptimizer"),
            ("metaprompt", "MetaPromptOptimizer"),
            ("hierarchical_reflective", "HierarchicalReflectiveOptimizer"),
            ("gepa", "GepaOptimizer"),
            ("parameter", "ParameterOptimizer"),
        ]

        for optimizer_type, class_name in opik_optimizers:
            with patch(f"app.services.optimizer.opik.adapters.{class_name}") as mock_optimizer:
                mock_instance = MagicMock()
                mock_optimizer.return_value = mock_instance

                mock_result = MagicMock()
                mock_result.prompt = MagicMock()
                mock_result.prompt.messages = [{"role": "system", "content": f"Optimized by {optimizer_type}"}]
                mock_instance.optimize_prompt.return_value = mock_result

                response = await optimize_prompt(
                    current_prompt="Original",
                    test_cases=test_cases,
                    results=results,
                    framework="opik",
                    optimizer_type=optimizer_type,
                )

                assert isinstance(response, OptimizeResponse)
                assert response.optimized_prompt == f"Optimized by {optimizer_type}"
