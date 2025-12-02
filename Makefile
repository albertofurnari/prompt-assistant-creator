.PHONY: install lint test clean

install:
	python -m pip install --upgrade pip
	python -m pip install -e .

lint:
	ruff check .
	mypy optimizer.py prompt_optimizer

test:
	pytest

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} \;
	rm -rf .mypy_cache .pytest_cache
