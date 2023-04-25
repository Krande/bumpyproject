import os
import pathlib

import tempfile
import pytest
from distutils.dir_util import copy_tree
from bumpyproject import env_vars as env
import git

MOCK_PROJ_A_DIR = pathlib.Path(__file__).parent.parent / "files/mock_project_a"


@pytest.fixture
def mock_proj_a():
    with tempfile.TemporaryDirectory() as temp_dir:
        copy_tree(str(MOCK_PROJ_A_DIR), temp_dir)
        env.PYPROJECT_TOML = str((pathlib.Path(temp_dir) / "pyproject.toml").resolve().absolute())
        env.ROOT_DIR = pathlib.Path(temp_dir)

        # Initialize a new Git repository in the temporary directory
        repo = git.Repo.init(temp_dir)

        # Perform any Git-related operations here, e.g., adding and committing files
        repo.git.add('.')
        repo.git.commit('-m', 'Initial commit')
        yield temp_dir

