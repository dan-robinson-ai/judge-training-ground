from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.api import router as api_router

# Load environment variables from .env file
load_dotenv()

print("=== LOADING MAIN.PY V2 - CUSTOM CORS ===")  # DEBUG

app = FastAPI(
    title="Judge Training Ground",
    description="A training ground for LLM judges - generate test cases, evaluate, and optimize prompts",
    version="1.0.0"
)


# Custom CORS middleware to ensure headers are set
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # Handle preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            content={},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Include API routes
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
