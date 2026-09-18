# 🛡️ Enterprise QA Automation & Security Penetration Framework

> **A mission-critical, enterprise-grade test automation platform and live execution dashboard powered by Playwright, Pytest, and Flask.**

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-2EAD33.svg?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![Pytest Engine](https://img.shields.io/badge/Pytest-7.4%2B-0A9EDC.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Flask Server](https://img.shields.io/badge/Flask-3.0%2B-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Code Style: Flake8 & Black](https://img.shields.io/badge/Code%20Style-Black%20%7C%20Flake8-000000.svg)](https://github.com/psf/black)
[![Framework Architecture](https://img.shields.io/badge/Design%20Pattern-Page%20Object%20Model%20(POM)-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents
1. [Executive Summary](#-executive-summary)
2. [Tech Stack & Tooling](#-tech-stack--tooling)
3. [Project Architecture & Directory Layout](#-project-architecture--directory-layout)
4. [Prerequisites](#-prerequisites)
5. [Step-by-Step Installation & Setup](#-step-by-step-installation--setup)
6. [Configuration & Environment Management](#-configuration--environment-management)
7. [Test Execution Guide](#-test-execution-guide)
   - [CLI Test Execution (Pytest)](#cli-test-execution-pytest)
   - [Selective Execution via Markers](#selective-execution-via-markers)
   - [Multi-Browser & Headless Control](#multi-browser--headless-control)
   - [Interactive Dashboard Execution (Flask)](#interactive-dashboard-execution-flask)
8. [Reporting & Artifacts](#-reporting--artifacts)
9. [Architectural Principles & Best Practices](#-architectural-principles--best-practices)
10. [CI/CD Pipeline Integration](#-cicd-pipeline-integration)
11. [Authors & License](#-authors--license)

---

## 🏛️ Executive Summary

Modern web applications require more than superficial functional testing; they demand robust reliability, SLA performance adherence, and rigorous security verification. 

The **Enterprise QA Automation Framework** is designed to address this challenge. It provides an end-to-end testing suite paired with a real-time, interactive execution dashboard. The framework unifies:
- **Functional End-to-End Testing (UI):** Deterministic browser automation leveraging Playwright's auto-waiting locators and the Page Object Model (POM).
- **API Health & Performance SLA Verification:** Real-time HTTP health, contract status verification, and microsecond-level latency tracking against Service Level Agreements (SLAs).
- **Automated Security Probing:** Dictionary-based credential bruteforce probes, session cookie security flag audits (`HttpOnly`, `Secure`, `SameSite`), token leakage prevention, and logout invalidation checks.
- **Live Execution Streaming:** A Flask-powered management engine broadcasting real-time progress and milestone events via Server-Sent Events (SSE) directly to an interactive frontend.

---

## 🛠️ Tech Stack & Tooling

| Category | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `>= 3.11` | Core development and test scripting language |
| **Browser Engine** | Playwright for Python | `>= 1.40.0` | Multi-engine browser automation (Chromium, Firefox, WebKit) |
| **Test Runner** | Pytest | `>= 7.4.0` | Test orchestration, parameterization, and lifecycle fixtures |
| **HTML Reporting** | pytest-html | `>= 4.1.0` | Standalone, self-contained HTML test execution reporting |
| **Metadata Engine** | pytest-metadata | `>= 3.1.0` | Injected environment telemetry for test reporting |
| **HTTP Client** | Requests | `>= 2.31.0` | REST API health probing, SLA measurements, and session testing |
| **Configuration** | python-dotenv | `>= 1.0.0` | Strict environment variable separation and secret handling |
| **Management Server** | Flask | `>= 3.0.0` | Web control portal, RBAC, OTP verification, and SSE streaming |
| **Persistence** | SQLite3 | Native | Lightweight user authentication and scan log tracking |

---

## 📂 Project Architecture & Directory Layout

The project enforces strict separation of concerns, eliminating circular dependencies and isolating test data, drivers, and business logic:

```text
QA_Playwright_Project/
├── .env.example               # Template environment configuration (secrets excluded)
├── .gitignore                  # Comprehensive version control exclusions
├── conftest.py                # Pytest global fixtures, browser sessions & reporting hooks
├── pytest.ini                 # Pytest configuration, paths, and marker registrations
├── requirements.txt           # Pinned production Python dependencies
├── README.md                  # Comprehensive technical documentation
│
├── config/                    # Centralized Configuration & Environment Layer
│   ├── __init__.py
│   └── settings.py            # Strongly-typed configuration dataclass and path management
│
├── core/                      # Browser Driver & Engine Management
│   ├── __init__.py
│   └── browser_factory.py     # Playwright lifecycle, context isolation, and engine factory
│
├── pages/                     # Page Object Model (POM) Abstraction Layer
│   ├── __init__.py
│   ├── base_page.py           # Core interactions, explicit waits, screenshots, and logging
│   ├── login_page.py          # Encapsulated login portal interactions and assertions
│   └── auth_security_page.py  # Session cookie, localStorage, and token penetration probing
│
├── test_data/                 # Externalized Test Datasets (Data-Driven Testing)
│   └── credentials_wordlist.json # Dictionary wordlists for credential security probing
│
├── tests/                     # Test Suites (Descriptive, Isolated, Behavior-Driven)
│   ├── __init__.py
│   ├── test_login.py          # UI Positive & Negative authentication flows
│   ├── test_credentials.py    # Dictionary bruteforce & weak credential probe
│   ├── test_api.py            # REST API endpoint status & SLA latency benchmarks
│   └── test_auth.py           # Cookie flags, token leakage & session termination security
│
├── utils/                     # Shared Framework Utilities & Helpers
│   ├── __init__.py
│   ├── api_client.py          # Latency-measuring HTTP client wrapper
│   ├── data_loader.py         # JSON/CSV dataset loader with environment override logic
│   └── logger.py              # Structured console & rotating file logging utility
│
├── reports/                   # Generated Test Artifacts (Git-ignored)
│   ├── report.html            # Standalone pytest-html execution report
│   └── screenshots/           # Failure snapshots and visual evidence
│
├── logs/                      # Persistent Runtime Logs (Git-ignored)
│   └── automation.log         # Rotating execution log file
│
├── static/                    # Dashboard Assets (CSS, Images, Icons)
│   ├── css/main.css
│   └── images/
│
└── templates/                 # Web Dashboard Jinja2 Templates
    ├── index.html             # Interactive scan launcher & SSE milestone terminal
    ├── login.html             # Dashboard authentication
    ├── results.html           # Historical scan analytics
    ├── signup.html
    └── create_admin.html      # Administrative RBAC & OTP verification flow
```

---

## ⚡ Prerequisites

Before installing and running the framework, ensure your environment meets the following specifications:

- **Operating System:** Windows 10/11, macOS Monterey+, or Ubuntu 20.04+ LTS.
- **Python:** Python `3.11` to `3.14` installed and accessible via PATH.
- **Package Manager:** `pip` (version 23.0 or newer).
- **Network Access:** Outbound HTTPS access to target endpoints (default: `https://www.saucedemo.com`).

---

## 🚀 Step-by-Step Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Mohammed9620/QA_Playwright_Project.git
cd QA_Playwright_Project
```

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Playwright Browser Binaries
Install the required browser binaries (Chromium, Firefox, WebKit) and OS dependencies:
```bash
playwright install chromium
# Optional: install all browser engines
playwright install
```

---

## ⚙️ Configuration & Environment Management

The framework strictly decouples test configuration from code logic via environment variables.

1. Create your local `.env` file by copying `.env.example`:
   ```bash
   cp .env.example .env     # Linux / macOS
   copy .env.example .env   # Windows Command Prompt / PowerShell
   ```

2. Configure environment settings in `.env`:
   ```ini
   # Target Application & Authentication
   TARGET_URL=https://www.saucedemo.com
   TEST_USER=standard_user
   TEST_PASS=secret_sauce

   # Browser Engine Controls
   BROWSER=chromium         # Options: chromium, firefox, webkit
   HEADLESS=true            # Options: true, false
   TIMEOUT=10000            # Milliseconds

   # API Validation Parameters
   API_EXPECTED_STATUS=200
   API_SLA_MS=3000

   # Web Dashboard Security
   SECRET_KEY=generate-a-secure-random-32-byte-hex-key
   ADMIN_DEFAULT_EMAIL=admin@test.com
   ADMIN_DEFAULT_PASSWORD=AdminPassword123!Secure
   ```

3. (Optional) Initialize the local user database for the web dashboard:
   ```bash
   python init_db.py
   ```

---

## 🧪 Test Execution Guide

### CLI Test Execution (Pytest)

Run all tests across all suites:
```bash
pytest
```

Run a specific test suite:
```bash
pytest tests/test_login.py
pytest tests/test_api.py
pytest tests/test_auth.py
pytest tests/test_credentials.py
```

Run with real-time console streaming and verbose logging:
```bash
pytest -v -s
```

---

### Selective Execution via Markers

The framework registers explicit Pytest markers in `pytest.ini` for targeted test runs:

| Marker | Description | Command |
| :--- | :--- | :--- |
| `@pytest.mark.ui` | Browser-based end-to-end tests | `pytest -m ui` |
| `@pytest.mark.api` | REST API availability and contracts | `pytest -m api` |
| `@pytest.mark.auth` | Authentication and authorization tests | `pytest -m auth` |
| `@pytest.mark.security` | Penetration checks & credential probes | `pytest -m security` |
| `@pytest.mark.performance`| SLA response latency validations | `pytest -m performance` |
| `@pytest.mark.negative`| Validation error handling tests | `pytest -m negative` |

---

### Multi-Browser & Headless Control

Override browser engine or execution mode at runtime via CLI environment injection:

**Run in Headed Mode (see browser UI):**
```bash
# Windows PowerShell
$env:HEADLESS="false"; pytest tests/test_login.py

# Linux / macOS
HEADLESS=false pytest tests/test_login.py
```

**Run on Firefox or WebKit:**
```bash
# Windows PowerShell
$env:BROWSER="firefox"; pytest tests/test_login.py

# Linux / macOS
BROWSER=firefox pytest tests/test_login.py
```

---

### Interactive Dashboard Execution (Flask)

The project includes an interactive web control console:

1. Launch the web server:
   ```bash
   python app.py
   ```
2. Navigate to `http://127.0.0.1:5000` in your web browser.
3. Authenticate with your seeded administrator credentials (or register via the self-service flow).
4. Select a scan module (**Login Test**, **Credential Bruteforce Probe**, **API Health Check**, **Broken Auth Audit**, or **Full Scan**).
5. Watch the test execution milestone stream in real time via Server-Sent Events (SSE).
6. Click **View Test Report** to open the branded HTML execution summary.

---

## 📊 Reporting & Artifacts

### Generating HTML Reports
Generate a self-contained HTML report with embedded styles and metadata:
```bash
pytest --html=reports/report.html --self-contained-html
```

The report is written directly to `reports/report.html`. To open the report in your default browser:
```bash
# Windows
start reports/report.html

# macOS
open reports/report.html

# Linux
xdg-open reports/report.html
```

### Failure Artifacts
- **Screenshots:** When configured, automated screenshots are saved to `reports/screenshots/`.
- **Structured Logs:** All execution steps, warnings, and errors are appended to `logs/automation.log` with a 10MB rotating file handler.

---

## 📐 Architectural Principles & Best Practices

1. **Page Object Model (POM):** UI locators and user actions are strictly isolated in `pages/`, keeping test specifications in `tests/` readable, concise, and maintainable.
2. **Strict Environment Decoupling:** Credentials, target endpoints, and thresholds are sourced dynamically from `config/settings.py` via `.env`, eliminating hardcoded secrets.
3. **Data-Driven Separation:** Test datasets (such as security wordlists) live in `test_data/*.json` and are accessed through dedicated loaders (`utils/data_loader.py`).
4. **Structured Milestone Logging:** The unified logger (`utils/logger.py`) outputs standardized log levels (`[INFO]`, `[PASS]`, `[WARN]`, `[FAIL]`, `[ERROR]`), powering both file auditing and real-time SSE streaming to the Flask dashboard.
5. **Robust Assertions with Failure Diagnostics:** Every assertion provides a rich, descriptive diagnostic message explaining expected vs. actual values to accelerate root-cause analysis.

---

## 🔄 CI/CD Pipeline Integration

Here is a reference GitHub Actions workflow configuration (`.github/workflows/test.yml`):

```yaml
name: QA Automation Pipeline

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install Playwright Browsers
        run: playwright install --with-deps chromium

      - name: Execute Automated Test Suite
        env:
          TARGET_URL: ${{ secrets.TARGET_URL }}
          TEST_USER: ${{ secrets.TEST_USER }}
          TEST_PASS: ${{ secrets.TEST_PASS }}
          HEADLESS: "true"
        run: |
          pytest --html=reports/report.html --self-contained-html

      - name: Archive Test Reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-execution-report
          path: reports/
```

---

## 👨‍💻 Authors & License

- **Lead QA Architect:** Principal QA Automation Architect & Maintainer
- **License:** Distributed under the [MIT License](LICENSE).
