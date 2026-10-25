.PHONY: install test api ui

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev,aws]"
	cd frontend && npm install

test:
	cd backend && .venv/bin/pytest -q

api:
	cd backend && .venv/bin/uvicorn app.main:app --reload

ui:
	cd frontend && npm run dev
