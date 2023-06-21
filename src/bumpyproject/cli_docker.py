import argparse

from bumpyproject.project import Project
from bumpyproject import env_vars as env
from bumpyproject import docker_helper


def main():
    parser = argparse.ArgumentParser(description="Bump version")
    parser.add_argument(
        "--bump-level",
        choices=["major", "minor", "patch", "pre-release", "pre"],
        help="Bump level (major, minor, patch or pre-release)",
        default="pre-release",
    )
    parser.add_argument("--pyproject-toml", help="Path to pyproject.toml", default=env.PYPROJECT_TOML)
    parser.add_argument("--package-json", help="Path to package.json", default=env.PKG_JSON)
    parser.add_argument("--acr-repo-name", help="Azure ACR repository name", default=env.ACR_REPO_NAME)
    parser.add_argument("--context-dir", required=True, help="Context directory for .")
    parser.add_argument("--dockerfile", required=True, help="Dockerfile absolute or relative path (to context dir).")
    parser.add_argument("--push", action="store_true", help="Docker push.")
    parser.add_argument("--build", action="store_true", help="Docker build.")
    parser.add_argument("--use-native-client", action="store_true", help="Use native docker client.")

    args = parser.parse_args()

    if args.acr_repo_name:
        env.ACR_REPO_NAME = args.acr_repo_name

    project = Project(
        pyproject_toml=args.pyproject_toml,
        package_json=args.package_json,
        docker_context=args.context_dir,
        dockerfile=args.dockerfile,
    )

    docker_helper.bump_acr_docker_image(project, args.build, args.push, args.use_native_client)


if __name__ == "__main__":
    main()
