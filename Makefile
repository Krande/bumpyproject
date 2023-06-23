
bump:
	bumpy pyproject --push

dev:
	mamba env update -f environment.yml --prune

format:
	black --config pyproject.toml . && isort . && ruff . --fix