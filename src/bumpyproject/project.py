import json

import semver
import tomlkit

from bumpyproject import env_vars as env


class Project:
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
