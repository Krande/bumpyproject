dev:
	mamba update -f environment.yml --prune

format:
	black --config pyproject.toml . && isort . && ruff . --fix