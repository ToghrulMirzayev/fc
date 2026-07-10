import re
import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from app.pages.members_page import MembersPage


@pytest.mark.members
class TestMembers:
    """Suite of tests covering Member directory search, filtering, and profile actions."""

    def test_search_and_navigate_to_profile(self, authenticated_page: Page, members_page: MembersPage):
        """Verifies searching for a member and clicking their profile."""
        members_page.navigate_members()

        # Search for a seeded member (Aysel Mammadova)
        target_member = "Aysel Mammadova"
        members_page.search_members(target_member)
        members_page.wait_for(f'{members_page.MEMBER_ROWS}:has-text("{target_member}")')
        
        # Verify result row displays
        assert members_page.get_member_row_count() >= 1
        
        # Navigate to detail page
        members_page.click_member_row_by_name(target_member)
        
        # Verify URL is correct (using UUID pattern regex)
        expect(members_page.page).to_have_url(re.compile(rf"{settings.BASE_URL}/members/[0-9a-fA-F\-]+"))
        
        # Verify detail page headers
        assert members_page.get_profile_name() == target_member
        assert members_page.get_profile_info("Phone") == "+994 50 123 4567"
        assert members_page.get_profile_info("Email") == "aysel.m@example.az"
        assert members_page.get_profile_info("Status") == "active"

    def test_telegram_link_code_generation(self, authenticated_page: Page, members_page: MembersPage):
        """Verifies generating a 6-digit one-time Telegram registration code on the profile."""
        members_page.navigate_members()
        
        # Navigate to a member profile
        members_page.search_members("Aysel Mammadova")
        members_page.click_member_row_by_name("Aysel Mammadova")
        
        # Generate link code
        code = members_page.generate_linking_code()
        
        # Check it is a valid 6-digit numeric string
        assert len(code) == 6
        assert code.isdigit()

    def test_status_filter_tabs(self, authenticated_page: Page, members_page: MembersPage):
        """Verifies filtering members via status tabs (Active, Inactive)."""
        members_page.navigate_members()
        
        # Filter by Active
        members_page.select_status_filter("Active")
        row_count = members_page.get_member_row_count()
        
        # Check if rows exist (at least one active member in seeds)
        assert row_count > 0
        
        # Verify all displayed rows are 'active' (using selectors from the page object)
        for i in range(min(row_count, 5)):
            status_pill_selector = members_page.get_member_row_status_selector(i)
            expect(members_page.page.locator(status_pill_selector)).to_have_text("active")
