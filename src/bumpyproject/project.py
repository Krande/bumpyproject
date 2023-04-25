import json

import semver
import tomlkit

from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpHelper
from bumpyproject.git_helper import GitHelper
from bumpyproject.py_distro import CondaHelper, PypiHelper


class Project:
    @staticmethod
    def bump_project(bump_level, ignore_git_state, ci_git_bump, check_pypi, check_conda):
        if ci_git_bump:
            bump_level = GitHelper.get_bump_level_from_commit()

        current_version = Project.get_pyproject_version()
        new_version = BumpHelper.bump_version(current_version, bump_level)

        if check_pypi:
            pypi_version = PypiHelper.get_latest_pypi_version()
            if not BumpHelper.is_newer(current_version, pypi_version):
                raise ValueError(f"New version {new_version} < {pypi_version}")

        if check_conda:
            conda_version = CondaHelper.get_latest_conda_version()
            if not BumpHelper.is_newer(current_version, conda_version):
                raise ValueError(f"New version {new_version} < {conda_version}")

        # Before the image is pushed we do some checks
        if not ignore_git_state:
            GitHelper.check_git_state()

        # If exists bump package.json file
        is_jsbumped = True
        if env.PKG_JSON.exists():
            is_jsbumped = Project.bump_package_json(new_version)

        # Bump pyproject.toml file
        is_pybumped = Project.bump_pyproject(new_version)

        # Commit and tag the new version
        if not ignore_git_state and (is_pybumped and is_jsbumped):
            GitHelper.commit_and_tag(current_version, new_version)

    @staticmethod
    def get_pyproject_version() -> str:
        with open(env.PYPROJECT_TOML, mode="r") as fp:
            toml_data = tomlkit.load(fp)

        old_version = toml_data["project"]["version"]

        # Convert back the pre-release tag from PEP 440 compliant to semver compliant
        if env.RELEASE_TAG in old_version:
            old_version = old_version.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

        return old_version

    @staticmethod
    def bump_pyproject(new_version) -> bool:
        with open(env.PYPROJECT_TOML, mode="r") as fp:
            toml_data = tomlkit.load(fp)

        old_version = toml_data["project"]["version"]
        if env.RELEASE_TAG in old_version:
            old_version = old_version.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

        compare = semver.compare(old_version, new_version)
        if compare == 1:
            raise ValueError(f"New version {new_version} is less than old version {old_version}")
        elif compare == 0:
            print("No version change")
            return False

        # Because PEP 440 does not allow hyphens in version numbers, we need to remove them
        if "-" in new_version:
            new_version = new_version.replace("-", "")

        toml_data["project"]["version"] = new_version
        with open(env.PYPROJECT_TOML, "w") as f:
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
