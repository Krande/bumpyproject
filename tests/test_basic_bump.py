import pytest

from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpLevelSizeError
from bumpyproject.project import Project


def test_basic_bump(mock_proj_a):
    env.IGNORE_GIT_STATE = False
    env.GIT_PUSH = True

    proj = Project()

    assert proj.get_pyproject_version() == "0.0.1"

    proj.bump("pre-release")
    assert proj.get_pyproject_version() == "0.0.2-alpha.1"
    assert proj.git.get_latest_tag() == "0.0.2-alpha.1"

    proj.bump("patch")
    assert proj.get_pyproject_version() == "0.0.3"
    assert proj.git.get_latest_tag() == "0.0.3"

    proj.bump("minor")
    assert proj.get_pyproject_version() == "0.1.0"
    assert proj.git.get_latest_tag() == "0.1.0"

    proj.bump("major")
    assert proj.get_pyproject_version() == "1.0.0"
    assert proj.git.get_latest_tag() == "1.0.0"


def test_catch_invalid_bump_level(mock_proj_a):
    """Raise exception when inadvertently trying to bump 2 levels compared with latest remote (git) version."""
    env.IGNORE_GIT_STATE = False
    env.CHECK_GIT = False
    env.GIT_PUSH = False
    project = Project()
    assert project.get_pyproject_version() == "0.0.1"

    project.bump("pre-release")
    project.bump("pre-release")
    with pytest.raises(BumpLevelSizeError):
        project.check_git_history()


def test_invalid_bump_level_on_non_main_branch(mock_proj_a):
    env.IGNORE_GIT_STATE = False
    env.GIT_PUSH = False

    project = Project()
    assert project.get_pyproject_version() == "0.0.1"
    project.bump("pre-release")
    project.git.push()

    project.git.create_branch("test_branch")

    project.bump("pre-release")
    project.bump("pre-release")
    with pytest.raises(BumpLevelSizeError):
        project.check_git_history()
