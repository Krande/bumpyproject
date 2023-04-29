import requests
from bumpyproject import env_vars as env


class PypiHelper:
    @staticmethod
    def get_latest_pypi_version() -> str:
        # Make a GET request to the URL
        response = requests.get(env.PYPI_URL)
        data = response.json()
        latest_pypi_version = data["info"]["version"]

        if "a" in latest_pypi_version:
            latest_pypi_version = latest_pypi_version.replace("a", "-alpha.")

        return latest_pypi_version


class CondaHelper:
    @staticmethod
    def get_latest_conda_version() -> str:
        # Make a GET request to the URL
        response = requests.get(env.CONDA_URL)
        data = response.json()

        latest_conda_version = data["files"][-1]["version"]
        if env.RELEASE_TAG in latest_conda_version:
            latest_conda_version = latest_conda_version.replace(env.RELEASE_TAG, f"-{env.RELEASE_TAG}")

        return latest_conda_version
