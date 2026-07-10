from app.pages.base_page import BasePage
from app.components.sidebar import Sidebar
from config.settings import settings


class MembersPage(BasePage):
    """Page Object for managing and viewing members list and profiles."""

    def __init__(self, page) -> None:
        super().__init__(page)
        self.sidebar = Sidebar(page)

    # Selectors - Members List
    SEARCH_INPUT = 'input[placeholder="Name, phone, email…"]'
    MEMBER_ROWS = 'table tbody tr'
    ADD_MEMBER_BUTTON = 'button:has-text("Add member")'
    STATUS_CHIPS = 'button.font-mono.text-xs'  # Chip filters: All, Active, Frozen, Expired, Inactive

    # Selectors - Member Details
    MEMBER_TITLE = 'h1.text-primary'
    DETAILS_PANEL = 'div.grid-cols-\\[280px_1fr\\] > div:first-child'  # Profile summary on the left
    PLAN_PANEL = 'div.grid-cols-\\[280px_1fr\\] > div:nth-child(2)'    # Active/Pending Plan on the right

    # Action Buttons on Profile
    LINK_TELEGRAM_BUTTON = 'button:has-text("Link Telegram"), button:has-text("Re-link Telegram")'
    FREEZE_BUTTON = 'button:has-text("Freeze 14d")'
    RESUME_BUTTON = 'button:has-text("Resume")'
    ASSIGN_PLAN_BUTTON = 'button:has-text("Assign plan")'
    COPY_ID_BUTTON = 'button:has-text("Copy ID for payment")'

    # Success/Error and Linking Code boxes
    SUCCESS_ALERT = 'div[class*="border-ozone"]'
    ERROR_ALERT = 'div[class*="border-danger"]'
    LINKING_CODE_BOX = 'div[class*="border-coral/40"]'  # Parent container of linking code
    LINKING_CODE_VAL = 'div[class*="border-coral/40"] div.text-3xl'

    def navigate_members(self) -> None:
        """Navigates directly to the members directory page."""
        self.navigate(f"{settings.BASE_URL}/members")

    def search_members(self, query: str) -> None:
        """Fills the search field with query, waiting for the search request to settle."""
        self.wait_for(self.SEARCH_INPUT)
        with self.page.expect_response("**/api/v1/members*"):
            self.fill(self.SEARCH_INPUT, query)

    def select_status_filter(self, status: str) -> None:
        """Clicks a status filter tab and waits for the request to resolve."""
        if status.lower() == "active":
            selector = f'{self.STATUS_CHIPS}:not(:has-text("Inactive")):has-text("Active")'
        else:
            selector = f'{self.STATUS_CHIPS}:has-text("{status.capitalize()}")'
        self.wait_for(selector)
        with self.page.expect_response("**/api/v1/members*"):
            self.click(selector)

    def get_member_row_count(self) -> int:
        """Gets count of rows in member list."""
        return self.count(self.MEMBER_ROWS)

    def get_member_row_status_selector(self, index: int) -> str:
        """Returns the selector for the status pill of a member row by index."""
        return f"{self.MEMBER_ROWS}:nth-child({index + 1}) span.pill"

    def click_member_row_by_name(self, name: str) -> None:
        """Clicks the row matching the member's full name."""
        selector = f'{self.MEMBER_ROWS}:has-text("{name}")'
        self.wait_for(selector)
        self.click(selector)

    # Member Profile Methods
    def get_profile_name(self) -> str:
        """Gets the member name header text from profile."""
        self.wait_for(self.MEMBER_TITLE)
        return self.get_text(self.MEMBER_TITLE)

    def get_profile_info(self, field_name: str) -> str:
        """Gets profile info value (e.g. Phone, Email, Status, Locale) from details panel."""
        self.wait_for(self.DETAILS_PANEL)
        selector = f'{self.DETAILS_PANEL} > div:has-text("{field_name.capitalize()}") span.font-medium'
        return self.get_inner_text(selector)

    def generate_linking_code(self) -> str:
        """Clicks the Link Telegram button and returns the generated 6-digit code."""
        self.wait_for(self.LINK_TELEGRAM_BUTTON)
        self.click(self.LINK_TELEGRAM_BUTTON)
        self.wait_for(self.LINKING_CODE_VAL)
        return self.get_text(self.LINKING_CODE_VAL)

    def freeze_membership(self) -> None:
        """Clicks the Freeze 14d button."""
        self.wait_for(self.FREEZE_BUTTON)
        self.click(self.FREEZE_BUTTON)
        self.wait_for(self.SUCCESS_ALERT)

    def resume_membership(self) -> None:
        """Clicks the Resume button and waits for status to transition."""
        self.wait_for(self.RESUME_BUTTON)
        self.click(self.RESUME_BUTTON)
        self.wait_for(self.FREEZE_BUTTON)
