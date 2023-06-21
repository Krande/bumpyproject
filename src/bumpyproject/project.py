import json
import pathlib

import semver
import tomlkit
from bumpyproject.git_helper import GitHelper

from bumpyproject import env_vars as env


class Project:
    def __init__(self, root_dir=None, pyproject_toml=None, package_json=None, dockerfile=None, docker_context=None):
        if pyproject_toml is None:
            pyproject_toml = env.PYPROJECT_TOML

        if package_json is None:
            package_json = env.PKG_JSON

        if isinstance(pyproject_toml, str):
            pyproject_toml = pathlib.Path(pyproject_toml)

        if not pyproject_toml.exists():
            raise FileNotFoundError(f"Could not find {pyproject_toml}")

        self._root_dir = root_dir
        self._pyproject_toml = pyproject_toml.resolve().absolute()
        self._package_json = package_json
        self._git_helper = GitHelper(self.root_dir)
        self._dockerfile = dockerfile if dockerfile is None else pathlib.Path(dockerfile)
        self._docker_context = docker_context if docker_context is None else pathlib.Path(docker_context)
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

    def check_git_history(self, new_version):
        from bumpyproject import bumper

        current_version = self.get_pyproject_version()
        git_old_version = self.get_pyproject_toml_version_from_latest_pushed_commit()
        if git_old_version is None or current_version == git_old_version:
            return None

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
            latest_file = latest_pushed_commit.tree / str(toml_rel)
        except KeyError:
            print("Error: 'pyproject.toml' not found in the latest or previous commit.")
            return

        # Read the contents of the files
        toml_data = tomlkit.parse(latest_file.data_stream.read().decode("utf-8"))

        # Get the version from the file
        version = toml_data["project"]["version"]

        version = make_py_ver_semver(version)
        return version

    def bump(self, bump_level):
        from bumpyproject import py_distro
        from bumpyproject import bumper
        from bumpyproject import docker_helper

        git_helper = self.git

        if env.CI_GIT_BUMP:
            bump_level = git_helper.get_bump_level_from_commit()

        current_version = self.get_pyproject_version()

        new_version = bumper.bump_version(current_version, bump_level)

        if env.CHECK_GIT:
            self.check_git_history(new_version)

        if env.CHECK_PYPI:
            pypi_version = py_distro.get_latest_pypi_version()
            if not bumper.is_newer(current_version, pypi_version):
                raise ValueError(f"New version {new_version=} < {pypi_version=}")

        if env.CHECK_CONDA:
            conda_version = py_distro.get_latest_conda_version()
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
        is_pyproject_bumped = bump_pyproject(self.pyproject_toml_path, new_version)

        # Commit and tag the new version
        if not env.IGNORE_GIT_STATE and (is_pyproject_bumped and is_pkg_json_bumped):
            git_helper.commit_and_tag(current_version, new_version)

        # Push the new version to git
        if not env.IGNORE_GIT_STATE and env.GIT_PUSH:
            git_helper.push()

    def get_pyproject_version(self) -> str:
        with open(self.pyproject_toml_path, mode="r") as fp:
            toml_data = tomlkit.load(fp)

        old_version = toml_data["project"]["version"]
        old_version = make_py_ver_semver(old_version)

        return old_version


def make_py_ver_semver(pyver: str) -> str:
    # Convert back the pre-release tag from PEP 440 compliant to semver compliant
    if env.RELEASE_TAG in pyver and '-' not in pyver:
        pyver = pyver.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

    return pyver


def bump_pyproject(pyproject_toml_path: str | pathlib.Path, new_version: str) -> bool:
    with open(pyproject_toml_path, mode="r") as fp:
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

        git_helper = GitHelper()
        pyproject_toml = git_helper.repo_root_dir / env.PYPROJECT_TOML

    if not pyproject_toml.exists():
        raise FileNotFoundError(f"Could not find {pyproject_toml}")

    pyproject_toml = pyproject_toml.resolve().absolute()
    return pyproject_toml
