from bumpyproject.project import Project
from bumpyproject.git_helper import GitHelper
from bumpyproject import env_vars as env


def test_basic_bump(mock_proj_a):
    env.IGNORE_GIT_STATE = False
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
