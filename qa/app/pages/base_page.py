import logging
import os
from pathlib import Path
from playwright.sync_api import Page, Response

logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all Page Objects in the framework.

    Contains atomic Playwright wrappers only.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    # --- Basic interactions ---

    def click(self, locator: str, timeout: float | None = None) -> None:
        """Clicks an element defined by locator."""
        logger.debug(f"Clicking element: {locator}")
        self.page.locator(locator).click(timeout=timeout)

    def fill(self, locator: str, value: str, timeout: float | None = None) -> None:
        """Fills an input field with the provided value after clearing it."""
        logger.debug(f"Filling element {locator} with value: {value}")
        self.page.locator(locator).fill(value, timeout=timeout)

    def hover(self, locator: str) -> None:
        """Hovers over the element defined by locator."""
        logger.debug(f"Hovering over element: {locator}")
        self.page.locator(locator).hover()

    # --- Text retrieval ---

    def get_text(self, locator: str, timeout: float | None = None) -> str:
        """Retrieves text content of an element."""
        # Wait for it to be attached/visible according to locator defaults
        text = self.page.locator(locator).text_content(timeout=timeout) or ""
        logger.debug(f"Text for {locator}: {text}")
        return text

    def get_inner_text(self, locator: str, timeout: float | None = None) -> str:
        """Retrieves inner text of an element."""
        text = self.page.locator(locator).inner_text(timeout=timeout)
        logger.debug(f"Inner text for {locator}: {text}")
        return text

    def get_input_value(self, locator: str, timeout: float | None = None) -> str:
        """Retrieves the input value of a form field."""
        value = self.page.locator(locator).input_value(timeout=timeout)
        logger.debug(f"Input value for {locator}: {value}")
        return value

    def get_all_texts(self, locator: str) -> list[str]:
        """Retrieves list of text contents for all matching elements."""
        texts = self.page.locator(locator).all_text_contents()
        logger.debug(f"All texts for {locator}: {texts}")
        return texts

    # --- Element count ---

    def count(self, locator: str) -> int:
        """Returns the number of elements matching the locator."""
        cnt = self.page.locator(locator).count()
        logger.debug(f"Count for {locator}: {cnt}")
        return cnt

    # --- Form controls ---

    def select_option(self, locator: str, **kwargs) -> list[str]:
        """Selects options in a dropdown element."""
        logger.debug(f"Selecting option on {locator} with args: {kwargs}")
        return self.page.locator(locator).select_option(**kwargs)

    def check(self, locator: str) -> None:
        """Checks a checkbox or radio button."""
        logger.debug(f"Checking element: {locator}")
        self.page.locator(locator).check()

    def uncheck(self, locator: str) -> None:
        """Unchecks a checkbox."""
        logger.debug(f"Unchecking element: {locator}")
        self.page.locator(locator).uncheck()

    def upload_file(self, locator: str, files: str | Path | list[str | Path]) -> None:
        """Sets input files for file upload inputs."""
        logger.debug(f"Uploading files {files} to element: {locator}")
        self.page.locator(locator).set_input_files(files)

    # --- State checks ---

    def is_visible(self, locator: str, timeout: float | None = None) -> bool:
        """Checks if an element is visible on the screen."""
        try:
            # page.is_visible does not auto-wait, it checks instantly.
            # However, self.page.locator(locator).is_visible() is the same.
            visible = self.page.locator(locator).is_visible(timeout=timeout)
            logger.debug(f"Element {locator} visibility: {visible}")
            return visible
        except Exception:
            return False

    def is_hidden(self, locator: str, timeout: float | None = None) -> bool:
        """Checks if an element is hidden or not in the DOM."""
        try:
            hidden = self.page.locator(locator).is_hidden(timeout=timeout)
            logger.debug(f"Element {locator} hiddenness: {hidden}")
            return hidden
        except Exception:
            return True

    # --- Waits & navigation ---

    def wait_for(self, locator: str, state: str = "visible", timeout: float | None = None) -> None:
        """Waits for an element to satisfy a specific state (visible, hidden, attached, detached)."""
        logger.debug(f"Waiting for selector: {locator} state: {state}")
        # Convert state from standard naming if needed
        self.page.locator(locator).wait_for(state=state, timeout=timeout)

    def navigate(self, url: str) -> Response | None:
        """Navigates to the specified URL."""
        logger.debug(f"Navigating to: {url}")
        return self.page.goto(url)

    def take_screenshot(self, name: str) -> None:
        """Takes a full page screenshot for debugging purposes."""
        # Ensure directories exist
        os.makedirs("artifacts/screenshots", exist_ok=True)
        path = f"artifacts/screenshots/{name}.png"
        logger.debug(f"Taking screenshot: {path}")
        self.page.screenshot(path=path, full_page=True)
