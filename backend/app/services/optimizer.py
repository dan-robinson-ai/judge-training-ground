"""Prompt optimization service using DSPy optimizers."""

import random
from typing import Literal

import dspy

from app.schemas import (
    EvaluationResult,
    OptimizeResponse,
    OptimizerType,
    TestCase,
)


# Model to DSPy provider mapping (mirrors frontend/src/lib/types.ts AVAILABLE_MODELS)
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


def split_test_cases(
    test_cases: list[TestCase],
    train_ratio: float = 0.7,
) -> tuple[list[TestCase], list[TestCase]]:
    """
    Split test cases into train and test sets.

    Args:
        test_cases: List of test cases to split
        train_ratio: Ratio of cases for training (default 0.7 = 70%)

    Returns:
        Tuple of (train_cases, test_cases)
    """
    shuffled = test_cases.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * train_ratio)

    train_cases = [
        tc.model_copy(update={"split": "train"})
        for tc in shuffled[:split_idx]
    ]
    test_split = [
        tc.model_copy(update={"split": "test"})
        for tc in shuffled[split_idx:]
    ]

    return train_cases, test_split


class JudgeSignature(dspy.Signature):
    """Judge whether input passes or fails based on the evaluation criteria."""

    input_text: str = dspy.InputField(desc="The text to evaluate")
    verdict: Literal["PASS", "FAIL"] = dspy.OutputField(desc="PASS if the input meets criteria, FAIL otherwise")
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
    def metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:  # noqa: ARG001
        expected = example.expected_verdict
        actual = pred.verdict

        if expected == actual:
            return 1.0
        return 0.0

    def metric_with_feedback(example: dspy.Example, pred: dspy.Prediction, trace=None):  # noqa: ARG001
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


def create_optimizer(
    optimizer_type: OptimizerType,
    metric,
):
    """Create a DSPy optimizer based on the type.

    Args:
        optimizer_type: Type of optimizer to create
        metric: Metric function for evaluation

    Returns:
        Configured DSPy optimizer (uses globally configured LM)
    """
    if optimizer_type == "bootstrap_fewshot":
        return dspy.BootstrapFewShot(
            metric=metric,
            max_bootstrapped_demos=4,
            max_labeled_demos=8,
            max_rounds=1,
            max_errors=5,
        )
    elif optimizer_type == "miprov2":
        return dspy.MIPROv2(
            metric=metric,
            auto="light",
            num_threads=4,
        )
    elif optimizer_type == "copro":
        return dspy.COPRO(
            metric=metric,
            breadth=3,
            depth=2,
        )
    else:
        raise ValueError(f"Unknown optimizer type: {optimizer_type}")


def extract_optimized_prompt(
    optimized_module: JudgeModule,
    original_prompt: str,
    optimizer_type: OptimizerType,
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
    if hasattr(predictor, 'signature') and predictor.signature:
        sig = predictor.signature
        if hasattr(sig, 'instructions') and sig.instructions:
            parts.append(sig.instructions)
            notes.append("Updated instructions from optimizer")

    # Check for fewshot demos
    if hasattr(predictor, 'demos') and predictor.demos:
        demos = predictor.demos
        if demos:
            parts.append("\n\n## Examples:")
            for i, demo in enumerate(demos, 1):
                input_text = getattr(demo, 'input_text', 'N/A')
                verdict = getattr(demo, 'verdict', 'N/A')
                reasoning = getattr(demo, 'reasoning', 'N/A')
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
        modification_notes = f"Optimizer ({optimizer_type}) ran but made no changes"

    return optimized_prompt, modification_notes


async def optimize_prompt(
    current_prompt: str,
    test_cases: list[TestCase],
    results: list[EvaluationResult],  # noqa: ARG001 - kept for API compatibility
    optimizer_type: OptimizerType = "bootstrap_fewshot",
    model: str = "gpt-4o",
) -> OptimizeResponse:
    """Optimize the system prompt using DSPy optimizers.

    This function automatically splits the data if not already split,
    then uses the specified DSPy optimizer to improve the prompt.

    Args:
        current_prompt: The current system prompt to optimize
        test_cases: List of test cases (will be auto-split if needed)
        results: Evaluation results from running the judge
        optimizer_type: Type of optimizer to use
        model: LiteLLM model name

    Returns:
        OptimizeResponse with optimized prompt and split test cases
    """
    # 1. Auto-split if not already split
    has_split = any(tc.split is not None for tc in test_cases)
    if not has_split:
        train_cases, test_split = split_test_cases(test_cases)
    else:
        train_cases = [tc for tc in test_cases if tc.split == "train"]
        test_split = [tc for tc in test_cases if tc.split == "test"]

    # If no training cases, return early
    if not train_cases:
        return OptimizeResponse(
            optimized_prompt=current_prompt,
            modification_notes="No training cases available for optimization",
            train_cases=train_cases,
            test_cases=test_split,
        )

    # 2. Configure DSPy with the model using context manager (async-safe)
    dspy_model = get_dspy_model_name(model)
    with dspy.context(lm=dspy.LM(dspy_model)):
        # 3. Prepare training examples from train cases
        # Include the expected verdict and reasoning as labels
        train_examples = []
        for tc in train_cases:
            example = dspy.Example(
                input_text=tc.input_text,
                expected_verdict=tc.expected_verdict,
                reasoning=tc.reasoning,
                # These are the expected outputs
                verdict=tc.expected_verdict,
            ).with_inputs("input_text")
            train_examples.append(example)

        # 4. Create the metric and optimizer
        use_feedback = optimizer_type in ("copro", "miprov2")
        metric = create_metric(with_feedback=use_feedback)
        optimizer = create_optimizer(optimizer_type, metric)

        # 5. Create the base module with the current prompt as instructions
        base_module = JudgeModule()
        # Set the current prompt as the signature instructions
        base_module.judge.signature = base_module.judge.signature.with_instructions(current_prompt)

        # 6. Run optimization
        try:
            optimized_module = optimizer.compile(
                base_module,
                trainset=train_examples,
            )

            # 7. Extract the optimized prompt
            optimized_prompt, modification_notes = extract_optimized_prompt(
                optimized_module,
                current_prompt,
                optimizer_type,
            )

        except Exception as e:
            # If optimization fails, return original prompt with error note
            optimized_prompt = current_prompt
            modification_notes = f"Optimization failed: {str(e)}"

    return OptimizeResponse(
        optimized_prompt=optimized_prompt,
        modification_notes=modification_notes,
        train_cases=train_cases,
        test_cases=test_split,
    )
