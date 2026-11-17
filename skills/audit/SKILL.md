---
name: audit
description: Full App Store Review Guidelines audit of an Apple-platform app (iOS, iPadOS, macOS, watchOS, tvOS, visionOS; Swift, SwiftUI, UIKit, React Native, Expo, Flutter, Capacitor). Checks every guideline in Safety, Performance, Business, Design and Legal plus upload requirements (privacy manifest, purpose strings, icon). Shows what the app violates and what it already follows, with file:line evidence, a readiness score and a GREENLIGHT_REPORT.md. Use for "will my app pass App Review", "audit my app for the App Store", "App Store compliance check", "is my app ready to submit", or before any submission.
argument-hint: "[project-path]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" *) Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 🟢 Greenlight: full App Store audit

Audit the project at `$ARGUMENTS` (if blank, the current working directory `.`) the way an App Reviewer would, with evidence for every call.

Reference files (read them before step 4):
- Checklist of every guideline: `${CLAUDE_PLUGIN_ROOT}/references/checklist.md`
- Report layout and scoring: `${CLAUDE_PLUGIN_ROOT}/references/report-template.md`

## 1. Map the project

Find the app: `*.xcodeproj` / `*.xcworkspace` / `Package.swift`, `app.json` (Expo), `package.json` (React Native, Capacitor), `pubspec.yaml` (Flutter). Note the stack, the platforms, and every target: main app, widgets, extensions, App Clips, watchOS app, keyboard. Guidelines 2.5.16, 2.5.18 and 4.4 apply per target.

## 2. Check the guidelines are current

Fetch https://developer.apple.com/app-store/review/guidelines/ and read the "Last Updated" date. The checklist snapshot is **October 16, 2026**.
- Same date: continue.
- Newer: tell the user, read the changed sections, and apply the new rules on top of the checklist.
- Fetch fails: continue, and put "against snapshot of October 16, 2026" in the report.

## 3. Run the static scanner

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" "<project-path>"
```

Treat the output as leads, not verdicts. Open the file behind every ❌ before you accept it: a hit can sit in DEBUG-only code, a comment, a vendored library or dead code. Downgrade false positives and say why. The scanner can't see screens, flows or App Store Connect; that's your job in steps 4 to 6.

## 4. Build the app profile

Read the code (entry point, navigation, onboarding, auth, paywall, settings, networking, SDK list) and answer each item with evidence:
- What the app does, in one line, and whether it is more than a website (4.2).
- **Accounts:** sign-up? which login providers? guest access? delete-account flow (and does it really delete)?
- **Money:** IAP types, subscriptions, ads, physical goods, external purchase links, which storefronts (the US rules for 3.1.1(a) and 3.1.3 differ).
- **Content:** UGC, chat, comments, AI generation, creator content, mini apps, kids audience.
- **Sensitive data:** each permission, tracking or ad SDKs, analytics, third-party AI endpoints, health, location, contacts.
- **Regulated:** finance, loans, gambling, crypto, medical, VPN, MDM, cannabis. Note the account type these need (5.1.1(ix)).

The profile decides which guidelines are N/A. Every N/A needs a reason.

For large codebases, launch parallel Explore subagents, one per guideline section. Give each one the profile and its section of the checklist, and have it return findings as `id · status · file:line · note`.

## 5. Walk every guideline

Go through `checklist.md` top to bottom: section 0, sections 1 to 5, then "Platform requirements". Give each guideline one status:
- ✅ **PASS**: cite the evidence (`file:line` or the config key).
- ❌ **FAIL**: cite the evidence, the severity from the checklist (raise or lower it with a reason), and a concrete fix.
- 🔎 **REVIEW**: needs the owner's decision. Name the options.
- ❓ **MANUAL**: only checkable in App Store Connect or on a device. Say exactly what to check.
- ➖ **N/A**: give the reason.

Rules:
- No PASS without evidence and no FAIL without evidence. "Couldn't find X" is a FAIL only when X must exist (privacy policy link, account deletion, restore purchases). Otherwise it's MANUAL.
- Read the actual flows: first launch, permission prompts and what happens after "Don't Allow", login, paywall, settings, report and block, delete account.
- Judge like a strict but fair reviewer. Don't invent violations, and don't wave real ones through.

## 6. Check the store listing

If `fastlane/metadata/`, `metadata/` or screenshots exist, apply the `/greenlight:metadata` rules (2.3.x: 30-character name, keyword rules, no prices or other platforms, screenshots show the app in use, description claims match the code). Otherwise list them as MANUAL.

## 7. Score, write and summarise

1. Score and verdict exactly as `report-template.md` defines them.
2. Write `GREENLIGHT_REPORT.md` in the project root, following the template. Include the full guideline matrix.
3. In chat, print only: the verdict banner and score, the section table, the top 5 fixes (one line each with `file:line`), and the report path.
4. Offer next steps: fix the blockers (only after the user says yes), `/greenlight:notes` for review notes, `/greenlight:privacy` or `/greenlight:paywall` for deep dives.

Never promise approval. Greenlight lowers the risk; App Review decides.
