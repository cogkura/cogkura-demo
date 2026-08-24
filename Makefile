.PHONY: dev dev-api dev-web verify install-api install-web

dev:
	@echo "Starting API and web (run in separate terminals if preferred: make dev-api / make dev-web)"
	@$(MAKE) -j2 dev-api dev-web

dev-api:
	cd apps/api && uv run uvicorn cogkura_demo.main:app --host $${DEMO_API_HOST:-127.0.0.1} --port $${DEMO_API_PORT:-8000} --workers 1 --reload

dev-web:
	cd apps/web && npm run dev

install-api:
	uv sync --project apps/api --dev --locked

install-web:
	npm ci --prefix apps/web

verify:
	./scripts/verify.sh
