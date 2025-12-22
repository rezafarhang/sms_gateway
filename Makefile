.PHONY: help build up down logs shell db-shell redis-cli test clean migrate seed

help:
	@echo "SMS Gateway - Available commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs"
	@echo "  make shell       - Enter app container shell"
	@echo "  make db-shell    - Enter PostgreSQL shell"
	@echo "  make redis-cli   - Enter Redis CLI"
	@echo "  make migrate     - Run database migrations"
	@echo "  make seed        - Seed test data"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Remove containers and volumes"

build:
	cd docker && docker-compose build

up:
	cd docker && docker-compose up -d

down:
	cd docker && docker-compose down

logs:
	cd docker && docker-compose logs -f

shell:
	cd docker && docker-compose exec app /bin/bash

db-shell:
	cd docker && docker-compose exec postgres psql -U smsuser -d sms_gateway

redis-cli:
	cd docker && docker-compose exec redis redis-cli

migrate:
	cd docker && docker-compose exec app alembic upgrade head

seed:
	cd docker && docker-compose exec app python scripts/seed_data.py

test:
	cd docker && docker-compose exec app pytest

clean:
	cd docker && docker-compose down -v
