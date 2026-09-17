import os
import sys
import shutil

# Дозволяємо імпорт спільних хелперів із core/ незалежно від точки запуску.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core"))
from utils import ffuf_scan, collect_results, save_state, read_words

MODULE_NAME = "files"


def find_files(target, project_name, wordlist_path, extensions, config, verbose=False):
    """Оркеструє ffuf для пошуку файлів/бекапів: словник × розширення.

    ffuf через прапорець -e додає до кожного слова розширення з config.json
    (`.bak`, `.zip`, `.old` тощо), тож перебираються і чисті імена, і їхні
    бекап-варіанти. Результати нормалізуються у єдиний формат.
    """
    if not os.path.isfile(wordlist_path):
        print(f"[-] Wordlist not found: {wordlist_path}")
        return []

    tool_cfg = config.get("tools", {}).get("files", {})
    binary = tool_cfg.get("binary") or "ffuf"
    if shutil.which(binary) is None:
        print(f"[-] Tool not found in PATH: {binary}")
        return []

    extra = ["-e", ",".join(extensions)] if extensions else None

    # ffuf з -e перебирає і чисте слово, і слово+розширення — саме такі
    # кандидати вважаємо справжніми (решта у виводі -ac = калібрувальні зонди).
    words = set(read_words(wordlist_path))

    def is_candidate(fuzz):
        if fuzz in words:
            return True
        return any(fuzz.endswith(ext) and fuzz[: -len(ext)] in words for ext in extensions)

    print(f"[*] File/backup bruteforce via ffuf on {target}")
    hits = ffuf_scan(binary, f"{target}/FUZZ", wordlist_path, config, tool_cfg, verbose,
                     extra, keep=is_candidate)
    results = collect_results(target, MODULE_NAME, hits, config["filters"], verbose)

    save_state(project_name, MODULE_NAME, target, results)
    print(f"[+] File/backup bruteforce done: {len(results)} hits saved.")
    return results
