import git

from bumpyproject import env_vars as env
from bumpyproject.versions import BumpLevel


class DirtyRepoError(Exception):
    pass


class GitHelper:
    @staticmethod
    def check_git_state():
        curr_repo = git.Repo(env.ROOT_DIR)
        if curr_repo.is_dirty():
            raise DirtyRepoError("There are uncommitted changes!")

    @staticmethod
    def get_latest_tag() -> str:
        curr_repo = git.Repo(env.ROOT_DIR)
        tags = list(curr_repo.tags)
        return tags[-1].name

    @staticmethod
    def commit_and_tag(old_version, new_version):
        commit_message = f"bump {old_version} --> {new_version}"
        curr_repo = git.Repo(env.ROOT_DIR)
        curr_repo.git.config("user.email", env.GITHUB_USER_EMAIL)
        curr_repo.git.config("user.name", env.GITHUB_USER)
        curr_repo.git.execute(["git", "commit", "-am", commit_message])
        curr_repo.git.execute(["git", "tag", "-a", new_version, "-m", commit_message])

    @staticmethod
    def get_bump_level_from_commit() -> BumpLevel:
        curr_repo = git.Repo(env.ROOT_DIR)
        commits = list(curr_repo.iter_commits(max_count=1))
        latest_commit = commits[0]
        msg = latest_commit.message
        for level in BumpLevel:
            if f"[{level.value}]" in msg:
                return level

        if "[pre]" in msg:
            return BumpLevel.PRE_RELEASE

        raise ValueError(f'No bump level found in commit message "{msg}"')
