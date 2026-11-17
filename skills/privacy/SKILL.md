---
name: privacy
description: Deep privacy X-ray of an Apple-platform app against App Store Guidelines 5.1 (data collection, consent, account deletion, ATT, third-party AI sharing, health, kids, location), 1.6, 2.5.14 and 4.8, plus the privacy manifest (PrivacyInfo.xcprivacy) and App Privacy nutrition label. Maps every permission and SDK to the data it touches, drafts the App Store Connect privacy answers and a missing privacy manifest. Use for "privacy audit", "App Privacy label", "privacy manifest", "ITMS-91053", "purpose string rejected", "ATT", "guideline 5.1.1 / 5.1.2".
argument-hint: "[project-path]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" *) Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 🔐 Greenlight privacy X-ray

Audit privacy for the project at `$ARGUMENTS` (if blank, the current working directory `.`). Rules: `${CLAUDE_PLUGIN_ROOT}/references/checklist.md`, sections 1.6, 2.5.14, 4.8, 5.1 and "Platform requirements".

Start with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" "<project-path>"` and keep its purpose-string, manifest, ATT, AI and account findings as leads. Then build these six tables from the code.

## 1. Permission map (5.1.1(ii)–(iv), 5.1.5)

| Resource | Requested at (`file:line`) | When (launch / in context) | Purpose string | Minimal? | Works after "Don't Allow"? |

Flag: prompts at launch with no context; vague purpose strings ("We need access"); full Photos or Contacts where `PHPickerViewController` or `CNContactPickerViewController` would do; "always" location without a background feature; features or payment gated on unrelated permissions; no fallback after denial (e.g. no manual address entry).

## 2. SDK and data-flow inventory (5.1.2, ATT)

List every dependency (Podfile.lock, Package.resolved, package.json, pubspec.yaml) and every outbound host.

| SDK / host | Data it gets | Linked to user? | Tracking? | Own privacy manifest needed? | Consent before init? |

- Tracking (linking your data with other companies' data for ads or measurement, or sharing with data brokers) requires the ATT prompt **before** the SDK collects. Check the init order in `AppDelegate`, the `App` struct or the JS entry point.
- **Third-party AI** (OpenAI, Anthropic, Gemini and others): the app must say which data goes to which provider and get explicit permission first (5.1.2(i)). Find the consent screen or flag its absence.
- Analytics or ads in an app for kids → 1.3 / 5.1.4.

## 3. Accounts (5.1.1(v), 4.8)

Is there guest access where possible? Is there an in-app **Delete Account** that really deletes server data (trace the call to the backend)? Are Sign in with Apple tokens revoked on deletion? Is there an equivalent privacy-focused login next to Google or Facebook? Are personal-data fields optional unless they're core?

## 4. Privacy policy (5.1.1(i))

Is it linked in the app (Settings/About, sign-up, paywall)? Does it cover: what is collected, how, and why; third parties giving equal protection; retention and deletion; how to revoke consent or request deletion; AI providers? If the policy URL is in the code, fetch it and check.

## 5. Privacy manifest (ITMS-91053)

For each Required Reason API the app's own code uses (UserDefaults, file timestamps, system boot time, disk space, active keyboards), check `PrivacyInfo.xcprivacy` declares the category with a valid reason. If it's missing, **draft** the file with `NSPrivacyTracking`, `NSPrivacyTrackingDomains`, `NSPrivacyCollectedDataTypes` and `NSPrivacyAccessedAPITypes`. Common reasons: UserDefaults `CA92.1`; file timestamps `C617.1` (files in your container) or `DDA9.1` (shown to the user); boot time `35F9.1`; disk space `E174.1` or `85F4.1`. Confirm each code against https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api before writing. Create or edit the file only after the user agrees, and remind them to add it to the app target.

## 6. Draft App Privacy label (App Store Connect)

| Data type | Collected by (app / SDK) | Linked to identity | Used for tracking | Purposes |

Use Apple's categories (Contact Info, Health & Fitness, Financial Info, Location, Sensitive Info, Contacts, User Content, Browsing History, Search History, Identifiers, Purchases, Usage Data, Diagnostics, Other Data). Include data your SDKs collect.

## Output

Write `GREENLIGHT_PRIVACY.md` in the project root with the six tables, a ❌ list ranked by severity (each with `file:line` and the fix), and a ✅ list of what's already right. In chat, print the verdict line (`🔐 Privacy: <n> blockers · <n> high · <n> medium`), the top fixes, and the file path.
