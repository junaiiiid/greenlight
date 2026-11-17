#!/usr/bin/env python3
"""Greenlight static scanner.

Scans an Apple-platform app project (Swift/ObjC, SwiftUI/UIKit, React Native/Expo,
Flutter, Capacitor) for App Store Review Guideline problems that show up in source
code and config. It gathers evidence for the audit; it is not the verdict. Anything
that needs human judgement is reported as REVIEW.

Usage:  python3 greenlight_scan.py [PROJECT_DIR]
Stdlib only, Python 3.8+.
"""
import json
import os
import plistlib
import re
import struct
import sys
from collections import namedtuple

SKIP_DIRS = {
    "node_modules", "Pods", "build", "Build", "DerivedData", "Carthage", "SourcePackages",
    "android", "vendor", "dist", "web-build", "fastlane", "docs", "__pycache__",
}
TEST_PATH = re.compile(r"(^|/)(\w*Tests|__tests__|tests?|spec|Mocks?|Preview Content)(/|$)")
CODE_EXT = {
    ".swift", ".m", ".mm", ".h", ".c", ".cpp", ".js", ".jsx", ".ts", ".tsx", ".dart",
    ".cs", ".storyboard", ".xib", ".strings", ".stringsdict", ".xcstrings", ".html", ".vue",
}
DEP_FILES = {"package.json", "Podfile", "Podfile.lock", "Package.swift", "Package.resolved",
             "pubspec.yaml", "Cartfile"}
UI_TEXT_EXT = {".strings", ".stringsdict", ".xcstrings", ".storyboard", ".xib", ".swift", ".m"}
NATIVE_EXT = {".swift", ".m", ".mm", ".h", ".c", ".cpp"}
MAX_BYTES = 1000000  # skip minified bundles and generated blobs

SEV_WEIGHT = {"BLOCKER": 15, "HIGH": 7, "MEDIUM": 3, "LOW": 1}

# when / unless are ("code" | "config", regex) or None. when=None means "always applies".
Rule = namedtuple("Rule", "id guideline sev title when unless fix exts", defaults=(None,))


def C(rx):
    return ("code", rx)


def P(rx):
    return ("config", rx)


ATT = r"ATTrackingManager|requestTrackingAuthorization|tracking-transparency|app_tracking_transparency"

# (Info.plist key regex, feature, code signal)
PURPOSE = [
    ("NSCameraUsageDescription", "Camera",
     r"AVCaptureDevice|AVCaptureSession|sourceType\s*=\s*\.camera|\.camera\b.*UIImagePickerController|VNDocumentCameraViewController|DataScannerViewController|expo-camera|react-native-vision-camera|react-native-camera|\bimage_picker\b|\bcamera:\s*\^"),
    ("NSMicrophoneUsageDescription", "Microphone",
     r"AVAudioRecorder|requestRecordPermission|installTap\(onBus|react-native-audio-recorder|flutter_sound|\brecord:\s*\^"),
    ("NSPhotoLibraryUsageDescription", "Photo library",
     r"PHPhotoLibrary\.requestAuthorization|PHAsset\.fetchAssets|PHImageManager|react-native-image-picker|expo-media-library|photo_manager|@react-native-camera-roll"),
    ("NSPhotoLibraryAddUsageDescription|NSPhotoLibraryUsageDescription", "Saving to Photos",
     r"UIImageWriteToSavedPhotosAlbum|PHAssetChangeRequest|PHAssetCreationRequest"),
    ("NSLocationWhenInUseUsageDescription", "Location",
     r"CLLocationManager|requestWhenInUseAuthorization|CLLocationUpdate|expo-location|geolocation|\bgeolocator\b"),
    ("NSLocationAlwaysAndWhenInUseUsageDescription", "Always-on location",
     r"requestAlwaysAuthorization"),
    ("NSContactsUsageDescription", "Contacts",
     r"CNContactStore|expo-contacts|react-native-contacts|flutter_contacts|contacts_service"),
    ("NSCalendarsUsageDescription|NSCalendarsFullAccessUsageDescription|NSCalendarsWriteOnlyAccessUsageDescription",
     "Calendar", r"EKEventStore|expo-calendar|react-native-calendar-events|device_calendar"),
    ("NSRemindersUsageDescription|NSRemindersFullAccessUsageDescription", "Reminders",
     r"requestFullAccessToReminders|EKEntityType\.reminder|entityType:\s*\.reminder"),
    ("NSBluetoothAlwaysUsageDescription", "Bluetooth",
     r"CBCentralManager|CBPeripheralManager|react-native-ble|flutter_blue|flutter_reactive_ble"),
    ("NSFaceIDUsageDescription", "Face ID",
     r"LAContext|expo-local-authentication|react-native-biometrics|\blocal_auth\b"),
    ("NSMotionUsageDescription", "Motion & Fitness",
     r"CMMotionActivityManager|CMPedometer|CMAltimeter|\bpedometer\b"),
    ("NSHealthShareUsageDescription", "HealthKit",
     r"HKHealthStore|react-native-health|\bhealth:\s*\^"),
    ("NSUserTrackingUsageDescription", "App Tracking Transparency", ATT),
    ("NSSpeechRecognitionUsageDescription", "Speech recognition",
     r"SFSpeechRecognizer|@react-native-voice|speech_to_text"),
    ("NSLocalNetworkUsageDescription", "Local network",
     r"NWBrowser|NetServiceBrowser|NWListener|MCNearbyServiceBrowser|react-native-zeroconf"),
    ("NSHomeKitUsageDescription", "HomeKit", r"HMHomeManager"),
    ("NSAppleMusicUsageDescription", "Media library", r"MPMediaLibrary|MPMediaQuery|MusicAuthorization"),
    ("NFCReaderUsageDescription", "NFC",
     r"NFCNDEFReaderSession|NFCTagReaderSession|react-native-nfc-manager|nfc_manager"),
]

