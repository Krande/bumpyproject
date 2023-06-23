import os


def set_github_actions_variable(var_name, var_value):
    env_file = os.environ.get("GITHUB_OUTPUT", None)
    if env_file is None:
        raise ValueError("GITHUB_OUTPUT environment variable not set")

    with open(env_file, "a") as my_file:
        my_file.write(f"{var_name}={var_value}\n")
