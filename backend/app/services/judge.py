"""LLM Judge service for evaluating test cases."""

import asyncio

from app.schemas import EvaluationResult, JudgeVerdict, TestCase
from app.services.llm import call_llm


class LLMJudge:
    """LLM-based judge that evaluates inputs against a system prompt."""

    def __init__(self, system_prompt: str, model: str = "gpt-4o"):
        self.system_prompt = system_prompt
        self.model = model

    async def evaluate_single(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate a single test case."""

        evaluation_prompt = f"""Based on the SYSTEM PROMPT provided, evaluate the following INPUT and determine if it should PASS or FAIL.

INPUT: {test_case.input_text}

Provide your verdict and detailed reasoning."""

        try:
            result = await call_llm(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": evaluation_prompt},
                ],
                response_model=JudgeVerdict,
                model=self.model,
                temperature=0.1,
            )

            return EvaluationResult(
                test_case_id=test_case.id,
                actual_verdict=result.verdict,
                reasoning=result.reasoning,
                correct=result.verdict == test_case.expected_verdict,
            )

        except Exception as e:
            return EvaluationResult(
                test_case_id=test_case.id,
                actual_verdict="ERROR",
                reasoning=f"Evaluation error: {str(e)}",
                correct=False,
            )

    async def evaluate_batch(self, test_cases: list[TestCase]) -> list[EvaluationResult]:
        """Evaluate multiple test cases concurrently, limited to 10 at a time."""

        semaphore = asyncio.Semaphore(10)

        async def limited_evaluate(tc: TestCase) -> EvaluationResult:
            async with semaphore:
                return await self.evaluate_single(tc)

        tasks = [limited_evaluate(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks)

        return list(results)
