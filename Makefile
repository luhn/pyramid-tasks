
lint:
	isort pyramid_tasks tests
	black pyramid_tasks tests
	flake8 pyramid_tasks tests

test:
	pytest tests