RULES = [
    Rule("purpose-" + re.sub(r"\W+", "-", feat.lower()).strip("-"), "5.1.1(ii)", "BLOCKER",
         "%s used without %s in Info.plist" % (feat, key.split("|")[0]), C(code), P(key),
         "Add %s with a specific reason (\"Scan receipts so expenses fill in automatically\"). "
         "A missing key crashes the app on first access and fails upload (ITMS-90683)." % key.split("|")[0])
    for key, feat, code in PURPOSE
]

# Required-reason APIs: Apple rejects uploads that use them without a privacy manifest entry (ITMS-91053).
REQUIRED_REASON = [
    ("UserDefaults", r"\bUserDefaults\b|NSUserDefaults|@AppStorage"),
    ("FileTimestamp", r"fileModificationDate|contentModificationDateKey|creationDateKey|NSFileCreationDate|NSFileModificationDate|attributesOfItem\(atPath|\bfstat\(|\bstat\(|getattrlist"),
    ("SystemBootTime", r"systemUptime|mach_absolute_time"),
    ("DiskSpace", r"volumeAvailableCapacity|systemFreeSize|NSFileSystemFreeSize|\bstatfs\(|\bstatvfs\("),
    ("ActiveKeyboards", r"activeInputModes"),
]
RULES += [
    Rule("manifest-" + cat.lower(), "5.1.1 / ITMS-91053", "BLOCKER",
         "%s API used without a PrivacyInfo.xcprivacy declaration" % cat, C(code),
         P("NSPrivacyAccessedAPICategory" + cat),
         "Add PrivacyInfo.xcprivacy to the app target with NSPrivacyAccessedAPICategory%s and an approved "
         "reason code. Without it App Store Connect rejects the upload." % cat, NATIVE_EXT)
    for cat, code in REQUIRED_REASON
]

