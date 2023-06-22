import os

import typer
from typing_extensions import Annotated

from bumpyproject import env_vars as env
from bumpyproject import project
from bumpyproject.bumper import BumpLevel
from bumpyproject.docker_helper import DockerACRHelper
from bumpyproject.helpers import find_file_in_subdirectories

app = typer.Typer()


@app.command()
def pyproject(
        bump_level: BumpLevel = BumpLevel.PRE_RELEASE,
        pyproject_toml: Annotated[str, typer.Option(envvar="PYPROJECT_TOML")] = None,
        package_json: Annotated[str, typer.Option(envvar="PACKAGE_JSON")] = None,
        pypi_url: Annotated[str, typer.Option(envvar="PYPI_URL")] = None,
        conda_url: Annotated[str, typer.Option(envvar="CONDA_URL")] = None,
):
    if pyproject_toml is None:
        pyproject_toml = find_file_in_subdirectories(os.getcwd(), "pyproject.toml")
    if package_json is None:
        package_json = find_file_in_subdirectories(os.getcwd(), "package.json")

    proj = project.Project(pyproject_toml=pyproject_toml, package_json=package_json, pypi_url=pypi_url,
                           conda_url=conda_url)
    proj.bump(bump_level)


@app.command()
def docker(
        context_dir: Annotated[str, typer.Option()],
        dockerfile: Annotated[str, typer.Option()],
        acr_repo_name: Annotated[str, typer.Option(envvar="AZ_ACR_REPO_NAME")],
        acr_name: Annotated[str, typer.Option(envvar="AZ_ACR_NAME")] = env.ACR_NAME,
        pyproject_toml: Annotated[str, typer.Option(envvar="PYPROJECT_TOML")] = None,
        build: bool = False,
        push: bool = False,
        use_native_client=False,
        package_json: Annotated[str, typer.Option(envvar="PKG_JSON")] = None,
        tenant_id: Annotated[str, typer.Option(envvar="AZ_TENANT_ID")] = None,
        client_id: Annotated[str, typer.Option(envvar="AZ_ACR_SERVICE_PRINCIPAL_USERNAME")] = None,
        client_secret: Annotated[str, typer.Option(envvar="AZ_ACR_SERVICE_PRINCIPAL_PASSWORD")] = None,
):
    proj = project.Project(
        pyproject_toml=pyproject_toml,
        package_json=package_json,
        docker_context=context_dir,
        dockerfile=dockerfile,
    )
    docker_helper = DockerACRHelper(acr_name, acr_repo_name, tenant_id, client_id, client_secret)
    docker_helper.bump_acr_docker_image(proj, build, push, use_native_client)
