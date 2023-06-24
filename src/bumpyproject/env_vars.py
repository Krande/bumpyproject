import os
import pathlib

from dotenv import load_dotenv, find_dotenv

curr_env = '.env'
res = find_dotenv(curr_env)
if not res:
    curr_env = pathlib.Path(os.getcwd()) / '.env'

load_dotenv(curr_env)


RELEASE_TAG = os.environ.get("RELEASE_TAG", "alpha")

# Core env variables


ONLY_VALID_REPOS = os.getenv("VALID_REPOS", "").split(";")

# Git related env variables
GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "bumpybot@bumpyproject.com")
GIT_USER = os.getenv("GIT_USER", "bumpybot")
GIT_LOCAL_TEMP_DIR = os.getenv("GIT_LOCAL_TEMP_DIR", "temp")
if isinstance(GIT_LOCAL_TEMP_DIR, str):
    GIT_LOCAL_TEMP_DIR = pathlib.Path(GIT_LOCAL_TEMP_DIR)


# These are only applicable for any AZURE Container Registry docker resources
AZ_TENANT_ID = os.getenv("AZ_TENANT_ID")
ACR_CLIENT_ID = os.getenv("AZ_ACR_SERVICE_PRINCIPAL_USERNAME")
ACR_CLIENT_SECRET = os.getenv("AZ_ACR_SERVICE_PRINCIPAL_PASSWORD")
ACR_NAME = os.getenv("AZ_ACR_NAME")
ACR_REPO_NAME = os.getenv("AZ_ACR_REPO_NAME")
