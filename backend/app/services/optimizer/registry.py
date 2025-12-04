"""Optimizer registry and main entry point."""

import random

from app.schemas import (
    EvaluationResult,
    OptimizeResponse,
    OptimizerFramework,
    OptimizerType,
    TestCase,
)
from app.services.optimizer.base import OptimizationConfig
from app.services.optimizer.dspy.factory import DSPyOptimizerFactory
from app.services.optimizer.opik.factory import OpikOptimizerFactory


def split_test_cases(
    test_cases: list[TestCase],
    train_ratio: float = 0.7,
) -> tuple[list[TestCase], list[TestCase]]:
    """Split test cases into train and test sets.

    Args:
        test_cases: List of test cases to split
        train_ratio: Ratio of cases for training (default 0.7 = 70%)

    Returns:
        Tuple of (train_cases, test_cases)
    """
    shuffled = test_cases.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * train_ratio)

    train_cases = [tc.model_copy(update={"split": "train"}) for tc in shuffled[:split_idx]]
    test_split = [tc.model_copy(update={"split": "test"}) for tc in shuffled[split_idx:]]

    return train_cases, test_split


class OptimizerRegistry:
    """Central registry for all optimizer frameworks and types."""

    def __init__(self):
        self._factories = {
            "dspy": DSPyOptimizerFactory(),
            "opik": OpikOptimizerFactory(),
        }

    def get_frameworks(self) -> list[str]:
        """Return list of available frameworks."""
        return list(self._factories.keys())

    def get_optimizer_types(self, framework: str) -> list[str]:
        """Return optimizer types available for a framework."""
        if framework not in self._factories:
            raise ValueError(f"Unknown framework: {framework}")
        return self._factories[framework].get_optimizer_types()

    def validate_optimizer(
        self,
        framework: OptimizerFramework,
        optimizer_type: OptimizerType,
    ) -> None:
        """Validate that framework supports the optimizer type."""
        if framework not in self._factories:
            raise ValueError(f"Unknown framework: {framework}")

        available = self._factories[framework].get_optimizer_types()
        if optimizer_type not in available:
            raise ValueError(
                f"Optimizer '{optimizer_type}' not available in {framework}. "
                f"Available: {available}"
            )

    async def optimize(
        self,
        current_prompt: str,
        test_cases: list[TestCase],
        results: list[EvaluationResult],  # noqa: ARG002 - kept for API compatibility
        framework: OptimizerFramework,
        optimizer_type: OptimizerType,
        model: str,
    ) -> OptimizeResponse:
        """Run optimization using specified framework and optimizer."""
        # Validate combination
        self.validate_optimizer(framework, optimizer_type)

        # Auto-split if needed
        has_split = any(tc.split is not None for tc in test_cases)
        if not has_split:
            train_cases, test_split = split_test_cases(test_cases)
        else:
            train_cases = [tc for tc in test_cases if tc.split == "train"]
            test_split = [tc for tc in test_cases if tc.split == "test"]

        # Early return if no training data
        if not train_cases:
            return OptimizeResponse(
                optimized_prompt=current_prompt,
                modification_notes="No training cases available for optimization",
                train_cases=train_cases,
                test_cases=test_split,
            )

        # Create configuration
        config = OptimizationConfig(
            model=model,
            n_threads=8,
            seed=42,
            verbose=0,
        )

        # Get factory and create adapter
        factory = self._factories[framework]
        adapter = factory.create_adapter(optimizer_type, config)

        try:
            # Run optimization
            optimized_prompt, modification_notes = await adapter.optimize(
                current_prompt=current_prompt,
                train_cases=train_cases,
                config=config,
            )
        except Exception as e:
            optimized_prompt = current_prompt
            modification_notes = f"Optimization failed: {str(e)}"

        return OptimizeResponse(
            optimized_prompt=optimized_prompt,
            modification_notes=modification_notes,
            train_cases=train_cases,
            test_cases=test_split,
        )


# Global singleton instance
_registry = None


def get_registry() -> OptimizerRegistry:
    """Get the global optimizer registry singleton."""
    global _registry
    if _registry is None:
        _registry = OptimizerRegistry()
    return _registry


# Convenience function matching old API signature with backward compatibility
async def optimize_prompt(
    current_prompt: str,
    test_cases: list[TestCase],
    results: list[EvaluationResult],
    optimizer_type: OptimizerType = "bootstrap_fewshot",
    model: str = "gpt-4o",
    framework: OptimizerFramework = "dspy",
) -> OptimizeResponse:
    """Optimize prompt using specified framework and optimizer.

    This is the main entry point for optimization, maintaining
    backward compatibility with the original function signature
    while adding framework support.

    Args:
        current_prompt: The current system prompt to optimize
        test_cases: List of test cases (will be auto-split if needed)
        results: Evaluation results from running the judge
        optimizer_type: Type of optimizer to use
        model: LiteLLM model name
        framework: Optimizer framework ('dspy' or 'opik')

    Returns:
        OptimizeResponse with optimized prompt and split test cases
    """
    registry = get_registry()
    return await registry.optimize(
        current_prompt=current_prompt,
        test_cases=test_cases,
        results=results,
        framework=framework,
        optimizer_type=optimizer_type,
        model=model,
    )
