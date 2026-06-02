from playwright.sync_api import Page
from app.pages.login_page import LoginPage
from app.pages.dashboard_page import DashboardPage


class AuthFlow:
    """Business flow for authentication operations."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def login(self, slug: str, email: str, password: str) -> DashboardPage:
        """Executes the full multi-step login flow and returns DashboardPage."""
        login_page = LoginPage(self.page)
        login_page.navigate_login()
        login_page.enter_workspace(slug)
        login_page.login(email, password)
        return DashboardPage(self.page)
