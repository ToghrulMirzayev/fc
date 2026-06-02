import json
import logging
import urllib.request
from urllib.error import HTTPError
from config.settings import settings

logger = logging.getLogger(__name__)


class APIClient:
    """Base API client handling raw requests, token storage, and serialization."""

    def __init__(self, base_url: str = settings.API_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token: str | None = None

    def set_token(self, token: str) -> None:
        """Sets the authorization token for subsequent requests."""
        self.access_token = token

    def request(self, method: str, path: str, json_data: dict | None = None, headers: dict | None = None) -> dict | list:
        """Performs an HTTP request and parses the JSON response."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = {"Content-Type": "application/json"}
        
        if headers:
            req_headers.update(headers)
        
        if self.access_token and "Authorization" not in req_headers:
            req_headers["Authorization"] = f"Bearer {self.access_token}"

        req_data = None
        if json_data is not None:
            req_data = json.dumps(json_data).encode("utf-8")

        req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
        logger.info(f"API Request: {method} {url}")

        try:
            with urllib.request.urlopen(req) as res:
                response_bytes = res.read()
                if not response_bytes:
                    return {}
                return json.loads(response_bytes.decode("utf-8"))
        except HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                error_body = "Could not read error body"
            logger.error(f"API Request failed: {e.code} - {error_body}")
            raise e
