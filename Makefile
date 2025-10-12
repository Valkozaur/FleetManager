.PHONY: help dev test build deploy

help:
	@echo "FleetManager - Available targets"
	@echo "  make dev            - Start services in dev mode (docker-compose)"
	@echo "  make test           - Run tests for services"
	@echo "  make build          - Build docker images"
	@echo "  make deploy         - Deploy using prod compose (requires setup)"

dev:
	docker-compose -f infrastructure/docker/docker-compose.yml up --build

test:
	./scripts/run-tests.sh

build:
	docker-compose -f infrastructure/docker/docker-compose.yml build

deploy:
	@echo "Deploy step is environment specific. See .github workflows for CI/CD examples."
