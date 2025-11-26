from fastapi import APIRouter, HTTPException
from app.schemas import (
    GenerateRequest,
    GenerateResponse,
    RunRequest,
    RunStats,
    OptimizeRequest,
    OptimizeResponse
)
from app.services.generator import generate_test_cases
from app.services.judge import LLMJudge
from app.services.optimizer import optimize_prompt

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(request: GenerateRequest) -> GenerateResponse:
    """Generate synthetic test cases and initial system prompt for a given intent."""
    try:
        test_cases, system_prompt = await generate_test_cases(
            intent=request.intent,
            count=request.count,
            model=request.model,
        )
        return GenerateResponse(test_cases=test_cases, system_prompt=system_prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/run", response_model=RunStats)
async def run_endpoint(request: RunRequest) -> RunStats:
    """Run the judge on test cases and return statistics."""
    try:
        judge = LLMJudge(
            system_prompt=request.system_prompt,
            model=request.model_name
        )

        results = await judge.evaluate_batch(request.test_cases)

        # Calculate statistics
        total = len(results)
        passed = sum(1 for r in results if r.correct)
        errors = sum(1 for r in results if r.actual_verdict == "ERROR")
        failed = total - passed - errors
        accuracy = (passed / total * 100) if total > 0 else 0

        return RunStats(
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            accuracy=round(accuracy, 2),
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_endpoint(request: OptimizeRequest) -> OptimizeResponse:
    """Optimize the system prompt based on evaluation results."""
    try:
        result = await optimize_prompt(
            current_prompt=request.current_prompt,
            test_cases=request.test_cases,
            results=request.results
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
