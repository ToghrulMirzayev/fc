from app.pages.base_page import BasePage
from config.settings import settings


class LoginPage(BasePage):
    """Page Object for the multi-step Login page."""

    # Selectors - Step 1: Workspace
    WORKSPACE_INPUT = 'input[placeholder="e.g. demo"]'
    CONTINUE_BUTTON = 'button:has-text("Continue"), button:has-text("Looking up…")'

    # Selectors - Step 2: Credentials
    EMAIL_INPUT = 'input[type="email"]'
    PASSWORD_INPUT = 'input[type="password"]'
    SIGN_IN_BUTTON = 'button:has-text("Sign in"), button:has-text("Signing in…")'

    # Common
    ERROR_ALERT = 'div.text-danger'

    def navigate_login(self) -> None:
        """Navigates directly to the login base page."""
        self.navigate(f"{settings.BASE_URL}/login")

    def enter_workspace(self, slug: str) -> None:
        """Fills the workspace slug and moves to the credentials step."""
        self.wait_for(self.WORKSPACE_INPUT)
        self.fill(self.WORKSPACE_INPUT, slug)
        self.click(self.CONTINUE_BUTTON)

    def login(self, email: str, password: str) -> None:
        """Fills credentials on Step 2 and logs in."""
        self.wait_for(self.EMAIL_INPUT)
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SIGN_IN_BUTTON)

    def get_error_message(self, timeout: float = 2000) -> str | None:
        """Returns error alert message if present, waiting for it to appear first."""
        try:
            self.wait_for(self.ERROR_ALERT, state="visible", timeout=timeout)
            return self.get_text(self.ERROR_ALERT)
        except Exception:
            return None
