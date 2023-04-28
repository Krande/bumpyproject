
bump:
	conda run -n bumpyproject --live-stream bumpy --bump-level pre-release --ignore-git-state --push

dev:
	mamba env update -f environment.yml --prune

format:
	black --config pyproject.toml . && isort . && ruff . --fix