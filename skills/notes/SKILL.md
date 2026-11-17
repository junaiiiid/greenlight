---
name: notes
description: Writes the App Review Information notes for App Store Connect from the code. Covers demo access, where every in-app purchase lives, non-obvious features, permission and background-mode reasons, third-party AI and UGC moderation, ATS exceptions, hardware or region needs, and specific What's New items, all within the notes limit. Use for "write my review notes", "App Review notes", "notes for reviewer", "demo account instructions", or before submitting.
argument-hint: "[project-path]"
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 📝 Greenlight review notes

Write ready-to-paste App Review notes for the project at `$ARGUMENTS` (if blank, the current working directory `.`). Clear notes prevent 2.1 "couldn't access" rejections and 2.3.1(a) "generic notes" rejections.

## Gather from the code

- **Access (2.1(a)):** is a login required? Write placeholder credentials only: `Email: <demo email>` / `Password: <demo password>`. **Never** put real credentials in files or chat. Include 2FA or OTP bypass steps, the demo-mode path, and any QR codes or hardware needed.
- **New in this version (2.3.1(a)):** specific features, with where each one is (from git log or diff since the last tag, if available).
- **In-app purchases (2.1(b)):** each product and the exact tap path to its paywall; sandbox notes; why any configured IAP isn't visible.
- **Permissions and background modes (2.5.4, 5.1.1):** one line each on why it's needed and where it's triggered.
- **Sensitive features:** third-party AI (what's sent, and the consent screen), UGC moderation (filter, report, block, response time), health, location, kids parental gate, VPN or regulatory licences, ATS exceptions.
- **Business model (3.x):** physical goods using non-IAP payment (3.1.3(e)); US-only external links; reader-app status.
- **Feature flags (2.5.19):** confirm every feature is enabled for the review build.
- **Region, hardware, account type:** anything a reviewer outside your country needs.

## Output

A single code block, plain text, **under 4,000 characters**, in this order: Access → What's new → How to test key flows → In-app purchases → Permissions → Other notes → Contact. Short lines, numbered steps, no marketing language. List the `<placeholders>` the user must fill in. If `fastlane/metadata/review_information/` exists, offer to save it to `notes.txt` (without credentials).
