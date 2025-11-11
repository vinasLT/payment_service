# Repository Guidelines

## Project Structure & Module Organization
- `main.py` starts the FastAPI app; `router/` groups versioned HTTP routes such as `router/v1/account_management/plan.py`.
- `services/` holds domain logic (payments, integrations) while `database/` contains SQLAlchemy models, CRUD services, and Alembic migrations (`alembic/`).
- RPC interfaces live under `rpc_server/`, shared DTOs in `schemas/`, and reusable helpers in `core/` plus `dependencies/`.
- Local fixtures and regression tests sit in `tests/`; prefer mirroring the package path when adding new suites (e.g., `tests/router/test_plan.py`).

## Build, Test, and Development Commands
- `poetry install` – sets up the Python 3.13 virtual environment with all runtime/test dependencies.
- `poetry run uvicorn main:app --reload` – launches the FastAPI server with hot reload for local development.
- `poetry run pytest` – executes the test suite; use `-k pattern` to target specific modules.
- `poetry run alembic upgrade head` – applies database migrations; pair with `alembic revision --autogenerate -m "message"` when schema changes.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and type hints on public interfaces; async endpoints should return Pydantic models defined in `schemas/`.
- Keep module names snake_case and class names PascalCase; request/response models should end with `Create`, `Read`, `Update`, or `Payload` to match current patterns.
- Prefer service classes in `database/crud` or `services/` for business logic rather than embedding SQL in routers.

## Testing Guidelines
- Use `pytest` with async fixtures (via `pytest.mark.asyncio`) for coroutine-based services; place shared factories under `tests/conftest.py`.
- Name tests after the behavior under verification, e.g., `test_list_plans_returns_paginated_payload`.
- Aim to cover new endpoints, background tasks, and migrations; add regression tests before touching payment-critical code.

## Commit & Pull Request Guidelines
- Commits are short, imperative statements (`enhance webhook request function...`); keep related changes together and reference issue IDs when available.
- Each PR should describe the motivation, summarize the solution, list testing evidence (`pytest`, manual API calls), and include screenshots or curl snippets for API surface changes.
- Ensure CI basics pass locally (lint, tests, migrations) before requesting review and flag any backward-incompatible changes in the description.

## Security & Configuration Tips
- Store secrets in environment variables or `.env`; never commit credentials. `config.py` already consumes settings via `pydantic-settings`.
- When running locally, prefer SQLite (`db.sqlite`) but validate migrations against the target Postgres flavor (see `docker-compose.yml`) before deployment.
