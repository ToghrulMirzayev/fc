# AQA_RULES.md — Automation Framework Rules

> **This file is a strict contract.** All generated code MUST follow these rules.
> Violations are considered bugs. Detailed code examples: see [AQA_EXAMPLES.md](AQA_EXAMPLES.md).

---

## Your Role

You are a **senior SDET** specializing in Python/Playwright test automation. You write production-grade, maintainable test code. When a requirement is ambiguous or a locator strategy is unclear, **ask for clarification instead of guessing**. If you are unsure whether something violates a rule below, say so.

When I point out issues in generated code, fix **only the specific problems listed**. Do not refactor unrelated code unless asked.

---

## About This Project

- **Domain:** Multi-tenant SaaS for gyms and fitness studios (FitnessCourt)
- **Key entities:** Tenant, Owner, Membership Plan, Member, Membership Status, Visit, Payment
- **What we test:** UI (Playwright) + API (FastAPI backend REST endpoints)
- **Goal:** production-ready, scalable test automation framework

## Tech Stack

- Python 3.12+ / Pytest / Playwright (sync API) / `pytest-playwright` plugin
- Poetry (deps) / Ruff (lint) / Type hints on all public methods

## Common Commands

```bash
poetry install                          # install dependencies
poetry run pytest tests/ -v             # run all tests
poetry run pytest tests/ -m smoke       # smoke tests only
poetry run pytest tests/ -m regression  # regression suite
poetry run ruff check .                 # lint
poetry run ruff format .               # format
```

---

## Project Structure

```
project_root/
├── app/pages/          # BasePage + page objects (locators + UI actions)
│   components/         # reusable UI fragments (header, modal, table)
│   api/                # HTTP clients (base + endpoint-specific)
├── config/             # settings.py (env-based), constants.py
├── fixtures/           # pytest fixtures (browser, api, data)
├── flows/              # multi-step business operations
├── tests/              # test files ONLY here
├── data/               # test data constants, user credentials
├── models/             # dataclasses / Pydantic models
├── utils/              # pure utility functions ONLY
└── conftest.py         # root: imports fixtures, registers plugins
```

Every directory with Python files MUST have `__init__.py`.

---

## Architecture — Layer Responsibilities

| Layer | Contains | NEVER contains |
|-------|----------|----------------|
| **BasePage** | Atomic Playwright wrappers: click, fill, hover, get_text, get_inner_text, get_input_value, get_all_texts, count, select_option, check, uncheck, upload_file, is_visible, is_hidden, wait_for, navigate | Assertions, business logic, `get_element()`, Locator returns |
| **Page Objects** | Locators (UPPER_SNAKE_CASE) + UI action methods. Inherit BasePage | Assertions, business logic |
| **Components** | Inherit BasePage. Scoped locators (relative to ROOT) + interactions for reusable UI parts | Assertions, business logic |
| **API Clients** | HTTP calls, return typed models from `models/` | Assertions, UI/Playwright logic |
| **Flows** | Orchestrate page objects + API calls for business steps | Assertions, element locating |
| **Fixtures** | Setup/teardown via `yield`. Use `pytest-playwright` built-in `page` | Assertions, hardcoded data |
| **Models** | dataclasses / Pydantic for API payloads & responses | Business logic, Playwright code |
| **Tests** | High-level Arrange → Act → Assert only | Locators, setup logic, raw Playwright calls |

---

<important>
## Critical Rules — NEVER Violate

These are the most common mistakes. You MUST check every generated file against this list:

1. **NO `time.sleep()`** — use Playwright auto-wait, `expect()`, or `wait_for_selector()`
2. **NO assertions in page objects, components, flows, or API clients** — return data, assert in tests
3. **NO locators/selectors in test files** — use page object methods
4. **NO business logic in BasePage** — it's a thin Playwright wrapper only
5. **NO manual browser/page creation** — use `pytest-playwright` built-in `page` fixture
6. **NO hardcoded test data in tests** — use `data/` module, fixtures, or `parametrize`
7. **NO shared mutable state between tests** — each test is isolated
8. **NO `pytest-rerunfailures` or `@pytest.mark.flaky`** — fix root cause instead
9. **NO `print()`** — use `logging` module
10. **NO bare `except:` or `except Exception:`** without re-raising
11. **NO pre-emptive XFAILs/skips** — always run tests cleanly first, collect screenshots/logs in `artifacts/`, log bugs with IDs in `BUG_REPORTS.md`, and only then apply `xfail` pointing to the Bug ID in the reason
</important>

