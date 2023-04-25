import argparse

from bumpyproject.project import Project


def main():
    parser = argparse.ArgumentParser(description="Bump version")
    parser.add_argument(
        "--bump-level",
        choices=["major", "minor", "patch", "pre-release"],
        help="Bump level (major, minor, patch or pre-release)",
        default="pre-release",
    )
    parser.add_argument("--ignore-git-state", action="store_true", help="Ignores checking for unstaged git commit.")
    parser.add_argument(
        "--ci-git-bump",
        action="store_true",
        help="Bump level based on git commit message.",
    )
    parser.add_argument(
        "--check-pypi", action="store_true", help="Checks if the new version is higher than the latest pypi version."
    )
    parser.add_argument(
        "--check-conda", action="store_true", help="Checks if the new version is higher than the latest conda version."
    )

    args = parser.parse_args()
    Project.bump_project(args.bump_level, args.ignore_git_state, args.ci_git_bump, args.check_pypi, args.check_conda)


if __name__ == "__main__":
    main()
