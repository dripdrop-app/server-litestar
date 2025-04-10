.PHONY: makemigration
makemigration:
	litestar database make-migration --auto-generate

.PHONY: install
install:
	uv sync && pre-commit install

.PHONY: lint
lint:
	ruff check --select I --fix

.PHONY: test
test:
	ENV=testing python -m unittest discover

.PHONY: deploy-local
deploy-local:
	docker compose --profile dev up -d 

.PHONY: run
run:
	litestar run

.PHONY: clean
clean:
	rm -rf $(shell find app -name __pycache__)