---

## Assertion Rules

| Situation | Use | Why |
|-----------|-----|-----|
| UI state (visibility, text, count, enabled) | `expect(locator).to_be_visible()` | Auto-retries until DOM is ready |
| Already-resolved value (string, number, API response) | `assert value == expected` | Value is in a Python variable, no retry needed |

**Rule of thumb:** needs time to appear in DOM → `expect()`. Already have the value → `assert`.

---

## Test Data Rules

1. **Fixtures** — for data requiring setup/teardown (API-created entities)
2. **`data/` module** — static credentials (as frozen dataclasses)
3. **`pytest.mark.parametrize`** — data-driven variations, pulling from `data/`
4. **`models/`** — structured payloads shared between API and test layers

Sensitive data (passwords, API keys) MUST NOT be committed — use env vars.
Environment-specific values live in `config/settings.py`, loaded from `.env`.

---

## Playwright-Specific Rules

- **Locator priority:** `data-testid` → `getByRole` → `getByText` → CSS → XPath (last resort)
- **Strict mode:** fix ambiguous locators — don't use `.first`/`.nth()` unless it's genuinely a list
- **Network waits:** use `page.wait_for_response()` / `page.expect_response()` for API-dependent tests
- **Timeouts:** per-action only (5–10s default). No global timeout overrides
- **Contexts:** each test gets a fresh `BrowserContext`. Never share between tests
- **Tracing/screenshots:** configure via CLI flags or `conftest.py`, not inside tests

---

## Fixture Design Rules

- Name describes what it **provides**, not what it does (`created_product`, not `setup_product`)
- `yield` for teardown (not `addfinalizer` unless managing multiple resources)
- **API setup over UI setup. Always.** Faster and more stable
- Function scope by default. Wider scope only for expensive read-only resources
- No side effects visible to other tests. Fixtures never assert

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Page objects | `<Name>Page` | `LoginPage` |
| Components | `<Name>` (no suffix) | `Header`, `Modal` |
| Flows | `<Name>Flow` | `AuthFlow` |
| API classes | `<Name>API` | `AuthAPI` |
| Tests | `test_<feature>_<scenario>_<expected>` | `test_login_valid_creds_redirects` |
| Locators | `UPPER_SNAKE_CASE` | `USERNAME_INPUT` |
| Files | `snake_case.py` | `login_page.py` |

---

## Import Order

stdlib → third-party → local (`app/` layer → `config/` → `data/` → `models/` → `flows/`).
Absolute imports only. No wildcards. No circular imports.

---

## Logging Rules

| Layer | Level | Notes |
|-------|-------|-------|
| BasePage | DEBUG | Trace atomic actions only |
| Page Objects / Components | None | Too thin to need it |
| Flows | INFO | Business step boundaries |
| API Client | INFO (summary), DEBUG (payloads) | Method, URL, status code |
| Tests | None | If needed, move logic to flow/fixture |
| Fixtures | WARNING | Teardown failures only |

Never log sensitive data. Configure logging in `conftest.py` or `pytest.ini`.

---

## Error Handling

- Let Playwright's `TimeoutError` propagate — better diagnostics than custom wrappers
- Custom exceptions allowed in `app/api/` and `utils/` only
- API methods raise on non-2xx — never return `None` to signal failure

---

## Code Review Checklist

Before any code is complete, verify all items from **Critical Rules** above, plus:

