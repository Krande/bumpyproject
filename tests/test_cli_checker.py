import pathlib

from typer.testing import CliRunner

from bumpyproject.cli_bumpy import app

runner = CliRunner()


def test_app(mock_proj_b):
    mock_proj_b = pathlib.Path(mock_proj_b)
    result = runner.invoke(app, [
        "docker",
        str(mock_proj_b),
        "DockerFile",
        f"--pyproject-toml={mock_proj_b / 'pyproject.toml'}",
        '--build',
        '--no-acr'
    ])
    assert result.exit_code == 0
    assert "Hello Camila" in result.stdout
    assert "Let's have a coffee in Berlin" in result.stdout
