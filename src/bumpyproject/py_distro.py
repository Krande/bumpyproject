import requests

from bumpyproject import env_vars as env
from bumpyproject.versions import get_latest_version_from_list_of_versions_by_numeric_sorting


def get_latest_pypi_version() -> str:
    # Make a GET request to the URL
    response = requests.get(env.PYPI_URL)
    data = response.json()

    latest_version = get_latest_version_from_list_of_versions_by_numeric_sorting(list(data["releases"].keys()))

    return latest_version


def get_latest_conda_version() -> str:
    # Make a GET request to the URL
    response = requests.get(env.CONDA_URL)
    data = response.json()

    versions = [file["version"] for file in data["files"]]
    latest_conda_version = get_latest_version_from_list_of_versions_by_numeric_sorting(versions)

    return latest_conda_version
