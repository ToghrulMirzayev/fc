import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from app.pages.dashboard_page import DashboardPage


@pytest.mark.dashboard
class TestDashboard:
    """Suite of tests covering the admin dashboard operations and layouts."""

    def test_dashboard_greeting_and_cards(self, authenticated_page: Page, dashboard_page: DashboardPage):
        """Verifies that the dashboard greeting loads correctly and all KPI metrics cards are visible."""
        # 1. Greeting message checks
        greeting = dashboard_page.get_greeting()
        assert "good" in greeting.lower()
        assert "demo" in greeting.lower()

        # 2. KPI metrics layout checks
        assert dashboard_page.get_kpi_card_count() == 4
        
        expected_kpi_labels = [
            "Active members",
            "Revenue / Month",
            "Check-ins today",
            "Churn risk"
        ]

        for i, expected_label in enumerate(expected_kpi_labels):
            kpi_data = dashboard_page.get_kpi_card_data(i)
            assert kpi_data["label"] == expected_label.upper()
            assert kpi_data["value"] is not None
            assert len(kpi_data["value"].strip()) > 0

    def test_sidebar_navigation_flow(self, authenticated_page: Page, dashboard_page: DashboardPage):
        """Verifies that clicking navigation items in the sidebar transitions to correct URLs."""
        # Click to members
        dashboard_page.sidebar.click_members()
        expect(dashboard_page.page).to_have_url(f"{settings.BASE_URL}/members")

        # Click to plans
        dashboard_page.sidebar.click_plans()
        expect(dashboard_page.page).to_have_url(f"{settings.BASE_URL}/plans")