RULES += [
    # ---- 1. Safety ----
    Rule("ugc-report", "1.2", "HIGH", "User-generated content without a way to report it",
         C(r"StreamChat|SendbirdChat|TwilioConversations|PubNub|CometChat|GetStream|(?i:createPost|addComment|postComment|uploadPost|sendMessage)"),
         C(r"(?i:report\s*(user|content|post|comment|abuse|message)|reportUser|reportContent|flagContent)"),
         "Add 'Report' on every post, comment, message and profile, and act on reports within 24 hours."),
    Rule("ugc-block", "1.2", "HIGH", "User-generated content without a way to block abusive users",
         C(r"StreamChat|SendbirdChat|TwilioConversations|PubNub|CometChat|GetStream|(?i:createPost|addComment|postComment|uploadPost|sendMessage)"),
         C(r"(?i:block\s*user|blockUser|blocked\s*users|muteUser)"),
         "Add 'Block user' that hides that user's content immediately; also filter objectionable content."),
    Rule("hardcoded-secret", "1.6", "HIGH", "Secret API key shipped inside the app",
         C(r"sk_live_[0-9A-Za-z]{16,}|sk-ant-[0-9A-Za-z_-]{16,}|sk-(proj-)?[A-Za-z0-9_-]{32,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC )?PRIVATE KEY"),
         None, "Move the key to your server and call the provider from there; rotate the leaked key now."),
    Rule("ats-disabled", "1.6", "MEDIUM", "App Transport Security disabled globally (NSAllowsArbitraryLoads)",
         P(r"NSAllowsArbitraryLoads = True|NSAllowsArbitraryLoads\W+true"), None,
         "Use HTTPS everywhere or per-domain NSExceptionDomains, and justify any exception in App Review notes."),

    # ---- 2. Performance ----
    Rule("placeholder-content", "2.1(a)", "MEDIUM", "Placeholder or unfinished content",
         C(r"(?i:lorem ipsum|\bcoming soon\b|placeholder text)"), None,
         "Remove placeholder text and 'coming soon' features; ship only finished functionality."),
    Rule("dev-endpoint", "2.1(a)", "MEDIUM", "Backend URL points at a dev machine or tunnel",
         C(r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)|ngrok(-free)?\.(io|app|dev)"), None,
         "Make sure release builds use the production backend and that it is live during review. Ignore if DEBUG-only."),
    Rule("programmatic-exit", "2.1(a)", "LOW", "App quits itself (looks like a crash to the reviewer)",
         C(r"\bexit\(\s*-?\d+\s*\)|SystemNavigator\.pop|BackHandler\.exitApp"), None,
         "Never quit programmatically on iOS; show a message or an error screen instead."),
    Rule("beta-name", "2.2", "HIGH", "App name says beta/test/demo/trial",
         P(r"CFBundle(Display)?Name = ['\"]?[^'\"\n]*\b(?i:beta|test|demo|trial)\b"), None,
         "Ship betas through TestFlight; remove 'beta/test/demo/trial' from the display name."),
    Rule("other-platform", "2.3.10", "MEDIUM", "Mentions another mobile platform in app text",
         C(r"\"[^\"\n]*\b(?i:android|google play|play store)\b[^\"\n]*\""), None,
         "Remove Android / Google Play references from user-facing text and metadata.", UI_TEXT_EXT),
    Rule("kids-terms", "2.3.8", "MEDIUM", "'For Kids' / 'For Children' in app name",
         P(r"CFBundle(Display)?Name = .*(?i:for kids|for children)"), None,
         "These terms are reserved for the Kids Category; remove them or join the category."),
    Rule("private-api", "2.5.1", "HIGH", "Possible private API or private framework use",
         C(r"/PrivateFrameworks/|LSApplicationWorkspace|NS(Selector|Class)FromString\(\s*@?\"_|valueForKey(Path)?:\s*@\"_|value\(forKey:\s*\"_|\bdlopen\(|\bdlsym\("), None,
         "Use public APIs only. If the hit is inside a vendored library, update or replace that library."),
    Rule("private-settings-url", "2.5.1", "HIGH", "Opens private Settings URL (App-Prefs: / prefs:root)",
         C(r"App-Prefs:|prefs:root"), None,
         "Use UIApplication.openSettingsURLString (your app's settings page) instead."),
    Rule("downloaded-code", "2.5.2", "HIGH", "Downloads or hot-patches executable code",
         C(r"JSPatch|rollout\.io|evaluateScript\(\s*(try\s+)?String\(contentsOf:\s*(URL|url)"), None,
         "Remove runtime code download that changes features; ship all native functionality in the binary."),
    Rule("ota-updates", "2.5.2", "REVIEW", "Over-the-air JS updates (CodePush / expo-updates)",
         C(r"react-native-code-push|expo-updates|\bshorebird\b"), None,
         "Allowed for bug fixes only if updates don't change the app's primary purpose or add features that skip review."),
    Rule("ipv4-literal", "2.5.5", "MEDIUM", "Hard-coded IPv4 address (breaks on IPv6-only networks)",
         C(r"https?://(?!127\.|10\.|192\.168\.|0\.0\.0\.0)\d{1,3}(\.\d{1,3}){3}"), None,
         "Use a hostname; App Review tests on an IPv6-only (NAT64) network."),
    Rule("bg-location", "2.5.4", "HIGH", "'location' background mode without background location code",
         P(r"UIBackgroundModes = .*\blocation\b"),
         C(r"allowsBackgroundLocationUpdates|startMonitoringSignificantLocationChanges|startMonitoringVisits|CLBackgroundActivitySession|CLMonitor|background-geolocation|BackgroundGeolocation|expo-task-manager"),
         "Remove the background mode or implement the feature that needs it and explain it in review notes."),
    Rule("bg-audio", "2.5.4", "HIGH", "'audio' background mode without audio playback code",
         P(r"UIBackgroundModes = .*\baudio\b"),
         C(r"AVAudioPlayer|AVPlayer|AVQueuePlayer|AVAudioEngine|AudioQueue|AVSpeechSynthesizer|react-native-track-player|expo-av|expo-audio|just_audio|audioplayers|audio_service|react-native-video"),
         "Remove the audio background mode unless the app plays audible content in the background."),
    Rule("bg-voip", "2.5.4", "HIGH", "'voip' background mode without CallKit/PushKit",
         P(r"UIBackgroundModes = .*\bvoip\b"),
         C(r"PKPushRegistry|PushKit|CXProvider|CallKit|react-native-callkeep|flutter_callkit|react-native-voip-push"),
         "VoIP mode is only for real VoIP calling apps that use CallKit + PushKit."),
    Rule("recording", "2.5.14", "REVIEW", "Screen or activity recording",
         C(r"RPScreenRecorder|ReplayKit|RPSystemBroadcast"), None,
         "Get explicit consent and show a clear visual/audible indicator while recording."),
    Rule("launch-screen", "2.1(a)", "HIGH", "No launch screen configured", None,
         P(r"UILaunchStoryboardName|UILaunchScreen"),
         "Add a launch storyboard or the UILaunchScreen Info.plist key; without one the app shows letterboxed."),

    # ---- 3. Business ----
    Rule("iap-restore", "3.1.1", "HIGH", "In-app purchases without a Restore Purchases option",
         C(r"SKPaymentQueue|SKProductsRequest|Product\.products\(|Purchases\.configure|Purchases\.shared|react-native-iap|react-native-purchases|\bin_app_purchase\b|purchases_flutter|SubscriptionStoreView|StoreView\("),
         C(r"restoreCompletedTransactions|AppStore\.sync|restorePurchases|restoreTransactions|getAvailablePurchases|\.restorePurchases\b"),
         "Add a visible 'Restore Purchases' button (StoreKit 2: try await AppStore.sync())."),
    Rule("sub-terms", "3.1.2(c)", "HIGH", "Subscriptions without a Terms of Use (EULA) link",
         C(r"subscriptionPeriod|autoRenewable|SubscriptionStoreView|subscriptionGroup|getOfferings|getSubscriptions|\.subscription\b"),
         C(r"(?i:terms\s*(of\s*)?(use|service)|\beula\b|stdeula)"),
         "Show price, billing period, what's included, auto-renew, plus Terms of Use and Privacy Policy links on the paywall."),
    Rule("loot-box-odds", "3.1.1", "HIGH", "Randomized paid items without disclosed odds",
         C(r"(?i:loot\s*box|gacha|mystery\s*box|random\s*reward)"),
         C(r"(?i:\bodds\b|drop\s*rate|probabilit)"),
         "Show the odds of each item type before purchase."),
    Rule("third-party-payments", "3.1.1 / 3.1.3", "REVIEW", "Third-party payment SDK or checkout",
         C(r"StripePaymentSheet|StripePayments|import Stripe\b|@stripe/stripe-react-native|flutter_stripe|Braintree|PayPalCheckout|RazorpayCheckout|razorpay_flutter|react-native-razorpay|checkout\.stripe\.com|buy\.stripe\.com|paddle\.com|lemonsqueezy|gumroad\.com"), None,
         "Fine for physical goods/services (3.1.3(e)) or 1:1 real-time services (3.1.3(d)). Digital content, features or subscriptions must use IAP."),
    Rule("external-purchase-link", "3.1.1(a) / 3.1.3", "REVIEW", "Link or button to an external purchase page",
         C(r"https?://[^\s\"']*(checkout|billing|pricing|subscribe|upgrade|purchase|/buy)\b"), None,
         "Allowed on the US storefront. Elsewhere it needs a StoreKit External Purchase Link entitlement (or is a reader app)."),
    Rule("crypto", "3.1.5", "REVIEW", "Crypto wallet, exchange or NFT functionality",
         C(r"\bweb3\b|\bethers\b|WalletConnect|walletconnect|@solana/web3|bitcoinjs"), None,
         "Wallets need an organization account; exchanges need licensing; no on-device mining; NFTs can't unlock features."),
    Rule("gambling", "5.3", "REVIEW", "Gambling, betting or sweepstakes features",
         C(r"(?i:sports?\s*bet|casino|poker|slot\s*machine|\bwager|sweepstake)"), None,
         "Real-money gaming needs licensing + geo-restriction and a free app; sweepstakes need official rules saying Apple isn't a sponsor."),

    # ---- 4. Design ----
    Rule("web-wrapper", "4.2", "REVIEW", "Web-view based app (risk of 'repackaged website')",
         C(r"@capacitor/core|\bcordova\b|WKWebView\(|webview_flutter|react-native-webview"), None,
         "Make sure the app gives native value beyond the website: offline, push, native navigation, device features."),
    Rule("login-alternative", "4.8", "HIGH", "Third-party login without an equivalent privacy-focused option",
         C(r"GIDSignIn|GoogleSignIn|@react-native-google-signin|google_sign_in|FBSDKLoginKit|react-native-fbsdk-next|flutter_facebook_auth|LineSDK|signInWithGoogle|signInWithFacebook|providers/google|providers/facebook"),
         C(r"ASAuthorizationAppleIDProvider|SignInWithAppleButton|expo-apple-authentication|react-native-apple-authentication|sign_in_with_apple|signInWithApple|AppleAuthProvider|apple\.com['\"]"),
         "Add Sign in with Apple (or another login that limits data to name+email, allows a private email, and doesn't track)."),
    Rule("push-marketing", "4.5.4", "REVIEW", "Push notifications",
         C(r"registerForRemoteNotifications|UNUserNotificationCenter|expo-notifications|OneSignal|firebase_messaging|@react-native-firebase/messaging"), None,
         "Push can't be required to use the app; marketing pushes need explicit in-app opt-in and an opt-out."),
    Rule("review-prompt", "5.6.1", "MEDIUM", "Custom 'rate us' prompt without the system review API",
         C(r"(?i:rate (us|this app|our app)|enjoying (the|this) app)"),
         C(r"SKStoreReviewController|requestReview|react-native-in-app-review|expo-store-review|\bin_app_review\b"),
         "Use SKStoreReviewController / RequestReviewAction; don't gate or pre-filter ratings."),

    # ---- 5. Legal ----
    Rule("privacy-policy-link", "5.1.1(i)", "HIGH", "No privacy policy link inside the app", None,
         C(r"(?i:privacy[\s_-]*policy|/privacy\b)"),
         "Add a Privacy Policy link reachable from Settings/About (and the paywall/sign-up)."),
    Rule("account-deletion", "5.1.1(v)", "BLOCKER", "Account sign-up without in-app account deletion",
         C(r"createUser|createUserWithEmailAndPassword|signUp\(|signUpWithEmail|\.signUp\b|registerUser|createAccount|(?i:create\s*account|sign\s*up)\b"),
         C(r"deleteAccount|delete_account|deleteUser|user\??\.delete\(|currentUser\??\.delete|deleteMyAccount|(?i:delete\s*(my\s*)?account)"),
         "Add 'Delete Account' in Settings that deletes the account and its data (not just deactivates). Revoke Sign in with Apple tokens."),
    Rule("idfa-no-att", "5.1.2(i)", "BLOCKER", "Reads the advertising identifier without an ATT prompt",
         C(r"advertisingIdentifier|ASIdentifierManager"), C(ATT),
         "Call ATTrackingManager.requestTrackingAuthorization before reading the IDFA."),
    Rule("tracking-sdk-no-att", "5.1.2(i)", "HIGH", "Ad/attribution SDK present but no ATT prompt",
         C(r"FBSDKCoreKit|FacebookCore|FBAudienceNetwork|react-native-fbsdk|facebook_app_events|GoogleMobileAds|google_mobile_ads|react-native-google-mobile-ads|AppsFlyerLib|react-native-appsflyer|appsflyer_sdk|AdjustSdk|react-native-adjust|adjust_sdk|AppLovinSDK|applovin|IronSource|UnityAds|VungleAds|ChartboostSDK|InMobiSDK|TikTokBusinessSDK"),
         C(ATT),
         "If any SDK links your data with other companies' data for ads/measurement, request ATT first and declare it in App Privacy."),
    Rule("third-party-ai", "5.1.2(i)", "REVIEW", "Sends data to a third-party AI service",
         C(r"api\.openai\.com|import OpenAI|\bopenai\b|api\.anthropic\.com|\banthropic\b|generativelanguage\.googleapis\.com|GoogleGenerativeAI|FirebaseVertexAI|FirebaseAI|api\.mistral\.ai|api\.groq\.com|replicate\.com|api\.perplexity\.ai|openrouter\.ai|api\.deepseek\.com|api\.x\.ai"), None,
         "Tell users which data goes to which AI provider and get explicit permission first. AI-generated content also needs 1.2 moderation."),
    Rule("health-data", "5.1.3", "REVIEW", "Health data (HealthKit)",
         C(r"HKHealthStore|react-native-health"), None,
         "No ads/marketing use of health data, never store it in iCloud, disclose exactly which types you read/write."),
    Rule("media-download", "5.2.3", "HIGH", "Downloads media from third-party sources (YouTube etc.)",
         C(r"(?i:youtube-dl|yt-dlp|youtubei/v1|googlevideo\.com)"), None,
         "Remove download/convert features unless you have written authorization from the source."),
    Rule("vpn", "5.4", "REVIEW", "VPN functionality",
         C(r"NEVPNManager|NETunnelProviderManager|NEPacketTunnelProvider"), None,
         "Needs an organization account, a data-use declaration screen before purchase/use, and a no-sharing privacy policy."),
    Rule("export-compliance", "Export compliance", "LOW", "ITSAppUsesNonExemptEncryption not set", None,
         P(r"ITSAppUsesNonExemptEncryption"),
         "Set ITSAppUsesNonExemptEncryption (usually NO for HTTPS-only apps) to skip the export prompt on every build."),
]
RULES = [r._replace(when=(r.when[0], re.compile(r.when[1])) if r.when else None,
                    unless=(r.unless[0], re.compile(r.unless[1])) if r.unless else None)
         for r in RULES]


