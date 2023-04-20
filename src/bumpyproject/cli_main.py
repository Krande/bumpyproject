import argparse
import pathlib

from bumpyproject import env_vars as env
from bumpyproject.bumper import BumpHelper
from bumpyproject.docker_helper import DockerHelper
from bumpyproject.git_helper import GitHelper
from bumpyproject.project import Project


def do_something(
    context_dir,
    dockerfile_name,
    repository,
    bump_level,
    skip_build,
    skip_push,
    ignore_git_state,
    ci_git_bump,
    use_native_client,
):

    if isinstance(context_dir, str):
        context_dir = pathlib.Path(context_dir).resolve().absolute()

    latest_tag = DockerHelper.get_latest_tagged_image(repository)
    if ci_git_bump:
        bump_level = GitHelper.get_bump_level_from_commit()

    new_version = BumpHelper.bump_version(latest_tag, bump_level)

    # Build the Docker image
    tagged_name = f"{env.ACR_NAME}.azurecr.io/{repository}:{new_version}"
    # if skip_push is True and skip_build is True:
    #     print(f"Bumping '{repository}' {latest_tag} --> {new_version}")
    #     return None

    # Before the image is pushed we do some checks
    if not ignore_git_state:
        GitHelper.check_git_state()

    # Bump pyproject.toml and package.json file
    is_jsbumped = Project.bump_package_json(new_version)
    is_pybumped = Project.bump_pyproject(new_version)

    # Commit and tag the new version
    if not ignore_git_state and (is_pybumped or is_jsbumped):
        GitHelper.commit_and_tag(latest_tag, new_version)

    if skip_build is False or skip_push is False:
        DockerHelper.build(context_dir, dockerfile_name, tagged_name)

    # Push the Docker image to Azure Container Registry
    if skip_push is False:
        DockerHelper.push(repo=f"{tagged_name}", use_native_client=use_native_client)


def main():
    parser = argparse.ArgumentParser(description="Bump version")
    parser.add_argument(
        "--bump-level",
        choices=["major", "minor", "patch", "pre-release"],
        help="Bump level (major, minor, patch or pre-release)",
        default="pre-release",
    )
    parser.add_argument("--context-dir", required=True, help="Context directory for .")
    parser.add_argument("--dockerfile-name", required=True, help="Only bump version.")
    parser.add_argument("--repository-name", required=True, help="Name of ACR repository.")
    parser.add_argument("--push", action="store_true", help="Docker push.")
    parser.add_argument("--build", action="store_true", help="Docker build.")
    parser.add_argument("--ignore-git-state", action="store_true", help="Ignores checking for unstaged git commit.")
    parser.add_argument(
        "--ci-git-bump",
        action="store_true",
        help="Bump level based on git commit message.",
    )
    parser.add_argument("--use-native-client", action="store_true", help="Use native docker client.")

    args = parser.parse_args()
    do_something(
        args.context_dir,
        args.dockerfile_name,
        args.repository_name,
        args.bump_level,
        not args.build,
        not args.push,
        args.ignore_git_state,
        args.ci_git_bump,
        args.use_native_client,
    )


if __name__ == "__main__":
    main()
