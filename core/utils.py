import os
import json
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
