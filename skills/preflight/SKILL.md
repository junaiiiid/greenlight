---
name: preflight
description: Fast go/no-go check before hitting Submit in App Store Connect. Runs the Greenlight static scanner, then verifies Apple's "Before You Submit" list and the ten most common App Review rejection causes (crashes, placeholder content, demo account, purpose strings, privacy policy, account deletion, IAP restore, Sign in with Apple, background modes, privacy manifest). Prints a checklist in chat; writes no files. Use for "quick check before I submit", "preflight", "am I good to submit", "last check before App Review".
argument-hint: "[project-path]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" *) Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 🛫 Greenlight preflight

A two-minute go/no-go for the project at `$ARGUMENTS` (if blank, the current working directory `.`). For the full guideline-by-guideline review, use `/greenlight:audit`.

1. Run the scanner:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" "<project-path>"
   ```
2. For each ❌ BLOCKER or HIGH, open the cited file and confirm it's real. Drop false positives (DEBUG-only code, comments, vendored code).
3. Check sections **0. Before you submit** and **Top rejection causes** in `${CLAUDE_PLUGIN_ROOT}/references/checklist.md` against the code. Anything only App Store Connect knows (demo account, backend live, review notes, age rating) becomes a checkbox for the user.
4. Print this, and nothing longer:

```
🛫 PREFLIGHT: <app> · <GO 🟢 | FIX FIRST 🟡 | NO-GO 🔴>

Blockers
❌ <id> <title> · <file:line> · <one-line fix>

Warnings
⚠️ <id> <title> · <file:line>

Confirm in App Store Connect
☐ Demo account (or demo mode) in review notes, backend live
☐ Notes for Review describe new features specifically (2.3.1(a))
☐ What's New lists the significant changes (2.3.12)
☐ Age rating and App Privacy answers match the app
☐ Built with the currently required Xcode/SDK

Passed: <n> checks ✅
```

Verdict: any confirmed BLOCKER → NO-GO; any HIGH → FIX FIRST; otherwise GO. Then offer `/greenlight:audit` for depth, or offer to fix the blockers once the user agrees.
