from __future__ import annotations

import typer
from typing_extensions import Annotated

from bumpyproject import project
from bumpyproject.bumper import BumpLevel
from bumpyproject.docker_helper import DockerACRHelper
from bumpyproject.log_utils import logger
from bumpyproject.github_helper import set_github_actions_variable

logger.setLevel("INFO")
app = typer.Typer()


@app.command()
def pyproject(
    bump_level: BumpLevel = BumpLevel.PRE_RELEASE,
    pyproject_toml: Annotated[str, typer.Option(envvar="PYPROJECT_TOML")] = None,
    package_json: Annotated[str, typer.Option(envvar="PACKAGE_JSON")] = None,
    pypi_url: Annotated[str, typer.Option(envvar="PYPI_URL")] = None,
    conda_url: Annotated[str, typer.Option(envvar="CONDA_URL")] = None,
    check_current: bool = False,
    ga_version_output: bool = False,
):
    proj = project.Project(
        pyproject_toml=pyproject_toml, package_json=package_json, pypi_url=pypi_url, conda_url=conda_url
    )
    new_version = proj.bump(bump_level, check_current_version=check_current)

    if ga_version_output:
        set_github_actions_variable("VERSION", new_version)


@app.command()
def docker(
    context_dir: Annotated[str, typer.Option()],
    dockerfile: Annotated[str, typer.Option()],
    acr_repo_name: Annotated[str, typer.Option(envvar="AZ_ACR_REPO_NAME")],
    acr_name: Annotated[str, typer.Option(envvar="AZ_ACR_NAME")],
    tenant_id: Annotated[str, typer.Option(envvar="AZ_TENANT_ID")],
    client_id: Annotated[str, typer.Option(envvar="AZ_ACR_SERVICE_PRINCIPAL_USERNAME")],
    client_secret: Annotated[str, typer.Option(envvar="AZ_ACR_SERVICE_PRINCIPAL_PASSWORD")],
    build: bool = False,
    push: bool = False,
    use_native_client=False,
    pyproject_toml: Annotated[str, typer.Option(envvar="PYPROJECT_TOML")] = None,
    package_json: Annotated[str, typer.Option(envvar="PKG_JSON")] = None,
    git_root_dir: Annotated[str, typer.Option(envvar="GIT_ROOT_DIR")] = None,
):
    proj = project.Project(
        git_root_dir=git_root_dir,
        pyproject_toml=pyproject_toml,
        package_json=package_json,
        docker_context=context_dir,
        dockerfile=dockerfile,
    )
    docker_helper = DockerACRHelper(acr_name, acr_repo_name, tenant_id, client_id, client_secret)
    docker_helper.bump_acr_docker_image(proj, build, push, use_native_client)
