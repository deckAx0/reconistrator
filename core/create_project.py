import subprocess


def create_project(project_name):
    projects_dir = "../data/projects/"

    try:
        duplicate_check = subprocess.run(["ls", f"{projects_dir}{project_name}"], check=True, capture_output=True, text=True)
        if duplicate_check.returncode == 0:
            print(f"Project '{project_name}' already exists. Please choose a different name.")
            return False
        try:
            # Create a new directory for the project
            subprocess.run(["mkdir", "-p", f"{projects_dir}{project_name}"], check=True)
            create_project_files(project_name)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating project '{project_name}': {e}")
    except subprocess.CalledProcessError:
        # TODO: Handle the case where the project does not exist (i.e., the ls command fails)
        pass
    return False


def create_project_files(project_name):
    # TODO: Create necessary files for the project (JSON state files)
    subdirs = ["reports", "state"]

    for subdir in subdirs:
        try:
            subprocess.run(["mkdir", "-p", f"../data/projects/{project_name}/{subdir}"], check=True)
        except subprocess.CalledProcessError as e:
            pass