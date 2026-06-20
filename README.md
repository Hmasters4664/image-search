# FastAPI Scaffold

A minimal FastAPI project scaffold with a health endpoint and test setup.

## Project Structure

```
.
├── app
│   ├── api
│   │   └── routes.py
│   └── main.py
├── tests
│   └── test_health.py
├── requirements.txt
└── README.md
```

## Quick Start

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Create a local env file:

```bash
cp .env.example .env
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
uvicorn app.main:app --reload
```

5. Open:
- API root docs: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/api/health`

The app loads `APP_NAME` and `APP_ENV` from `.env` via `pydantic-settings`.

## Run Tests

```bash
pytest
```
