import json
import pathlib

import semver
import tomlkit

from bumpyproject import env_vars as env
from bumpyproject.log_utils import logger


class Project:
    def __init__(self, pyproject_toml=None, package_json=None):
        if pyproject_toml is None:
            pyproject_toml = env.PYPROJECT_TOML

        if package_json is None:
            package_json = env.PKG_JSON

        if isinstance(pyproject_toml, str):
            pyproject_toml = pathlib.Path(pyproject_toml)

        if not pyproject_toml.exists():
            raise FileNotFoundError(f"Could not find {pyproject_toml}")

        self._pyproject_toml = pyproject_toml.resolve().absolute()
        self._package_json = package_json

    @property
    def pyproject_toml_path(self):
        return self._pyproject_toml


def bump_project(bump_level):
    from bumpyproject.git_helper import GitHelper
    from bumpyproject.py_distro import CondaHelper, PypiHelper
    from bumpyproject import bumper
    from bumpyproject import docker_helper

    git_helper = GitHelper(env.GIT_ROOT_DIR)

    if env.CI_GIT_BUMP:
        bump_level = git_helper.get_bump_level_from_commit()

    current_version = get_pyproject_version()

    if env.CHECK_GIT:
        git_helper.check_git_history()

    new_version = bumper.bump_version(current_version, bump_level)

    if env.CHECK_PYPI:
        pypi_version = PypiHelper.get_latest_pypi_version()
        if not bumper.is_newer(current_version, pypi_version):
            raise ValueError(f"New version {new_version=} < {pypi_version=}")

    if env.CHECK_CONDA:
        conda_version = CondaHelper.get_latest_conda_version()
        if not bumper.is_newer(current_version, conda_version):
            raise ValueError(f"New version {new_version=} < {conda_version=}")

    if env.CHECK_ACR:
        acr_version = docker_helper.get_latest_tagged_image()
        if not bumper.is_newer(current_version, acr_version):
            raise ValueError(f"New version {new_version=} < {acr_version=}")

    # Before the image is pushed we do some checks
    if not env.IGNORE_GIT_STATE:
        git_helper.check_git_state()

    # If exists bump package.json file
    is_pkg_json_bumped = True
    if env.PKG_JSON.exists():
        is_pkg_json_bumped = bump_package_json(new_version)

    # Bump pyproject.toml file
    is_pyproject_bumped = bump_pyproject(new_version)

    # Commit and tag the new version
    if not env.IGNORE_GIT_STATE and (is_pyproject_bumped and is_pkg_json_bumped):
        git_helper.commit_and_tag(current_version, new_version)

    # Push the new version to git
    if not env.IGNORE_GIT_STATE and env.GIT_PUSH:
        git_helper.push()


def make_py_ver_semver(pyver: str) -> str:
    # Convert back the pre-release tag from PEP 440 compliant to semver compliant
    if env.RELEASE_TAG in pyver:
        pyver = pyver.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

    return pyver


def get_pyproject_version() -> str:
    with open(get_pyproject_toml_path_from_env(), mode="r") as fp:
        toml_data = tomlkit.load(fp)

    old_version = toml_data["project"]["version"]
    old_version = make_py_ver_semver(old_version)

    return old_version


def bump_pyproject(new_version) -> bool:
    with open(get_pyproject_toml_path_from_env(), mode="r") as fp:
        toml_data = tomlkit.load(fp)

    old_version = toml_data["project"]["version"]
    if env.RELEASE_TAG in old_version:
        old_version = old_version.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

    compare = semver.Version.compare(semver.Version.parse(old_version), semver.Version.parse(new_version))
    if compare == 1:
        raise ValueError(f"New version {new_version} is less than old version {old_version}")
    elif compare == 0:
        print("No version change")
        return False

    # Because PEP 440 does not allow hyphens in version numbers, we need to remove them
    if "-" in new_version:
        new_version = new_version.replace("-", "")

    toml_data["project"]["version"] = new_version
    with open(get_pyproject_toml_path_from_env(), "w") as f:
        f.write(tomlkit.dumps(toml_data))

    return True


def bump_package_json(new_version) -> bool:
    with open(env.PKG_JSON, "r") as f:
        data = json.load(f)

    old_version = data["version"]
    compare = semver.compare(old_version, new_version)
    if compare == 1:
        raise ValueError(f"New version {new_version} is less than old version {old_version}")
    elif compare == 0:
        print("No version change")
        return False

    data["version"] = new_version
    with open(env.PKG_JSON, "w") as f:
        json.dump(data, f, indent=2)

    return True


def get_pyproject_toml_path_from_env() -> pathlib.Path:
    pyproject_toml = env.PYPROJECT_TOML

    if isinstance(pyproject_toml, str):
        pyproject_toml = pathlib.Path(pyproject_toml)

    if not pyproject_toml.exists():
        from bumpyproject.git_helper import GitHelper

        pyproject_toml = GitHelper.get_git_root_dir() / env.PYPROJECT_TOML

    if not pyproject_toml.exists():
        raise FileNotFoundError(f"Could not find {pyproject_toml}")

    pyproject_toml = pyproject_toml.resolve().absolute()
    return pyproject_toml
