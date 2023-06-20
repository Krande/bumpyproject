from bumpyproject import env_vars as env
import git


def pull_repo_to_temp_dir():
    repo = git.Repo.clone_from(env.GH_REPO_URL, env.GIT_LOCAL_TEMP_DIR, branch=env.GH_BRANCH_NAME)
    repo.git.config("user.email", env.GIT_USER_EMAIL)
    repo.git.config("user.name", env.GIT_USER)
