import os
import pathlib

import tempfile
import pytest
from distutils.dir_util import copy_tree
from bumpyproject import env_vars as env
import git

FILES_DIR = pathlib.Path(__file__).parent.parent / "files"
MOCK_PROJ_A_DIR = FILES_DIR / "mock_project_a"
MOCK_PROJ_B_DIR = FILES_DIR / "mock_project_b"


@pytest.fixture(scope="function")
def project_b_dir():
    return MOCK_PROJ_B_DIR


def create_mock_project(mock_project_path):
    # Create a temporary directory for the remote repository
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize the remote repository
        remote_repo = git.Repo.init(os.path.join(temp_dir, "remote_repo.git"), bare=True)

        # Create a temporary directory for the local repository
        with tempfile.TemporaryDirectory() as local_temp_dir:
            copy_tree(str(mock_project_path), local_temp_dir)
            os.environ['PYPROJECT_TOML'] = str((pathlib.Path(local_temp_dir) / "pyproject.toml").resolve().absolute())
            os.environ['GIT_ROOT_DIR'] = local_temp_dir

            # Initialize a new Git repository in the temporary directory
            local_repo = git.Repo.init(local_temp_dir)

            # Add the remote repository
            local_repo.create_remote("origin", url=remote_repo.git_dir)
            curr_branch = local_repo.active_branch

            # Add the username and email
            local_repo.git.config("user.email", env.GIT_USER_EMAIL)
            local_repo.git.config("user.name", env.GIT_USER)

            # Perform any Git-related operations here, e.g., adding and committing files
            local_repo.git.add(".")
            local_repo.git.execute(["git", "commit", "-am", "Initial Commit"])
            local_repo.git.push("origin", curr_branch.name, set_upstream=True)
            yield local_temp_dir


@pytest.fixture(scope="function")
def mock_proj_a():
    yield from create_mock_project(MOCK_PROJ_A_DIR)


@pytest.fixture(scope="function")
def mock_proj_b():
    yield from create_mock_project(MOCK_PROJ_B_DIR)
