import json
import copy

# Дефолтні значення. Використовуються, якщо у config.json чогось бракує,
# щоб модулі не падали через відсутній ключ (потоки/таймаути/заголовки тощо).
DEFAULT_CONFIG = {
    "http": {
        "threads": 20,
        "timeout": 10,
        "retries": 2,
        "allow_redirects": False,
        "verify_ssl": False,
        "headers": {
            "User-Agent": "Reconistrator/0.1 (authorized recon)"
        }
    },
    "filters": {
        # Порожній status_include => приймаємо всі коди, крім status_exclude.
        "status_include": [],
        "status_exclude": [404],
        "hide_lengths": []
    },
    "tools": {
        # Зовнішні утиліти, якими оркеструємо кожен модуль.
        "directories": {
            "engine": "ffuf",     # "ffuf" | "gobuster"
            "binary": None,       # None => береться назва рушія з PATH
            "extra_args": []      # довільні додаткові прапорці утиліти
        }
    },
    "active_recon": {
        "find_files": {
            "extensions": [".bak", ".old", ".zip"]
        }
    },
    "wordlist": {
        "endpoints": "../data/wordlists/directory_list.txt",
        "parameters": "../data/wordlists/burp-parameter-names.txt",
        "files": "../data/wordlists/directory_list.txt"
    }
}


def load_config(config_path):
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print(f"[-] Configuration file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"[-] Invalid JSON in configuration file: {e}")
        return None

    # Значення з config.json перекривають дефолти, відсутні — беруться з дефолтів.
    return _merge_defaults(DEFAULT_CONFIG, config)


def _merge_defaults(defaults, override):
    """Глибоке злиття словників: override має пріоритет над defaults."""
    merged = copy.deepcopy(defaults)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_defaults(merged[key], value)
        else:
            merged[key] = value
    return merged
