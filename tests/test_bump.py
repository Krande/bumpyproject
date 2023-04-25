from bumpyproject.project import Project
from bumpyproject.git_helper import GitHelper


def test_basic_bump(mock_proj_a):
    assert Project.get_pyproject_version() == "0.0.1"

    Project.bump_project("pre-release", False, False, False, False)
    assert Project.get_pyproject_version() == "0.0.2-alpha.1"
    assert GitHelper.get_latest_tag() == "0.0.2-alpha.1"

    Project.bump_project("patch", False, False, False, False)
    assert Project.get_pyproject_version() == "0.0.3"
    assert GitHelper.get_latest_tag() == "0.0.3"

    Project.bump_project("minor", False, False, False, False)
    assert Project.get_pyproject_version() == "0.1.0"
    assert GitHelper.get_latest_tag() == "0.1.0"

    Project.bump_project("major", False, False, False, False)
    assert Project.get_pyproject_version() == "1.0.0"
    assert GitHelper.get_latest_tag() == "1.0.0"
