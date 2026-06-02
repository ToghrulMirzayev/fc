import logging
import os
import pytest
from config.settings import settings

# Setup root logger level
logging.basicConfig(level=logging.INFO)

# Register modular fixture plugins
pytest_plugins = [
    "fixtures.ui",
    "fixtures.api",
    "fixtures.data",
]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Override viewport and context options."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Override headless mode and slow_mo delay from settings."""
    return {
        **browser_type_launch_args,
        "headless": settings.HEADLESS,
        "slow_mo": settings.SLOW_MO,
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture screenshots on test failure and save to artifacts/screenshots/."""
    outcome = yield
    rep = outcome.get_result()
    
    # Capture screenshot only if test failed in actual call phase
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            screenshot_dir = "artifacts/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            # Sanitize file name
            clean_name = "".join(c for c in item.name if c.isalnum() or c in ("-", "_")).rstrip()
            screenshot_path = f"{screenshot_dir}/{clean_name}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                logging.info(f"Captured failure screenshot to {screenshot_path}")
            except Exception as e:
                logging.warning(f"Failed to capture failure screenshot: {e}")
