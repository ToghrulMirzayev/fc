import logging
import pytest
from playwright.sync_api import Page
from config.settings import settings
from flows.auth_flow import AuthFlow
from app.api.auth_api import AuthAPI
from app.pages.login_page import LoginPage
from app.pages.dashboard_page import DashboardPage
from app.pages.members_page import MembersPage

logger = logging.getLogger(__name__)


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Fixture to get an initialized LoginPage instance."""
    return LoginPage(page)


@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    """Fixture to get an initialized DashboardPage instance."""
    return DashboardPage(page)


@pytest.fixture
def members_page(page: Page) -> MembersPage:
    """Fixture to get an initialized MembersPage instance."""
    return MembersPage(page)


@pytest.fixture
def auth_flow(page: Page) -> AuthFlow:
    """Fixture providing AuthFlow instance."""
    return AuthFlow(page)


@pytest.fixture
def authenticated_page(page: Page, auth_api: AuthAPI, dashboard_page: DashboardPage) -> Page:
    """Logs in to the admin dashboard via API and populates localStorage for fast auth."""
    logger.info("Performing fast API-based authentication for test session...")
    
    # 1. Authenticate via API background HTTP call
    auth_data = auth_api.login(
        email=settings.ADMIN_EMAIL,
        password=settings.ADMIN_PASSWORD
    )
    
    # 2. Navigate to base URL so the page is in the correct origin context to set localStorage
    page.goto(settings.BASE_URL)
    
    # 3. Inject access and refresh tokens into localStorage
    page.evaluate(
        """(tokens) => {
            localStorage.setItem('auth.access', tokens.access);
            localStorage.setItem('auth.refresh', tokens.refresh);
        }""",
        {"access": auth_data.access_token, "refresh": auth_data.refresh_token}
    )
    
    # 4. Navigate to base URL again to trigger app load with initialized localStorage
    page.goto(settings.BASE_URL)
    
    # 5. Verify landing on Dashboard by waiting for greeting element
    dashboard_page.wait_for(dashboard_page.GREETING_HEADER)
    logger.info("Authentication successful, on Dashboard.")
    
    return page
