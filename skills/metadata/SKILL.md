---
name: metadata
description: Lints an App Store listing (app name, subtitle, keywords, description, promotional text, What's New, screenshots, support and privacy URLs) against App Store Guidelines 2.3.x, 2.3.10, 4.1, 5.1.4 and 5.2.4, and cross-checks every marketing claim against the code. Reads fastlane metadata, an App Store URL, or pasted text. Use for "check my App Store listing", "metadata rejected", "guideline 2.3", "is my app name OK", "review my screenshots", "write What's New".
argument-hint: "[fastlane-dir | App Store URL | (paste text)]"
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 🏷️ Greenlight metadata lint

## 1. Get the listing

In order of preference:
1. `$ARGUMENTS` is a path, or `fastlane/metadata/` exists: read `<locale>/name.txt`, `subtitle.txt`, `keywords.txt`, `description.txt`, `promotional_text.txt`, `release_notes.txt`, `support_url.txt`, `privacy_url.txt`, and screenshots in `fastlane/screenshots/<locale>/`. Lint every locale.
2. `$ARGUMENTS` is an `apps.apple.com` URL: fetch it and lint what's public. Keywords aren't public, so ask for them.
3. Otherwise, ask the user to paste the fields.

## 2. Hard limits

| Field | Limit |
|---|---|
| Name | 30 characters (2.3.7) |
| Subtitle | 30 characters |
| Keywords | 100 bytes, comma-separated |
| Promotional text | 170 characters |
| Description | 4,000 characters |
| What's New | 4,000 characters |

## 3. Guideline checks (each finding cites the field and the exact text)

- **2.3.7** No prices, "free", "sale", or terms that don't belong to the field in the name, subtitle or screenshots. No trademarks, competitor or popular app names in keywords. No keyword stuffing. Subtitle has no other app references and no unverifiable claims ("#1", "best", "fastest").
- **4.1(c) / 5.2.1** No other developer's brand in the name or icon without permission.
- **2.3.8 / 5.1.4** "For Kids" or "For Children" only in the Kids Category; nothing implying children are the main audience otherwise. Icons, screenshots and previews are suitable for 4+.
- **2.3.10** No Android, Google Play, other platforms or alternative marketplaces.
- **5.2.4** No "Apple approved/recommended", no Apple logos or implied endorsement.
- **2.3.2** The description says which features, levels or subscriptions cost extra.
- **2.3.1(a)** **Claims vs code.** For every feature the description or screenshots promise, find it in the code (`file:line`). A claimed feature that doesn't exist, is unfinished, or is "coming soon" is a misleading-metadata rejection.
- **2.3.12** What's New lists the significant changes specifically. Generic text is OK only for bug, security or performance fixes.
- **2.3.3 / 2.3.4** View the screenshots with the Read tool. They must show the app in use (not only a splash, title art or login screen). No device frames or UI from other platforms, no real people's data (2.3.9), nothing above 4+.
- **1.5 / 5.1.1(i)** The support URL has a way to contact you and the privacy URL loads (fetch both).

## 4. Output

One table per locale: `Field · Value · Length/limit · Issues · Suggested fix`. Under it, the claims-vs-code table: `Claim · Found at · Status`. Offer rewrites that keep the meaning and fit the limits; write them to the fastlane files only after the user agrees.
