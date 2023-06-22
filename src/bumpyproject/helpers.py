import pathlib

from bumpyproject import env_vars as env


def check_git_repo_validity(repository):
    if len(env.ONLY_VALID_REPOS) > 0 and repository not in env.ONLY_VALID_REPOS:
        raise ValueError(f"Repository {repository} is not in the list of valid repositories: {env.ONLY_VALID_REPOS}")


def find_file_in_subdirectories(root_dir, file_name):
    if isinstance(root_dir, str):
        root_dir = pathlib.Path(root_dir)
    files = []
    for path in root_dir.rglob(file_name):
        if 'node_modules' in str(path):
            continue
        if path.is_file():
            files.append(path)

    if len(files) == 0:
        raise FileNotFoundError(f"Could not find {file_name} in {root_dir}")
    elif len(files) > 1:
        raise ValueError(f"Found multiple {file_name} files in {root_dir}")

    return files[0]