def flatten(v, key=""):
    """Yield (dotted_key, leaf_value) pairs for plist/JSON data."""
    if isinstance(v, dict):
        for k, x in v.items():
            for kv in flatten(x, "%s.%s" % (key, k) if key else str(k)):
                yield kv
    elif isinstance(v, list) and any(isinstance(x, (dict, list)) for x in v):
        for i, x in enumerate(v):
            for kv in flatten(x, "%s[%d]" % (key, i)):
                yield kv
    else:
        yield key, v


def load(root):
    code, config, purposes = [], [], []  # code/config: (relpath, lineno, text)
    meta = {"root": root, "files": 0, "ios_config": 0, "manifests": 0, "stack": set(),
            "icon_sets": [], "xcodeproj": False, "unparsed": []}

    def add_config(rel, data):
        for k, v in flatten(data):
            leaf = k.rsplit(".", 1)[-1]
            config.append((rel, 0, "%s = %r" % (leaf, v)))
            if leaf.endswith("UsageDescription") and isinstance(v, str):
                purposes.append((rel, leaf, v))

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        for d in list(dirnames):
            if d.endswith(".xcodeproj"):
                meta["xcodeproj"] = True
                meta["stack"].add("Xcode")
            if d.endswith(".appiconset") or (d.endswith(".icon") and not d.startswith(".")):
                meta["icon_sets"].append(os.path.join(dirpath, d))
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.normpath(os.path.join(rel_dir, name))
            ext = os.path.splitext(name)[1]
            if TEST_PATH.search(rel):
                continue
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
                if name.endswith("Info.plist") or ext in (".xcprivacy", ".entitlements"):
                    with open(path, "rb") as f:
                        add_config(rel, plistlib.load(f))
                    meta["ios_config"] += name.endswith("Info.plist")
                    meta["manifests"] += ext == ".xcprivacy"
                elif name == "project.pbxproj":
                    with open(path, encoding="utf-8", errors="replace") as f:
                        for line in f:
                            m = re.match(r"\s*INFOPLIST_KEY_(\w+) = \"?(.*?)\"?;\s*$", line)
                            if m:
                                add_config(rel, {m.group(1): m.group(2)})
                    meta["ios_config"] += 1
                elif name in ("app.json", "app.config.json"):
                    with open(path, encoding="utf-8") as f:
                        add_config(rel, json.load(f))
                    meta["stack"].add("Expo")
                if ext in CODE_EXT or name in DEP_FILES:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        lines = f.read().splitlines()
                    meta["files"] += 1
                    code.extend((rel, i + 1, line[:2000]) for i, line in enumerate(lines))
                    if name == "package.json":
                        text = "\n".join(lines)
                        for marker, label in (("react-native", "React Native"), ("@capacitor/core", "Capacitor"),
                                              ("cordova", "Cordova"), ("\"expo\"", "Expo")):
                            if marker in text:
                                meta["stack"].add(label)
                    elif name == "pubspec.yaml":
                        meta["stack"].add("Flutter")
                    elif ext == ".swift":
                        meta["stack"].add("Swift")
                    elif ext in (".m", ".mm"):
                        meta["stack"].add("Objective-C")
            except Exception:  # malformed/unreadable plist or JSON must not abort the whole scan
                meta["unparsed"].append(rel)
    return meta, code, config, purposes


