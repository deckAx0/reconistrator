import os

PROJECTS_DIR = "../projects"


def create_project(project_name):
    project_dir = f"{PROJECTS_DIR}/{project_name}"

    if os.path.isdir(project_dir):
        print(f"Project '{project_name}' already exists. Please choose a different name.")
        return False

    create_project_files(project_name)
    return True


def create_project_files(project_name):
    # Кожен проєкт тримає JSON-стан модулів та згенеровані звіти окремо.
    for subdir in ["reports", "state"]:
        os.makedirs(f"{PROJECTS_DIR}/{project_name}/{subdir}", exist_ok=True)
