import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

RELEASE_TAG = os.environ.get("RELEASE_TAG", "alpha")
GIT_ROOT_DIR = os.getenv("GIT_ROOT_DIR", pathlib.Path(__file__).parent.parent.parent)
if isinstance(GIT_ROOT_DIR, str):
    GIT_ROOT_DIR = pathlib.Path(GIT_ROOT_DIR)

# CLI arguments (that also have env variables)
IGNORE_GIT_STATE = os.getenv("IGNORE_GIT_STATE", False)
CI_GIT_BUMP = os.getenv("CI_GIT_BUMP", False)
CHECK_PYPI = os.getenv("CHECK_PYPI", False)
CHECK_CONDA = os.getenv("CHECK_CONDA", False)
CHECK_ACR = os.getenv("CHECK_ACR", False)
CHECK_GIT = os.getenv("CHECK_GIT", False)
GIT_PUSH = os.getenv("GIT_PUSH", False)

# Core env variables
PYPROJECT_TOML = os.getenv("PYPROJECT_TOML", "pyproject.toml")
if isinstance(PYPROJECT_TOML, str):
    PYPROJECT_TOML = pathlib.Path(PYPROJECT_TOML)

if not PYPROJECT_TOML.exists() and GIT_ROOT_DIR:
    pyproject_alt_pos = GIT_ROOT_DIR / PYPROJECT_TOML
    if pyproject_alt_pos.exists():
        PYPROJECT_TOML = pyproject_alt_pos

PKG_JSON = pathlib.Path(os.getenv("PKG_JSON", "package.json"))
ONLY_VALID_REPOS = os.getenv("VALID_REPOS", "").split(";")

# Git related env variables
GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "bumpybot@bumpyproject.com")
GIT_USER = os.getenv("GIT_USER", "bumpybot")
GIT_LOCAL_TEMP_DIR = os.getenv("GIT_LOCAL_TEMP_DIR", "temp")
if isinstance(GIT_LOCAL_TEMP_DIR, str):
    GIT_LOCAL_TEMP_DIR = pathlib.Path(GIT_LOCAL_TEMP_DIR)

# Github related env variables
GH_REPO_OWNER = os.getenv("GH_REPO_OWNER")
GH_REPO_NAME = os.getenv("GH_REPO_NAME")
GH_BRANCH_NAME = os.getenv("GH_BRANCH_NAME", "main")
GH_REPO_URL = f"git@github.com:{GH_REPO_OWNER}/{GH_REPO_NAME}.git"

# These are only applicable for any AZURE Container Registry docker resources
AZ_TENANT_ID = os.getenv("AZ_TENANT_ID")
ACR_CLIENT_ID = os.getenv("AZ_ACR_SERVICE_PRINCIPAL_USERNAME")
ACR_CLIENT_SECRET = os.getenv("AZ_ACR_SERVICE_PRINCIPAL_PASSWORD")
ACR_NAME = os.getenv("AZ_ACR_NAME")
ACR_REPO_NAME = os.getenv("AZ_ACR_REPO_NAME")

# "https://pypi.org/pypi/<packagename>/json"
PYPI_URL = os.getenv("PYPI_URL")
# "https://api.anaconda.org/package/<username/organization>/<packagename>"
CONDA_URL = os.getenv("CONDA_URL")