def find(corpus, rx, exts=None, limit=3):
    hits = []
    for rel, ln, text in corpus:
        if exts and os.path.splitext(rel)[1] not in exts:
            continue
        if rx.search(text):
            hits.append((rel, ln, text.strip()[:110]))
            if len(hits) >= limit:
                break
    return hits


def result(rule, status, evidence=()):
    return {"id": rule.id, "guideline": rule.guideline, "sev": rule.sev, "title": rule.title,
            "status": status, "evidence": list(evidence), "fix": rule.fix}


def png_header(path):
    """(width, color_type) from a PNG's IHDR, or None."""
    with open(path, "rb") as f:
        h = f.read(26)
    if len(h) < 26 or h[:8] != b"\x89PNG\r\n\x1a\n" or h[12:16] != b"IHDR":
        return None
    return struct.unpack(">I", h[16:20])[0], h[25]


def check_icons(meta):
    rule = Rule("app-icon", "2.1(a) / ITMS-90717", "BLOCKER", "App Store icon (1024px, no alpha)", None, None,
                "Provide a 1024x1024 PNG App Store icon without an alpha channel (export with 'Alpha' unchecked).")
    if not meta["icon_sets"]:
        return result(rule._replace(sev="HIGH"), "FAIL" if meta["xcodeproj"] else "MANUAL",
                      [("no AppIcon.appiconset or .icon found", 0, "")])
    if any(s.endswith(".icon") for s in meta["icon_sets"]):
        return result(rule, "PASS", [(os.path.relpath(meta["icon_sets"][0], meta["root"]), 0, "Icon Composer icon")])
    big = []
    for s in meta["icon_sets"]:
        for name in os.listdir(s):
            if name.lower().endswith(".png"):
                p = os.path.join(s, name)
                info = png_header(p)
                if info and info[0] >= 1024:
                    big.append((os.path.relpath(p, meta["root"]), info[1]))
    if not big:
        return result(rule._replace(sev="HIGH"), "FAIL", [("no 1024x1024 PNG in the AppIcon set", 0, "")])
    # shortcut: checks the alpha color types (4, 6) only, not a tRNS chunk on RGB/palette PNGs
    alpha = [(p, 0, "PNG color type %d has an alpha channel" % ct) for p, ct in big if ct in (4, 6)]
    return result(rule, "FAIL", alpha) if alpha else result(rule, "PASS", [(big[0][0], 0, "")])


