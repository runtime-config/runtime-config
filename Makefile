test:
	pytest tests

lint:
	pre-commit run --all

migrate:
	alembic upgrade head

build-img:
	docker build --build-arg CURRENT_ENV=prod -t ghcr.io/runtime-config/runtime-config:${ver} .

up:
	docker compose -f ./docker-compose.dev.yml up
