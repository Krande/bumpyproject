
bump:
	bumpy --bump-level=pre-release --git-push --check-git

dev:
	mamba env update -f environment.yml --prune

format:
	black --config pyproject.toml . && isort . && ruff . --fix