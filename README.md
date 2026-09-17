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
- `--modules` — які модулі запускати: `directories`, `files`, `params`
  (дефолт — усі три).
- `--verbose` — друкувати команду утиліти та кожну знахідку.

Залежності: сам оркестратор — лише стандартна бібліотека Python; модулі
розвідки вимагають встановленого **ffuf** (і опційно **gobuster**) у `PATH`.

## Реалізовані модулі

### 1. Bruteforce директорій — `modules/active_recon/endpoints.py`
Це **оркестратор**, а не власний сканер: `find_directories()` будує команду
для зовнішньої утиліти (`ffuf` або `gobuster`) за параметрами з `config.json`,
запускає її, нормалізує вивід у єдиний формат
(`target`, `module`, `path`, `status_code`, `length`, `timestamp`) і зберігає у
`projects/<name>/state/directories.json`.

- **ffuf** — вивід у JSON (`-of json`), парситься масив `results`.
- **gobuster** — текстовий вивід парситься регуляркою.

Рушій обирається в `config.json` (`tools.directories.engine`). Потоки, таймаут
і заголовки передаються утиліті; фільтри статус-кодів/розмірів застосовуються
до її виводу однаково для будь-якого рушія. Новий рушій додається одним записом
у реєстр `ENGINES`.

### 2. Bruteforce файлів/бекапів — `modules/active_recon/files.py`
`find_files()` оркеструє **ffuf** зі словником та розширеннями з
`active_recon.find_files.extensions` (прапорець `-e`), тож перебираються і чисті
імена, і бекап-варіанти (`config` → `config.bak`, `config.zip`, …). Результат
іде у `state/files.json`.

### 3. Bruteforce GET-параметрів — `modules/active_recon/params.py`
`find_params()` оркеструє **ffuf** по шаблону `?FUZZ=<value>` для виявлення
прихованих параметрів. Результат іде у `state/params.json`.

**Автокалібрування (`-ac`).** Файли й параметри (і директорії через ffuf) за
замовчуванням запускаються з ffuf `-ac`: утиліта сама калібрує фільтри проти
wildcard/soft-404 відповідей, коли ціль повертає 200 «на все». Вимикається через
`autocalibrate: false` у відповідній секції `tools`. Оркестратор додатково
залишає у звіті лише ті шляхи, що реально є у словнику, — так калібрувальні
зонди ffuf не потрапляють у результати як хибні знахідки.

### 4. Звіти — `reporting/report.py`
`generate_report()` збирає всі JSON-снепшоти з `state/` і рендерить зведений
`projects/<name>/reports/report.md` (таблиця по кожному модулю).

### 5. Конфігурація — `config/config.json` + `core/config.py`
`load_config()` зливає користувацький конфіг із дефолтами (`DEFAULT_CONFIG`),
тож відсутні ключі не ламають запуск. Секції:

- `http` — `threads`, `timeout`, `retries`, `allow_redirects`, `verify_ssl`, `headers`.
- `filters` — `status_include`, `status_exclude`, `hide_lengths`.
- `tools.directories` — `engine` (`ffuf`/`gobuster`), `binary` (шлях до
  виконуваного файлу або `null`), `autocalibrate` (ffuf `-ac`), `extra_args`.
- `tools.files` — `binary`, `autocalibrate`, `extra_args`.
- `tools.params` — `binary`, `autocalibrate`, `value` (значення у `?FUZZ=<value>`),
  `extra_args`.
- `wordlist` — шляхи до словників (`endpoints`, `parameters`, `files`).
- `active_recon.find_files.extensions` — розширення для модуля файлів.

Спільні хелпери (нормалізація URL, формат результату, фільтри, читання/запис
стану) живуть у `core/utils.py`.

## Обмеження / TODO

- Файли/параметри — лише через ffuf (gobuster підтримано тільки для директорій).
- Рендер `.html` зі звіту не реалізований.
- Об'єднання результатів кількох таргетів в один звіт — TODO.
- `create_project` не перезаписує наявний проєкт: для повторного запуску
  беріть нову назву.
- ffuf `-ac` недетермінований: на простих (не-wildcard) цілях може зрідка
  пропускати справжні знахідки — там доцільно `autocalibrate: false`.
