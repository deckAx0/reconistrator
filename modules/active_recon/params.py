import os
import sys
import shutil

# Дозволяємо імпорт спільних хелперів із core/ незалежно від точки запуску.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core"))
from utils import ffuf_scan, collect_results, save_state, read_words

MODULE_NAME = "params"


def find_params(target, project_name, wordlist_path, config, verbose=False):
    """Оркеструє ffuf для перебору імен GET-параметрів (?FUZZ=value).

    Тут автокалібрування (-ac) особливо важливе: валідні й невалідні
    параметри часто повертають однакову сторінку, тож ffuf сам відсіює
    базову відповідь, лишаючи параметри, що змінюють поведінку.
    """
    if not os.path.isfile(wordlist_path):
        print(f"[-] Wordlist not found: {wordlist_path}")
        return []

    tool_cfg = config.get("tools", {}).get("params", {})
    binary = tool_cfg.get("binary") or "ffuf"
    if shutil.which(binary) is None:
        print(f"[-] Tool not found in PATH: {binary}")
        return []

    value = tool_cfg.get("value", "1")
    fuzz_url = f"{target}/?FUZZ={value}"

    words = set(read_words(wordlist_path))

    print(f"[*] GET-parameter bruteforce via ffuf on {target}")
    hits = ffuf_scan(binary, fuzz_url, wordlist_path, config, tool_cfg, verbose,
                     keep=lambda fuzz: fuzz in words)
    results = collect_results(target, MODULE_NAME, hits, config["filters"], verbose)

    save_state(project_name, MODULE_NAME, target, results)
    print(f"[+] GET-parameter bruteforce done: {len(results)} hits saved.")
    return results
