import semver

from bumpyproject import env_vars as env
from bumpyproject.versions import BumpLevel


class BumpLevelSizeError(Exception):
    pass


def version_to_tuple(version: str) -> tuple:
    ver = semver.VersionInfo.parse(version).to_tuple()
    output = []
    for x in ver:
        if x is None:
            output.append(0)
        elif isinstance(x, int):
            output.append(x)
        elif env.RELEASE_TAG in x:
            res = int(float(x.split(".")[-1]))
            output.append(res)
        else:
            raise ValueError(f"Invalid version tuple {ver}")

    return tuple(output)


def get_bump_delta(old_version: str, new_version: str) -> list[int, int, int, int, int]:
    new_tuple, old_tuple = version_to_tuple(new_version), version_to_tuple(old_version)
    res = [x - y for x, y in zip(new_tuple, old_tuple)]
    return res


def is_newer(old_version: str, new_version: str) -> bool:
    if env.RELEASE_TAG in old_version:
        old_version = old_version.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

    compare = semver.compare(old_version, new_version)
    if compare == 1:
        raise ValueError(f"Next bump is outdated! {new_version=} < {old_version=}")
    elif compare == 0:
        raise ValueError(f"No version change {new_version=} == {old_version=}")

    return True


def bump_version(current_version: str | BumpLevel, bump_level: str | BumpLevel) -> str:
    if isinstance(bump_level, str):
        bump_level = BumpLevel.from_string(bump_level)

    ver = semver.VersionInfo.parse(current_version)
    if bump_level == BumpLevel.MAJOR:
        ver = ver.bump_major()
    elif bump_level == BumpLevel.MINOR:
        ver = ver.bump_minor()
    elif bump_level == BumpLevel.PATCH:
        ver = ver.bump_patch()
    elif bump_level == BumpLevel.PRE_RELEASE:
        if ver.prerelease is None:
            ver = ver.bump_patch()
        ver = ver.bump_prerelease(env.RELEASE_TAG)
    else:
        raise ValueError(f"Invalid bump level '{bump_level}'")

    return str(ver)
