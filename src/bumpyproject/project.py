import json
import os
import pathlib

import semver
import tomlkit

from bumpyproject import bumper
from bumpyproject import docker_helper
from bumpyproject import env_vars as env
from bumpyproject import py_distro
from bumpyproject.bumper import NoVersionChangeError, OutdatedBumpError
from bumpyproject.git_helper import GitHelper
from bumpyproject.github_helper import set_github_actions_variable
from bumpyproject.helpers import find_file_in_subdirectories
from bumpyproject.versions import make_semver_compatible, make_pep440_compatible
from bumpyproject.log_utils import logger


class Project:
    def __init__(
            self,
            root_dir=None,
            pyproject_toml=None,
            package_json=None,
            dockerfile=None,
            docker_context=None,
            pypi_url=None,
            conda_url=None,
            ga_version_output=False,
    ):
        if root_dir is None:
            root_dir = os.getcwd()

        if pyproject_toml is None:
            pyproject_toml = find_file_in_subdirectories(root_dir, "pyproject.toml")

        if package_json is None:
            try:
                package_json = find_file_in_subdirectories(root_dir, "package.json")
            except FileNotFoundError:
                package_json = "package.json"

        if isinstance(pyproject_toml, str):
            pyproject_toml = pathlib.Path(pyproject_toml)

        if isinstance(package_json, str):
            package_json = pathlib.Path(package_json)

        if not pyproject_toml.exists():
            raise FileNotFoundError(f"Could not find {pyproject_toml}")

        self._root_dir = root_dir
        self._pyproject_toml = pyproject_toml.resolve().absolute()
        self._package_json = package_json
        self._git_helper = GitHelper(self.root_dir)
        self._dockerfile = dockerfile if dockerfile is None else pathlib.Path(dockerfile)
        self._docker_context = docker_context if docker_context is None else pathlib.Path(docker_context)
        self.pypi_url = pypi_url
        self.conda_url = conda_url
        self._ga_version_output = ga_version_output

        if self._dockerfile is not None and not self._dockerfile.exists():
            if self._docker_context is not None:
                self._dockerfile = self._docker_context / self._dockerfile.name
            if not self._dockerfile.exists():
                raise FileNotFoundError(f"Could not find {self._dockerfile}")

            self._dockerfile = self._dockerfile.absolute().resolve()
            self._docker_context = self._docker_context.absolute().resolve()

    @property
    def pyproject_toml_path(self):
        return self._pyproject_toml

    @property
    def package_json_path(self):
        return self._package_json

    @property
    def root_dir(self):
        return self._root_dir

    @property
    def git(self) -> GitHelper:
        return self._git_helper

    @property
    def dockerfile(self) -> pathlib.Path | None:
        return self._dockerfile

    @property
    def docker_context(self) -> pathlib.Path | None:
        return self._docker_context

    def check_git_history(self, new_version=None):
        from bumpyproject import bumper

        current_version = self.get_pyproject_version()
        git_old_version = self.get_pyproject_toml_version_from_latest_pushed_commit()
        if git_old_version is None or current_version == git_old_version:
            return None

        if new_version is None:
            new_version = current_version

        delta = bumper.get_bump_delta(git_old_version, new_version)

        # Catch bumping more than one level
        non_ones_or_zeros = [i for i, x in enumerate(delta) if x != 0 and x != 1]
        if len(non_ones_or_zeros) > 0:
            raise bumper.BumpLevelSizeError(
                f"Cannot bump to {new_version=} from {git_old_version=} because it is not a single level bump"
            )

    def get_pyproject_toml_version_from_latest_pushed_commit(self):
        # Initialize the repo object
        remote = self.git.git_remote

        # If there are no pushed commits return None
        if len(remote.refs) == 0:
            return None

        active_local_branch = self.git.git_repo.active_branch.name
        remote_head = None
        for ref in remote.refs:
            if ref.remote_head == active_local_branch:
                remote_head = ref
                break

        # Get the last pushed commit to active branch
        latest_pushed_commit = remote_head.commit

        pytoml = self.pyproject_toml_path

        toml_rel = pytoml.relative_to(self.git.repo_root_dir)

        # Get the pyproject.toml file from both commits
        try:
            latest_file = latest_pushed_commit.tree / str(toml_rel.as_posix())
        except KeyError as e:
            print(f"Error: {e} 'pyproject.toml' not found in the latest or previous commit.")
            return

        # Read the contents of the files
        toml_data = tomlkit.parse(latest_file.data_stream.read().decode("utf-8"))

        # Get the version from the file
        version = toml_data["project"]["version"]

        version = make_semver_compatible(version)
        return version

    def bump(
            self, bump_level, check_git=True, ignore_git_state=False, git_push=False, check_current_version=False,
            dry_run=False
    ) -> str:
        git_helper = self.git

        current_version = self.get_pyproject_version()

        if check_current_version:
            new_version = current_version
        else:
            new_version = bumper.bump_version(current_version, bump_level)

        if check_git:
            self.check_git_history(new_version)

        if self.pypi_url is not None:
            pypi_version = py_distro.get_latest_pypi_version(self.pypi_url)
            try:
                bumper.is_newer(pypi_version, new_version)
                if self._ga_version_output:
                    set_github_actions_variable("PYPIBUMP", "TRUE")
                logger.info(f"Latest version on PyPI '{pypi_version}' OK for push to '{new_version}'")
            except (OutdatedBumpError, NoVersionChangeError) as e:
                if self._ga_version_output:
                    set_github_actions_variable("PYPIBUMP", "FALSE")
                    logger.info(f"Latest version on PyPI '{pypi_version}' NOT OK for push to '{new_version}'")
                else:
                    raise e

        if self.conda_url is not None:
            conda_version = py_distro.get_latest_conda_version(self.conda_url)
            try:
                bumper.is_newer(conda_version, new_version)
                if self._ga_version_output:
                    set_github_actions_variable("CONDABUMP", "TRUE")
                logger.info(f"Latest version on Conda '{conda_version}' OK for push to '{new_version}'")
            except (OutdatedBumpError, NoVersionChangeError) as e:
                if self._ga_version_output:
                    set_github_actions_variable("CONDABUMP", "FALSE")
                    logger.info(f"Latest version on Conda '{conda_version}' NOT OK for push to '{new_version}'")
                else:
                    raise e

        check_acr = env.ACR_NAME is not None and env.ACR_REPO_NAME is not None
        if check_acr:
            acr_version = docker_helper.DockerACRHelper(env.ACR_NAME, env.ACR_REPO_NAME).get_latest_tagged_image()
            bumper.is_newer(acr_version, new_version)
            logger.info(f"Latest version on ACR '{acr_version}' OK for push to '{new_version}'")

        if check_current_version:
            logger.info(f"Current version '{current_version}' is ready to be pushed.")
            return new_version

            # Before the image is pushed we do some checks
        if not ignore_git_state:
            git_helper.check_git_state()

        if dry_run:
            logger.info(f"Dry run: Version '{new_version}' would be pushed.")
            return new_version

        # If exists bump package.json file
        is_pkg_json_bumped = True
        if self.package_json_path.exists():
            is_pkg_json_bumped = bump_package_json(self.package_json_path, new_version)

        # Bump pyproject.toml file
        is_pyproject_bumped = bump_pyproject(self.pyproject_toml_path, new_version)

        # Commit and tag the new version
        if not ignore_git_state and (is_pyproject_bumped and is_pkg_json_bumped):
            git_helper.commit_and_tag(current_version, new_version)

        # Push the new version to git
        if git_push:
            git_helper.push()

        return new_version

    def get_pyproject_version(self) -> str:
        with open(self.pyproject_toml_path, mode="r") as fp:
            toml_data = tomlkit.load(fp)

        old_version = toml_data["project"]["version"]
        old_version = make_semver_compatible(old_version)

        return old_version


def bump_pyproject(pyproject_toml_path: str | pathlib.Path, new_version: str) -> bool:
    with open(pyproject_toml_path, mode="r") as fp:
        toml_data = tomlkit.load(fp)

    old_version = toml_data["project"]["version"]

    old_version = make_semver_compatible(old_version)
    compare = semver.Version.compare(semver.Version.parse(old_version), semver.Version.parse(new_version))
    if compare == 1:
        raise ValueError(f"New version {new_version} is less than old version {old_version}")
    elif compare == 0:
        print("No version change")
        return False

    new_version = make_pep440_compatible(new_version)
    toml_data["project"]["version"] = new_version
    with open(pyproject_toml_path, "w") as f:
        f.write(tomlkit.dumps(toml_data))

    return True


def bump_package_json(package_json, new_version) -> bool:
    with open(package_json, "r") as f:
        data = json.load(f)

    old_version = data["version"]
    compare = semver.compare(old_version, new_version)
    if compare == 1:
        raise ValueError(f"New version {new_version} is less than old version {old_version}")
    elif compare == 0:
        print("No version change")
        return False

    data["version"] = new_version
    with open(package_json, "w") as f:
        json.dump(data, f, indent=2)

    return True
