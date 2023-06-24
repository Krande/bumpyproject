from __future__ import annotations

import pathlib
import subprocess
from typing import TYPE_CHECKING

import docker
from azure.containerregistry import ContainerRegistryClient
from azure.identity import ClientSecretCredential

from bumpyproject import bumper
from bumpyproject import env_vars as env
from bumpyproject.versions import get_latest_version_from_list_of_versions_by_numeric_sorting

if TYPE_CHECKING:
    from bumpyproject.project import Project

colors = {"black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34, "magenta": 35, "cyan": 36, "white": 37}


class DockerACRHelper:
    def __init__(
            self,
            acr_name,
            acr_repo_name,
            tenant_id=env.AZ_TENANT_ID,
            client_id=env.ACR_CLIENT_ID,
            client_secret=env.ACR_CLIENT_SECRET,
    ):
        self._acr_name = acr_name
        self._acr_repo_name = acr_repo_name
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret

        if acr_name is None:
            raise ValueError("ACR_NAME environment variable is not set")

        if acr_repo_name is None:
            raise ValueError("repository argument is not set")

    @property
    def acr_name(self):
        return self._acr_name

    @property
    def acr_repo_name(self):
        return self._acr_repo_name

    def bump_acr_docker_image(self, project: Project, should_build, should_push, use_native_client):
        pyproject_version = project.get_pyproject_version()
        current_docker_image_version = self.get_latest_tagged_image()

        bumper.is_newer(current_docker_image_version, pyproject_version)

        # Build the Docker image
        tagged_name = f"{self.acr_name}.azurecr.io/{self.acr_repo_name}:{pyproject_version}"

        if should_build or should_push:
            self.build(project.docker_context, project.dockerfile, tagged_name)

        # Push the Docker image to Azure Container Registry
        if should_push:
            self.push(repo=tagged_name, use_native_client=use_native_client)

    def get_latest_tagged_image(self):
        # Get the service principal credentials
        credential = ClientSecretCredential(
            tenant_id=self._tenant_id, client_id=self._client_id, client_secret=self._client_secret
        )

        # Create a ContainerRegistryClient object
        acr_client = ContainerRegistryClient(
            endpoint=f"https://{self.acr_name}.azurecr.io",
            credential=credential,
            audience="https://management.azure.com",
        )

        # Get the list of tags for repository
        versions = [tag.name for tag in acr_client.list_tag_properties(repository=self.acr_repo_name)]
        latest_version = get_latest_version_from_list_of_versions_by_numeric_sorting(versions)

        print(f"The latest tagged image of {self.acr_repo_name} is: {latest_version}")

        return latest_version

    @staticmethod
    def build(context_dir: pathlib.Path, dockerfile: pathlib.Path, tag):
        print(f'Building docker image with tag "{tag}"...')

        # find relative path from context dir to dockerfile
        dockerfile = dockerfile.relative_to(context_dir)
        print_logs(
            docker.APIClient().build(
                path=str(context_dir),
                tag=tag,
                dockerfile=str(dockerfile),
                decode=True,
                # pull=False,
            )
        )
        print("Docker image build complete.")

    def push(self, repo, use_native_client=False):
        print(f'Pushing docker image with tag "{repo}" {use_native_client=}...')
        if self._client_id is None:
            raise ValueError("AZ_ACR_SERVICE_PRINCIPAL_USERNAME environment variable is not set")
        if self._client_secret is None:
            raise ValueError("AZ_ACR_SERVICE_PRINCIPAL_PASSWORD environment variable is not set")

        if use_native_client:
            subprocess.run(
                [
                    "docker",
                    "push",
                    repo,
                ]
            )
            return

        print_logs(
            docker.APIClient().push(
                repository=repo,
                decode=True,
                auth_config={"username": self._client_id, "password": self._client_secret},
                stream=True,
            )
        )
        print("Docker image push complete.")


def colorize_text(color, text):
    cm = colors.get(color)
    return f"\033[{cm}m" + text + "\033[0m"


class NoAuthenticationError(Exception):
    pass


def print_logs(build_logs, color="green"):
    while True:
        try:
            json_output = build_logs.__next__()
            status = json_output.get("status", None)
            stream = json_output.get("stream", None)
            if stream is not None:
                if "unauthorized: authentication required" in stream:
                    raise NoAuthenticationError("unauthorized: authentication required")
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