def check_purpose_quality(purposes):
    rule = Rule("purpose-quality", "5.1.1(ii)", "MEDIUM", "Purpose strings are specific", None, None,
                "Say what you access and why, with an example: \"Uses your location to show nearby stores.\"")
    bad = [(rel, 0, "%s = %r" % (k, v[:80])) for rel, k, v in purposes
           if len(v.strip()) < 25 or re.search(r"(?i)\b(todo|tbd|lorem|test)\b", v)
           or re.fullmatch(r"(?i)allow \$\(PRODUCT_NAME\) to access your [\w ]+\.?", v.strip())]
    if not purposes:
        return result(rule, "N/A")
    return result(rule._replace(title="Vague or placeholder purpose string"), "FAIL", bad) if bad \
        else result(rule, "PASS", [(purposes[0][0], 0, "%d purpose strings" % len(purposes))])


def scan(root):
    meta, code, config, purposes = load(root)
    corpus = {"code": code, "config": config}
    results = []
    for r in RULES:
        if r.when is None and (r.unless[0] == "code" and not code or r.unless[0] == "config" and not meta["ios_config"]):
            results.append(result(r, "MANUAL", [("no iOS config/source found to check", 0, "")]))
            continue
        hits = find(corpus[r.when[0]], r.when[1], r.exts) if r.when else []
        if r.when and not hits:
            results.append(result(r, "N/A"))
        elif r.sev == "REVIEW":
            results.append(result(r, "REVIEW", hits))
        elif r.unless is None:
            results.append(result(r, "FAIL", hits))
        elif r.unless[0] == "config" and not meta["ios_config"]:
            results.append(result(r, "MANUAL", hits))
        else:
            ok = find(corpus[r.unless[0]], r.unless[1], limit=1)
            results.append(result(r, "PASS", ok) if ok else result(r, "FAIL", hits))
    results.append(check_icons(meta))
    results.append(check_purpose_quality(purposes))
    return meta, results


