from bumpyproject import env_vars as env


def check_git_repo_validity(repository):
    if len(env.ONLY_VALID_REPOS) > 0 and repository not in env.ONLY_VALID_REPOS:
        raise ValueError(f"Repository {repository} is not in the list of valid repositories: {env.ONLY_VALID_REPOS}")
