import os
import sys
import argparse

# Доступ до пакетів modules/ та reporting/ при запуску скрипта з core/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from create_project import create_project
from config import load_config
from utils import normalize_url
from modules.active_recon.endpoints import find_directories
from reporting.report import generate_report


if __name__ == "__main__":
    DEFAULT_CONFIG_PATH = "../config/"

    parser = argparse.ArgumentParser(description="Reconichestrator: A Reconnaissance Orchestrator")
    parser.add_argument("--target", required=True, help="Target domain or IP address for reconnaissance")
    parser.add_argument("--project-name", required=True, help="Name of the project for organizing output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--report-format", choices=["md", "html"], default="md", help="Format of the output report (default: md)")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH + "config.json", help="Path to the configuration file (default: " + DEFAULT_CONFIG_PATH + "config.json)")

    args = parser.parse_args()

    if create_project(args.project_name):
        print(f"[+] Project '{args.project_name}' created successfully!")
    else:
        print(f"[-] Failed to create project '{args.project_name}'. Please check for errors.")
        exit(1)

    config = load_config(args.config)
    if config is None:
        exit(1)
    print(f"[+] Configuration loaded successfully from '{args.config}'")

    target = normalize_url(args.target)
    endpoints_wordlist = config["wordlist"]["endpoints"]

    # Фіча 1: brute force директорій → JSON-стан проєкту.
    find_directories(target, args.project_name, endpoints_wordlist, config, args.verbose)

    # Фіча 4: звіт із JSON-стану у .md.
    generate_report(args.project_name, target, args.report_format)
