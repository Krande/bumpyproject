from enum import Enum

import semver

from bumpyproject import env_vars as env


class BumpLevel(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE_RELEASE = "pre-release"

    @classmethod
    def from_string(cls, value: str):
        keymap = {x.lower(): x for x in BumpLevel}
        # add a short-name for PRE_RELEASE
        keymap.update({"pre": BumpLevel.PRE_RELEASE})

        result = keymap.get(value.lower())
        if result is None:
            raise ValueError(f"Bump level needs to be one of {list(keymap.keys())}")

        return result


def get_latest_version_from_list_of_versions_by_numeric_sorting(versions: list[str]) -> str:
    latest_version = make_semver_compatible(versions[0])
    for ver in versions[1:]:
        semver_compatible = make_semver_compatible(ver)
        if semver.compare(semver_compatible, latest_version) == 1:
            latest_version = semver_compatible

    return latest_version


def make_semver_compatible(version: str) -> str:
    if env.RELEASE_TAG in version and "-" not in version:
        version = version.replace(env.RELEASE_TAG, f"-{env.RELEASE_TAG}")

    elif "a" in version and "-" not in version:
        version = version.replace("a", "-alpha.")

    return version


def make_pep440_compatible(version: str) -> str:
    """Because PEP 440 does not allow hyphens in version numbers, we need to remove them.
    https://peps.python.org/pep-0440/#public-version-identifiers"""
    if "-" in version:
        version = version.replace("-", "")

    return version
