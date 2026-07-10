# AQA_EXAMPLES.md — Code Reference for Automation Framework

> Detailed code examples supporting rules in [AQA_RULES.md](AQA_RULES.md).
> Read this file when generating new code or reviewing architecture patterns.

---

## BasePage — Allowed Methods

```python
from pathlib import Path
from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    # --- Basic interactions ---

    def click(self, locator: str) -> None:
        self.page.locator(locator).click()

    def fill(self, locator: str, value: str) -> None:
        self.page.locator(locator).fill(value)

    def hover(self, locator: str) -> None:
        self.page.locator(locator).hover()

    # --- Text retrieval ---

    def get_text(self, locator: str) -> str:
        return self.page.locator(locator).text_content() or ""

    def get_inner_text(self, locator: str) -> str:
        return self.page.locator(locator).inner_text()

    def get_input_value(self, locator: str) -> str:
        return self.page.locator(locator).input_value()

    def get_all_texts(self, locator: str) -> list[str]:
        return self.page.locator(locator).all_text_contents()

    # --- Element count ---

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    # --- Form controls ---

    def select_option(self, locator: str, **kwargs) -> list[str]:
        return self.page.locator(locator).select_option(**kwargs)

    def check(self, locator: str) -> None:
        self.page.locator(locator).check()

    def uncheck(self, locator: str) -> None:
        self.page.locator(locator).uncheck()

    def upload_file(self, locator: str, files: str | Path | list[str | Path]) -> None:
        self.page.locator(locator).set_input_files(files)

    # --- State checks ---

    def is_visible(self, locator: str) -> bool:
        return self.page.locator(locator).is_visible()

    def is_hidden(self, locator: str) -> bool:
        return self.page.locator(locator).is_hidden()

    # --- Waits & navigation ---

    def wait_for(self, locator: str, state: str = "visible", timeout: float = 5000) -> None:
        self.page.locator(locator).wait_for(state=state, timeout=timeout)

    def navigate(self, url: str) -> None:
        self.page.goto(url)
```

No `get_element()`. No assertions. No business logic. No Locator returns.
If you need an interaction not listed here, **add a new wrapper method to BasePage** — never use raw `page.locator()` outside this class.

---

## Page Object Example

```python
from app.pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT = "[data-testid='username']"
    PASSWORD_INPUT = "[data-testid='password']"
    SUBMIT_BUTTON = "[data-testid='login-submit']"
    ERROR_MESSAGE = "[data-testid='login-error']"

    def enter_username(self, username: str) -> None:
        self.fill(self.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        self.fill(self.PASSWORD_INPUT, password)

    def click_submit(self) -> None:
        self.click(self.SUBMIT_BUTTON)

    def get_error_text(self) -> str:
        return self.get_text(self.ERROR_MESSAGE)
```

---

## Component Example

Components inherit `BasePage` and scope all locators under a `ROOT` selector.

```python
from app.pages.base_page import BasePage
from playwright.sync_api import Page


class Header(BasePage):
    ROOT = "[data-testid='header']"
    USERNAME_DISPLAY = f"{ROOT} [data-testid='user-name']"
    LOGOUT_BUTTON = f"{ROOT} [data-testid='logout-btn']"

    def get_username_display(self) -> str:
        return self.get_text(self.USERNAME_DISPLAY)

    def click_logout(self) -> None:
        self.click(self.LOGOUT_BUTTON)
```

---

## API Client Example

```python
from app.api.api_client import APIClient
from models.user_model import User


class AuthAPI:
    def __init__(self, client: APIClient) -> None:
        self.client = client

    def login(self, username: str, password: str) -> str:
        response = self.client.post("/auth/login", json={"username": username, "password": password})
        return response.json()["token"]

    def get_current_user(self, token: str) -> User:
        response = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        return User(**response.json())
```

---

## Flow Example

```python
from playwright.sync_api import Page
from app.pages.login_page import LoginPage
from app.pages.dashboard_page import DashboardPage


class AuthFlow:
    def __init__(self, page: Page) -> None:
        self.page = page

    def login(self, username: str, password: str) -> DashboardPage:
        login_page = LoginPage(self.page)
        login_page.enter_username(username)
        login_page.enter_password(password)
        login_page.click_submit()
        return DashboardPage(self.page)
```

---

## Fixture Examples

