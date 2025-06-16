.PHONY: makemigration
makemigration:
	infisical run --env=dev -- uv run litestar database make-migration --auto-generate

.PHONY: install
install:
	uv sync && uv run pre-commit install

.PHONY: lint
lint:
	ruff check --select I --fix

.PHONY: test-app
test-app:
	ENV=testing infisical run --env=dev -- uv run pytest tests/routes

.PHONY: test-queue
test-queue:
	ENV=testing infisical run --env=dev -- uv run pytest tests/queue

.PHONY: test
test: test-app test-queue

.PHONY: cov-app
coverage-app:
	ENV=testing infisical run --env=dev -- uv run pytest --cov=tests/routes

.PHONY: cov-queue
coverage-queue:
	ENV=testing infisical run --env=dev -- uv run pytest --cov=tests/queue

.PHONY: cov
coverage: cov-app cov-queue

.PHONY: deploy-local
deploy-local:
	docker compose --profile dev up -d 

.PHONY: run-dev
run-dev:
	infisical run --env=dev -- uv run litestar run --debug --reload

.PHONY: worker-dev
worker-dev:
	infisical run --env=dev -- uv run litestar workers run --verbose --debug

.PHONY: clean
clean:
	rm -rf $(shell find app -name __pycache__)
