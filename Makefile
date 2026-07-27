up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api worker beat web

migrate:
	docker compose exec api alembic upgrade head

test:
	docker compose exec api pytest

format:
	docker compose exec api ruff format app tests
	docker compose exec api ruff check app tests --fix
