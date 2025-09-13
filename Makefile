
lint:
	ruff check pyramid_tasks tests
	ruff format --check pyramid_tasks tests

lint-fix:
	ruff check --fix pyramid_tasks tests

format:
	ruff format pyramid_tasks tests

test:
	pytest tests
