import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

# Github related env variables
GITHUB_USER_EMAIL = os.getenv("GITHUB_USER_EMAIL", "bumpybot@bumpyproject.com")
GITHUB_USER = os.getenv("GITHUB_USER", "bumpybot")
RELEASE_TAG = os.environ.get("RELEASE_TAG", "alpha")
ROOT_DIR = os.getenv("GIT_ROOT_DIR", pathlib.Path(__file__).parent.parent.parent)
if isinstance(ROOT_DIR, str):
    ROOT_DIR = pathlib.Path(ROOT_DIR)


PYPROJECT_TOML = os.getenv("PYPROJECT_TOML", "pyproject.toml")
PKG_JSON = pathlib.Path(os.getenv("PKG_JSON", "package.json"))
ONLY_VALID_REPOS = os.getenv("VALID_REPOS", "").split(";")

# These are only applicable for any AZURE Container Registry docker resources
TENANT_ID = os.getenv("AZ_TENANT_ID")
ACR_CLIENT_ID = os.getenv("AZ_ACR_SERVICE_PRINCIPAL_USERNAME")
ACR_CLIENT_SECRET = os.getenv("AZ_ACR_SERVICE_PRINCIPAL_PASSWORD")
ACR_NAME = os.getenv("AZ_ACR_NAME")

# "https://pypi.org/pypi/<packagename>/json"
PYPI_URL = os.getenv("PYPI_URL")
# "https://api.anaconda.org/package/<username/organization>/<packagename>"
CONDA_URL = os.getenv("CONDA_URL")
