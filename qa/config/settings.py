import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve and load root .env file if it exists
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

ENV = os.getenv("ENV", "local")
_config_path = Path(__file__).parent / "environments" / f"{ENV}.json"

if not _config_path.exists():
    _config = {
        "BASE_URL": "http://localhost:3000",
        "API_URL": "http://localhost:8000",
        "ADMIN_EMAIL": "demo@fitnesscourt.com",
        "ADMIN_PASSWORD": "demo12345",
        "HEADLESS": True,
        "SLOW_MO": 0,
        "BROWSER": "chromium",
        "TIMEOUT": 30000,
    }
else:
    with open(_config_path) as f:
        _config = json.load(f)

# Allow environment variables to override JSON configs (highest precedence)
BASE_URL: str = os.getenv("BASE_URL", _config["BASE_URL"]).rstrip("/")
API_URL: str = os.getenv("API_URL", _config["API_URL"]).rstrip("/")
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", _config["ADMIN_EMAIL"])
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", _config["ADMIN_PASSWORD"])
HEADLESS: bool = os.getenv("HEADLESS", str(_config["HEADLESS"])).lower() in ("true", "1", "yes")
SLOW_MO: int = int(os.getenv("SLOW_MO", str(_config["SLOW_MO"])))
BROWSER: str = os.getenv("BROWSER", _config["BROWSER"]).lower()
TIMEOUT: int = int(os.getenv("TIMEOUT", str(_config.get("TIMEOUT", 30000))))


class Settings:
    """Framework-wide settings configuration class loaded dynamically from environments."""

    def __init__(self) -> None:
        self.BASE_URL = BASE_URL
        self.API_URL = API_URL
        self.ADMIN_EMAIL = ADMIN_EMAIL
        self.ADMIN_PASSWORD = ADMIN_PASSWORD
        self.HEADLESS = HEADLESS
        self.SLOW_MO = SLOW_MO
        self.BROWSER = BROWSER
        self.TIMEOUT = TIMEOUT


settings = Settings()