def score(results):
    lost = sum(SEV_WEIGHT.get(r["sev"], 0) for r in results if r["status"] == "FAIL")
    return max(0, 100 - lost)


def render(meta, results):
    by = {}
    for r in results:
        by.setdefault(r["status"], []).append(r)
    fails = sorted(by.get("FAIL", []), key=lambda r: -SEV_WEIGHT.get(r["sev"], 0))
    counts = {s: sum(1 for r in fails if r["sev"] == s) for s in SEV_WEIGHT}
    s = score(results)
    light = "🔴" if counts["BLOCKER"] else "🟡" if counts["HIGH"] else "🟢"
    out = [
        "# %s Greenlight scan: %s" % (light, os.path.basename(meta["root"].rstrip("/")) or meta["root"]),
        "",
        "Stack: %s · source files: %d · iOS config files: %d · privacy manifests: %d" % (
            ", ".join(sorted(meta["stack"])) or "unknown", meta["files"], meta["ios_config"], meta["manifests"]),
        "",
    ]
    if meta["unparsed"]:
        out += ["Could not parse: %s" % ", ".join(meta["unparsed"][:5]), ""]
    out += [
        "**Static score: %d/100** · BLOCKER %d · HIGH %d · MEDIUM %d · LOW %d · review %d · pass %d · manual %d · n/a %d" % (
            s, counts["BLOCKER"], counts["HIGH"], counts["MEDIUM"], counts["LOW"], len(by.get("REVIEW", [])),
            len(by.get("PASS", [])), len(by.get("MANUAL", [])), len(by.get("N/A", []))),
        "",
    ]

    def section(title, items, passing=False):
        if not items:
            return
        out.extend([title, ""])
        for r in items:
            if passing:  # rule titles describe the failure, so show the rule id + proof instead
                out.append("- **%s** `%s`" % (r["guideline"], r["id"]))
            else:
                out.append("- **[%s] %s**: %s" % (r["sev"], r["guideline"], r["title"]))
            for rel, ln, text in r["evidence"]:
                loc = "%s:%d" % (rel, ln) if ln else rel
                out.append("  - `%s`%s" % (loc, ("  `%s`" % text.replace("`", "'")) if text else ""))
            if not passing:
                out.append("  - fix: %s" % r["fix"])
        out.append("")

    section("## ❌ Failing", fails)
    section("## 🔎 Needs a human decision", by.get("REVIEW", []))
    section("## ❓ Could not verify statically", by.get("MANUAL", []))
    section("## ✅ Passing", by.get("PASS", []), passing=True)
    out.append("_Static checks only. Run `/greenlight:audit` for the full guideline-by-guideline review._")
    return "\n".join(out)


def main(argv):
    root = os.path.abspath(argv[1] if len(argv) > 1 else ".")
    if not os.path.isdir(root):
        sys.exit("greenlight: not a directory: %s" % root)
    meta, results = scan(root)
    print(render(meta, results))


if __name__ == "__main__":
    main(sys.argv)
