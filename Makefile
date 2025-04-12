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
	ENV=testing infisical run --env=dev -- uv run python -m unittest discover

.PHONY: deploy-local
deploy-local:
	docker compose --profile dev up -d 

.PHONY: run
run:
	infisical run --env=dev -- uv run litestar run

.PHONY: clean
clean:
	rm -rf $(shell find app -name __pycache__)

.PHONY: commit
commit:
	uv run cz commit
