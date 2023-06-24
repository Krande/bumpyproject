import pytest

from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpLevelSizeError
from bumpyproject.project import Project


def test_basic_bump(mock_proj_a):
    proj = Project(mock_proj_a)

    assert proj.get_pyproject_version() == "0.0.1"

    proj.bump("pre-release", git_push=True)
    assert proj.get_pyproject_version() == "0.0.2-alpha.1"
    assert proj.git.get_latest_tag() == "0.0.2-alpha.1"

    proj.bump("patch", git_push=True)
    assert proj.get_pyproject_version() == "0.0.3"
    assert proj.git.get_latest_tag() == "0.0.3"

    proj.bump("minor", git_push=True)
    assert proj.get_pyproject_version() == "0.1.0"
    assert proj.git.get_latest_tag() == "0.1.0"

    proj.bump("major", git_push=True)
    assert proj.get_pyproject_version() == "1.0.0"
    assert proj.git.get_latest_tag() == "1.0.0"


def test_catch_invalid_bump_level(mock_proj_a):
    """Raise exception when inadvertently trying to bump 2 levels compared with latest remote (git) version."""
    project = Project(mock_proj_a)
    assert project.get_pyproject_version() == "0.0.1"

    project.bump("pre-release")
    with pytest.raises(BumpLevelSizeError):
        project.bump("pre-release")


def test_invalid_bump_level_on_non_main_branch(mock_proj_a):
    project = Project(mock_proj_a)
    assert project.get_pyproject_version() == "0.0.1"
    project.bump("pre-release", git_push=True)

    project.git.create_branch("test_branch")

    project.bump("pre-release")
    with pytest.raises(BumpLevelSizeError):
        project.bump("pre-release")

