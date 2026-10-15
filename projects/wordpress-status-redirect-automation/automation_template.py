"""
WordPress Status & Redirect Automation — Portfolio Template
===========================================================

A configurable Playwright scaffold demonstrating a cautious workflow for:
1. Checking a WordPress post/page status.
2. Changing it to Draft only when necessary.
3. Checking whether a Yoast redirect already exists.
4. Creating a 301 regex redirect only when absence is confirmed.
5. Verifying the saved status and public redirect.

IMPORTANT
---------
- This is a public portfolio template, not a plug-and-play script.
- Configure selectors for the exact WordPress / Yoast versions you use.
- Run against a staging site or disposable test page first.
- Authentication is intentionally manual. Complete any WordPress, 2FA, or
  Cloudflare checks yourself. This script does not bypass security challenges.
- Do not commit passwords, session cookies, TOTP seeds, API keys, or real
  production URLs/page IDs to a public repository.
- The redirect-list selectors are site/version-specific. The script fails
  closed if it cannot confidently check for an existing redirect.

Install:
    python -m pip install playwright
    python -m playwright install chromium

Run:
    python automation_template.py

Environment variables:
    WP_BASE_URL=https://staging.example.com
    WP_LOGIN_URL=https://staging.example.com/wp-login.php
    WP_REDIRECTS_URL=https://staging.example.com/wp-admin/admin.php?page=wpseo_redirects
    WP_HOME_URL=https://staging.example.com/
    WP_HEADLESS=false

Optional target configuration:
    WP_TARGETS_JSON=[{"name":"Demo page","edit_url":"https://staging.example.com/wp-admin/post.php?post=123&action=edit","public_url":"https://staging.example.com/demo-page/","regex_source":"^/demo-page/?$"}]

The JSON example above is illustrative only. Use test URLs and IDs you control.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("WP_BASE_URL", "").rstrip("/")
LOGIN_URL = os.getenv("WP_LOGIN_URL", f"{BASE_URL}/wp-login.php")
REDIRECTS_URL = os.getenv(
    "WP_REDIRECTS_URL",
    f"{BASE_URL}/wp-admin/admin.php?page=wpseo_redirects",
)
HOME_URL = os.getenv("WP_HOME_URL", f"{BASE_URL}/")
HEADLESS = os.getenv("WP_HEADLESS", "false").strip().lower() in {
    "1", "true", "yes", "on"
}
LOGIN_TIMEOUT_SECONDS = int(os.getenv("WP_LOGIN_TIMEOUT_SECONDS", "180"))
ACTION_TIMEOUT_MS = int(os.getenv("WP_ACTION_TIMEOUT_MS", "15000"))
VERIFY_TIMEOUT_MS = int(os.getenv("WP_VERIFY_TIMEOUT_MS", "15000"))


@dataclass(frozen=True)
class Target:
    name: str
    edit_url: str
    public_url: str
    regex_source: str


def load_targets() -> list[Target]:
    raw = os.getenv("WP_TARGETS_JSON", "").strip()
    if not raw:
        raise RuntimeError(
            "WP_TARGETS_JSON is empty. Configure at least one disposable "
            "staging/test page before running."
        )

    try:
        records = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"WP_TARGETS_JSON is not valid JSON: {exc}") from exc

    if not isinstance(records, list) or not records:
        raise RuntimeError("WP_TARGETS_JSON must be a non-empty JSON array.")

    targets: list[Target] = []
    for index, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"Target #{index} must be a JSON object.")
        try:
            target = Target(
                name=str(item["name"]).strip(),
                edit_url=str(item["edit_url"]).strip(),
                public_url=str(item["public_url"]).strip(),
                regex_source=str(item["regex_source"]).strip(),
            )
        except KeyError as exc:
            raise RuntimeError(
                f"Target #{index} is missing required field {exc.args[0]!r}."
            ) from exc

        if not all(
            (target.name, target.edit_url, target.public_url, target.regex_source)
        ):
            raise RuntimeError(f"Target #{index} contains an empty required field.")

        for candidate in (target.edit_url, target.public_url):
            parsed = urlparse(candidate)
            if parsed.scheme != "https" or not parsed.netloc:
                raise RuntimeError(
                    f"Target #{index} URLs must be valid HTTPS URLs."
                )
            if BASE_URL and parsed.netloc != urlparse(BASE_URL).netloc:
                raise RuntimeError(
                    f"Target #{index} URL host must match WP_BASE_URL. "
                    "This template intentionally limits actions to one site."
                )

        if not target.regex_source.startswith("^"):
            raise RuntimeError(
                f"Target #{index} regex_source should begin with '^' "
                "for an anchored Yoast regex redirect."
            )
        targets.append(target)

    return targets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(message: str) -> None:
    print(message, flush=True)


def ensure_same_site(url: str) -> None:
    if not BASE_URL:
        raise RuntimeError("Set WP_BASE_URL before running.")
    if urlparse(url).netloc != urlparse(BASE_URL).netloc:
        raise RuntimeError(f"Refusing to navigate outside configured site: {url}")


async def wait_for_manual_login(page: Page) -> None:
    """
    Opens the login screen and waits for the operator to complete authentication.
    This does not attempt to bypass Cloudflare or any other security challenge.
    """
    ensure_same_site(LOGIN_URL)
    log(f"Opening WordPress login: {LOGIN_URL}")
    await page.goto(LOGIN_URL, wait_until="domcontentloaded")
    log(
        "Complete WordPress login, 2FA, and any security checks in the browser. "
        "The script will continue once a WordPress admin page is detected."
    )

    deadline = asyncio.get_running_loop().time() + LOGIN_TIMEOUT_SECONDS
    while asyncio.get_running_loop().time() < deadline:
        current = page.url
        current_host = urlparse(current).netloc
        if current_host == urlparse(BASE_URL).netloc:
            is_login = "wp-login.php" in current
            is_admin = "/wp-admin/" in current and not is_login
            if is_admin:
                log("Admin area detected; continuing.")
                return

        # Security challenges must be completed by the operator.
        try:
            title = (await page.title()).lower()
            body = (await page.locator("body").inner_text(timeout=1000)).lower()
            challenge_words = (
                "checking your browser",
                "verify you are human",
                "security check",
                "just a moment",
            )
            if any(word in title or word in body[:4000] for word in challenge_words):
                log("Security challenge detected. Complete it manually in the browser.")
        except PlaywrightTimeoutError:
            pass

        await asyncio.sleep(1)

    raise TimeoutError(
        "Timed out waiting for manual authentication. No security challenge "
        "was bypassed. Check the browser and increase WP_LOGIN_TIMEOUT_SECONDS "
        "if appropriate."
    )


async def read_post_status(page: Page) -> str:
    """Read WordPress's current status from the classic post editor."""
    status_select = page.locator("#post_status")
    await status_select.wait_for(state="attached", timeout=ACTION_TIMEOUT_MS)
    value = (await status_select.input_value()).strip().lower()
    if not value:
        raise RuntimeError("The post status selector returned an empty value.")
    return value


