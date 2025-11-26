# Judge Training Ground

A tool for training and evaluating LLM-based judges through synthetic test case generation and iterative prompt optimization.

## Prerequisites

- **Python 3.13+** with [uv](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** with npm
- API keys for LLM providers (OpenAI, Anthropic, etc.)

## Project Structure

```
judge-training/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── routers/  # API endpoints
│   │   ├── services/ # Business logic (generator, judge, optimizer)
│   │   └── schemas.py
│   └── tests/        # pytest tests
├── frontend/         # Next.js React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── lib/      # API client, store, types
│   │   └── __tests__/ # vitest tests
│   └── package.json
└── README.md
```

## Backend Setup

### 1. Navigate to backend directory

```bash
cd backend
```

### 2. Install dependencies

```bash
uv sync
```

This installs both production and dev dependencies (pytest, ruff, etc.).

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 4. Start the backend server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

**API Endpoints:**
- `GET /health` - Health check
- `POST /api/generate` - Generate test cases and system prompt
- `POST /api/run` - Run evaluation on test cases
- `POST /api/optimize` - Optimize system prompt based on results

## Frontend Setup

### 1. Navigate to frontend directory

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Start the development server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Testing

### Backend Tests

Run all backend tests:

```bash
cd backend
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Run specific test file:

```bash
uv run pytest tests/test_api.py
```

Run with coverage:

```bash
uv run pytest --cov=app
```

### Frontend Tests

Run all frontend tests:

```bash
cd frontend
npm test
```

Run tests in watch mode:

```bash
npm test -- --watch
```

Run with UI:

```bash
npm run test:ui
```

Run with coverage:

```bash
npm run test:coverage
```

## Linting

### Backend (Ruff)

Check for linting issues:

```bash
cd backend
uv run ruff check .
```

Auto-fix issues:

```bash
uv run ruff check . --fix
```

Format code:

```bash
uv run ruff format .
```

### Frontend (ESLint)

```bash
cd frontend
npm run lint
```

## Development Workflow

1. **Start both servers:**
   - Terminal 1: `cd backend && uv run uvicorn app.main:app --reload`
   - Terminal 2: `cd frontend && npm run dev`

2. **Using the app:**
   - Enter a Judge Intent (e.g., "Detect toxic messages")
   - Set the number of test cases to generate (default: 50)
   - Select a model
   - Click "Generate Test Cases"
   - Review the generated system prompt and test cases
   - Click "Run Evaluation" to test the judge
   - Click "Auto-Optimize" if accuracy is below 100%

## Available Models

- GPT-4o (OpenAI)
- GPT-4o Mini (OpenAI)
- Claude 3.5 Sonnet (Anthropic)
- Claude 3.5 Haiku (Anthropic)

## Troubleshooting

### Backend won't start
- Ensure Python 3.13+ is installed
- Ensure uv is installed: `pip install uv`
- Check that `.env` file exists with valid API keys

### Frontend won't connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Verify `NEXT_PUBLIC_API_URL` environment variable if using non-default port

### Tests failing
- Backend: Ensure dev dependencies are installed with `uv sync`
- Frontend: Ensure test dependencies are installed with `npm install`
