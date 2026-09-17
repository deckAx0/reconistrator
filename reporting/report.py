import os
import json
import glob
from datetime import datetime, timezone


def _load_states(project_name):
    """Збирає всі JSON-снепшоти станів модулів для проєкту."""
    states = []
    for path in sorted(glob.glob(f"../projects/{project_name}/state/*.json")):
        try:
            with open(path, "r") as state_file:
                states.append(json.load(state_file))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return states


def _render_markdown(project_name, target, states):
    """Рендерить зведений .md звіт по всіх модулях таргета."""
    lines = [
        f"# Recon report — {project_name}",
        "",
        f"- **Target:** {target}",
        f"- **Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    for state in states:
        results = state.get("results", [])
        lines.append(f"## Module: {state.get('module', 'unknown')} ({len(results)} hits)")
        lines.append("")

        if not results:
            lines.append("_No results._")
            lines.append("")
            continue

        lines.append("| Path | Status | Length | Timestamp |")
        lines.append("| --- | --- | --- | --- |")
        for item in results:
            lines.append(
                f"| {item.get('path', '')} "
                f"| {item.get('status_code', '')} "
                f"| {item.get('length', '')} "
                f"| {item.get('timestamp', '')} |"
            )
        lines.append("")

    return "\n".join(lines)


def generate_report(project_name, target, report_format="md"):
    """Формує .md звіт із JSON-стану проєкту. Рендер у .html — TODO."""
    states = _load_states(project_name)

    reports_dir = f"../projects/{project_name}/reports"
    os.makedirs(reports_dir, exist_ok=True)

    report_path = f"{reports_dir}/report.md"
    with open(report_path, "w") as report_file:
        report_file.write(_render_markdown(project_name, target, states))

    if report_format == "html":
        print("[!] HTML report not implemented yet — wrote .md instead.")

    print(f"[+] Report written: {report_path}")
    return report_path
