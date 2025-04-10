.PHONY: makemigration
makemigration:
	litestar database make-migration --auto-generate

.PHONY: install
install:
	uv sync && pre-commit install

.PHONY: lint
lint:
	ruff check --fix

.PHONY: test
test:
	ENV=testing python -m unittest discover

.PHONY: deploy-local
deploy-local:
	docker compose --profile dev up -d 
