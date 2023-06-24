import requests

from bumpyproject.versions import get_latest_version_from_list_of_versions_by_numeric_sorting


def get_latest_pypi_version(pypi_url) -> str:
    """URL to the JSON API of the PyPI package. For example: https://pypi.org/pypi/ada-py/json"""
    # Make a GET request to the URL
    response = requests.get(pypi_url)
    data = response.json()

    latest_version = get_latest_version_from_list_of_versions_by_numeric_sorting(list(data["releases"].keys()))

    return latest_version


def get_latest_conda_version(conda_url) -> str:
    """URL to the JSON API of the Conda package. For example: https://api.anaconda.org/package/krande/ada-py"""
    # Make a GET request to the URL
    response = requests.get(conda_url)
    data = response.json()

    versions = [file["version"] for file in data["files"]]
    latest_conda_version = get_latest_version_from_list_of_versions_by_numeric_sorting(versions)

    return latest_conda_version
