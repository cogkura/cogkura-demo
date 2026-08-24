#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Backend: sync"
uv sync --project apps/api --dev --locked

echo "==> Backend: ruff check"
uv run --project apps/api ruff check apps/api

echo "==> Backend: ruff format"
uv run --project apps/api ruff format --check apps/api

echo "==> Backend: mypy"
uv run --project apps/api mypy apps/api/src

echo "==> Backend: pytest"
uv run --project apps/api pytest apps/api/tests

echo "==> Frontend: npm ci"
npm ci --prefix apps/web

echo "==> Frontend: lint"
npm run lint --prefix apps/web

echo "==> Frontend: typecheck"
npm run typecheck --prefix apps/web

echo "==> Frontend: build"
npm run build --prefix apps/web

echo "All checks passed."
