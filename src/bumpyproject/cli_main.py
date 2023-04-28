import argparse
import pathlib

from bumpyproject.project import Project
from bumpyproject import env_vars as env


def main():
    parser = argparse.ArgumentParser(description="Bump version")
    parser.add_argument(
        "--bump-level",
        choices=["major", "minor", "patch", "pre-release", "pre"],
        help="Bump level (major, minor, patch or pre-release)",
        default="pre-release",
    )
    parser.add_argument("--git-root", help="Path to git root directory", default=".")
    parser.add_argument("--ignore-git-state", action="store_true", help="Ignores checking for unstaged git commit.")
    parser.add_argument(
        "--ci-git-bump",
        action="store_true",
        help="Bump level based on git commit message.",
    )
    parser.add_argument("--git-push", action="store_true", help="Pushes changes to git.")
    parser.add_argument(
        "--check-pypi", action="store_true", help="Checks if the new version is higher than the latest pypi version."
    )
    parser.add_argument(
        "--check-conda", action="store_true", help="Checks if the new version is higher than the latest conda version."
    )
    parser.add_argument(
        "--check-acr", action="store_true", help="Checks if the new version is higher than the latest acr version."
    )
    parser.add_argument(
        "--check-git",
        action="store_true",
        help="Checks if the new version is 1 increment higher than the latest pushed git tag.",
    )

    args = parser.parse_args()
    if args.ignore_git_state:
        env.IGNORE_GIT_STATE = args.ignore_git_state

    if args.ci_git_bump:
        env.CI_GIT_BUMP = args.ci_git_bump

    if args.check_pypi:
        env.CHECK_PYPI = args.check_pypi

    if args.check_conda:
        env.CHECK_CONDA = args.check_conda

    if args.check_acr:
        env.CHECK_ACR = args.check_acr

    if args.check_git:
        env.CHECK_GIT = args.check_git

    if args.git_root:
        env.GIT_ROOT = pathlib.Path(args.git_root).resolve().absolute()

    if args.git_push:
        env.GIT_PUSH = args.git_push

    Project.bump_project(args.bump_level)


if __name__ == "__main__":
    main()
