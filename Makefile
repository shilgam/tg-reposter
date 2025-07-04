# Makefile for tg-reposter

.PHONY: help setup install test login repost delete sync

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Create temp input/output directories if missing.
	@mkdir -p ./temp/input ./temp/output
	@mkdir -p ./data/input ./data/output

install: ## Install production and development dependencies.
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -r dev-requirements.txt

test: ## Run tests using Docker Compose (CI style).
	docker compose -f docker-compose.ci.yml up \
		--build \
		--abort-on-container-exit \
		--exit-code-from reposter

login: ## Creates a new session file by logging in.
	@touch anon.session
	@docker-compose run --rm reposter python -m src.main login

repost: ## Reposts messages from file. Requires ARGS="--source=<source> --destination=<dest>".
	@docker-compose run --rm reposter python -m src.main repost $(ARGS)

delete: ## Deletes messages. Pass CLI arguments via the ARGS variable.
	@docker-compose run --rm reposter python -m src.main delete $(ARGS)

sync: ## Syncs messages. Pass CLI arguments via the ARGS variable.
	$(MAKE) repost ARGS="$(ARGS)" && $(MAKE) delete ARGS="$(ARGS)"
