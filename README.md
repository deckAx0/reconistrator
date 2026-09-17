# Reconistrator

Оркестратор інструментів активної розвідки веб-застосунків. Координує brute
force-модулі, зберігає результати як JSON-стан і формує звіти.

> Лише для **авторизованого** тестування з дозволом власника цілі.

## Запуск

Запускати з теки `core/` (усі шляхи в конфізі відносні до неї):

```bash
cd core
python reconichestrator.py --target example.com --project-name myscan
```

Аргументи:

- `--target` — домен або IP цілі (схема `http://` додається автоматично).
- `--project-name` — назва проєкту; результати йдуть у `projects/<name>/`.
- `--config` — шлях до конфігу (дефолт `../config/config.json`).
- `--report-format` — `md` (дефолт) або `html` (`html` поки що TODO → пише `.md`).
- `--verbose` — друкувати кожну знахідку.

Залежності: `requests`.

## Реалізовані модулі

### 1. Bruteforce директорій — `modules/active_recon/endpoints.py`
`find_directories()` перебирає шляхи зі словника (`wordlist.endpoints`),
застосовує фільтри статус-кодів/розмірів і зберігає знахідки у
`projects/<name>/state/directories.json` в єдиному форматі результату
(`target`, `module`, `path`, `status_code`, `length`, `timestamp`).
Потоки/таймаути/ретраї/заголовки — з `config.json`.

### 4. Звіти — `reporting/report.py`
`generate_report()` збирає всі JSON-снепшоти з `state/` і рендерить зведений
`projects/<name>/reports/report.md` (таблиця по кожному модулю).

### 5. Конфігурація — `config/config.json` + `core/config.py`
`load_config()` зливає користувацький конфіг із дефолтами (`DEFAULT_CONFIG`),
тож відсутні ключі не ламають запуск. Секції:

- `http` — `threads`, `timeout`, `retries`, `allow_redirects`, `verify_ssl`, `headers`.
- `filters` — `status_include`, `status_exclude`, `hide_lengths`.
- `wordlist` — шляхи до словників (`endpoints`, `parameters`, `files`).
- `active_recon.find_files.extensions` — розширення для модуля файлів.

Спільні хелпери (HTTP-сесія, формат результату, фільтри, читання/запис стану)
живуть у `core/utils.py`.

## Обмеження / TODO

- Модулі файлів (`files.py`) та GET-параметрів (`params.py`) ще заглушки.
- Рендер `.html` зі звіту не реалізований.
- Об'єднання результатів кількох таргетів в один звіт — TODO.
- `create_project` не перезаписує наявний проєкт: для повторного запуску
  беріть нову назву.
