# Makefile for tg-reposter

.PHONY: help install test build up down logs login repost delete sync

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

build: ## Build the Docker image.
	@echo "Building Docker image..."
	docker build -t tg-reposter .

up: ## Start the application using Docker Compose.
	@echo "Starting application with Docker Compose..."
	docker-compose up --build -d

down: ## Stop the application using Docker Compose.
	@echo "Stopping application with Docker Compose..."
	docker-compose down

logs: ## View application logs.
	@echo "Tailing application logs..."
	docker-compose logs -f

login: ## (Placeholder) Run the login flow.
	@echo "login command not yet implemented."

repost: ## (Placeholder) Run the repost command.
	@echo "repost command not yet implemented."

delete: ## (Placeholder) Run the delete command.
	@echo "delete command not yet implemented."

sync: ## (Placeholder) Run the sync command.
	@echo "sync command not yet implemented."