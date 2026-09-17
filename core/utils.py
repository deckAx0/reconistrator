import os
import json
import subprocess
from tempfile import NamedTemporaryFile
from datetime import datetime, timezone


def normalize_url(target):
    """Приводить ціль до вигляду scheme://host без завершального '/'."""
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    return target.rstrip("/")


def make_result(target, module, path, status_code, length):
    """Єдиний внутрішній формат результату для всіх brute force-модулів."""
    return {
        "target": target,
        "module": module,
        "path": path,
        "status_code": status_code,
        "length": length,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def passes_filters(status_code, length, filters):
    """Вирішує, чи потрапляє знахідка у результати за фільтрами config.json.

    Застосовується до виводу будь-якого рушія, щоб поведінка фільтрів була
    однаковою незалежно від обраної утиліти.
    """
    include = filters.get("status_include", [])
    exclude = filters.get("status_exclude", [])
    hide_lengths = filters.get("hide_lengths", [])

    if status_code in exclude:
        return False
    if include and status_code not in include:
        return False
    if length in hide_lengths:
        return False
    return True


def read_words(path):
    """Читає словник у список, ігноруючи порожні рядки та коментарі."""
    with open(path, "r", errors="ignore") as wordlist:
        return [
            line.strip()
            for line in wordlist
            if line.strip() and not line.startswith("#")
        ]


def collect_results(target, module, hits, filters, verbose):
    """Фільтрує «сирі» знахідки рушія і перетворює їх на єдиний формат."""
    results = []
    for hit in hits:
        if not passes_filters(hit["status"], hit["length"], filters):
            continue
        if verbose:
            print(f"[+] {hit['status']}  {hit['length']:>7}  {target}/{hit['path']}")
        results.append(make_result(target, module, hit["path"], hit["status"], hit["length"]))
    return results


def ffuf_scan(binary, fuzz_url, wordlist, config, tool_cfg, verbose, extra=None, keep=None):
    """Запускає ffuf для заданого шаблону FUZZ і повертає нормалізовані знахідки.

    Спільний для всіх ffuf-модулів (директорії/файли/параметри). Потоки,
    таймаут і заголовки беруться з config.json; за замовчуванням вмикає
    автокалібрування фільтрів (-ac). Повертає [{path, status, length}].

    keep — необовʼязковий предикат keep(fuzz)->bool. Він відсіює калібрувальні
    зонди ffuf: у результати потрапляє лише те, що реально є в словнику
    (інакше -ac може підмішати випадкові рядки як хибні знахідки).
    """
    http = config["http"]
    out = NamedTemporaryFile(prefix="ffuf_", suffix=".json", delete=False)
    out.close()

    cmd = [
        binary,
        "-u", fuzz_url,
        "-w", wordlist,
        "-t", str(http["threads"]),
        "-timeout", str(http["timeout"]),
        "-of", "json", "-o", out.name,
        "-s",
    ]
    for name, value in http.get("headers", {}).items():
        cmd += ["-H", f"{name}: {value}"]
    # -ac сам калібрує фільтри; ручний -fc з ним конфліктує (ffuf починає
    # плутати калібрувальні зонди з реальними знахідками). Тож -fc додаємо
    # лише коли автокалібрування вимкнене — status_exclude все одно
    # застосовується пост-фактум у passes_filters().
    if tool_cfg.get("autocalibrate", True):
        cmd += ["-ac"]
    else:
        exclude = config["filters"].get("status_exclude", [])
        if exclude:
            cmd += ["-fc", ",".join(str(code) for code in exclude)]
    if extra:
        cmd += extra
    cmd += tool_cfg.get("extra_args", [])

    if verbose:
        print("[*] " + " ".join(cmd))
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print(f"[-] Failed to launch: {binary}")
        os.path.exists(out.name) and os.unlink(out.name)
        return []

    hits = _parse_ffuf(out.name)
    if os.path.exists(out.name):
        os.unlink(out.name)
    if keep is not None:
        hits = [hit for hit in hits if keep(hit["path"])]
    return hits


def _parse_ffuf(path):
    """Читає JSON-звіт ffuf і дістає path/status/length з масиву results."""
    try:
        with open(path) as report:
            data = json.load(report)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [
        {
            "path": item.get("input", {}).get("FUZZ", item.get("url", "")),
            "status": item.get("status", 0),
            "length": item.get("length", 0),
        }
        for item in data.get("results", [])
    ]


def state_path(project_name, module):
    """Шлях до JSON-снепшота стану конкретного модуля таргета."""
    return f"../projects/{project_name}/state/{module}.json"


def save_state(project_name, module, target, results):
    """Зберігає результати модуля як окремий JSON-снепшот у теці проєкту."""
    path = state_path(project_name, module)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    snapshot = {
        "target": target,
        "module": module,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    with open(path, "w") as state_file:
        json.dump(snapshot, state_file, indent=2)
    return path


def load_state(project_name, module):
    """Читає JSON-снепшот стану модуля, або None якщо його ще нема."""
    try:
        with open(state_path(project_name, module), "r") as state_file:
            return json.load(state_file)
    except FileNotFoundError:
        return None
