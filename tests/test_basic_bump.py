import pytest

from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpLevelSizeError
from bumpyproject.git_helper import GitHelper
from bumpyproject.project import Project


def test_basic_bump(mock_proj_a):
    env.IGNORE_GIT_STATE = False
    env.GIT_PUSH = True

    assert Project.get_pyproject_version() == "0.0.1"

    Project.bump_project("pre-release")
    assert Project.get_pyproject_version() == "0.0.2-alpha.1"
    assert GitHelper.get_latest_tag() == "0.0.2-alpha.1"

    Project.bump_project("patch")
    assert Project.get_pyproject_version() == "0.0.3"
    assert GitHelper.get_latest_tag() == "0.0.3"

    Project.bump_project("minor")
    assert Project.get_pyproject_version() == "0.1.0"
    assert GitHelper.get_latest_tag() == "0.1.0"

    Project.bump_project("major")
    assert Project.get_pyproject_version() == "1.0.0"
    assert GitHelper.get_latest_tag() == "1.0.0"


def test_catch_invalid_bump_level(mock_proj_a):
    """Raise exception when inadvertently trying to bump 2 levels compared with latest remote (git) version."""
    env.IGNORE_GIT_STATE = False
    env.CHECK_GIT = False
    env.GIT_PUSH = False

    assert Project.get_pyproject_version() == "0.0.1"

    Project.bump_project("pre-release")
    Project.bump_project("pre-release")
    with pytest.raises(BumpLevelSizeError):
        GitHelper.check_git_history()


def test_invalid_bump_level_on_non_main_branch(mock_proj_a):
    env.IGNORE_GIT_STATE = False
    env.GIT_PUSH = False

    assert Project.get_pyproject_version() == "0.0.1"
    Project.bump_project("pre-release")
    GitHelper.push()

    GitHelper.create_branch("test_branch")

    Project.bump_project("pre-release")
    Project.bump_project("pre-release")
    with pytest.raises(BumpLevelSizeError):
        GitHelper.check_git_history()
