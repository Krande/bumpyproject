import pathlib
import subprocess

import docker
from azure.containerregistry import ContainerRegistryClient
from azure.identity import ClientSecretCredential

from bumpyproject import env_vars as env
from bumpyproject import bumper
from bumpyproject import project

colors = {"black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34, "magenta": 35, "cyan": 36, "white": 37}


def bump_acr_docker_image(context_dir, dockerfile_name, should_build, should_push, use_native_client):
    if env.ACR_NAME is None:
        raise ValueError("ACR_NAME environment variable is not set")

    if env.ACR_REPO_NAME is None:
        raise ValueError("repository argument is not set")

    if isinstance(context_dir, str):
        context_dir = pathlib.Path(context_dir).resolve().absolute()

    pyproject_version = project.get_pyproject_version()
    current_docker_image_version = get_latest_tagged_image()
    if not bumper.is_newer(current_docker_image_version, pyproject_version):
        raise ValueError(f"New version {pyproject_version} is not newer than {current_docker_image_version}")

    # Build the Docker image
    tagged_name = f"{env.ACR_NAME}.azurecr.io/{env.ACR_REPO_NAME}:{pyproject_version}"

    if should_build or should_push:
        build(context_dir, dockerfile_name, tagged_name)

    # Push the Docker image to Azure Container Registry
    if should_push:
        push(repo=tagged_name, use_native_client=use_native_client)


def colorize_text(color, text):
    cm = colors.get(color)
    return f"\033[{cm}m" + text + "\033[0m"


def print_logs(build_logs, color="green"):
    while True:
        try:
            json_output = build_logs.__next__()
            status = json_output.get("status", None)
            stream = json_output.get("stream", None)
            if stream is not None:
                print(colorize_text(color, stream.strip()))
            elif status is not None:
                id_str = json_output.get("id", "")
                prog_str = json_output.get("progress", "").strip()
                prog_detail = json_output.get("progressDetail", "")
                if isinstance(prog_detail, dict) and len(prog_detail.keys()) == 0:
                    prog_detail = ""

                state_message = f"{id_str}: {status} {prog_str} {prog_detail}"
                print(colorize_text(color, state_message))
            elif len(json_output.keys()) > 0:
                print(json_output)
        except StopIteration:
            break
        except ValueError:
            print("Error parsing output from docker image build: %s" % json_output)


def build(context_dir, dockerfile_name, tag):
    print(f'Building docker image with tag "{tag}"...')
    print_logs(
        docker.APIClient().build(
            path=str(context_dir),
            tag=tag,
            dockerfile=str(context_dir / dockerfile_name),
            decode=True,
        )
    )
    print("Docker image build complete.")


def push(repo, use_native_client=False):
    print(f'Pushing docker image with tag "{repo}"...')
    if use_native_client:
        subprocess.run(
            [
                "docker",
                "push",
                repo,
            ]
        )
    else:
        print_logs(
            docker.APIClient().push(
                repository=repo,
                decode=True,
                auth_config={"username": env.ACR_CLIENT_ID, "password": env.ACR_CLIENT_SECRET},
                stream=True,
            )
        )
    print("Docker image push complete.")


def get_latest_tagged_image():
    if env.ACR_REPO_NAME is None:
        raise ValueError("ACR_REPO_NAME environment variable is not set")

    # Get the service principal credentials
    credential = ClientSecretCredential(
        tenant_id=env.AZ_TENANT_ID, client_id=env.ACR_CLIENT_ID, client_secret=env.ACR_CLIENT_SECRET
    )

    # Create a ContainerRegistryClient object
    acr_client = ContainerRegistryClient(
        endpoint=f"https://{env.ACR_NAME}.azurecr.io",
        credential=credential,
        audience="https://management.azure.com",
    )

    # Get the list of tags for repository
    tags = list(acr_client.list_tag_properties(repository=env.ACR_REPO_NAME))
    latest_tag = tags[-1].name
    print(f"The latest tagged image of {env.ACR_REPO_NAME} is: {latest_tag}")
    return latest_tag
