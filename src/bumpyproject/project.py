import json
import pathlib

import semver
import tomlkit

from bumpyproject import env_vars as env
from bumpyproject.log_utils import logger


class Project:
    @staticmethod
    def bump_project(bump_level):
        from bumpyproject.git_helper import GitHelper
        from bumpyproject.py_distro import CondaHelper, PypiHelper
        from bumpyproject.bumper import BumpHelper
        from bumpyproject.docker_helper import DockerHelper

        if env.CI_GIT_BUMP:
            bump_level = GitHelper.get_bump_level_from_commit()

        current_version = Project.get_pyproject_version()

        git_old_version = GitHelper.get_pyproject_toml_version_from_latest_pushed_commit()
        if git_old_version is not None and current_version != git_old_version:
            old_sv, git_old_sv = semver.Version.parse(current_version), semver.Version.parse(git_old_version)
            logger.warning(f"Latest git commit version {current_version=} != {git_old_version=} from git")
            res = old_sv - git_old_sv
            print('sd')

        new_version = BumpHelper.bump_version(current_version, bump_level)

        if env.CHECK_PYPI:
            pypi_version = PypiHelper.get_latest_pypi_version()
            if not BumpHelper.is_newer(current_version, pypi_version):
                raise ValueError(f"New version {new_version=} < {pypi_version=}")

        if env.CHECK_CONDA:
            conda_version = CondaHelper.get_latest_conda_version()
            if not BumpHelper.is_newer(current_version, conda_version):
                raise ValueError(f"New version {new_version=} < {conda_version=}")

        if env.CHECK_ACR:
            acr_version = DockerHelper.get_latest_tagged_image()
            if not BumpHelper.is_newer(current_version, acr_version):
                raise ValueError(f"New version {new_version=} < {acr_version=}")

        # Before the image is pushed we do some checks
        if not env.IGNORE_GIT_STATE:
            GitHelper.check_git_state()

        # If exists bump package.json file
        is_pkg_json_bumped = True
        if env.PKG_JSON.exists():
            is_pkg_json_bumped = Project.bump_package_json(new_version)

        # Bump pyproject.toml file
        is_pyproject_bumped = Project.bump_pyproject(new_version)

        # Commit and tag the new version
        if not env.IGNORE_GIT_STATE and (is_pyproject_bumped and is_pkg_json_bumped):
            GitHelper.commit_and_tag(current_version, new_version)

        # Push the new version to git
        if not env.IGNORE_GIT_STATE and env.GIT_PUSH:
            GitHelper.push()

    @staticmethod
    def make_py_ver_semver(pyver: str) -> str:
        # Convert back the pre-release tag from PEP 440 compliant to semver compliant
        if env.RELEASE_TAG in pyver:
            pyver = pyver.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

        return pyver

    @staticmethod
    def get_pyproject_version() -> str:
        with open(Project.pyproject_toml_path(), mode="r") as fp:
            toml_data = tomlkit.load(fp)

        old_version = toml_data["project"]["version"]
        old_version = Project.make_py_ver_semver(old_version)

        return old_version

    @staticmethod
    def bump_pyproject(new_version) -> bool:
        with open(Project.pyproject_toml_path(), mode="r") as fp:
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
        with open(Project.pyproject_toml_path(), "w") as f:
            f.write(tomlkit.dumps(toml_data))

        return True

    @staticmethod
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

    @staticmethod
    def pyproject_toml_path() -> pathlib.Path:
        pyproject_toml = env.PYPROJECT_TOML

        if isinstance(pyproject_toml, str):
            pyproject_toml = pathlib.Path(env.PYPROJECT_TOML).resolve()

        if not pyproject_toml.exists():
            pyproject_toml = env.GIT_ROOT_DIR / env.PYPROJECT_TOML

        if not pyproject_toml.exists():
            raise FileNotFoundError(f"Could not find {env.PYPROJECT_TOML}")

        return pyproject_toml
