test:
	pytest tests

lint:
	pre-commit run --all

migrate:
	alembic upgrade head

build-img:
	docker build --build-arg CURRENT_ENV=prod -t ghcr.io/aleksey925/runtime-config:${ver} .

build-dev-img:
	docker build --build-arg CURRENT_ENV=dev -t ghcr.io/aleksey925/runtime-config:dev .
