import os
import re
import sys
import json
import shutil
import subprocess
from tempfile import NamedTemporaryFile

# Дозволяємо імпорт спільних хелперів із core/ незалежно від точки запуску.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core"))
from utils import make_result, passes_filters, save_state

MODULE_NAME = "directories"


def _run(cmd, verbose, capture=False):
    """Запускає зовнішню утиліту. Повертає stdout (capture) або bool успіху."""
    if verbose:
        print("[*] " + " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print(f"[-] Failed to launch: {cmd[0]}")
        return None if capture else False
    if proc.returncode != 0 and verbose and proc.stderr:
        print(proc.stderr.strip())
    return proc.stdout if capture else True


class FfufEngine:
    """Рушій на базі ffuf: вивід у JSON, парситься з масиву results."""

    @staticmethod
    def run(binary, target, wordlist, config, tool_cfg, verbose):
        http = config["http"]
        out = NamedTemporaryFile(prefix="ffuf_", suffix=".json", delete=False)
        out.close()

        cmd = [
            binary,
            "-u", f"{target}/FUZZ",
            "-w", wordlist,
            "-t", str(http["threads"]),
            "-timeout", str(http["timeout"]),
            "-of", "json", "-o", out.name,
            "-s",
        ]
        for name, value in http.get("headers", {}).items():
            cmd += ["-H", f"{name}: {value}"]
        exclude = config["filters"].get("status_exclude", [])
        if exclude:
            cmd += ["-fc", ",".join(str(code) for code in exclude)]
        cmd += tool_cfg.get("extra_args", [])

        _run(cmd, verbose)
        try:
            with open(out.name) as report:
                data = report.read()
        except FileNotFoundError:
            data = ""
        finally:
            if os.path.exists(out.name):
                os.unlink(out.name)
        return data

    @staticmethod
    def parse(raw):
        data = json.loads(raw) if raw.strip() else {}
        return [
            {
                "path": item.get("input", {}).get("FUZZ", item.get("url", "")),
                "status": item.get("status", 0),
                "length": item.get("length", 0),
            }
            for item in data.get("results", [])
        ]


class GobusterEngine:
    """Рушій на базі gobuster dir: текстовий вивід парситься регуляркою."""

    LINE = re.compile(r"^(\S+)\s+\(Status:\s*(\d+)\)\s+\[Size:\s*(\d+)\]")

    @staticmethod
    def run(binary, target, wordlist, config, tool_cfg, verbose):
        http = config["http"]
        cmd = [
            binary, "dir",
            "-u", target,
            "-w", wordlist,
            "-t", str(http["threads"]),
            "--timeout", f"{http['timeout']}s",
            "-q", "--no-progress", "--no-color",
        ]
        for name, value in http.get("headers", {}).items():
            cmd += ["-H", f"{name}: {value}"]
        cmd += tool_cfg.get("extra_args", [])
        return _run(cmd, verbose, capture=True) or ""

    @classmethod
    def parse(cls, raw):
        hits = []
        for line in raw.splitlines():
            match = cls.LINE.match(line.strip())
            if match:
                hits.append({
                    "path": match.group(1),
                    "status": int(match.group(2)),
                    "length": int(match.group(3)),
                })
        return hits


# Реєстр підтримуваних утиліт — сюди легко додати новий рушій.
ENGINES = {
    "ffuf": FfufEngine,
    "gobuster": GobusterEngine,
}


def find_directories(target, project_name, wordlist_path, config, verbose=False):
    """Оркеструє зовнішній fuzzer (ffuf/gobuster) для перебору директорій.

    Модуль сам не сканує: будує команду за config.json, запускає утиліту,
    нормалізує її вивід у єдиний формат і зберігає у стан проєкту.
    """
    if not os.path.isfile(wordlist_path):
        print(f"[-] Wordlist not found: {wordlist_path}")
        return []

    tool_cfg = config.get("tools", {}).get("directories", {})
    engine_name = tool_cfg.get("engine", "ffuf")
    engine = ENGINES.get(engine_name)
    if engine is None:
        print(f"[-] Unknown directories engine: {engine_name} (available: {list(ENGINES)})")
        return []

    binary = tool_cfg.get("binary") or engine_name
    if shutil.which(binary) is None:
        print(f"[-] Tool not found in PATH: {binary}")
        return []

    print(f"[*] Directory bruteforce via {engine_name} on {target}")
    raw_output = engine.run(binary, target, wordlist_path, config, tool_cfg, verbose)

    results = []
    for hit in engine.parse(raw_output):
        if not passes_filters(hit["status"], hit["length"], config["filters"]):
            continue
        if verbose:
            print(f"[+] {hit['status']}  {hit['length']:>7}  {target}/{hit['path']}")
        results.append(make_result(target, MODULE_NAME, hit["path"], hit["status"], hit["length"]))

    save_state(project_name, MODULE_NAME, target, results)
    print(f"[+] Directory bruteforce ({engine_name}) done: {len(results)} hits saved.")
    return results
