.PHONY: install test test-all lint run docker clean

install:
	python -m venv .venv
	.\.venv\Scripts\pip install fastapi uvicorn[standard] pydantic pandas numpy matplotlib sqlalchemy pytest httpx python-multipart
	.\.venv\Scripts\pip install -e .

test:
	.\.venv\Scripts\pytest tests/forecastos/

test-all:
	.\.venv\Scripts\pytest tests/forecastos/ v1/tests/

run:
	.\.venv\Scripts\python -m forecastos.api.main

docker:
	docker compose -f docker/docker-compose.yml up --build

clean:
	rm -rf .pytest_cache forecastos.db forecastos_audit_log.json
