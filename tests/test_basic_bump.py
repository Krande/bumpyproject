import pytest

from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpLevelSizeError
from bumpyproject.git_helper import GitHelper
from bumpyproject import project


def test_basic_bump(mock_proj_a):
    env.IGNORE_GIT_STATE = False
    env.GIT_PUSH = True
    git_helper = GitHelper()

    assert project.get_pyproject_version() == "0.0.1"

    project.bump_project("pre-release")
    assert project.get_pyproject_version() == "0.0.2-alpha.1"
    assert git_helper.get_latest_tag() == "0.0.2-alpha.1"

    project.bump_project("patch")
    assert project.get_pyproject_version() == "0.0.3"
    assert git_helper.get_latest_tag() == "0.0.3"

    project.bump_project("minor")
    assert project.get_pyproject_version() == "0.1.0"
    assert git_helper.get_latest_tag() == "0.1.0"

    project.bump_project("major")
    assert project.get_pyproject_version() == "1.0.0"
    assert git_helper.get_latest_tag() == "1.0.0"


def test_catch_invalid_bump_level(mock_proj_a):
    """Raise exception when inadvertently trying to bump 2 levels compared with latest remote (git) version."""
    env.IGNORE_GIT_STATE = False
    env.CHECK_GIT = False
    env.GIT_PUSH = False

    assert project.get_pyproject_version() == "0.0.1"

    project.bump_project("pre-release")
    project.bump_project("pre-release")
    with pytest.raises(BumpLevelSizeError):
        GitHelper().check_git_history()


def test_invalid_bump_level_on_non_main_branch(mock_proj_a):
    env.IGNORE_GIT_STATE = False
    env.GIT_PUSH = False
    git_helper = GitHelper()

    assert project.get_pyproject_version() == "0.0.1"
    project.bump_project("pre-release")
    git_helper.push()

    git_helper.create_branch("test_branch")

    project.bump_project("pre-release")
    project.bump_project("pre-release")
    with pytest.raises(BumpLevelSizeError):
        git_helper.check_git_history()