async def set_status_to_draft_if_needed(page: Page, target: Target) -> None:
    ensure_same_site(target.edit_url)
    log(f"[{target.name}] Opening editor.")
    await page.goto(target.edit_url, wait_until="domcontentloaded")
    await page.locator("#post_status").wait_for(
        state="attached", timeout=ACTION_TIMEOUT_MS
    )

    current_status = await read_post_status(page)
    log(f"[{target.name}] Current status: {current_status}")

    if current_status == "draft":
        log(f"[{target.name}] Already Draft; skipping status update.")
        return

    # Classic WordPress editor controls. Gutenberg or custom editors may need
    # a site-specific adapter; fail rather than guessing at a control.
    edit_status = page.locator("#post-status-select a.edit-post-status")
    if await edit_status.count() == 0:
        edit_status = page.get_by_role("button", name=re.compile("edit status", re.I))

    if await edit_status.count() == 0:
        raise RuntimeError(
            f"[{target.name}] Cannot find the status-edit control. "
            "Configure the editor adapter for this WordPress version."
        )

    await edit_status.first.click()
    draft_option = page.locator("#post_status option[value='draft']")
    await draft_option.wait_for(state="attached", timeout=ACTION_TIMEOUT_MS)
    await page.locator("#post_status").select_option("draft")

    ok_button = page.locator("#post-status-select a.save-post-status")
    if await ok_button.count():
        await ok_button.first.click()
    else:
        # Some editor versions apply the select immediately. Saving still
        # must be explicitly performed and verified below.
        log(f"[{target.name}] Status selection applied; continuing to save.")

    update_button = page.locator("#publish, #save-post")
    if await update_button.count() == 0:
        update_button = page.get_by_role(
            "button", name=re.compile(r"^(update|save draft|save)$", re.I)
        )
    if await update_button.count() == 0:
        raise RuntimeError(
            f"[{target.name}] Cannot find a save/update button; refusing to guess."
        )

    await update_button.first.click()
    await page.wait_for_load_state("domcontentloaded", timeout=VERIFY_TIMEOUT_MS)

    # Reopen the editor to verify persisted state rather than trusting the click.
    await page.goto(target.edit_url, wait_until="domcontentloaded")
    saved_status = await read_post_status(page)
    if saved_status != "draft":
        raise RuntimeError(
            f"[{target.name}] Status verification failed; expected 'draft', "
            f"found {saved_status!r}."
        )
    log(f"[{target.name}] Draft status saved and verified.")


