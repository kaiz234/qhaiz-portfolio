# Test Plan — WordPress Status & Redirect Automation

## 1. Purpose

This test plan describes how to validate a configurable Playwright workflow that changes a WordPress page to Draft when needed, manages a Yoast SEO redirect, and verifies the resulting public redirect.

This is a portfolio demonstration plan. Run tests on a staging site or disposable test pages that you control.

## 2. Scope

### In scope
- Manual WordPress authentication and waiting for an authenticated admin page.
- Reading the current post status.
- Skipping the status update when the page is already Draft.
- Saving and rechecking a Draft status.
- Checking for an existing redirect before attempting to create one.
- Verifying the public redirect destination.
- Logging failures and reporting outcomes for configured targets.
- Rejecting invalid or cross-site target configuration.

### Out of scope
- Bypassing Cloudflare, CAPTCHA, WordPress login controls, or two-factor authentication.
- Testing against production pages without explicit authorization.
- Claiming a redirect was created without confirmation that the Yoast form saved it.
- Testing every WordPress editor, plugin version, theme, or hosting configuration.
- Performance, load, penetration, or security testing.

## 3. Preconditions

- Use a staging WordPress site or disposable test pages.
- Confirm the test account has only the permissions needed for the test.
- Complete login, 2FA, and any security challenge manually in the browser.
- Configure `WP_BASE_URL`, `WP_LOGIN_URL`, `WP_REDIRECTS_URL`, and `WP_HOME_URL`.
- Configure `WP_TARGETS_JSON` with test-only URLs and IDs.
- Adapt the status editor and Yoast selectors to the tested WordPress and Yoast versions.
- Implement and validate `redirect_exists()` before running redirect-creation tests.
- Implement the Yoast add-form and save-confirmation logic before treating the full workflow as runnable.
- Do not put passwords, TOTP seeds, cookies, API keys, or private production details in the repository.

## 4. Test cases

These are planned tests. They are not evidence that the tests have already been executed.

| ID | Scenario | Test setup / action | Expected result | Status |
|---|---|---|---|---|
| TC-01 | Valid configuration | Provide a valid staging URL and one test target | Configuration is accepted and the browser opens the configured site | Not run |
| TC-02 | Missing base URL | Leave `WP_BASE_URL` empty | Script stops with a configuration error before browser actions | Not run |
| TC-03 | Invalid target JSON | Set `WP_TARGETS_JSON` to malformed JSON | Script reports a configuration error and exits | Not run |
| TC-04 | Cross-site target URL | Configure a target on a different host | Script rejects the target and does not navigate to it | Not run |
| TC-05 | Manual authentication | Open login and complete login / 2FA manually | Script continues after an authenticated admin page is detected | Not run |
| TC-06 | Authentication timeout | Do not complete login within the configured timeout | Script stops with a timeout message | Not run |
| TC-07 | Page already Draft | Configure a test page whose status is Draft | Status update is skipped; redirect processing remains eligible to continue | Not run |
| TC-08 | Page not Draft | Configure a disposable page in Published status | Script selects Draft, saves, reopens the editor, and confirms Draft | Not run |
| TC-09 | Status control unavailable | Use an editor whose status controls do not match configured selectors | Script reports a clear failure rather than guessing at a control | Not run |
| TC-10 | Draft save does not persist | Observe a save that leaves the page non-Draft | Verification fails and the target is reported as failed | Not run |
| TC-11 | Matching redirect already exists | Configure the redirect checker to find the exact regex source and destination | Script skips redirect creation | Not run |
| TC-12 | Redirect checker cannot determine state | Make the redirect list unavailable or ambiguous | Script fails closed; it must not assume the redirect is absent | Not run |
| TC-13 | Redirect absent | Configure a confirmed absence in the redirect list | The configured Yoast form creates the redirect and confirms the saved result | Not run |
| TC-14 | Redirect save fails | Prevent the Yoast form from saving or withhold its success confirmation | Script reports failure; it must not report redirect creation as successful | Not run |
| TC-15 | Correct public redirect | Open the test page after a confirmed 301 redirect to the configured homepage | Final URL matches the expected homepage URL | Not run |
| TC-16 | Incorrect redirect destination | Redirect the test page to an unexpected path or host | Verification fails and reports the unexpected final URL | Not run |
| TC-17 | Frontend server error | Make the test URL return HTTP 5xx | Verification reports the server error | Not run |
| TC-18 | Multiple targets | Configure multiple disposable test pages, including one failing case | Each target receives an outcome log; failures are summarized at the end | Not run |
| TC-19 | Operator interruption | Stop the script with Ctrl+C | Script reports that it was stopped by the operator | Not run |

## 5. Acceptance criteria

The workflow is ready for a controlled demonstration when:
- Invalid configuration is rejected before changes are made.
- The script stays within the configured site.
- Already-Draft pages are not unnecessarily updated.
- A status change is verified by reopening the editor and reading the saved status.
- The redirect checker reliably distinguishes an existing redirect from an absent one.
- Redirect creation is followed by positive saved-state confirmation.
- The frontend check confirms the intended destination.
- Errors are visible in logs and included in the final failure summary.
- No secrets or private production details are stored in the public repository.

## 6. Evidence to capture

For each executed test, record:
- Test case ID and date.
- Environment (staging, WordPress version, Yoast version, browser version).
- Test page alias or sanitized identifier; avoid publishing real production IDs/URLs.
- Expected result and actual result.
- Pass / Fail / Blocked.
- Relevant sanitized log output or screenshot.
- Defect or follow-up notes.

Never include credentials, session cookies, TOTP seeds, personal data, or sensitive admin URLs in evidence.

## 7. Results summary template

Complete this section only after actually running the tests.

| Metric | Result |
|---|---|
| Tests planned | 19 |
| Tests executed | Not recorded |
| Passed | Not recorded |
| Failed | Not recorded |
| Blocked | Not recorded |
| Environment | Not recorded |

## 8. Known implementation gates

The current portfolio `automation_template.py` intentionally leaves two Yoast-specific operations unimplemented:

1. `redirect_exists()` — must inspect the redirect list and confirm whether the exact regex source and destination already exist.
2. `add_redirect_if_missing()` — must use selectors verified for the target Yoast version and confirm that the redirect was saved.

Until these are implemented and tested, redirect-management test cases are blocked and the script is not a complete end-to-end runnable solution. This is intentional: the template fails closed rather than risking duplicate or incorrectly configured redirects.

The WordPress status selectors may also require an adapter for Gutenberg or a customized editor.

## 9. Portfolio reporting note

Describe this file as a **test plan** until the cases have been executed and evidence recorded. Do not label planned tests as passed, and do not claim measured coverage or success rates without actual results.
