---
name: explain
description: Explains any App Store Review Guideline by number or topic (e.g. "4.8", "5.1.1(v)", "loot boxes", "external payment links", "account deletion"). Covers what it requires in plain English, what reviewers actually check, common rejection triggers, exemptions, and how to comply in your stack with code. With no argument, prints the Greenlight command menu and guideline map. Use for "what does guideline X mean", "explain 3.1.1", "do I need Sign in with Apple", "greenlight help".
argument-hint: "[guideline-id or topic]"
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 📖 Greenlight explain

## No argument: print the menu

```
🟢 GREENLIGHT: get the green light from App Review

/greenlight:audit      Full guideline-by-guideline audit → GREENLIGHT_REPORT.md
/greenlight:preflight  2-minute go/no-go before you hit Submit
/greenlight:privacy    Permissions, SDKs, ATT, AI sharing, privacy manifest, App Privacy label
/greenlight:paywall    IAP, subscriptions, paywall disclosure, external payments
/greenlight:metadata   Name, subtitle, keywords, screenshots, claims vs code
/greenlight:rejected   Paste a rejection → root cause, fix, reply to App Review
/greenlight:notes      Ready-to-paste App Review notes
/greenlight:explain    Explain any guideline: /greenlight:explain 4.8

1 Safety · 2 Performance · 3 Business · 4 Design · 5 Legal
```

Then list the five sections with their main sub-guidelines (one line each) from the checklist.

## With an argument: explain `$ARGUMENTS`

Find it in `${CLAUDE_PLUGIN_ROOT}/references/checklist.md`. If it's a topic, map it to the guideline IDs first. If it isn't there, or the user wants the latest wording, fetch https://developer.apple.com/app-store/review/guidelines/. Answer in this shape:

1. **In plain English:** two or three sentences.
2. **What reviewers check:** the concrete behaviours they test.
3. **Common rejection triggers:** a short list.
4. **Exemptions and edge cases:** e.g. US-storefront link rules, 4.8 exemptions, physical vs digital goods.
5. **How to comply:** a short code snippet for the current project's stack (look at the repo; default to SwiftUI).
6. **Related guidelines** and Apple's link: `https://developer.apple.com/app-store/review/guidelines/#<id>`, with parentheses dropped (`5.1.1(v)` → `#5.1.1v`).

If the current directory is an app project, end with one line on whether this app appears affected, and offer `/greenlight:audit`.