```python
import pytest
from typing import Generator
from playwright.sync_api import Page
from app.api.api_client import APIClient
from config.settings import BASE_URL


@pytest.fixture
def api_client() -> Generator[APIClient, None, None]:
    client = APIClient(base_url=BASE_URL)
    yield client
    client.close()


@pytest.fixture
def authenticated_page(page: Page, api_client: APIClient) -> Page:
    """Uses pytest-playwright's built-in page — no manual browser setup."""
    token = api_client.login(username="testuser", password="testpass")
    page.context.add_cookies([{"name": "auth", "value": token, "url": BASE_URL}])
    page.goto(BASE_URL)
    return page


@pytest.fixture
def created_product(api_client: APIClient) -> Generator[Product, None, None]:
    product = api_client.create_product(name="Test Product", price=9.99)
    yield product
    api_client.delete_product(product.id)
```

---

## Test Example

```python
import pytest
from playwright.sync_api import Page, expect
from flows.auth_flow import AuthFlow
from app.pages.login_page import LoginPage
from app.pages.dashboard_page import DashboardPage
from data.users import VALID_USER, INVALID_PASSWORD_USER


class TestLogin:
    @pytest.mark.smoke
    def test_login_with_valid_credentials_redirects_to_dashboard(
        self, page: Page
    ) -> None:
        """Test: AUTH-F01 — Login with valid credentials"""
        # Arrange
        auth_flow = AuthFlow(page)

        # Act
        dashboard = auth_flow.login(VALID_USER.username, VALID_USER.password)

        # Assert — UI state, use expect()
        expect(page.locator(DashboardPage.WELCOME_HEADER)).to_be_visible()

    def test_login_with_invalid_password_shows_error(
        self, page: Page
    ) -> None:
        """Test: AUTH-F02 — Login with invalid password"""
        # Arrange
        login_page = LoginPage(page)

        # Act
        login_page.enter_username(INVALID_PASSWORD_USER.username)
        login_page.enter_password(INVALID_PASSWORD_USER.password)
        login_page.click_submit()

        # Assert — already resolved value, use assert
        assert login_page.get_error_text() == "Invalid credentials"
```

---

## Test Data Example

```python
# data/users.py
from dataclasses import dataclass


@dataclass(frozen=True)
class UserCredentials:
    username: str
    password: str


VALID_USER = UserCredentials(username="testuser", password="testpass")
ADMIN_USER = UserCredentials(username="admin", password="adminpass")
INVALID_PASSWORD_USER = UserCredentials(username="testuser", password="wrong")
```

---

## Model Example

```python
from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    role: str = "user"
```

---

## Import Order Example

```python
# Standard library
from typing import Generator
from dataclasses import dataclass

# Third-party
import pytest
from playwright.sync_api import Page, expect

# Local — app layer
from app.pages.login_page import LoginPage
from app.api.auth_api import AuthAPI
from app.components.header import Header

# Local — other
from config.settings import BASE_URL
from data.users import VALID_USER
from models.user_model import User
from flows.auth_flow import AuthFlow
```

---

## Anti-Pattern Examples (WRONG → CORRECT)

### time.sleep — BANNED
```python
# WRONG
time.sleep(3)

# CORRECT
page.wait_for_selector("[data-testid='loaded']")
expect(page.locator("[data-testid='result']")).to_be_visible(timeout=5000)
```

### Assertions in Page Objects — BANNED
```python
# WRONG
class LoginPage(BasePage):
    def verify_error_shown(self):
        assert self.is_visible(self.ERROR_MESSAGE)  # VIOLATION

# CORRECT — return data, assert in test
class LoginPage(BasePage):
    def get_error_text(self) -> str:
        return self.get_text(self.ERROR_MESSAGE)
```

### Locators in Tests — BANNED
```python
# WRONG
def test_something(page):
    page.locator("[data-testid='submit']").click()

# CORRECT
def test_something(page):
    login_page = LoginPage(page)
    login_page.click_submit()
```

### Manual Browser Creation — BANNED
```python
# WRONG
@pytest.fixture
def page():
    browser = sync_playwright().start().chromium.launch()
    page = browser.new_page()
    yield page
    browser.close()

# CORRECT — use pytest-playwright built-in
def test_something(page: Page):  # provided by pytest-playwright
    ...
```

### Hardcoded Data in Tests — BANNED
```python
# WRONG
login_page.enter_username("admin@test.com")

# CORRECT
from data.users import VALID_USER
login_page.enter_username(VALID_USER.username)
```

