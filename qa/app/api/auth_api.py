import logging
from app.api.api_client import APIClient
from models.auth_model import LoginResponse

logger = logging.getLogger(__name__)


class AuthAPI:
    """API client dedicated to authentication endpoints."""

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def login(self, email: str, password: str) -> LoginResponse:
        """Logs in via the API and returns the typed LoginResponse containing access and refresh tokens."""
        logger.info(f"Logging in user via API: {email}")
        payload = {"email": email, "password": password}
        response = self.client.request("POST", "/api/v1/auth/login", json_data=payload)
        
        assert isinstance(response, dict)
        res = LoginResponse(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            token_type=response.get("token_type", "bearer")
        )
        self.client.set_token(res.access_token)
        return res
