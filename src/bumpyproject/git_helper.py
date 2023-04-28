import git
import tomlkit
from bumpyproject import env_vars as env
from bumpyproject.versions import BumpLevel


class DirtyRepoError(Exception):
    pass


class GitHelper:
    @staticmethod
    def get_pyproject_toml_version_from_latest_pushed_commit():
        # Initialize the repo object
        repo = git.Repo(env.GIT_ROOT_DIR)

        # check if there is a remote
        remotes = list(repo.remotes)
        if len(remotes) == 0:
            return None
        elif len(remotes) > 1:
            raise ValueError("Currently only one git remote is supported.")

        remote = remotes[0]

        # If there are no pushed commits return None
        if len(remote.refs) == 0:
            return None

        # Get the latest and previous commits
        latest_commit = repo.head.commit
        # Get the last pushed commit
        all_commits = list(repo.iter_commits())

        # Get the pyproject.toml file from both commits
        try:
            latest_file = latest_commit.tree / env.PYPROJECT_TOML
        except KeyError:
            print("Error: 'pyproject.toml' not found in the latest or previous commit.")
            return

        # Read the contents of the files
        toml_data = tomlkit.parse(latest_file.data_stream.read().decode("utf-8"))

        # Get the version from the file
        return toml_data["project"]["version"]

    @staticmethod
    def check_git_state():
        curr_repo = git.Repo(env.GIT_ROOT_DIR)
        if curr_repo.is_dirty():
            raise DirtyRepoError("There are uncommitted changes!")

    @staticmethod
    def get_latest_tag() -> str:
        curr_repo = git.Repo(env.GIT_ROOT_DIR)
        tags = list(curr_repo.tags)
        return tags[-1].name

    @staticmethod
    def commit_and_tag(old_version, new_version):
        commit_message = f"bump {old_version} --> {new_version}"
        curr_repo = git.Repo(env.GIT_ROOT_DIR)
        curr_repo.git.config("user.email", env.GIT_USER_EMAIL)
        curr_repo.git.config("user.name", env.GIT_USER)
        curr_repo.git.execute(["git", "commit", "-am", commit_message])
        curr_repo.git.execute(["git", "tag", "-a", new_version, "-m", commit_message])

    @staticmethod
    def push():
        curr_repo = git.Repo(env.GIT_ROOT_DIR)
        curr_repo.git.push()
        curr_repo.git.push("--tags")

    @staticmethod
    def get_bump_level_from_commit() -> BumpLevel:
        curr_repo = git.Repo(env.GIT_ROOT_DIR)
        commits = list(curr_repo.iter_commits(max_count=1))
        latest_commit = commits[0]
        msg = latest_commit.message
        for level in BumpLevel:
            if f"[{level.value}]" in msg:
                return level

        if "[pre]" in msg:
            return BumpLevel.PRE_RELEASE

        raise ValueError(f'No bump level found in commit message "{msg}"')
