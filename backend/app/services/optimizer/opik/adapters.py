"""Opik optimizer adapter implementations."""

import asyncio

from opik_optimizer import (
    ChatPrompt,
    EvolutionaryOptimizer,
    FewShotBayesianOptimizer,
    GepaOptimizer,
    HierarchicalReflectiveOptimizer,
    MetaPromptOptimizer,
    ParameterOptimizer,
)

from app.schemas import TestCase
from app.services.optimizer.base import OptimizationConfig, OptimizerAdapter


def create_opik_metric():
    """Create metric function for Opik optimizers.

    The metric compares the LLM output verdict against expected verdict.
    """

    def metric_function(dataset_item: dict, llm_output: str) -> float:
        expected = dataset_item.get("expected_verdict", "").upper()

        # Parse LLM output to extract verdict
        output_upper = llm_output.upper()
        if "PASS" in output_upper:
            actual = "PASS"
        elif "FAIL" in output_upper:
            actual = "FAIL"
        else:
            actual = ""

        return 1.0 if expected == actual else 0.0

    return metric_function


def convert_test_cases_to_dataset(train_cases: list[TestCase]) -> list[dict]:
    """Convert TestCase objects to Opik dataset format."""
    return [
        {
            "input_text": tc.input_text,
            "expected_verdict": tc.expected_verdict,
            "reasoning": tc.reasoning,
        }
        for tc in train_cases
    ]


class BaseOpikAdapter(OptimizerAdapter):
    """Base class for Opik optimizer adapters."""

    framework = "opik"

    def __init__(self, config: OptimizationConfig):
        self.config = config

    def _create_chat_prompt(self, current_prompt: str) -> ChatPrompt:
        """Create ChatPrompt from current system prompt."""
        return ChatPrompt(
            messages=[
                {"role": "system", "content": current_prompt},
                {
                    "role": "user",
                    "content": (
                        "Evaluate the following input and determine if it "
                        "should PASS or FAIL based on the criteria above.\n\n"
                        "INPUT: {input_text}\n\n"
                        "Provide your verdict (PASS or FAIL) and reasoning."
                    ),
                },
            ]
        )

    def _extract_result(self, result, original_prompt: str) -> tuple[str, str]:
        """Extract optimized prompt from Opik result."""
        # Access the optimized prompt from result
        # The exact access pattern depends on OptimizationResult structure
        if hasattr(result, "prompt") and result.prompt:
            # Get the system message content from the optimized prompt
            messages = getattr(result.prompt, "messages", [])
            if messages and len(messages) > 0:
                system_msg = messages[0]
                if isinstance(system_msg, dict):
                    optimized_prompt = system_msg.get("content", original_prompt)
                else:
                    optimized_prompt = getattr(system_msg, "content", original_prompt)
                modification_notes = f"Optimized by Opik {self.name}"
            else:
                optimized_prompt = original_prompt
                modification_notes = f"Optimizer ({self.name}) ran but made no changes"
        else:
            optimized_prompt = original_prompt
            modification_notes = f"Optimizer ({self.name}) ran but made no changes"

        return optimized_prompt, modification_notes


class EvolutionaryOptimizerAdapter(BaseOpikAdapter):
    """Adapter for Opik EvolutionaryOptimizer."""

    name = "evolutionary"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        optimizer = EvolutionaryOptimizer(
            model=config.model,
            n_threads=config.n_threads,
            seed=config.seed,
            verbose=config.verbose,
        )

        prompt = self._create_chat_prompt(current_prompt)
        dataset = convert_test_cases_to_dataset(train_cases)
        metric = create_opik_metric()

        # Run in thread pool since Opik optimizers are synchronous
        result = await asyncio.to_thread(
            optimizer.optimize_prompt,
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            n_samples=len(train_cases),
        )

        return self._extract_result(result, current_prompt)


class FewShotBayesianAdapter(BaseOpikAdapter):
    """Adapter for Opik FewShotBayesianOptimizer."""

    name = "fewshot_bayesian"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        optimizer = FewShotBayesianOptimizer(
            model=config.model,
            min_examples=2,
            max_examples=8,
            n_threads=config.n_threads,
            seed=config.seed,
            verbose=config.verbose,
        )

        prompt = self._create_chat_prompt(current_prompt)
        dataset = convert_test_cases_to_dataset(train_cases)
        metric = create_opik_metric()

        # Run in thread pool since Opik optimizers are synchronous
        result = await asyncio.to_thread(
            optimizer.optimize_prompt,
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            n_samples=len(train_cases),
        )

        return self._extract_result(result, current_prompt)


class MetaPromptAdapter(BaseOpikAdapter):
    """Adapter for Opik MetaPromptOptimizer."""

    name = "metaprompt"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        optimizer = MetaPromptOptimizer(
            model=config.model,
            n_threads=config.n_threads,
            seed=config.seed,
            verbose=config.verbose,
        )

        prompt = self._create_chat_prompt(current_prompt)
        dataset = convert_test_cases_to_dataset(train_cases)
        metric = create_opik_metric()

        # Run in thread pool since Opik optimizers are synchronous
        result = await asyncio.to_thread(
            optimizer.optimize_prompt,
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            n_samples=len(train_cases),
        )

        return self._extract_result(result, current_prompt)


class HierarchicalReflectiveAdapter(BaseOpikAdapter):
    """Adapter for Opik HierarchicalReflectiveOptimizer."""

    name = "hierarchical_reflective"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        optimizer = HierarchicalReflectiveOptimizer(
            model=config.model,
            n_threads=config.n_threads,
            seed=config.seed,
            verbose=config.verbose,
        )

        prompt = self._create_chat_prompt(current_prompt)
        dataset = convert_test_cases_to_dataset(train_cases)
        metric = create_opik_metric()

        # Run in thread pool since Opik optimizers are synchronous
        result = await asyncio.to_thread(
            optimizer.optimize_prompt,
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            n_samples=len(train_cases),
        )

        return self._extract_result(result, current_prompt)


class GepaAdapter(BaseOpikAdapter):
    """Adapter for Opik GepaOptimizer."""

    name = "gepa"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        optimizer = GepaOptimizer(
            model=config.model,
            n_threads=config.n_threads,
            seed=config.seed,
            verbose=config.verbose,
        )

        prompt = self._create_chat_prompt(current_prompt)
        dataset = convert_test_cases_to_dataset(train_cases)
        metric = create_opik_metric()

        # Run in thread pool since Opik optimizers are synchronous
        result = await asyncio.to_thread(
            optimizer.optimize_prompt,
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            n_samples=len(train_cases),
        )

        return self._extract_result(result, current_prompt)


class ParameterAdapter(BaseOpikAdapter):
    """Adapter for Opik ParameterOptimizer."""

    name = "parameter"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        optimizer = ParameterOptimizer(
            model=config.model,
            n_threads=config.n_threads,
            seed=config.seed,
            verbose=config.verbose,
        )

        prompt = self._create_chat_prompt(current_prompt)
        dataset = convert_test_cases_to_dataset(train_cases)
        metric = create_opik_metric()

        # Run in thread pool since Opik optimizers are synchronous
        result = await asyncio.to_thread(
            optimizer.optimize_prompt,
            prompt=prompt,
            dataset=dataset,
            metric=metric,
            n_samples=len(train_cases),
        )

        return self._extract_result(result, current_prompt)
