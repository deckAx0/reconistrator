import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

# Дозволяємо імпорт спільних хелперів із core/ незалежно від точки запуску.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core"))
from utils import build_session, make_result, passes_filters, save_state

MODULE_NAME = "directories"


def _read_wordlist(path):
    """Читає словник, ігноруючи порожні рядки та коментарі."""
    try:
        with open(path, "r", errors="ignore") as wordlist:
            return [
                line.strip()
                for line in wordlist
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        print(f"[-] Wordlist not found: {path}")
        return []


def find_directories(target, project_name, wordlist_path, config, verbose=False):
    """Перебирає директорії за словником і зберігає знахідки у стан проєкту.

    Параметри мережі (потоки, таймаут, ретраї, заголовки) та фільтри
    беруться з config.json, а не хардкодяться.
    """
    words = _read_wordlist(wordlist_path)
    if not words:
        return []

    http_cfg = config["http"]
    filters = config["filters"]
    session = build_session(http_cfg)
    results = []

    def probe(word):
        url = f"{target}/{word}"
        try:
            response = session.get(
                url,
                timeout=http_cfg["timeout"],
                allow_redirects=http_cfg["allow_redirects"],
                verify=http_cfg["verify_ssl"],
            )
        except requests.RequestException:
            return None

        length = len(response.content)
        if not passes_filters(response.status_code, length, filters):
            return None
        if verbose:
            print(f"[+] {response.status_code}  {length:>7}  {url}")
        return make_result(target, MODULE_NAME, word, response.status_code, length)

    print(f"[*] Directory bruteforce: {len(words)} paths on {target}")
    with ThreadPoolExecutor(max_workers=http_cfg["threads"]) as pool:
        for result in pool.map(probe, words):
            if result:
                results.append(result)

    save_state(project_name, MODULE_NAME, target, results)
    print(f"[+] Directory bruteforce done: {len(results)} hits saved.")
    return results
