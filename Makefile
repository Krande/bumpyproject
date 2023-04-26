
bump:
	conda run -n bumpyproject --live-stream bumpy --bump-level pre-release --ignore-git-state --push

dev:
	mamba update -f environment.yml

format:
	black --config pyproject.toml . && isort . && ruff . --fix