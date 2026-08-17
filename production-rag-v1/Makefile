.PHONY: setup db-up db-down test validate

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -e '.[dev,openai,local-embeddings]'

db-up:
	docker compose up -d

db-down:
	docker compose down

test:
	pytest -q

validate:
	ragv1 validate-golden evals/golden/v1.sample.jsonl
