from __future__ import annotations

import re
import tempfile

import typer
from typing_extensions import Annotated

from bumpyproject import project
from bumpyproject.bumper import BumpLevel
from bumpyproject.docker_helper import DockerACRHelper
from bumpyproject.git_helper import GitHelper
from bumpyproject.log_utils import logger
from bumpyproject.github_helper import set_github_actions_variable

logger.setLevel("INFO")
app = typer.Typer()

_pyproject_toml = typer.Option(None, envvar="PYPROJECT_TOML")
_package_json = typer.Option(None, envvar="PACKAGE_JSON")


@app.command()
def pyproject(
    bump_level: BumpLevel = BumpLevel.PRE_RELEASE,
    pyproject_toml: str = _pyproject_toml,
    package_json: str = _package_json,
    pypi_url: str = typer.Option(None, envvar="PYPI_URL"),
    conda_url: str = typer.Option(None, envvar="CONDA_URL"),
    check_current: bool = False,
    ga_version_output: bool = False,
    push: bool = False,
    dry_run: bool = False,
):
    proj = project.Project(
        pyproject_toml=pyproject_toml,
        package_json=package_json,
        pypi_url=pypi_url,
        conda_url=conda_url,
        ga_version_output=ga_version_output,
    )

    new_version = proj.bump(bump_level, check_current_version=check_current, dry_run=dry_run)

    if ga_version_output:
        set_github_actions_variable("VERSION", new_version)

    if push:
        proj.git.push()


@app.command()
def docker(
    context_dir: Annotated[str, typer.Option()],
    dockerfile: Annotated[str, typer.Option()],
    acr_repo_name: str = typer.Option(envvar="AZ_ACR_REPO_NAME"),
    acr_name: str = typer.Option(envvar="AZ_ACR_NAME"),
    tenant_id: str = typer.Option(envvar="AZ_TENANT_ID"),
    client_id: str = typer.Option(envvar="AZ_ACR_SERVICE_PRINCIPAL_USERNAME"),
    client_secret: str = typer.Option(envvar="AZ_ACR_SERVICE_PRINCIPAL_PASSWORD"),
    build: bool = False,
    push: bool = False,
    use_native_client=False,
    pyproject_toml: str = _pyproject_toml,
    package_json: str = _package_json,
    git_root_dir: str = typer.Option(None, envvar="GIT_ROOT_DIR"),
):
    proj = project.Project(
        root_dir=git_root_dir,
        pyproject_toml=pyproject_toml,
        package_json=package_json,
        docker_context=context_dir,
        dockerfile=dockerfile,
    )
    docker_helper = DockerACRHelper(acr_name, acr_repo_name, tenant_id, client_id, client_secret)
    docker_helper.bump_acr_docker_image(proj, build, push, use_native_client)


@app.command()
def git_file_editor(git_url: str, file_path: str, re_find_version: str, new_version: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        git_helper = GitHelper.from_git_url(git_url, temp_dir)
        file_path = git_helper.repo_root_dir / file_path
        with open(file_path, "r") as f:
            file_content = f.read()

        curr_version = re.search(re_find_version, file_content, flags=re.MULTILINE).group(1)
        new_file_content = re.sub(re_find_version, new_version, file_content, flags=re.MULTILINE)
        with open(file_path, "w") as f:
            f.write(new_file_content)

        commit_message = f"bumping version {curr_version} -> {new_version}"
        git_helper.git_repo.git.execute(["git", "commit", "-am", commit_message])
