import argparse

from core.create_project import create_project


















if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconichestrator: A Reconnaissance Orchestrator")
    parser.add_argument("--target", required=True, help="Target domain or IP address for reconnaissance")
    parser.add_argument("--project-name", required=True, help="Name of the project for organizing output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--report-format", choices=["md", "html"], default="md", help="Format of the output report (default: json)")
    parser.add_argument("--config", default="config.yaml", help="Path to the configuration file (default: config.json)")

    args = parser.parse_args()

    if create_project(args.project_name):
        print(f"[+] Project '{args.project_name}' created successfully!")
    else: 
        print(f"[-] Failed to create project '{args.project_name}'. Please check for errors.")

    

    