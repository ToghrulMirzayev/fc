# FitnessCourt Automated Test Suite

A modular, robust end-to-end automated testing framework for the **FitnessCourt** Admin Portal using **Python**, **Pytest**, and **Playwright**. It employs the **Page Object Model (POM)** pattern to keep test cases clean, legible, and maintainable.

---

## Architecture Overview

```
FitnessCourt/qa/
├── app/
│   ├── pages/              # Page Object Model (POM) representations
│   │   ├── base_page.py    # Base utilities and wrapper for Playwright APIs
│   │   ├── login_page.py   # Actions/selectors for Multi-Step Login
│   │   ├── dashboard_page.py # Actions/selectors for Admin Dashboard
│   │   └── members_page.py # Actions/selectors for Member management
│   └── api/
│       └── api_client.py   # Python API client helper for backend operations
├── config/settings.py      # Environment variables and configurations loader
├── data/
│   └── users.py            # Centralized test credentials (e.g. DEMO_USER)
├── tests/                  # Automated test suites
│   ├── conftest.py         # Test-scoped fixtures (e.g., auto-login browser session)
│   ├── test_auth.py        # Authentication & workspace validation tests
│   ├── test_dashboard.py   # Dashboard widgets & layout tests
│   └── test_members.py     # Member search, filtering, and profiles tests
├── conftest.py             # Root level conftest (browser capability overrides)
├── pytest.ini              # Pytest CLI preferences, log formatting & custom markers
└── requirements.txt        # Python package dependencies
```

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- FitnessCourt application running locally (or pointing to a remote staging server)

### 2. Environment Setup
Create a Python virtual environment and activate it:
```bash
# Navigate to test folder
cd qa

# Create virtual environment
python3 -m venv venv

# Activate on macOS/Linux:
source venv/bin/activate

# Or on Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
Install Python libraries and download the browser binaries required by Playwright:
```bash
# Install pip dependencies
pip install -r requirements.txt

# Download Playwright web drivers
playwright install chromium
```

### 4. Configuration
Create your local environment configuration file:
```bash
cp .env.example .env
```
Edit `.env` and set parameters appropriate for your target environment:
- `BASE_URL`: The URL of the frontend (e.g., `http://localhost:3000`).
- `API_URL`: The URL of the backend server (e.g., `http://localhost:8000`).
- `ADMIN_EMAIL` / `ADMIN_PASSWORD`: Valid owner credentials matching target DB state.
- `HEADLESS`: `true` to run browsers in the background, or `false` to see browser windows.

---

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test suites using custom markers
```bash
# Run only authentication tests
pytest -m auth

# Run only members management tests
pytest -m members

# Run only dashboard tests
pytest -m dashboard
```

### Run tests in headed browser mode
To observe the browser actions on screen during local execution:
```bash
pytest --headed
```

### Run tests across multiple CPU cores in parallel
```bash
pytest -n auto
```

---

## Reports and Artifacts
- **HTML Report**: Pytest yields a detailed visual HTML report after runs, saved at `reports/report.html`.
- **Screenshots**: Page Object error callbacks or manual captures save images to `reports/screenshots/`.
