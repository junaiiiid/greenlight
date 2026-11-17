---
name: rejected
description: Turns an App Review rejection message into a fix plan. Decodes each cited guideline (e.g. 2.1, 4.8, 5.1.1(v), 3.1.1) into plain English, finds the cause in the code with file:line, proposes the smallest fix, and drafts a polite App Review reply. Also says whether to fix and resubmit, reply with information, or appeal. Use when the user pastes a rejection, says "my app got rejected", "Guideline X.X.X", "Resolution Center", "App Review said…", or asks how to respond or appeal.
argument-hint: "(paste the rejection message)"
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 🧯 Greenlight rejection rescue

The rejection text is in `$ARGUMENTS`. If it's empty, ask the user to paste the full message from App Store Connect, including any screenshots or steps the reviewer listed.

## 1. Decode

For each guideline cited, look it up in `${CLAUDE_PLUGIN_ROOT}/references/checklist.md` (fetch Apple's page if it isn't there) and state:
- **What Apple is saying**, in one plain sentence.
- **What the reviewer saw**: device, OS, the steps or screen they quote.

## 2. Classify each issue

- **Bug or crash**: reproduce the path in code, find the root cause, fix it. A new build is needed.
- **Missing information**: demo account, how to find an IAP, why a permission or background mode exists, regulatory documents. Often a reply is enough and no new build is needed.
- **Policy or design**: code or metadata must change (e.g. add account deletion, Sign in with Apple, Restore, purpose strings, IAP instead of Stripe).
- **Reviewer misunderstanding**: explain clearly with steps. If they still disagree, appeal to the App Review Board.

## 3. Find and fix

Locate the cause with `file:line` evidence. Propose the **smallest** compliant fix, with code in the project's language. Apply it only after the user agrees. Then check whether the same problem exists elsewhere in the app (other targets, other screens). Reviewers re-check everything.

## 4. Draft the reply (App Store Connect → App Review)

Courteous, specific, no arguing (5.6):

```
Hello App Review team,

Thank you for your feedback on <version> regarding Guideline <id>.

We have <made these changes / here is the information you asked for>:
- <change 1>: <where to find it in the app, exact steps>
- <change 2>: …

<Demo account / steps to reach the feature, if relevant.>

<If disagreeing: the facts, calmly, with steps to verify.>

Thank you for your time.
```

## 5. Route

- Fixed in code → resubmit with updated review notes (`/greenlight:notes`).
- Information only → reply in App Store Connect, no new build.
- Genuine disagreement → appeal to the App Review Board with the facts.
- App already live, and the issue isn't legal or safety → mention Apple's **Bug Fix Submission** option: bug fixes can ship while the guideline issue is fixed in the next version.

Finish with: "Run `/greenlight:preflight` before resubmitting."
