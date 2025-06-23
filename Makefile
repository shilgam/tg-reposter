# Makefile for tg-reposter

.PHONY: help install test login repost delete sync

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install production and development dependencies.
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -r dev-requirements.txt

test: ## Run tests using pytest.
	@echo "Running tests..."
	pytest

login: ## Creates a new session file by logging in.
	@touch anon.session
	@docker-compose run --rm reposter python -m src.main login

repost: ## Reposts a message. Pass CLI arguments via the ARGS variable.
	@docker-compose run --rm reposter python -m src.main repost $(ARGS)

delete: ## Deletes messages. Pass CLI arguments via the ARGS variable.
	@docker-compose run --rm reposter python -m src.main delete $(ARGS)

sync: ## Syncs messages. Pass CLI arguments via the ARGS variable.
	@docker-compose run --rm reposter python -m src.main sync $(ARGS)