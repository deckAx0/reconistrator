import os
import re
import sys
import shutil
import subprocess

# Дозволяємо імпорт спільних хелперів із core/ незалежно від точки запуску.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core"))
from core.utils import ffuf_scan, collect_results, save_state, read_words

MODULE_NAME = "directories"


class FfufEngine:
    """Рушій на базі ffuf: FUZZ підставляється у шлях цілі."""

    @staticmethod
    def scan(binary, target, wordlist, config, tool_cfg, verbose):
        words = set(read_words(wordlist))
        return ffuf_scan(binary, f"{target}/FUZZ", wordlist, config, tool_cfg, verbose,
                         keep=lambda fuzz: fuzz in words)


class GobusterEngine:
    """Рушій на базі gobuster dir: текстовий вивід парситься регуляркою."""

    LINE = re.compile(r"^(\S+)\s+\(Status:\s*(\d+)\)\s+\[Size:\s*(\d+)\]")

    @classmethod
    def scan(cls, binary, target, wordlist, config, tool_cfg, verbose):
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

        if verbose:
            print("[*] " + " ".join(cmd))
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            print(f"[-] Failed to launch: {binary}")
            return []
        return cls._parse(proc.stdout)

    @classmethod
    def _parse(cls, raw):
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
    hits = engine.scan(binary, target, wordlist_path, config, tool_cfg, verbose)
    results = collect_results(target, MODULE_NAME, hits, config["filters"], verbose)

    save_state(project_name, MODULE_NAME, target, results)
    print(f"[+] Directory bruteforce ({engine_name}) done: {len(results)} hits saved.")
    return results
