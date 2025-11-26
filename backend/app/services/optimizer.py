import json
import litellm
from app.schemas import TestCase, EvaluationResult, OptimizeResponse


OPTIMIZATION_PROMPT = """You are an expert prompt engineer. Your task is to improve a system prompt based on evaluation results.

CURRENT SYSTEM PROMPT:
{current_prompt}

FAILED TEST CASES (the judge got these wrong):
{failed_cases}

PASSED TEST CASES (the judge got these correct - do NOT break these):
{passed_cases}

Analyze why the judge failed on the failed cases and rewrite the system prompt to:
1. Fix the issues that caused failures on the failed cases
2. NOT break any of the currently passing cases
3. Be clearer and more comprehensive
4. Handle edge cases better

Respond with a JSON object in this exact format:
{{
  "optimized_prompt": "Your improved system prompt here",
  "modification_notes": "Bullet points explaining what you changed and why"
}}

Only respond with the JSON object, no other text."""


async def optimize_prompt(
    current_prompt: str,
    test_cases: list[TestCase],
    results: list[EvaluationResult],
    model: str = "gpt-4o"
) -> OptimizeResponse:
    """Optimize the system prompt based on evaluation results."""

    # Build lookup for test cases
    tc_lookup = {tc.id: tc for tc in test_cases}

    # Separate passed and failed cases
    failed_cases = []
    passed_cases = []

    for result in results:
        tc = tc_lookup.get(result.test_case_id)
        if not tc:
            continue

        case_info = {
            "input": tc.input_text,
            "expected": tc.expected_verdict,
            "actual": result.actual_verdict,
            "expected_reasoning": tc.reasoning,
            "judge_reasoning": result.reasoning
        }

        if result.correct:
            passed_cases.append(case_info)
        else:
            failed_cases.append(case_info)

    # If no failed cases, return the original prompt
    if not failed_cases:
        return OptimizeResponse(
            optimized_prompt=current_prompt,
            modification_notes="All test cases passed. No optimization needed."
        )

    prompt = OPTIMIZATION_PROMPT.format(
        current_prompt=current_prompt,
        failed_cases=json.dumps(failed_cases, indent=2),
        passed_cases=json.dumps(passed_cases[:5], indent=2)  # Limit passed cases to avoid token limits
    )

    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    try:
        result = json.loads(content)
        return OptimizeResponse(
            optimized_prompt=result["optimized_prompt"],
            modification_notes=result["modification_notes"]
        )
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse optimization response: {e}")
