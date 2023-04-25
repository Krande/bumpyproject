dev:
	mamba update -f environment.yml

format:
	black --config pyproject.toml . && isort . && ruff . --fix