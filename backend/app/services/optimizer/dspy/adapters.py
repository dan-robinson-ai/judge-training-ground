"""DSPy optimizer adapter implementations."""

from typing import Literal

import dspy

from app.schemas import TestCase
from app.services.optimizer.base import OptimizationConfig, OptimizerAdapter

# Model provider mapping (mirrors frontend/src/lib/types.ts AVAILABLE_MODELS)
MODEL_PROVIDER_MAP = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "claude-3-5-sonnet-20241022": "anthropic",
    "claude-3-5-haiku-20241022": "anthropic",
}


def get_dspy_model_name(model: str) -> str:
    """Convert model name to DSPy-compatible format (provider/model).

    Args:
        model: Model name (e.g., "gpt-4o" or already prefixed "openai/gpt-4o")

    Returns:
        DSPy-compatible model string with provider prefix
    """
    if "/" in model:
        return model  # Already has provider prefix
    provider = MODEL_PROVIDER_MAP.get(model, "openai")  # Default to openai
    return f"{provider}/{model}"


class JudgeSignature(dspy.Signature):
    """Judge whether input passes or fails based on the evaluation criteria."""

    input_text: str = dspy.InputField(desc="The text to evaluate")
    verdict: Literal["PASS", "FAIL"] = dspy.OutputField(
        desc="PASS if the input meets criteria, FAIL otherwise"
    )
    reasoning: str = dspy.OutputField(desc="Explanation for the verdict")


class JudgeModule(dspy.Module):
    """DSPy module that wraps the judge evaluation logic."""

    def __init__(self):
        super().__init__()
        self.judge = dspy.Predict(JudgeSignature)

    def forward(self, input_text: str) -> dspy.Prediction:
        return self.judge(input_text=input_text)


def create_metric(with_feedback: bool = False):
    """Create a metric function for DSPy optimization.

    Args:
        with_feedback: If True, return detailed feedback for COPRO/MIPROv2
    """

    def metric(
        example: dspy.Example, pred: dspy.Prediction, trace=None  # noqa: ARG001
    ) -> float:
        expected = example.expected_verdict
        actual = pred.verdict

        if expected == actual:
            return 1.0
        return 0.0

    def metric_with_feedback(
        example: dspy.Example, pred: dspy.Prediction, trace=None  # noqa: ARG001
    ):
        expected = example.expected_verdict
        actual = pred.verdict

        if expected == actual:
            return dspy.Prediction(score=1.0, feedback="Correct verdict")

        feedback = (
            f"Expected {expected} but got {actual}. "
            f"Input: '{example.input_text[:100]}...' "
            f"Ground truth reasoning: {example.reasoning}"
        )
        return dspy.Prediction(score=0.0, feedback=feedback)

    return metric_with_feedback if with_feedback else metric


