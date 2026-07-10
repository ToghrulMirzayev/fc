from app.pages.base_page import BasePage
from app.components.sidebar import Sidebar


class DashboardPage(BasePage):
    """Page Object representing the admin dashboard."""

    def __init__(self, page) -> None:
        super().__init__(page)
        self.sidebar = Sidebar(page)

    # Selectors
    GREETING_HEADER = 'h1:has-text("Good morning"), h1:has-text("Good afternoon"), h1:has-text("Good evening")'
    KPI_CARDS = 'div.grid-cols-4 > div'

    def get_greeting(self) -> str:
        """Gets the welcome greeting text from the page header."""
        self.wait_for(self.GREETING_HEADER)
        return self.get_inner_text(self.GREETING_HEADER)

    def get_kpi_card_count(self) -> int:
        """Returns the number of KPI cards visible on the dashboard."""
        self.wait_for(f"{self.KPI_CARDS}:first-child")
        return self.count(self.KPI_CARDS)

    def get_kpi_card_data(self, index: int) -> dict:
        """Retrieves label and value for a specific KPI card by index (0-indexed)."""
        card_selector = f"{self.KPI_CARDS}:nth-child({index + 1})"
        label = self.get_inner_text(f"{card_selector} div.tracking-caps")
        value = self.get_inner_text(f"{card_selector} div.text-3xl")
        return {"label": label, "value": value}
