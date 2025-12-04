"""Test case and system prompt generation service."""

from app.schemas import (
    TestCase,
    GeneratedTestCaseList,
    GeneratedSystemPrompt,
)
from app.services.llm import call_llm


GENERATION_PROMPT = """You are an expert at generating diverse test cases for AI evaluation systems.

Given an INTENT that describes what the judge should detect/evaluate, generate {count} diverse test cases.

CRITICAL REQUIREMENTS:
1. Include a mix of clear PASS cases, clear FAIL cases, TRICKY NEGATIVES (tricky cases that should FAIL but might fool a judge), and TRICKY POSITIVES (cases that should PASS but look suspicious).
2. The distribution should be roughly: 30% clear PASS, 30% clear FAIL, 20% tricky negatives, 20% tricky positives.
3. Each test case must have detailed reasoning explaining why it should pass or fail.
4. Make the inputs realistic and vary the tone, length, vocabulary, and noise levels (typos, slang).

INTENT: {intent}

Generate {count} test cases following the schema provided."""


SYSTEM_PROMPT_GENERATION = """You are an expert at writing system prompts for AI judges.

Given an INTENT that describes what the judge should detect/evaluate, write a clear, comprehensive system prompt that will guide the judge to make accurate verdicts.

The system prompt should:
1. Clearly define what constitutes a PASS vs FAIL verdict
2. List specific criteria or rules the judge should follow
3. Handle edge cases and ambiguous situations
4. Be concise but thorough

INTENT: {intent}

Generate a system prompt for this judge."""


async def generate_test_cases(
    intent: str, count: int = 50, model: str = "gpt-4o"
) -> tuple[list[TestCase], str]:
    """
    Generate synthetic test cases and an initial system prompt for a given intent.

    Args:
        intent: The intent description for the judge
        count: Number of test cases to generate
        model: LiteLLM model name

    Returns:
        Tuple of (list of TestCase objects, generated system prompt)
    """
    # Generate test cases using structured output
    # Note: Always use gpt-4o as it supports structured outputs via response_format
    test_cases_prompt = GENERATION_PROMPT.format(intent=intent, count=count)

    generated = await call_llm(
        messages=[{"role": "user", "content": test_cases_prompt}],
        response_model=GeneratedTestCaseList,
        model="gpt-4o",
        temperature=0.8,
    )

    # Convert to TestCase objects
    test_cases = [
        TestCase(
            input_text=case.input_text,
            expected_verdict=case.expected_verdict,
            reasoning=case.reasoning,
            verified=False,
        )
        for case in generated.test_cases
    ]

    # Generate initial system prompt
    system_prompt_prompt = SYSTEM_PROMPT_GENERATION.format(intent=intent)

    system_prompt_response = await call_llm(
        messages=[{"role": "user", "content": system_prompt_prompt}],
        response_model=GeneratedSystemPrompt,
        model="gpt-4o",
        temperature=0.7,
    )

    return test_cases, system_prompt_response.system_prompt
