---
name: paywall
description: Audits every purchase surface (paywalls, IAP, subscriptions, trials, ads, tips, external purchase links) against App Store Guidelines 3.1 to 3.2, 2.1(b), 2.3.2, 4.9 and 5.6. Checks price and period disclosure, trial terms, auto-renew, Terms and Privacy links, Restore Purchases, IAP vs external payments, US-storefront link rules, loot-box odds, forced reviews and dark patterns, and gives each paywall a compliance card with fixes. Use for "check my paywall", "subscription rejected", "guideline 3.1.1 / 3.1.2", "do I need IAP", "can I use Stripe", "external payment link".
argument-hint: "[project-path]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" *) Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# 💸 Greenlight paywall check

Audit monetization for the project at `$ARGUMENTS` (if blank, the current working directory `.`). Rules: section **3. Business**, plus 2.1(b), 2.3.2, 4.9, 4.10 and 5.6 in `${CLAUDE_PLUGIN_ROOT}/references/checklist.md`.

## 1. Find every way money moves

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/greenlight_scan.py" "<project-path>"`, then search for StoreKit (`Product`, `Transaction`, `SubscriptionStoreView`, `SKPaymentQueue`), RevenueCat, Adapty, Superwall, Qonversion, `react-native-iap`, `in_app_purchase`, Stripe, PayPal, Apple Pay (`PKPaymentRequest`), ad SDKs, tip jars, and outbound links to pricing or checkout pages. For each one, decide what is sold:

| What's sold | Digital (used in-app) or physical/real-world? | Required method | Method used | OK? |

Digital features, content, currency or subscriptions → IAP (3.1.1). Physical goods and real-world services → **not** IAP (3.1.3(e)). Real-time 1:1 services → either (3.1.3(d)). Reader apps, enterprise and multiplatform → 3.1.3(a)–(c). External purchase links or CTAs: allowed on the **US storefront**; elsewhere only with a StoreKit External Purchase entitlement. Check for storefront gating (`Storefront.current?.countryCode`).

## 2. Compliance card per paywall screen

For each paywall (`file:line`), mark ✅ or ❌:

- Price shown from StoreKit (`displayPrice`), not hard-coded; billing period next to it
- Price per unit, if shown, doesn't hide the real billed amount
- Trial: length, the price after the trial, and when the charge happens
- Auto-renews until cancelled; how to cancel (Settings → Apple ID → Subscriptions)
- What the subscription includes, stated before purchase (3.1.2(c))
- Working **Terms of Use (EULA)** and **Privacy Policy** links
- Visible **Restore Purchases** (3.1.1)
- Close button visible and tappable right away; no fake countdowns, no pre-checked add-ons, no "Free" label on a paid plan, no trial toggle that hides the charge (5.6)
- One subscription group per offering, so users can't double-subscribe (3.1.2(b))
- Paid features don't require extra tasks or unrelated permissions (3.1.2(a), 5.1.1(ii))
- Currency and credits never expire (3.1.1); random paid items show odds first (3.1.1)
- No rating, review or other-app download required to unlock anything (3.2.2(x))
- Promoted IAPs handled on launch (`PurchaseIntent` / `SKPaymentTransactionObserver`) (2.3.2)
- Apple Pay recurring charges disclose term, renewal, amount and how to cancel (4.9)
- No charging for built-in capabilities such as push, camera or iCloud (4.10)
- Product IDs in code match the StoreKit config / App Store Connect, and the reviewer can reach every IAP (2.1(b))

## 3. Output

Print each paywall's card, then a ranked ❌ list with `file:line` and a concrete fix. Offer a SwiftUI (or the project's framework) snippet for missing disclosure, Restore or links. Edit files only after the user agrees. End with what to say about IAPs in the review notes (`/greenlight:notes`).
