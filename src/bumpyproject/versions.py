from enum import Enum


class BumpLevel(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE_RELEASE = "pre-release"

    @classmethod
    def from_string(cls, value: str):
        keymap = {x.value.lower(): x for x in BumpLevel}
        # add a short-name for PRE_RELEASE
        keymap.update({"pre": BumpLevel.PRE_RELEASE})

        result = keymap.get(value.lower())
        if result is None:
            raise ValueError(f"Bump level needs to be one of {list(keymap.keys())}")

        return result
