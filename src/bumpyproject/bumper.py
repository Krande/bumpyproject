import semver

from bumpyproject import env_vars as env
from bumpyproject.versions import BumpLevel


class BumpHelper:
    @staticmethod
    def is_newer(old_version: str, new_version: str) -> bool:
        if env.RELEASE_TAG in old_version:
            old_version = old_version.replace(env.RELEASE_TAG, "-" + env.RELEASE_TAG)

        compare = semver.compare(old_version, new_version)
        if compare == 1:
            raise ValueError(f"Next bump is outdated! {new_version=} < {old_version=}")
        elif compare == 0:
            raise ValueError(f"No version change {new_version=} == {old_version=}")

        return True

    @staticmethod
    def bump_version(current_version: str | BumpLevel, bump_level: str | BumpLevel) -> str:
        if isinstance(bump_level, str):
            bump_level = BumpLevel.from_string(bump_level)

        # Have to replace 'next' with 'alpha' because PEP doesn't support 'next'
        if "next" in current_version:
            current_version = current_version.replace("next", "alpha")

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