async def redirect_exists(page: Page, regex_source: str, target_url: str) -> bool:
    """
    SAFETY GATE — implement for your exact Yoast Redirect Manager version.

    The redirect list UI and selectors vary between Yoast versions. This
    template deliberately does not guess selectors or assume that a redirect
    is absent merely because it is not visible on the current screen.

    Implement this function to inspect the existing redirect list (including
    pagination/search if present) and return True only when the matching regex
    source and destination are confirmed. If the check cannot be completed,
    raise an exception so a duplicate redirect is not created.
    """
    del page, regex_source, target_url
    raise NotImplementedError(
        "Configure redirect_exists() for your Yoast version before running. "
        "Failing closed to avoid duplicate redirects."
    )


async def add_redirect_if_missing(
    page: Page, regex_source: str, target_url: str, name: str
) -> None:
    ensure_same_site(REDIRECTS_URL)
    ensure_same_site(target_url)
    await page.goto(REDIRECTS_URL, wait_until="domcontentloaded")

    # A positive, working existing-redirect check is required before adding.
    exists = await redirect_exists(page, regex_source, target_url)
    if exists:
        log(f"[{name}] Matching redirect already exists; skipping creation.")
        return

    # Configure these selectors only after inspecting your Yoast version.
    # Deliberately do not guess which inputs correspond to source/target/type.
    raise NotImplementedError(
        "Redirect absence was confirmed, but the Yoast add-form selectors and "
        "save confirmation must be configured for your version before use."
    )


async def verify_public_redirect(page: Page, target: Target) -> None:
    ensure_same_site(target.public_url)
    ensure_same_site(HOME_URL)

    log(f"[{target.name}] Verifying public redirect.")
    response = await page.goto(
        target.public_url, wait_until="domcontentloaded", timeout=VERIFY_TIMEOUT_MS
    )
    final_url = page.url.rstrip("/")
    expected_url = HOME_URL.rstrip("/")

    if response is not None and response.status >= 500:
        raise RuntimeError(
            f"[{target.name}] Frontend returned HTTP {response.status}."
        )
    if urlparse(final_url).netloc != urlparse(expected_url).netloc:
        raise RuntimeError(
            f"[{target.name}] Redirect landed on an unexpected host: {final_url}"
        )
    if final_url != expected_url:
        raise RuntimeError(
            f"[{target.name}] Redirect verification failed. "
            f"Expected {expected_url}, received {final_url}."
        )
    log(f"[{target.name}] Frontend redirect verified: {final_url}")


async def main() -> int:
    if not BASE_URL:
        log("ERROR: Set WP_BASE_URL to your staging/test WordPress site.")
        return 2

    try:
        targets = load_targets()
    except RuntimeError as exc:
        log(f"CONFIGURATION ERROR: {exc}")
        return 2

    for url in (LOGIN_URL, REDIRECTS_URL, HOME_URL):
        try:
            ensure_same_site(url)
        except RuntimeError as exc:
            log(f"CONFIGURATION ERROR: {exc}")
            return 2

    failures: list[str] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=HEADLESS)
        context: BrowserContext = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(ACTION_TIMEOUT_MS)

        try:
            await wait_for_manual_login(page)

            for target in targets:
                log("=" * 64)
                try:
                    await set_status_to_draft_if_needed(page, target)
                    await add_redirect_if_missing(
                        page, target.regex_source, HOME_URL, target.name
                    )
                    await verify_public_redirect(page, target)
                    log(f"[{target.name}] COMPLETE")
                except Exception as exc:
                    failures.append(f"{target.name}: {exc}")
                    log(f"[{target.name}] FAILED: {exc}")
                    # Continue to report other target outcomes; no silent success.
        finally:
            await context.close()
            await browser.close()

    log("=" * 64)
    if failures:
        log(f"Finished with {len(failures)} failure(s):")
        for failure in failures:
            log(f" - {failure}")
        return 1

    log(f"Finished successfully for {len(targets)} target(s).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        log("Stopped by operator.")
        sys.exit(130)
