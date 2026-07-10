from app.pages.base_page import BasePage


class Sidebar(BasePage):
    """Component representing the navigation sidebar."""

    ROOT = "nav"
    MEMBERS_LINK = f"{ROOT} a[href='/members']"
    PLANS_LINK = f"{ROOT} a[href='/plans']"
    CHECKINS_LINK = f"{ROOT} a[href='/checkins']"
    PAYMENTS_LINK = f"{ROOT} a[href='/payments']"
    LOGOUT_BUTTON = 'button:has-text("sign out")'

    def click_members(self) -> None:
        """Clicks the Members link in the sidebar."""
        self.wait_for(self.MEMBERS_LINK)
        self.click(self.MEMBERS_LINK)

    def click_plans(self) -> None:
        """Clicks the Plans link in the sidebar."""
        self.wait_for(self.PLANS_LINK)
        self.click(self.PLANS_LINK)

    def click_logout(self) -> None:
        """Clicks the Sign out button in the sidebar."""
        self.wait_for(self.LOGOUT_BUTTON)
        self.click(self.LOGOUT_BUTTON)
