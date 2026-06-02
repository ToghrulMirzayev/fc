

# Project Structure — FitnessCourt Automation

## Обзор проекта

- **Домен:** Multi-tenant SaaS для спортзалов и фитнес-студий (FitnessCourt)
- **Что тестируем:** UI (Playwright, sync API) + API (REST)
- **Стек:** Python 3.12+ / Pytest / Playwright / Poetry / Ruff / Pre-commit
- **Цель:** production-ready, масштабируемый фреймворк автоматизации тестирования

---

## Полная структура

```
FitnessCourt/qa/
│
├── conftest.py                            # Корневой conftest — загружает .env, регистрирует fixtures/ плагины, скриншоты при ошибках
├── pytest.ini                             # Маркеры, флаги логирования, пути к тестам
├── pyproject.toml                         # Зависимости и конфигурация Poetry
├── poetry.lock                            # Фиксация версий пакетов Poetry
├── Makefile                               # Быстрые команды запуска (install, test, smoke и др.)
├── requirements.txt                       # Зависимости проекта (pytest, playwright, python-dotenv)
├── .env.example                           # Шаблон переменных окружения
├── .gitignore
├── README.md                              # Инструкции по установке и запуску
│
├── docs/                                  # Папка с документацией проекта
│   ├── [BUG_REPORTS.md](BUG_REPORTS.md)                     # Детальные отчеты о багах (Bug Reports) с ID
│   ├── [AQA_RULES.md](AQA_RULES.md)                       # Контракт AQA: архитектура, правила, чеклисты
│   ├── [AQA_EXAMPLES.md](AQA_EXAMPLES.md)                     # Примеры идеального кода AQA по стандартам проекта
│   ├── [GEMINI.md](GEMINI.md)                           # Инструкции и правила для ИИ-ассистента Gemini
│   ├── [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)                # Детальная структура проекта (этот файл)
│   ├── [TEST_PLAN_BACKEND.md](TEST_PLAN_BACKEND.md)                # Тест-план для бэкенд API и Telegram-бота
│   └── [TEST_PLAN_FRONTEND.md](TEST_PLAN_FRONTEND.md)               # Тест-план для фронтенд веб-портала
│
├── artifacts/                             # Генерируется при прогоне — НЕ коммитится
│   ├── screenshots/                       # Скриншоты при ошибках в тестах (авто-съемка)
│   ├── traces/                            # Playwright traces для отладки
│   └── videos/                            # Видеозаписи тестов
│
├── config/
│   ├── __init__.py
│   └── settings.py                        # Читает среду из ENV / .env файла
│
├── app/
│   ├── __init__.py
│   │
│   ├── pages/                             # Слои Page Object Model (POM)
│   │   ├── __init__.py
│   │   ├── base_page.py                   # Атомарные обёртки вокруг Playwright API (click, fill и др.)
│   │   ├── login_page.py                  # POM двухэтапного входа (workspace slug -> credentials)
│   │   ├── dashboard_page.py              # POM главного экрана администратора (KPI)
│   │   └── members_page.py                # POM списка участников, поиска, профилей
│   │
│   ├── components/                        # Переиспользуемые компоненты интерфейса
│   │   ├── __init__.py
│   │   └── sidebar.py                     # Компонент навигационного сайдбара
│   │
│   └── api/                               # Клиенты API
│       ├── __init__.py
│       ├── api_client.py                  # Базовый generic API клиент для HTTP запросов
│       ├── auth_api.py                    # Клиент API авторизации
│       ├── members_api.py                 # Клиент API работы с участниками
│       ├── plans_api.py                   # Клиент API работы с тарифами
│       └── dashboard_api.py               # Клиент API работы со статистикой
│
├── flows/                                 # Бизнес-сценарии и цепочки действий (Flows)
│   ├── __init__.py
│   └── auth_flow.py                       # Сценарий двухэтапной авторизации владельца
│
├── fixtures/                              # Модульные Pytest фикстуры (сетап, авторизация, данные)
│   ├── __init__.py
│   ├── api_fixtures.py                    # Фикстуры клиентов API
│   ├── page_fixtures.py                   # Фикстуры инициализации страниц (POM)
│   └── auth_fixtures.py                   # Фикстуры авторизационных сессий (authenticated_page)
│
├── models/                                # Датаклассы и Pydantic модели ответов API
│   ├── __init__.py
│   ├── member_model.py                    # Модели ответа списка участников
│   ├── plan_model.py                      # Модели ответа списка тарифов
│   └── dashboard_model.py                 # Модели ответа статистики дашборда
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py                       # Тесты входа в систему (успешный, ошибки, logout)
│   ├── test_dashboard.py                  # Тесты валидации KPI карточек и сайдбара
│   └── test_members.py                    # Тесты поиска участников, фильтров и линковки Telegram
│
└── utils/
    └── __init__.py                        # Вспомогательные утилиты
```

---

## Поток данных (E2E Flow)

```
test_members.py
    │
    ├── authenticated_page (fixture) ← fixtures/auth_fixtures.py (загружено в conftest.py)
    │       │
    │       ├── AuthFlow             ← flows/auth_flow.py
    │       │       ├── LoginPage    ← app/pages/login_page.py
    │       │       │       └── BasePage ← app/pages/base_page.py
    │       │       └── DashboardPage ← app/pages/dashboard_page.py
    │       │
    │       └── MembersPage          ← app/pages/members_page.py
    │               └── Sidebar      ← app/components/sidebar.py
    │
    ├── DEMO_USER (credentials)      ← data/users.py ← .env
    │
    └── assert / expect()            ← только в тестовых файлах
```

---

## Слои — кто что делает, кто что НЕ делает

| Слой | Делает | НЕ делает |
|------|--------|-----------|
| `tests/` | Вызывает методы POM и делает Assert / Expect | Содержит локаторы, сырые вызовы Playwright |
| `app/pages/` | Содержит локаторы (UPPER_SNAKE) + UI-действия | Делает ассерты, содержит бизнес-логику |
| `app/components/` | Содержит scoped локаторы + действия элементов | Содержит бизнес-логику или ассерты |
| `app/api/` | Выполняет HTTP-запросы и парсит JSON в модели | Содержит UI-логику или код Playwright |
| `flows/` | Координирует вызовы POM-страниц для сценариев | Содержит локаторы, делает ассерты |
| `fixtures/` | Предоставляет сетап, авторизацию и очистку | Делает ассерты |
| `models/` | Определяет типизированные структуры API | Содержит бизнес-логику |
| `data/` | Централизованно хранит тестовые данные и константы | Зависит от окружения (только через config) |
| `config/` | Загружает настройки из среды и .env | Содержит бизнес-логику |
| `utils/` | Содержит чистые хелперы (например, логгер) | Содержит логику Playwright, API-вызовы |

---

## Полезные команды (pytest)

- `pytest` — запустить все тесты
- `pytest -m auth` — запустить только тесты авторизации
- `pytest -m members` — запустить только тесты работы с участниками
- `pytest --headed` — запустить тесты в видимом окне браузера
- `pytest -n auto` — запустить тесты параллельно на всех ядрах процессора
