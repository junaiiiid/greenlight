# Greenlight audit checklist

Source: Apple App Review Guidelines, https://developer.apple.com/app-store/review/guidelines/
**Snapshot: Last Updated October 16, 2026.** Paraphrased for auditing; Apple's page is the authority.

How to read each line:

`ID` **Requirement**. *Applies:* when it is in scope. *Check:* where the evidence is. *Sev:* default severity if violated.

Evidence sources: **[code]** source/dependencies · **[config]** Info.plist, entitlements, privacy manifest · **[meta]** App Store listing (name, subtitle, description, screenshots, What's New, keywords) · **[asc]** App Store Connect settings (age rating, App Privacy, review notes, IAP setup) · **[run]** runtime behaviour · **[legal]** licences, entity type, regulatory documents.

Severity: **BLOCKER** = certain rejection or failed upload · **HIGH** = common rejection reason · **MEDIUM** = reviewer discretion / likely follow-up · **LOW** = polish or risk for later.

Status for each guideline in a report: ✅ PASS (evidence it complies) · ❌ FAIL (evidence it violates) · 🔎 REVIEW (needs a human decision) · ❓ MANUAL (only checkable outside the repo) · ➖ N/A (doesn't apply, give the reason).

---

## 0. Before you submit (Apple's pre-submission list)

- **0.1** No crashes or obvious bugs on current devices and OS. *Check:* [run] crash-prone patterns, force unwraps on network data, `fatalError` in release paths. *Sev:* BLOCKER
- **0.2** Metadata complete and accurate. *Check:* [meta]. *Sev:* HIGH
- **0.3** Up-to-date contact info in App Store Connect. *Check:* [asc]. *Sev:* MEDIUM
- **0.4** Full reviewer access: demo account or full-featured demo mode, plus any hardware, QR codes, or credentials needed. *Check:* [asc] review notes, [code] login walls. *Sev:* BLOCKER
- **0.5** Backend live and reachable during review. *Check:* [code] base URLs/environments. *Sev:* BLOCKER
- **0.6** Non-obvious features and IAPs explained in review notes, with docs. *Check:* [asc]. *Sev:* HIGH
- **0.7** Regulatory documents for regulated features (medical, finance, gambling, VPN licences). *Check:* [legal]. *Sev:* BLOCKER where applicable

## 1. Safety

- **1.1** No offensive, insensitive, upsetting, disgusting or creepy content. *Applies:* all. *Check:* [code] bundled content, seed data, [meta]. *Sev:* HIGH
  - **1.1.1** No defamatory or discriminatory content targeting religion, race, orientation, gender, origin or other groups (professional satire is generally exempt).
  - **1.1.2** No realistic killing, torture or abuse, or content encouraging violence. Game enemies can't solely target a real race, culture, government or company.
  - **1.1.3** No encouraging reckless weapon use; no facilitating purchase of firearms or ammunition.
  - **1.1.4** No overtly sexual or pornographic material, hookup apps, or anything facilitating prostitution or trafficking.
  - **1.1.5** No inflammatory religious commentary or misquoted religious texts.
  - **1.1.6** No false information or trick features (fake location trackers, fake device data, prank calls or SMS). "For entertainment" disclaimers don't help. *Check:* [code] does each feature really do what it claims? *Sev:* HIGH
  - **1.1.7** No cashing in on current tragedies (conflicts, attacks, epidemics).
- **1.2** User-generated content (social, UGC, **AI content creation**) must have: content filtering, a report mechanism with timely response, the ability to block abusive users, and published contact info. Apps used mainly for porn, random or anonymous chat, "hot-or-not", threats or bullying get removed. NSFW web content must be hidden by default and only enabled on your website. *Applies:* any posting, chat, comments, uploads, AI generation. *Check:* [code] report, block, filter and contact paths in the UI. *Sev:* HIGH
  - **1.2.1** Creator content (videos, articles, mini-games by non-developer creators) is treated as UGC and follows 1.2 and 3.1.1; tell users which content costs extra.
  - **1.2.1(a)** Creator apps must flag content above the app's age rating and restrict it by verified or declared age (e.g. Declared Age Range API). *Sev:* HIGH
- **1.3** Kids Category: no external links, purchases or distractions unless behind a parental gate. No third-party analytics or ads (narrow exceptions: no IDFA or identifiable data; contextual ads only from providers with human-reviewed creatives). No PII or device info sent to third parties. Obligations continue even if you leave the category. *Applies:* Kids Category or child-directed apps. *Check:* [code] SDK list, link-outs, parental gate. *Sev:* BLOCKER
- **1.4** Physical harm.
  - **1.4.1** Medical apps: disclose data and methodology behind accuracy claims. No "sensor-only" x-ray, blood pressure, temperature, glucose or SpO₂ claims. Remind users to consult a doctor. Link regulatory clearance if you have it. *Sev:* BLOCKER
  - **1.4.2** Drug dosage calculators only from manufacturers, hospitals, universities, insurers, pharmacies or approved entities (or FDA-approved). *Sev:* BLOCKER
  - **1.4.3** Don't encourage tobacco, vape, illegal drugs or excessive alcohol; nothing for minors; no selling controlled substances (licensed pharmacies and legal cannabis dispensaries excepted) or tobacco. *Sev:* BLOCKER
  - **1.4.4** Only DUI checkpoints published by law enforcement; never encourage drunk driving or speeding.
  - **1.4.5** Don't urge risky challenges or device use that risks harm.
- **1.5** Easy way to contact you in the app and on the Support URL; Wallet passes carry valid issuer contact and a brand-dedicated certificate. *Check:* [code] support/contact screen, [meta] Support URL works. *Sev:* MEDIUM
- **1.6** Appropriate security for user data: HTTPS/ATS, Keychain for secrets and tokens, no API secrets in the binary, no logging of PII. *Check:* [code] [config]. *Sev:* HIGH
- **1.7** Crime-reporting apps must involve local law enforcement and only ship where that's active. *Sev:* BLOCKER

## 2. Performance

- **2.1(a)** App Completeness: final build, no placeholder text, empty sites or temp content; all URLs work; tested on device; demo account info provided and backend on. A built-in demo mode needs prior approval and must show full functionality. Incomplete bundles or crashing binaries are rejected. *Check:* [code] TODO/"coming soon"/lorem/dead buttons, [run], [asc]. *Sev:* BLOCKER. *Most common rejection reason overall.*
- **2.1(b)** IAPs complete, visible to the reviewer and working; explain in notes any that can't be found. *Check:* [code] product IDs match ASC; paywall reachable without special state. *Sev:* HIGH
- **2.2** No demos, betas or trials on the App Store; use TestFlight. TestFlight builds must be intended for release and can't be paid for. *Check:* [config] display name, [meta]. *Sev:* HIGH
- **2.3** Accurate metadata (description, screenshots, previews, privacy info) reflecting the core experience, kept current.
  - **2.3.1(a)** Describe new features specifically in Notes for Review (generic notes are rejected) and make them accessible. No misleading marketing (fake virus scanners, false prices) inside or outside the store. *Sev:* HIGH
  - **2.3.1(b)** Egregious or repeated dishonesty means removal from the Developer Program.
  - **2.3.2** Description, screenshots and previews must say which items, levels or subscriptions cost extra. Promoted IAPs need public-appropriate name, screenshot and description, and the app must handle the promoted-purchase transaction on launch (`SKPaymentTransactionObserver` / StoreKit 2 `PurchaseIntent`). *Sev:* HIGH
  - **2.3.3** Screenshots show the app in use, not just title art, login or splash. Overlays OK. *Sev:* HIGH
  - **2.3.4** Previews use only screen captures of the app (narration and overlays OK). *Sev:* MEDIUM
  - **2.3.5** Pick the most accurate category. *Sev:* LOW
  - **2.3.6** Answer the age-rating questionnaire honestly (the current scale is 4+/9+/13+/16+/18+); comply with local content-rating rules for media. *Check:* [asc] vs real content (UGC, web access, AI chat, gambling-like mechanics). *Sev:* HIGH
  - **2.3.7** Unique name of **30 characters or fewer**. Keywords must be accurate: no trademarks, competitor names, prices or stuffing. Name, subtitle, screenshots and previews carry no prices or off-type text. Subtitles: no other app references or unverifiable claims ("#1", "best"). *Check:* [meta]. *Sev:* HIGH
  - **2.3.8** Icons, screenshots and previews are 4+ even if the app isn't. "For Kids"/"For Children" are reserved for the Kids Category. All icons (alternate, Watch) should be consistent. *Sev:* MEDIUM
  - **2.3.9** You hold rights to everything in icons, screenshots and previews; use fictional account data, not real people's. *Sev:* MEDIUM
  - **2.3.10** No other platforms or alternative marketplaces in app or metadata (Android, Google Play, etc.) unless it's approved interactive functionality; no irrelevant info. *Sev:* MEDIUM
  - **2.3.11** Pre-orders must be complete and deliverable; the release must match what was advertised; a business-model change restarts pre-orders. *Sev:* HIGH
  - **2.3.12** "What's New" clearly describes significant changes (generic is fine only for bug, security or performance fixes). *Sev:* MEDIUM
  - **2.3.13** In-app events: correct event type, accurate event-specific metadata, real dates across storefronts, deep link lands on the right place. *Sev:* MEDIUM
  - **2.3.14** Creative assets relate to the app or brand, are 4+, with no misleading app references, unverifiable claims, or specific/discounted prices. *Sev:* MEDIUM
- **2.4** Hardware compatibility.
  - **2.4.1** iPhone apps should run on iPad when possible (iPhone-only apps still get reviewed on iPad in compatibility mode, so test layouts there). *Check:* [config] `TARGETED_DEVICE_FAMILY`, [run]. *Sev:* MEDIUM
  - **2.4.2** Power-efficient; no rapid battery drain, heat, excessive disk writes, or "put the phone under your pillow while charging"; no unrelated background work such as crypto mining (including in ads). *Sev:* HIGH
  - **2.4.3** Apple TV apps work with the Siri Remote or game controllers; disclose controller requirements in metadata.
  - **2.4.4** Never require a device restart or unrelated system-setting changes (e.g. "turn off Wi-Fi"). *Sev:* HIGH
  - **2.4.5** Mac App Store: (i) sandboxed, proper APIs for other apps' data; (ii) Xcode packaging, no third-party installers, self-contained; (iii) no auto-launch or lingering processes without consent, no Dock or desktop clutter; (iv) no downloading apps, kexts or code; (v) no root escalation or setuid; (vi) no license screens or keys or custom copy protection; (vii) updates only via the Mac App Store; (viii) current OS, no deprecated or optional tech (e.g. Java); (ix) all localizations in one bundle. *Applies:* macOS. *Sev:* BLOCKER
- **2.5** Software requirements.
  - **2.5.1** Public APIs only, run on the current OS, phase out deprecated tech, use frameworks for their intended purpose and mention integrations in the description (HealthKit, HomeKit…). *Check:* [code] private selectors, `/PrivateFrameworks/`, `App-Prefs:` URLs. *Sev:* BLOCKER
  - **2.5.2** Self-contained bundle; no reading or writing outside the container; no downloading or executing code that adds or changes features (narrow exception: education apps teaching code, with source fully viewable and editable). *Check:* [code] hot-patching, remote JS that alters native features, OTA bundles that add features. *Sev:* BLOCKER
  - **2.5.3** No malware or code that disrupts the OS or hardware, push or Game Center. *Sev:* BLOCKER
  - **2.5.4** Background modes only for their purpose (VoIP, audio, location, task completion, notifications…). *Check:* [config] `UIBackgroundModes` vs [code]. *Sev:* HIGH
  - **2.5.5** Fully functional on IPv6-only networks. *Check:* [code] IPv4 literals, `inet_addr`, `AF_INET`-only sockets. *Sev:* HIGH
  - **2.5.6** Web browsing uses WebKit (alternative engines only with the EU/Japan entitlement). *Sev:* BLOCKER
  - **2.5.8** No alternate home-screen or desktop environments. *Sev:* BLOCKER
  - **2.5.9** Don't alter or disable standard switches (volume, ring/silent) or native UI behaviour; don't block links out to other apps. *Sev:* HIGH
  - **2.5.11** SiriKit/Shortcuts: only intents you can fully handle; vocabulary related to your app; aliases tied to your app or company; resolve directly with no ads in between. *Sev:* MEDIUM
  - **2.5.12** CallKit/SMS Fraud extensions block only confirmed spam, explain criteria in marketing text, never use the data for tracking or profiles. *Sev:* HIGH
  - **2.5.13** Face-based login uses LocalAuthentication (not ARKit or custom face recognition), with an alternative for users under 13. *Sev:* HIGH
  - **2.5.14** Explicit consent plus a clear visual or audible indicator whenever recording camera, mic, screen or other user activity. *Sev:* BLOCKER
  - **2.5.15** File pickers include Files app and iCloud documents (use `UIDocumentPickerViewController` / `.fileImporter`). *Sev:* LOW
  - **2.5.16** Widgets, extensions and notifications relate to the app. **(a)** App Clip features must also be in the main app; App Clips can't contain ads. *Sev:* MEDIUM
  - **2.5.17** Matter: pair via Apple's Matter framework; non-Apple Matter components need CSA certification. *Sev:* HIGH
  - **2.5.18** Ads only in the main app binary (not extensions, App Clips, widgets, notifications, keyboards, watchOS). Ads must match the age rating, let users see why they were targeted without leaving the app, and never target on sensitive data (health, ClassKit, kids). Interstitials must be clearly ads with visible, large close/skip buttons and no trick taps. Users must be able to report inappropriate ads. *Check:* [code] ad SDK placement, report-ad affordance. *Sev:* HIGH
  - **2.5.19** No hidden, dormant or undocumented features; obfuscating them gets the account terminated. *Check:* [code] remote flags that unlock unreviewed features, hidden screens. *Sev:* BLOCKER

## 3. Business

General: explain non-obvious business models in metadata and review notes; no rip-off pricing; no review or chart manipulation (paid, incentivized, filtered or fake reviews).

- **3.1.1** In-App Purchase is required to unlock features or content in the app (subscriptions, currencies, levels, premium content, full version). No license keys, AR markers, QR codes, crypto or wallets as unlock mechanisms. *Sev:* BLOCKER
  - Tips via IAP are OK. IAP credits and currencies never expire. **Provide a restore mechanism** for restorable purchases.
  - Gifting IAP items is OK (refund only to the purchaser, no exchange).
  - Loot boxes and random paid items must **disclose odds before purchase**.
  - Digital gift cards and vouchers redeemable for digital goods must be IAP (physical, mailed cards may use other payments).
  - Non-subscription free trial: a $0 non-consumable named "XX-day Trial" that states duration, what's lost, and later charges up front.
  - NFTs: IAP for minting, listing and transfer; viewing your own NFTs is OK, but ownership can't unlock features; no purchase CTAs outside IAP except on the US storefront.
- **3.1.1(a)** External purchase links need a StoreKit External Purchase Link (or Music Streaming) entitlement in the regions that allow it. **Not required on the United States storefront**, where buttons, links and CTAs to other purchase methods are allowed. Elsewhere, no CTAs to non-IAP purchasing. Misleading use means removal. *Check:* [code] storefront-aware gating (`Storefront.current?.countryCode`). *Sev:* BLOCKER outside US
- **3.1.2** Subscriptions:
  - **3.1.2(a)** Ongoing value; period ≥ 7 days; works on all of the user's devices; no extra tasks to get what was paid for (posting, contacts, check-ins); don't take paid primary features away from existing customers when moving to subscriptions; no bait-and-switch. *Sev:* BLOCKER
  - **3.1.2(b)** Clean upgrade and downgrade; users can't accidentally hold two tiers of the same thing (one subscription group). *Sev:* HIGH
  - **3.1.2(c)** Before subscribing, state clearly what users get for the price. The paywall should show title, length, price (and price per unit if shown), what's included, auto-renewal, and functional links to Privacy Policy and Terms of Use (EULA), in-app and in metadata. *Sev:* HIGH
- **3.1.3** Other purchase methods allowed (but no in-app nudges to them, except on the US storefront and per 3.1.1(a)/3.1.3(a)):
  - **(a)** Reader apps (magazines, news, books, audio, music, video) can give access to prior purchases; free-tier sign-up; External Link Account Entitlement (not needed on US storefront).
  - **(b)** Multiplatform services: content bought elsewhere can be accessed if also sold as IAP in the app.
  - **(c)** Enterprise services sold directly to organizations; consumer or family sales must be IAP.
  - **(d)** Real-time 1:1 person-to-person services (tutoring, consultations) may skip IAP; one-to-few or one-to-many must use IAP.
  - **(e)** Physical goods and services consumed outside the app **must not** use IAP (Apple Pay or card).
  - **(f)** Free companion apps to paid web tools (VoIP, cloud storage, email, hosting) with no in-app purchasing or CTAs.
  - **(g)** Ad-campaign management apps; but buying ads or boosts shown in the same app must be IAP.
- **3.1.4** Hardware-specific content may unlock without IAP; optional physical-product unlocks need an IAP option too; can't require unrelated purchases or marketing actions.
- **3.1.5** Crypto: (i) wallets only from organization accounts; (ii) no on-device mining; (iii) exchanges only where licensed; (iv) ICOs, futures and crypto-securities only from established financial institutions; (v) no crypto rewards for tasks (downloads, posting, referrals). *Sev:* BLOCKER
- **3.2.1** Acceptable: promote your own apps (not just a catalog); curated third-party app collections with editorial content for a specific need; rentals that expire; Wallet passes for payments, offers or ID; insurance apps free and without IAP; approved nonprofits fundraising with Apple Pay; optional person-to-person monetary gifts with 100% to the recipient (gifts tied to digital content need IAP); financial trading or investing only from licensed institutions.
- **3.2.2** Unacceptable: (i) App Store-like storefronts for third-party apps; (iii) faking ad impressions or clicks, or apps that exist mainly to show ads; (iv) in-app charity collection unless an approved nonprofit; (v) arbitrarily restricting users by location or carrier; (vii) manipulating rank or visibility on other services; (viii) binary options (CFDs/FOREX need licences everywhere); (ix) personal loans: show all terms and maximum APR, **APR ≤ 36%** including fees, no full repayment required in ≤ 60 days; **(x) never force ratings, reviews or other app downloads to unlock functionality** (rewarding in-app actions is fine). *Sev:* BLOCKER

## 4. Design

- **4.1** Copycats: (a) original ideas, don't clone popular apps; (b) no impersonating apps or services (Code of Conduct violation); (c) no other developers' icons, brands or product names in your icon or name without permission. *Check:* [meta] name, icon. *Sev:* BLOCKER
- **4.2** Minimum functionality: more than a repackaged website; useful, unique, "app-like", with lasting value. Songs or films belong on iTunes; books or game guides on Apple Books. *Check:* [code] native features beyond a web view (push, offline, device APIs, native navigation). *Sev:* HIGH
  - **4.2.1** ARKit apps must offer rich, integrated AR, not just dropping a model or replaying an animation.
  - **4.2.2** Not primarily marketing, ads, web clippings, aggregators or link collections (catalogs excepted).
  - **4.2.3(i)** Works without installing another app. **(ii)** If initial launch needs a download, disclose its size and ask first. *Sev:* HIGH
  - **4.2.6** Apps built from commercial templates or app generators are rejected unless submitted by the content provider (or a single "picker" aggregator app). *Sev:* BLOCKER
  - **4.2.7** Remote desktop clients: (a) user-owned PC or console on a local LAN; (b) everything runs and renders on the host; (c) account management on the host; (d) no store-like UI on the client; (e) thin clients for cloud apps aren't allowed.
- **4.3** Spam: (a) no multiple Bundle IDs of the same app (use IAP for variants); (b) no me-too apps in saturated categories (dating, flashlight, sound effects, wallpaper, simple timers, fortune telling) without meaningful difference; low-effort apps (drinking games, fart or burp, Kama Sutra) are rejected. *Sev:* BLOCKER
- **4.4** Extensions follow Apple's extension docs, include help and settings where possible, are disclosed in marketing text, and contain no marketing, ads or IAP.
  - **4.4.1** Keyboards: real typing input; follow Sticker rules for images and emoji; a next-keyboard button; work without full access or network; collect activity only to improve the keyboard; launch nothing but Settings; don't repurpose keys. *Sev:* BLOCKER
  - **4.4.2** Safari extensions: run on current Safari, don't interfere with system or Safari UI, nothing malicious, request the minimum site access. *Sev:* BLOCKER
- **4.5** Apple sites and services:
  - **4.5.1** Approved RSS feeds only; no scraping Apple sites or building rankings from them.
  - **4.5.2** MusicKit: user-initiated playback with standard controls; no paywalling or monetizing Apple Music access; no downloading or sharing MusicKit audio; licences for sync uses; cover art only for playback or playlists; purpose string discloses library access; no ad targeting with that data.
  - **4.5.3** No spam or phishing via Apple services (Game Center, push, Live Activities); never mine Game Center Player IDs.
  - **4.5.4** **Push must not be required** for the app to work, and must carry no sensitive data. Marketing pushes need explicit in-app opt-in consent language plus an in-app opt-out. *Check:* [code] permission prompt timing, settings toggle. *Sev:* HIGH
  - **4.5.5** Game Center Player IDs used only per Game Center terms and never displayed.
  - **4.5.6** Apple emoji via Unicode only; never embedded as images in the binary or used on other platforms.
- **4.7** Mini apps, mini games, streaming games, chatbots, plug-ins, emulators (non-embedded software): you're responsible for all of it.
  - **4.7.1** Follows privacy (5.1), has filtering, reporting and blocking (UGC rules), and uses IAP (3.1) for digital goods.
  - **4.7.2** Native APIs not exposed to that software without Apple's permission.
  - **4.7.3** No sharing data or permissions to individual software without explicit consent each time.
  - **4.7.4** Provide an index of the software, with universal links to each item.
  - **4.7.5** Flag software above the app's age rating and restrict it by verified or declared age. *Sev:* HIGH
- **4.8** Login services: if a third-party or social login (Google, Facebook, X, LinkedIn, Amazon, WeChat…) sets up the **primary account**, also offer an equivalent option that limits data to name and email, lets users hide their email, and doesn't track for ads without consent (**Sign in with Apple** satisfies this). Exempt: your own account system only; alternative-marketplace logins; education or enterprise accounts; government or industry e-ID; clients of a specific third-party service. *Check:* [code] auth providers. *Sev:* BLOCKER
- **4.9** Apple Pay: show all purchase info before sale; correct branding and UI. Recurring payments must disclose the renewal term and that it continues until cancelled, what each period provides, the actual charges, and how to cancel. *Sev:* HIGH
- **4.10** Don't monetize built-in capabilities (push, camera, gyroscope, Apple Music, iCloud storage, Screen Time APIs). *Sev:* BLOCKER

## 5. Legal

- **5.1.1 Data collection and storage**
  - **(i)** Privacy policy linked **in App Store Connect and inside the app** (easy to find). It must state what's collected, how and why; that third parties (analytics, ads, SDKs, affiliates) give equal protection; retention and deletion; and how to revoke consent or request deletion. *Check:* [code] link in Settings/About/onboarding, [meta] URL resolves. *Sev:* BLOCKER
  - **(ii)** Consent for collecting user or usage data, even "anonymous" data. Paid features can't depend on granting data access. Easy consent withdrawal. **Purpose strings must clearly and completely explain the use.** GDPR legitimate-interest use must follow GDPR in full. *Check:* [config] every `NS*UsageDescription`. *Sev:* BLOCKER
  - **(iii)** Data minimization: request only what the core features need. Prefer out-of-process pickers or share sheets (`PHPicker`, `CNContactPicker`) over full Photos or Contacts access. *Sev:* HIGH
  - **(iv)** Respect permission settings; no tricking or forcing consent; no unrelated permission gates (e.g. mic required to post photos); offer alternatives (e.g. manual address if location is denied). *Check:* [run] pre-prompt wording, behaviour after "Don't Allow". *Sev:* HIGH
  - **(v)** No login required unless the app has significant account-based features. **If you support account creation, offer in-app account deletion.** No required personal info unless core or legally needed. Social-network login can't be required unless the app is about that network; provide a way to revoke social credentials; never store social tokens off-device. *Check:* [code] guest mode, delete-account flow (real deletion, not deactivation). *Sev:* BLOCKER
  - **(vi)** No covertly discovering passwords or private data. *Sev:* BLOCKER
  - **(vii)** `SFSafariViewController` must be visible (not hidden or obscured) and never used to track users covertly. *Sev:* BLOCKER
  - **(viii)** No compiling personal info from sources other than the user (even public databases) without explicit consent. *Sev:* BLOCKER
  - **(ix)** Highly regulated fields (banking, finance, healthcare, gambling, legal cannabis, air travel, crypto exchanges) or sensitive data must be submitted by the **legal entity** providing the service, not an individual. Cannabis sales must be geo-restricted. *Check:* [legal] developer account type. *Sev:* BLOCKER
  - **(x)** Basic contact info (name, email) may be requested only as optional, with no features conditional on it. *Sev:* HIGH
- **5.1.2 Data use and sharing**
  - **(i)** Get permission before using, transmitting or sharing personal data. **Clearly disclose sharing with third parties, including third-party AI, and get explicit permission first.** Sharing only to improve the app or serve ads (per DPLA). **App Tracking Transparency** is required to track. Never require enabling push, location or tracking to use the app or get rewards. *Check:* [code] ATT before any tracking SDK init; AI data flows with an explicit consent screen. *Sev:* BLOCKER
  - **(ii)** No repurposing data without fresh consent.
  - **(iii)** No covert profiling; no de-anonymizing users or rebuilding profiles from "anonymized" or Apple-API data.
  - **(iv)** No building contact databases from Contacts or Photos; no collecting installed-app lists for analytics or ads.
  - **(v)** Contacting people from the user's Contacts or Photos only at the user's explicit, individual initiative: **no "Select All", no default all-selected**, and show the message preview and sender first. *Sev:* HIGH
  - **(vi)** HomeKit, HealthKit, Clinical Health Records, MovementDisorder, ClassKit, and depth or face-mapping data (ARKit, camera, photos) never used for marketing, ads or data mining.
  - **(vii)** Apple Pay data shared only to deliver goods or services.
- **5.1.3 Health**: (i) no ads, marketing or data mining with health, fitness or medical data; benefits like insurance discounts only from the entity providing them, without sharing; disclose specific health data collected. (ii) Never write false data to HealthKit; **never store personal health info in iCloud**. (iii) Research requires informed consent covering nature, procedures, confidentiality, contact and withdrawal (parental for minors). (iv) Independent ethics board approval. *Sev:* BLOCKER
- **5.1.4 Kids**: comply with COPPA, GDPR and similar. Birthdate and parent contact only for compliance, and the app must stay useful regardless of age. Child-directed apps: no third-party analytics or ads (narrow 1.3 exceptions). Apps collecting minors' personal data need a privacy policy and legal compliance. Non-Kids-Category apps can't imply children are the main audience in name, subtitle, icon, screenshots or description. *Sev:* BLOCKER
- **5.1.5 Location**: only when directly relevant; not for emergency services or autonomous vehicle or aircraft control (small drones, toys and car alarms excepted); notify and get consent; explain the purpose in-app. *Check:* [code] "always" vs "when in use" justified. *Sev:* HIGH
- **5.2 Intellectual property**
  - **5.2.1** No unlicensed trademarks, copyrighted works or patents; no misleading or copycat names in the bundle or developer name; submit from the rights owner or licensee. *Sev:* BLOCKER
  - **5.2.2** Using, displaying or monetizing third-party services or content needs permission under their terms (be ready to show it). *Sev:* HIGH
  - **5.2.3** No illegal file sharing; no saving, converting or downloading media from third-party sources (Apple Music, YouTube, SoundCloud, Vimeo…) without authorization. *Sev:* BLOCKER
  - **5.2.4** Don't imply Apple endorses or supplies the app; the Editors' Choice badge is applied by Apple only. *Check:* [meta] [code] "Apple approved" claims, Apple logos. *Sev:* HIGH
  - **5.2.5** Don't look confusingly like Apple products, UIs or ads; no Apple emoji images; iTunes or Apple Music previews not used as entertainment (background music) and must link to the store; Activity-ring visuals must not mimic the Activity control; follow WeatherKit attribution. *Sev:* HIGH
- **5.3 Gaming, gambling, lotteries**: (5.3.1) sweepstakes sponsored by the developer; (5.3.2) official rules in-app stating Apple isn't involved; (5.3.3) no IAP for real-money gaming credit; (5.3.4) real-money gaming or lotteries need licences, geo-restriction and a **free** app; no card counters; lotteries need consideration, chance and prize. *Sev:* BLOCKER
- **5.4 VPN**: must use `NEVPNManager`; organization accounts only; a clear data-use declaration screen before purchase or use; never sell, use or disclose data to third parties (committed in the privacy policy); local laws; licence info in review notes where required. *Sev:* BLOCKER
- **5.5 MDM**: Apple-granted capability; enterprises, schools, government (limited parental-control or security cases); data-use declaration screen; no data sharing; analytics limited to MDM-app performance. *Sev:* BLOCKER
- **5.6 Developer Code of Conduct**: respectful communication; no manipulative, misleading or fraudulent behaviour; no preying on users (unwanted purchases, forced data sharing, tricky price increases, undelivered features, dark patterns). *Check:* [code] paywall dark patterns: hidden close button, pre-checked upsells, misleading "free" labels, trial toggles that hide the charge. *Sev:* BLOCKER
  - **5.6.1** Respectful review replies with no PII or marketing. **Use the system API for review prompts** (`SKStoreReviewController` / `RequestReviewAction`); custom review prompts aren't allowed. *Sev:* HIGH
  - **5.6.2** Accurate, current developer identity and contact info.
  - **5.6.3** No discovery fraud (charts, search, reviews, referrals).
  - **5.6.4** Sustained quality: excess negative reviews or refunds signal a Code of Conduct problem.

---

## Platform requirements outside the guidelines (they still block submission)

- **Privacy manifest** (`PrivacyInfo.xcprivacy`): declare Required Reason API use (UserDefaults, file timestamps, system boot time, disk space, active keyboards) with approved reason codes, plus tracking domains and collected data types. Missing declarations: upload rejected (ITMS-91053). Commonly used third-party SDKs on Apple's list must include their own manifest and signature. *Sev:* BLOCKER
- **Purpose strings** for every protected resource you touch, including from SDKs (ITMS-90683). *Sev:* BLOCKER
- **App Privacy "nutrition label"** in App Store Connect must match real collection, including SDKs. *Sev:* HIGH
- **App Store icon**: 1024×1024, no transparency or alpha channel (ITMS-90717), or an Icon Composer `.icon`. *Sev:* BLOCKER
- **Launch screen** storyboard or `UILaunchScreen`. *Sev:* HIGH
- **Minimum Xcode and SDK**: check https://developer.apple.com/news/upcoming-requirements/ for the current build requirement before submitting. *Sev:* BLOCKER
- **Export compliance**: `ITSAppUsesNonExemptEncryption`. *Sev:* LOW
- **Sign in with Apple token revocation** on account deletion (REST `revoke`). *Sev:* HIGH
- **Age rating questionnaire** answered against the current scale (including UGC, messaging, AI chat, web access, loot boxes). *Sev:* HIGH

## Top rejection causes (check these first)

1. **2.1** Incomplete or crashing build, broken links, placeholder content, no demo account, backend down.
2. **2.3** Inaccurate metadata: screenshots not showing the app, prices or claims in name or subtitle, missing IAP disclosure.
3. **5.1.1** Privacy: vague purpose strings, no in-app privacy policy, no account deletion, forced login, data-hungry permissions.
4. **4.2 / 4.3** Web wrappers, template apps, me-too apps.
5. **3.1.1 / 3.1.2** Digital goods outside IAP, missing Restore, paywall missing terms or price clarity, purchase CTAs outside the US.
6. **4.8** Google or Facebook login without Sign in with Apple (or an equivalent).
7. **2.5.4 / 2.5.1** Unused background modes, private APIs, private settings URLs.
8. **5.1.2** Tracking without ATT, undisclosed third-party AI data sharing.
9. **1.2** UGC or AI generation without report, block and filter.
10. **2.3.1(a)** Vague Notes for Review on a release with new features.
