import pytest
from app.api.api_client import APIClient
from app.api.auth_api import AuthAPI
from app.api.members_api import MembersAPI
from app.api.plans_api import PlansAPI
from app.api.dashboard_api import DashboardAPI


@pytest.fixture(scope="session")
def api_client() -> APIClient:
    """Fixture providing a configured base APIClient instance."""
    return APIClient()


@pytest.fixture
def auth_api(api_client: APIClient) -> AuthAPI:
    """Fixture providing AuthAPI client."""
    return AuthAPI(api_client)


@pytest.fixture
def members_api(api_client: APIClient) -> MembersAPI:
    """Fixture providing MembersAPI client."""
    return MembersAPI(api_client)


@pytest.fixture
def plans_api(api_client: APIClient) -> PlansAPI:
    """Fixture providing PlansAPI client."""
    return PlansAPI(api_client)


@pytest.fixture
def dashboard_api(api_client: APIClient) -> DashboardAPI:
    """Fixture providing DashboardAPI client."""
    return DashboardAPI(api_client)
