run-docker-compose:
	uv sync
	docker compose up --build -d

clean-notebook-outputs:
	jupyter nbconvert --clear-output --inplace notebooks/*/*.ipynb

stop-docker-compose:
	docker compose down

run-evals-retriever:
	uv sync && \
	export PYTHONPATH="${PWD}/apps/api:${PWD}/apps/api/src:${PYTHONPATH}:${PWD}" && \
	uv run --env-file .env python -m api.evals.eval_retriever
