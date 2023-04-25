import argparse

from bumpyproject.docker_helper import DockerHelper


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
    parser.add_argument("--use-native-client", action="store_true", help="Use native docker client.")

    args = parser.parse_args()
    DockerHelper.bump_acr_docker_image(
        args.context_dir, args.dockerfile_name, args.repository_name, args.build, args.push, args.use_native_client
    )


if __name__ == "__main__":
    main()
