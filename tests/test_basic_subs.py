import tempfile

from bumpyproject.cli_bumpy import git_file_editor
from bumpyproject.git_helper import GitHelper


def test_repo_file_subs(mock_proj_a):
    yaml_file = "config/a_yaml_with_some_text.yaml"
    git_file_editor(mock_proj_a, yaml_file, "a_version_number: (.*)", "1.2.3")