class BaseDSPyAdapter(OptimizerAdapter):
    """Base class for DSPy optimizer adapters."""

    framework = "dspy"

    def __init__(self, config: OptimizationConfig):
        self.config = config

    def _prepare_examples(self, train_cases: list[TestCase]) -> list[dspy.Example]:
        """Convert test cases to DSPy examples."""
        examples = []
        for tc in train_cases:
            example = dspy.Example(
                input_text=tc.input_text,
                expected_verdict=tc.expected_verdict,
                reasoning=tc.reasoning,
                # These are the expected outputs
                verdict=tc.expected_verdict,
            ).with_inputs("input_text")
            examples.append(example)
        return examples

    def _extract_optimized_prompt(
        self,
        optimized_module: JudgeModule,
        original_prompt: str,
    ) -> tuple[str, str]:
        """Extract the optimized prompt from the optimized DSPy module.

        Returns:
            Tuple of (optimized_prompt, modification_notes)
        """
        # Get the predictor from the module
        predictor = optimized_module.judge

        # Build the optimized prompt from DSPy's internal representation
        parts = []
        notes = []

        # Check for updated instructions
        if hasattr(predictor, "signature") and predictor.signature:
            sig = predictor.signature
            if hasattr(sig, "instructions") and sig.instructions:
                parts.append(sig.instructions)
                notes.append("Updated instructions from optimizer")

        # Check for fewshot demos
        if hasattr(predictor, "demos") and predictor.demos:
            demos = predictor.demos
            if demos:
                parts.append("\n\n## Examples:")
                for i, demo in enumerate(demos, 1):
                    input_text = getattr(demo, "input_text", "N/A")
                    verdict = getattr(demo, "verdict", "N/A")
                    reasoning = getattr(demo, "reasoning", "N/A")
                    parts.append(
                        f"\n### Example {i}:\n"
                        f"Input: {input_text}\n"
                        f"Verdict: {verdict}\n"
                        f"Reasoning: {reasoning}"
                    )
                notes.append(f"Added {len(demos)} fewshot examples")

        # If we got optimizations, combine with original prompt
        if parts:
            # For instruction updates, replace; for examples, append
            if "Updated instructions" in str(notes):
                optimized_prompt = "\n".join(parts)
            else:
                optimized_prompt = original_prompt + "\n" + "\n".join(parts)
            modification_notes = "; ".join(notes)
        else:
            # Fallback: return original with a note
            optimized_prompt = original_prompt
            modification_notes = f"Optimizer ({self.name}) ran but made no changes"

        return optimized_prompt, modification_notes


class BootstrapFewShotAdapter(BaseDSPyAdapter):
    """Adapter for DSPy BootstrapFewShot optimizer."""

    name = "bootstrap_fewshot"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        dspy_model = get_dspy_model_name(config.model)

        with dspy.context(lm=dspy.LM(dspy_model)):
            train_examples = self._prepare_examples(train_cases)
            metric = create_metric(with_feedback=False)

            optimizer = dspy.BootstrapFewShot(
                metric=metric,
                max_bootstrapped_demos=4,
                max_labeled_demos=8,
                max_rounds=1,
                max_errors=5,
            )

            base_module = JudgeModule()
            base_module.judge.signature = base_module.judge.signature.with_instructions(
                current_prompt
            )

            optimized_module = optimizer.compile(
                base_module,
                trainset=train_examples,
            )

            return self._extract_optimized_prompt(optimized_module, current_prompt)


class MIPROv2Adapter(BaseDSPyAdapter):
    """Adapter for DSPy MIPROv2 optimizer."""

    name = "miprov2"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        dspy_model = get_dspy_model_name(config.model)

        with dspy.context(lm=dspy.LM(dspy_model)):
            train_examples = self._prepare_examples(train_cases)
            metric = create_metric(with_feedback=True)

            optimizer = dspy.MIPROv2(
                metric=metric,
                auto="light",
                num_threads=config.n_threads,
            )

            base_module = JudgeModule()
            base_module.judge.signature = base_module.judge.signature.with_instructions(
                current_prompt
            )

            optimized_module = optimizer.compile(
                base_module,
                trainset=train_examples,
            )

            return self._extract_optimized_prompt(optimized_module, current_prompt)


class COPROAdapter(BaseDSPyAdapter):
    """Adapter for DSPy COPRO optimizer."""

    name = "copro"

    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        dspy_model = get_dspy_model_name(config.model)

        with dspy.context(lm=dspy.LM(dspy_model)):
            train_examples = self._prepare_examples(train_cases)
            metric = create_metric(with_feedback=True)

            optimizer = dspy.COPRO(
                metric=metric,
                breadth=3,
                depth=2,
            )

            base_module = JudgeModule()
            base_module.judge.signature = base_module.judge.signature.with_instructions(
                current_prompt
            )

            optimized_module = optimizer.compile(
                base_module,
                trainset=train_examples,
            )

            return self._extract_optimized_prompt(optimized_module, current_prompt)
