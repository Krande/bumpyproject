import pathlib

import git
import tomlkit

from bumpyproject import env_vars as env
from bumpyproject.log_utils import logger
from bumpyproject.versions import BumpLevel


class DirtyRepoError(Exception):
    pass


class GitHelper:
    def __init__(self, git_root_dir=None, project=None):
        if git_root_dir is None:
            git_root_dir = env.GIT_ROOT_DIR

        if isinstance(git_root_dir, str):
            git_root_dir = pathlib.Path(git_root_dir)

        git_root_dir = git_root_dir.resolve().absolute()

        self._git_root_dir = git_root_dir
        self._git_repo = git.Repo(git_root_dir)
        self._project = project

        remotes = list(self._git_repo.remotes)
        if len(remotes) == 1:
            self._remote = remotes[0]
        elif len(remotes) > 1:
            raise ValueError("Currently only one git remote is supported.")
        else:
            logger.warning("No git remote found. This may cause issues.")

    @property
    def repo_root_dir(self) -> pathlib.Path:
        return self._git_root_dir

    @property
    def git_repo(self) -> git.Repo:
        return self._git_repo

    @property
    def git_remote(self) -> git.Remote:
        return self._remote

    def check_git_state(self):
        curr_repo = self._git_repo
        if curr_repo.is_dirty(self):
            raise DirtyRepoError("There are uncommitted changes!")

    def get_latest_tag(self) -> str:
        tags = list(self.git_repo.tags)
        return tags[-1].name

    def commit_and_tag(self, old_version, new_version):
        commit_message = f"bump {old_version} --> {new_version}"
        curr_repo = self.git_repo

        # Get configuration reader for the repository
        config_reader = curr_repo.config_reader()

        # Check if user.name and user.email are set
        user_name_is_set = config_reader.has_option('user', 'name')
        user_email_is_set = config_reader.has_option('user', 'email')
        if not user_name_is_set:
            curr_repo.git.config("user.name", env.GIT_USER)
        if not user_email_is_set:
            curr_repo.git.config("user.email", env.GIT_USER_EMAIL)

        curr_repo.git.execute(["git", "commit", "-am", commit_message])
        curr_repo.git.execute(["git", "tag", "-a", new_version, "-m", commit_message])

    def push(self):
        curr_repo = self.git_repo
        self.git_remote.push(refspec=f"{curr_repo.active_branch}:{curr_repo.active_branch}")
        curr_repo.git.push()
        curr_repo.git.push("--tags")

    def create_branch(self, branch_name, push=True):
        curr_repo = self.git_repo
        curr_repo.git.checkout("-b", branch_name)
        if push:
            curr_repo.git.push("--set-upstream", "origin", branch_name)

    def get_bump_level_from_commit(self) -> BumpLevel:
        commits = list(self.git_repo.iter_commits(max_count=1))
        latest_commit = commits[0]
        msg = latest_commit.message
        for level in BumpLevel:
            if f"[{level.value}]" in msg:
                return level

        if "[pre]" in msg:
            return BumpLevel.PRE_RELEASE

        raise ValueError(f'No bump level found in commit message "{msg}"')
