import pathlib

import git
import semver
import tomlkit
from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpHelper, BumpLevelSizeError
from bumpyproject.project import Project
from bumpyproject.versions import BumpLevel
from bumpyproject.log_utils import logger


class DirtyRepoError(Exception):
    pass


class GitHelper:
    @staticmethod
    def check_git_history():
        current_version = Project.get_pyproject_version()
        git_old_version = GitHelper.get_pyproject_toml_version_from_latest_pushed_commit()
        if git_old_version is None or current_version == git_old_version:
            return None

        delta = BumpHelper.get_bump_delta(git_old_version, current_version)

        # Catch bumping more than one level
        non_ones_or_zeros = [i for i, x in enumerate(delta) if x != 0 and x != 1]
        if len(non_ones_or_zeros) > 0:
            raise BumpLevelSizeError(
                f"Cannot bump {current_version=} from {git_old_version=} because it is not a single level bump"
            )



    @staticmethod
    def get_pyproject_toml_version_from_latest_pushed_commit():
        # Initialize the repo object
        remote = GitHelper.get_git_remote()

        # If there are no pushed commits return None
        if len(remote.refs) == 0:
            return None

        # Get the last pushed commit
        latest_pushed_commit = remote.refs[0].commit

        pytoml = Project.pyproject_toml_path()
        root_dir = GitHelper.get_git_root_dir()
        toml_rel = pytoml.relative_to(root_dir)

        # Get the pyproject.toml file from both commits
        try:
            latest_file = latest_pushed_commit.tree / str(toml_rel)
        except KeyError:
            print("Error: 'pyproject.toml' not found in the latest or previous commit.")
            return

        # Read the contents of the files
        toml_data = tomlkit.parse(latest_file.data_stream.read().decode("utf-8"))

        # Get the version from the file
        version = toml_data["project"]["version"]
        version = Project.make_py_ver_semver(version)
        return version

    @staticmethod
    def check_git_state():
        curr_repo = GitHelper.get_git_repo()
        if curr_repo.is_dirty():
            raise DirtyRepoError("There are uncommitted changes!")

    @staticmethod
    def get_latest_tag() -> str:
        curr_repo = GitHelper.get_git_repo()
        tags = list(curr_repo.tags)
        return tags[-1].name

    @staticmethod
    def commit_and_tag(old_version, new_version):
        commit_message = f"bump {old_version} --> {new_version}"
        curr_repo = GitHelper.get_git_repo()
        curr_repo.git.config("user.email", env.GIT_USER_EMAIL)
        curr_repo.git.config("user.name", env.GIT_USER)
        curr_repo.git.execute(["git", "commit", "-am", commit_message])
        curr_repo.git.execute(["git", "tag", "-a", new_version, "-m", commit_message])

    @staticmethod
    def push():
        curr_repo = GitHelper.get_git_repo()
        remote = GitHelper.get_git_remote()
        remote.push(refspec=f"{curr_repo.active_branch}:{curr_repo.active_branch}")
        curr_repo.git.push()
        curr_repo.git.push("--tags")

    @staticmethod
    def create_branch(branch_name, push=True):
        curr_repo = GitHelper.get_git_repo()
        curr_repo.git.checkout("-b", branch_name)
        if push:
            curr_repo.git.push("--set-upstream", "origin", branch_name)

    @staticmethod
    def get_bump_level_from_commit() -> BumpLevel:
        curr_repo = GitHelper.get_git_repo()
        commits = list(curr_repo.iter_commits(max_count=1))
        latest_commit = commits[0]
        msg = latest_commit.message
        for level in BumpLevel:
            if f"[{level.value}]" in msg:
                return level

        if "[pre]" in msg:
            return BumpLevel.PRE_RELEASE

        raise ValueError(f'No bump level found in commit message "{msg}"')

    @staticmethod
    def get_git_root_dir():
        git_root_dir = env.GIT_ROOT_DIR
        if isinstance(git_root_dir, str):
            git_root_dir = pathlib.Path(git_root_dir)

        git_root_dir = git_root_dir.resolve().absolute()
        return git_root_dir

    @staticmethod
    def get_git_repo() -> git.Repo:
        git_root_dir = GitHelper.get_git_root_dir()
        return git.Repo(git_root_dir)

    @staticmethod
    def get_git_remote() -> git.Remote | None:
        repo = GitHelper.get_git_repo()
        remotes = list(repo.remotes)
        if len(remotes) == 0:
            return None
        elif len(remotes) > 1:
            raise ValueError("Currently only one git remote is supported.")

        return remotes[0]
