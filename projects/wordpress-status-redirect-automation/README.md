# WordPress Status & Redirect Automation

**Project Type:** Application Engineering · Workflow Automation · Browser Automation

**Technologies:** Python, Playwright, WordPress, Yoast SEO, Google Colab, GitHub Actions

## 1. Project Overview

This project focuses on automating the administrative process of managing completed event and campaign pages on WordPress websites.

When an event finishes, its page needs to be set to Draft and its previous public URL redirected to the homepage. The automation streamlines these tasks using browser interactions, conditional checks, and verification.

## 2. Problem Statement

The original process required manually:

1. Logging into the WordPress administration dashboard.
2. Locating the relevant event or campaign page.
3. Changing the page status to Draft and saving the update.
4. Opening Yoast SEO Redirect Manager.
5. Creating a redirect from the old page URL to the homepage.
6. Visiting the original URL to confirm the redirect works.

Repeating these steps across multiple pages takes time and increases the risk of missed redirects, duplicate entries, and unnecessary updates.

## 3. Solution

Developed a Python-based browser automation workflow using Playwright to process target WordPress pages sequentially.

The workflow checks the existing page status, updates it only when necessary, checks for existing redirects, creates missing redirects, and verifies the results.

Google Colab is used for development and testing. GitHub provides version control, while GitHub Actions can support scheduled and manually triggered execution on compatible websites.

## 4. Workflow

1. Configure the target website and page identifiers.
2. Authenticate to the WordPress administration dashboard.
3. Inspect the current publication status.
4. If the page is already Draft, skip the status-change operation.
5. If the page is not Draft, change it to Draft and verify the update.
6. Open Yoast SEO Redirect Manager.
7. Check whether the required redirect already exists.
8. Create the redirect only when it is missing.
9. Visit the original public URL and verify the redirect destination.
10. Record the outcome and investigate any failures.

## 5. Safeguards

| Condition | Expected behaviour |
|---|---|
| Page is already Draft | Skip the status update |
| Page is not Draft | Set it to Draft and verify the result |
| Redirect already exists | Skip redirect creation |
| Redirect is missing | Create the required redirect |
| Frontend redirect fails | Record the failure for investigation |
| Authentication or security challenge blocks execution | Stop or use the supported authentication approach |

These safeguards are intended to make repeated execution more predictable and prevent unnecessary administrative changes.

## 6. Tools and Execution

### Python and Playwright

Used to automate browser interactions with WordPress administration pages and perform sequential processing of target pages.

### Google Colab

Used as a development and testing environment for the Python automation script.

### GitHub and GitHub Actions

Used to maintain the automation source code and support scheduled or manually triggered workflows where the website's authentication and security configuration permits execution.

### WordPress and Yoast SEO

WordPress manages the page publication status, while Yoast SEO Redirect Manager handles the redirects from old URLs to the homepage.

## 7. Testing Scenarios

The workflow should be evaluated against the following scenarios:

- A published page that needs to become Draft.
- A page that is already Draft.
- A page with an existing redirect.
- A page with a missing redirect.
- A redirect that does not reach the intended destination.
- An authentication failure or browser execution error.

Test results should be recorded as successful, skipped, or failed based on the actual outcome.

## 8. Practical AI-Assisted Development

AI tools can support code drafting, troubleshooting, test-case planning, and technical documentation.

Generated suggestions still require code review and execution-based validation. The automation must be tested against actual WordPress behaviour rather than assuming that generated code is correct.

## 9. Skills Demonstrated

- Python scripting and browser automation
- Playwright
- WordPress administration and page lifecycle management
- Yoast SEO redirect management
- Conditional logic and duplicate prevention
- Workflow scheduling with GitHub Actions
- Testing, verification, and troubleshooting
- Technical documentation and process improvement
- Practical AI-assisted development

## 10. Project Status

This case study documents the workflow design and intended safeguards. Implementation evidence, test results, and redacted screenshots will be added as the project documentation is finalised.

## Security Considerations

Production credentials, passwords, session cookies, authentication tokens, and confidential internal information must not be committed to this repository.

