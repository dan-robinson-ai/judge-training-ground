import json
import asyncio
import litellm
from typing import Literal
from app.schemas import TestCase, EvaluationResult


class LLMJudge:
    """LLM-based judge that evaluates inputs against a system prompt."""

    def __init__(self, system_prompt: str, model: str = "gpt-4o"):
        self.system_prompt = system_prompt
        self.model = model

    async def evaluate_single(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate a single test case."""

        evaluation_prompt = f"""Based on the SYSTEM PROMPT provided, evaluate the following INPUT and determine if it should PASS or FAIL.

INPUT: {test_case.input_text}

You must respond with a JSON object in this exact format:
{{
  "verdict": "PASS" or "FAIL",
  "reasoning": "Your detailed reasoning for this verdict"
}}

Only respond with the JSON object, no other text."""

        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            actual_verdict: Literal["PASS", "FAIL"] = result["verdict"]
            reasoning = result["reasoning"]

            return EvaluationResult(
                test_case_id=test_case.id,
                actual_verdict=actual_verdict,
                reasoning=reasoning,
                correct=actual_verdict == test_case.expected_verdict
            )

        except (json.JSONDecodeError, KeyError) as e:
            return EvaluationResult(
                test_case_id=test_case.id,
                actual_verdict="ERROR",
                reasoning=f"Failed to parse LLM response: {str(e)}",
                correct=False
            )
        except Exception as e:
            return EvaluationResult(
                test_case_id=test_case.id,
                actual_verdict="ERROR",
                reasoning=f"Evaluation error: {str(e)}",
                correct=False
            )

    async def evaluate_batch(self, test_cases: list[TestCase]) -> list[EvaluationResult]:
        """Evaluate multiple test cases concurrently using asyncio.gather."""

        tasks = [self.evaluate_single(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks)

        return list(results)