### Raw Playwright in Components — BANNED
```python
# WRONG — bypasses BasePage wrappers
class Header:
    def __init__(self, page: Page) -> None:
        self.page = page

    def click_logout(self) -> None:
        self.page.locator("[data-testid='logout-btn']").click()

# CORRECT — inherits BasePage, uses wrappers
class Header(BasePage):
    LOGOUT_BUTTON = "[data-testid='header'] [data-testid='logout-btn']"

    def click_logout(self) -> None:
        self.click(self.LOGOUT_BUTTON)
```

---

## Complex Scenario Examples

These examples cover real-world patterns beyond simple login/CRUD.

### Table with Pagination — Page Object

```python
from app.pages.base_page import BasePage


class ProductsPage(BasePage):
    PRODUCT_ROW = "[data-testid='product-row']"
    PRODUCT_NAME = "[data-testid='product-name']"
    NEXT_PAGE_BUTTON = "[data-testid='pagination-next']"
    CURRENT_PAGE = "[data-testid='pagination-current']"
    NO_RESULTS = "[data-testid='no-results']"

    def get_product_names(self) -> list[str]:
        return self.get_all_texts(self.PRODUCT_NAME)

    def get_row_count(self) -> int:
        return self.count(self.PRODUCT_ROW)

    def go_to_next_page(self) -> None:
        self.click(self.NEXT_PAGE_BUTTON)

    def get_current_page_number(self) -> str:
        return self.get_text(self.CURRENT_PAGE)

    def has_results(self) -> bool:
        return self.is_hidden(self.NO_RESULTS)
```

### File Upload — Page Object

```python
from pathlib import Path
from app.pages.base_page import BasePage


class ProfilePage(BasePage):
    AVATAR_INPUT = "[data-testid='avatar-upload']"
    AVATAR_IMAGE = "[data-testid='avatar-img']"
    SAVE_BUTTON = "[data-testid='save-profile']"

    def upload_avatar(self, file_path: str | Path) -> None:
        self.upload_file(self.AVATAR_INPUT, file_path)

    def click_save(self) -> None:
        self.click(self.SAVE_BUTTON)

    def get_avatar_src(self) -> str:
        return self.get_text(self.AVATAR_IMAGE)  # or use a dedicated attr method
```

### Modal Component

```python
from app.pages.base_page import BasePage


class ConfirmModal(BasePage):
    ROOT = "[data-testid='confirm-modal']"
    TITLE = f"{ROOT} [data-testid='modal-title']"
    CONFIRM_BUTTON = f"{ROOT} [data-testid='modal-confirm']"
    CANCEL_BUTTON = f"{ROOT} [data-testid='modal-cancel']"

    def get_title(self) -> str:
        return self.get_text(self.TITLE)

    def confirm(self) -> None:
        self.click(self.CONFIRM_BUTTON)

    def cancel(self) -> None:
        self.click(self.CANCEL_BUTTON)

    def is_open(self) -> bool:
        return self.is_visible(self.ROOT)
```

### Network Wait — Test with API-dependent UI

```python
class TestProductSearch:
    def test_search_returns_filtered_results(self, page: Page) -> None:
        # Arrange
        products_page = ProductsPage(page)
        products_page.navigate(f"{BASE_URL}/products")

        # Act — wait for API response before asserting
        with page.expect_response("**/api/products?search=*") as response_info:
            products_page.fill(ProductsPage.SEARCH_INPUT, "laptop")

        # Assert — response resolved, safe to check UI
        assert response_info.value.status == 200
        expect(page.locator(ProductsPage.PRODUCT_ROW)).to_have_count(3)
```

### Parametrized Test with Data Module

```python
import pytest
from data.products import SEARCH_SCENARIOS


class TestProductFilters:
    @pytest.mark.parametrize("scenario", SEARCH_SCENARIOS, ids=lambda s: s.name)
    def test_filter_returns_expected_count(
        self, page: Page, scenario
    ) -> None:
        # Arrange
        products_page = ProductsPage(page)
        products_page.navigate(f"{BASE_URL}/products")

        # Act
        products_page.apply_filter(scenario.filter_name, scenario.filter_value)

        # Assert
        assert products_page.get_row_count() == scenario.expected_count
```

```python
# data/products.py
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchScenario:
    name: str
    filter_name: str
    filter_value: str
    expected_count: int


SEARCH_SCENARIOS = [
    SearchScenario(name="electronics", filter_name="category", filter_value="Electronics", expected_count=15),
    SearchScenario(name="under_50", filter_name="max_price", filter_value="50", expected_count=8),
    SearchScenario(name="in_stock", filter_name="availability", filter_value="in_stock", expected_count=42),
]
```
