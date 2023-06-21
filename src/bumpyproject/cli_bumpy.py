import typer

from bumpyproject import env_vars as env
from bumpyproject.docker_helper import DockerACRHelper
from bumpyproject import project
from bumpyproject.bumper import BumpLevel
from typing_extensions import Required, Annotated

app = typer.Typer()


@app.command()
def pyproject(
    pyproject_toml: str = env.PYPROJECT_TOML,
    package_json: str = env.PKG_JSON,
    bump_level: BumpLevel = BumpLevel.PRE_RELEASE,
):
    proj = project.Project(pyproject_toml=pyproject_toml, package_json=package_json)
    proj.bump(bump_level)


@app.command()
def docker(
    context_dir: Annotated[str, typer.Option()],
    dockerfile: Annotated[str, typer.Option()],
    acr_repo_name: Annotated[str, typer.Option(envvar="AZ_ACR_REPO_NAME")],
    acr_name: Annotated[str, typer.Option(envvar="AZ_ACR_NAME")] = env.ACR_NAME,
    pyproject_toml: str = env.PYPROJECT_TOML,
    build=False,
    push=False,
    use_native_client=False,
    package_json: str = env.PKG_JSON,
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