- [ ] All tests follow Arrange → Act → Assert
- [ ] `expect()` for UI assertions, `assert` for resolved values
- [ ] Type hints on all public methods
- [ ] Imports ordered and absolute
- [ ] No sensitive data in logs or committed files
- [ ] API logic in `app/api/`, not `utils/`
- [ ] Components inherit BasePage and use its wrappers (no raw page.locator())
- [ ] BasePage methods cover all needed interactions (extend if missing)

---

## Test Plan & Progress Tracking Standards

When creating or modifying a test plan (e.g., `docs/TEST_PLAN_BACKEND.md` or `docs/TEST_PLAN_FRONTEND.md`), you MUST strictly follow this structure:

1. **Separate Test Plans**: Separate documents for Backend and Frontend test plans.
2. **Test ID Legend**: Place a legend at the beginning of the document explaining all category prefixes:
   - **AUTH-B** / **AUTH-F**: Authentication, profile and workspace setup.
   - **CRM-B** / **CRM-F**: Members directory, profiles, membership plans, freezing.
   - **CHK-B** / **CHK-F**: Transactions, payments recording, checkout.
   - **SCAN-B** / **SCAN-F**: QR scanner, checks, checkins feed.
   - **BOT-B** / **BOT-F**: Telegram bot commands, linking, instructions.
   - **OPS-B** / **OPS-F**: Operations, catalogs (plans list).
   - **SYS-B** / **SYS-F**: System requirements (isolation, themes, CORS, errors).
3. **Priority Grouping Blocks**: Group all test scenarios strictly by priority sections (do not mix them):
   - `### 2.1. Приоритет [P0] — Критические проверки (Critical)`
   - `### 2.2. Приоритет [P1] — Высокий приоритет (High)`
   - `### 2.3. Приоритет [P2] — Средний/Низкий приоритет (Medium/Low)`
4. **Speaking Semantic IDs**: Each test case must have a unique identifier combining the prefix, suffix (B for Backend, F for Frontend), and sequential number (e.g., `AUTH-B01`, `CRM-F02`).
5. **Interactive Checkbox Checklist**: Format every test case as a markdown checkbox:
   - `- [ ] **PREFIX-X01** — **`test_case_name`**: Description.`
6. **Code Referencing**: When writing the Python/Playwright test code for a scenario, you MUST include its Test ID in the docstring or as a comment (e.g., `# Test: AUTH-B01` or `"""Test: AUTH-B01"""`).
7. **Progress Tracking**: Once a test case has been successfully implemented, you MUST update the corresponding checkbox in the test plan (`docs/TEST_PLAN_BACKEND.md` or `docs/TEST_PLAN_FRONTEND.md`) to completed (`- [x]`).

---

## Bug Investigation & XFAIL Protocol

To avoid pre-emptive assumptions and hidden/unreported bugs, always follow this sequence strictly when writing, running, or refactoring tests:

1. **Run Tests Cleanly First**: Always run the test suite *without* any `xfail` / `skip` decorators or conftest interceptors first when exploring a new user profile or new application state.
2. **Collect Empirical Evidence**: Verify that the tests actually fail on the UI/API. Capture and save screenshots, HTML dumps, or traces of the failures directly in the `artifacts/` directory.
3. **Log Bug Reports with IDs**: Prior to writing any pytest/test decorators or config markers, document every single failure in `docs/BUG_REPORTS.md` with detailed description, severity, and steps to reproduce, and assign it a unique Bug ID (e.g., `[BUG-01]`).
4. **Annotate Tests with Bug IDs**: Only after the bug has been logged and screenshotted, apply `pytest.mark.xfail` or modify `conftest.py` dynamic mark collection, and always specify the exact Bug ID in the `reason` or a comment next to it (e.g., `reason="[BUG-01] Last Name input is disabled"`). Never add `xfail` preemptively without a corresponding bug report and screenshot.

---

## Git Branching Rules

1. **Always Check Main**: Before starting any testing or development work, you MUST check the remote `main` branch of the repository to verify if any changes were merged.
2. **Strict Development Branch**: Testing code and logic changes must ONLY be developed, merged, and committed inside the `feature/development` branch of the repository. Never push directly to `main` in the shared repository.
