import asyncio
import os
from pathlib import Path
import sys
from typing import Optional

from playwright.async_api import Page, async_playwright

try:
    from metrics.metrics import metrics_counter_inc
except ModuleNotFoundError:  # pragma: no cover - متریک در محیط prod الزامی نیست
    def metrics_counter_inc(*args, **kwargs):
        return None

try:
    from neo.utils import logger
except ModuleNotFoundError:  # pragma: no cover - در محیط‌های بدون neo از لاگر پیش‌فرض استفاده می‌کنیم
    import logging

    logger = logging.getLogger(__name__)

_BEDROCK_PROJECT = os.environ.get("BEDROCK_PROJECT", "")


def is_bedrock_env() -> bool:
    return _BEDROCK_PROJECT != ""


async def handle_new_page(page: Page):
    """
    Handle new page events and execute custom logic
    """
    print(f"New page created: {page.url}")


def _should_attempt_browser_install(exc: Exception) -> bool:
    message = str(exc)
    return "Executable doesn't exist" in message and "ms-playwright" in message


async def _install_playwright_chromium() -> bool:
    """Install Playwright Chromium browser at runtime if missing."""
    logger.warning("⚙️ Playwright Chromium browser not found. Attempting installation...")
    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if stdout:
            logger.info("Playwright install stdout: %s", stdout.decode().strip())
        if stderr:
            logger.warning("Playwright install stderr: %s", stderr.decode().strip())
        if process.returncode == 0:
            logger.info("✅ Playwright Chromium installation completed successfully.")
            return True
        logger.error("❌ Playwright Chromium installation failed with exit code %s", process.returncode)
    except FileNotFoundError:
        logger.error("❌ 'playwright' CLI not found. Ensure Playwright is installed and accessible in PATH.")
    except Exception as install_exc:  # pragma: no cover - راه‌اندازی در محیط prod
        logger.exception("❌ Unexpected error during Playwright installation: %s", install_exc)
    return False


async def visit_url_and_wait(
    url: str,
    wait_seconds: float = 4.0,
    *,
    headless: bool = True,
    timeout: Optional[float] = 30.0,
    _attempt_install: bool = True,
) -> None:
    """Open a Chromium page for the given URL and wait for the specified duration.

    Args:
        url: Target URL to open.
        wait_seconds: Seconds to keep the tab open after navigation.
        headless: Whether to run Chromium in headless mode.
        timeout: Navigation timeout in seconds; ``None`` disables the timeout.
    """

    playwright = await async_playwright().start()
    browser = None
    page = None
    playwright_stopped = False
    try:
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        goto_timeout = None if timeout is None else int(timeout * 1000)
        await page.goto(url, wait_until="domcontentloaded", timeout=goto_timeout)
        await page.wait_for_timeout(max(int(wait_seconds * 1000), 0))
        logger.info("✅ بازدید از لینک با موفقیت انجام شد: %s", url)
    except Exception as exc:
        if _attempt_install and _should_attempt_browser_install(exc):
            logger.warning("⚠️ Playwright Chromium executable missing. Trying to install and retry...")
            if page:
                await page.close()
                page = None
            if browser:
                await browser.close()
                browser = None
            if not playwright_stopped:
                await playwright.stop()
                playwright_stopped = True
            install_success = await _install_playwright_chromium()
            if install_success:
                logger.info("🔁 Retrying visit after Playwright installation...")
                return await visit_url_and_wait(
                    url,
                    wait_seconds,
                    headless=headless,
                    timeout=timeout,
                    _attempt_install=False,
                )
            logger.error("⚠️ Skipping visit; Playwright Chromium installation failed.")
        logger.exception("❌ خطا در باز کردن لینک %s: %s", url, exc)
        raise
    finally:
        if page:
            await page.close()
        if browser:
            await browser.close()
        if not playwright_stopped:
            await playwright.stop()


async def launch_chrome_debug(use_chrome_channel: bool = False, headless: bool = False):
    """
    Launch Chrome browser with remote debugging enabled on port 9222
    Returns the browser instance when launched successfully
    """
    try:
        extension_path = Path(os.path.dirname(__file__)).joinpath("browser_extension/error_capture")  # type: ignore
        playwright = await async_playwright().start()
        disable_security_args = [
            "--disable-web-security",
            "--disable-site-isolation-trials",
            "--disable-features=IsolateOrigins,site-per-process",
        ]
        workspace = "/workspace" if is_bedrock_env() else "./workspace"
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=os.path.join(workspace, "browser", "user_data"),
            headless=headless,
            viewport={"width": 1280, "height": 720},
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-popup-blocking",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-window-activation",
                "--disable-focus-on-load",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-position=0,0",
            ]
            + disable_security_args
            + [
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}",
                "--disable-web-security",
                "--disable-site-isolation-trials",
                "--remote-debugging-port=9222",
            ],
            channel="chromium" if not use_chrome_channel else "chrome",
            # proxy={"server": "http://data-capture-online.xaminim.com:3160", "username": "default-user", "password": "default"},
        )
        metrics_counter_inc("agent_browser_launch", {"status": "success"})

        # 监听新页面事件
        context.on("page", handle_new_page)

        # 处理已经打开的页面
        for page in context.pages:
            await handle_new_page(page)

        # Keep browser process alive
        while True:
            await asyncio.sleep(1000)

    except Exception as e:
        logger.exception(f"Failed to launch Chrome browser: {str(e)}")
        metrics_counter_inc("agent_browser_launch", {"status": "failed"})
        raise


if __name__ == "__main__":
    asyncio.run(launch_chrome_debug())
