.PHONY: makemigration
makemigration:
	infisical run --env=dev -- uv run litestar database make-migration --auto-generate

.PHONY: install
install:
	uv sync && uv run pre-commit install

.PHONY: lint
lint:
	ruff check --select I --fix

.PHONY: test
test:
	ENV=testing infisical run --env=dev -- uv run pytest

.PHONY: cov
coverage:
	ENV=testing infisical run --env=dev -- uv run pytest --cov=app

.PHONY: deploy-local
deploy-local:
	docker compose --profile dev up -d 

.PHONY: run-dev
run-dev:
	infisical run --env=dev -- uv run litestar run --debug --reload

.PHONY: worker-dev
worker-dev:
	infisical run --env=dev -- uv run litestar workers run --reload --debug

.PHONY: clean
clean:
	rm -rf $(shell find app -name __pycache__)
