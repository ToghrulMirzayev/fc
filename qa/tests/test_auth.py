import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from data.users import DEMO_USER
from flows.auth_flow import AuthFlow
from app.pages.login_page import LoginPage
from app.pages.dashboard_page import DashboardPage


@pytest.mark.auth
class TestAuth:
    """Suite of tests covering Admin authentication and workspace lookup."""

    def test_successful_login(self, auth_flow: AuthFlow, dashboard_page: DashboardPage):
        """Verifies that an owner can successfully log in through the two-step flow."""
        auth_flow.login(
            slug=DEMO_USER.tenant_slug,
            email=DEMO_USER.email,
            password=DEMO_USER.password
        )
        
        # Verify landing on Dashboard
        expect(dashboard_page.page).to_have_url(f"{settings.BASE_URL}/")
        assert "Demo" in dashboard_page.get_greeting()

    def test_invalid_credentials_login(self, auth_flow: AuthFlow, login_page: LoginPage):
        """Verifies proper error messages are shown for wrong passwords."""
        auth_flow.login(
            slug=DEMO_USER.tenant_slug,
            email=DEMO_USER.email,
            password="incorrectpassword"
        )
        
        error = login_page.get_error_message()
        assert error is not None
        assert "didn't match" in error.lower()

    def test_invalid_workspace_slug(self, login_page: LoginPage):
        """Verifies workspace verification fails on invalid slug name."""
        login_page.navigate_login()
        login_page.enter_workspace("nonexistent-workspace-slug-99")
        
        error = login_page.get_error_message()
        assert error is not None
        assert "couldn't find that workspace" in error.lower()

    def test_successful_logout(self, authenticated_page: Page, dashboard_page: DashboardPage):
        """Verifies logging out redirects the owner to the login portal."""
        dashboard_page.sidebar.click_logout()
        
        # Verify URL is redirected back to login screen
        expect(dashboard_page.page).to_have_url(f"{settings.BASE_URL}/login")
