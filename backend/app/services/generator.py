import json
import litellm
from app.schemas import TestCase


GENERATION_PROMPT = """You are an expert at generating diverse test cases for AI evaluation systems.

Given an INTENT that describes what the judge should detect/evaluate, generate {count} diverse test cases.

CRITICAL REQUIREMENTS:
1. Include a mix of clear PASS cases, clear FAIL cases, TRICKY NEGATIVES (tricky cases that should FAIL but might fool a judge), and TRICKY POSITIVES (cases that should PASS but look suspicious).
2. The distribution should be roughly: 30% clear PASS, 30% clear FAIL, 20% tricky negatives, 20% tricky positives.
3. Each test case must have detailed reasoning explaining why it should pass or fail.
4. Make the inputs realistic and vary the tone, length, vocabulary, and noise levels (typos, slang).

INTENT: {intent}

Respond with a JSON array of test cases in this exact format:
[
  {{
    "input_text": "The text to evaluate",
    "expected_result": "PASS" or "FAIL",
    "difficulty": "clear_pass" | "clear_fail" | "tricky_negative" | "tricky_positive",
    "reasoning": "Detailed explanation of why this should pass/fail"
  }},
  ...
]

Only respond with the JSON array, no other text."""


async def generate_test_cases(intent: str, count: int = 10, model: str = "gpt-4o") -> list[TestCase]:
    """Generate synthetic test cases for a given intent using an LLM."""

    prompt = GENERATION_PROMPT.format(intent=intent, count=count)

    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    # Parse the JSON response
    try:
        # Handle both array and object responses
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            # If it's an object, look for a test_cases or similar key
            cases_data = parsed.get("test_cases", parsed.get("cases", [parsed]))
            if not isinstance(cases_data, list):
                cases_data = [cases_data]
        else:
            cases_data = parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    # Convert to TestCase objects
    test_cases = []
    for case_data in cases_data:
        test_case = TestCase(
            input_text=case_data["input_text"],
            expected_verdict=case_data["expected_verdict"],
            reasoning=case_data["reasoning"],
            verified=False
        )
        test_cases.append(test_case)

    return test_cases
