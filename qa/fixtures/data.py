import pytest
from data.users import DEMO_USER


@pytest.fixture
def test_user_creds() -> dict:
    """Fixture providing standard demo user credentials."""
    return {
        "email": DEMO_USER.email,
        "password": DEMO_USER.password,
        "tenant_slug": DEMO_USER.tenant_slug
    }
