"""Self-check for the Greenlight scanner. Run: python3 -m unittest discover tests"""
import os
import plistlib
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import greenlight_scan as gs  # noqa: E402


def png(color_type):
    ihdr = struct.pack(">IIBBBBB", 1024, 1024, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr))


def build(root, files):
    for rel, content in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content if isinstance(content, bytes) else content.encode())


ICON = "App/Assets.xcassets/AppIcon.appiconset/icon-1024.png"
FAKE_SECRET = "sk_" + "live_" + "x" * 24  # assembled so no real-looking key sits in the repo

BAD = {
    "App.xcodeproj/project.pbxproj": "// placeholder\n",
    "App/Info.plist": plistlib.dumps({
        "CFBundleDisplayName": "Snapster Beta",
        "NSCameraUsageDescription": "Camera",
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": True},
        "UIBackgroundModes": ["location"],
    }),
    ICON: png(6),
    "App/Auth.swift": (
        "import GoogleSignIn\n"
        "func signUp() { Auth.auth().createUser(withEmail: e, password: p) }\n"
        "func google() { GIDSignIn.sharedInstance.signIn(withPresenting: vc) }\n"
        "let recorder = try AVAudioRecorder(url: u, settings: [:])\n"
        "let session = AVCaptureSession()\n"
        "let api = \"http://203.0.113.7:8080/v1\"\n"
        "let key = \"%s\"\n"
        "let ai = URL(string: \"https://api.openai.com/v1/chat/completions\")\n"
        "UserDefaults.standard.set(true, forKey: \"seen\")\n" % FAKE_SECRET
    ),
    "App/Paywall.swift": "let products = try await Product.products(for: ids)\nlet p = product.subscription?.subscriptionPeriod\n",
    "App/Chat.swift": "import StreamChat\n",
    "App/en.lproj/Localizable.strings": "\"cta\" = \"Also on Google Play\";\n",
}

GOOD = {
    "App.xcodeproj/project.pbxproj": "INFOPLIST_KEY_UILaunchScreen_Generation = YES;\n",
    "App/Info.plist": plistlib.dumps({
        "CFBundleDisplayName": "Snapster",
        "NSCameraUsageDescription": "Scan receipts so your expenses fill in automatically.",
        "NSMicrophoneUsageDescription": "Record voice notes that are attached to your expenses.",
        "ITSAppUsesNonExemptEncryption": False,
    }),
    "App/PrivacyInfo.xcprivacy": plistlib.dumps({"NSPrivacyAccessedAPITypes": [
        {"NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryUserDefaults",
         "NSPrivacyAccessedAPITypeReasons": ["CA92.1"]}]}),
    ICON: png(2),
    "App/Auth.swift": (
        "func signUp() { Auth.auth().createUser(withEmail: e, password: p) }\n"
        "func deleteAccount() async throws { try await Auth.auth().currentUser?.delete() }\n"
        "func google() { GIDSignIn.sharedInstance.signIn(withPresenting: vc) }\n"
        "let apple = ASAuthorizationAppleIDProvider().createRequest()\n"
        "let recorder = try AVAudioRecorder(url: u, settings: [:])\n"
        "let session = AVCaptureSession()\n"
        "UserDefaults.standard.set(true, forKey: \"seen\")\n"
    ),
    "App/Paywall.swift": (
        "let products = try await Product.products(for: ids)\n"
        "let p = product.subscription?.subscriptionPeriod\n"
        "Button(\"Restore Purchases\") { Task { try await AppStore.sync() } }\n"
        "Link(\"Terms of Use\", destination: terms)\nLink(\"Privacy Policy\", destination: privacy)\n"
    ),
    "AppTests/LeakyTests.swift": "let key = \"%s\"\n" % FAKE_SECRET,  # test targets are ignored
}


def statuses(files):
    with tempfile.TemporaryDirectory() as root:
        build(root, files)
        meta, results = gs.scan(root)
        gs.render(meta, results)  # must not raise
        return {r["id"]: r["status"] for r in results}, results


class ScanTest(unittest.TestCase):
    def test_bad_app_fails_the_expected_rules(self):
        st, _ = statuses(BAD)
        for rid in ["account-deletion", "login-alternative", "purpose-microphone", "purpose-quality",
                    "ats-disabled", "beta-name", "bg-location", "ipv4-literal", "hardcoded-secret",
                    "manifest-userdefaults", "app-icon", "iap-restore", "sub-terms", "ugc-report",
                    "ugc-block", "other-platform", "privacy-policy-link", "launch-screen"]:
            self.assertEqual(st[rid], "FAIL", rid)
        self.assertEqual(st["third-party-ai"], "REVIEW")
        self.assertEqual(st["purpose-camera"], "PASS")  # key present (quality is a separate rule)
        self.assertEqual(st["vpn"], "N/A")

    def test_good_app_has_no_blocker_or_high_failures(self):
        st, results = statuses(GOOD)
        bad = [r["id"] for r in results if r["status"] == "FAIL" and r["sev"] in ("BLOCKER", "HIGH")]
        self.assertEqual(bad, [])
        for rid in ["account-deletion", "login-alternative", "purpose-microphone", "purpose-camera",
                    "manifest-userdefaults", "app-icon", "iap-restore", "sub-terms", "privacy-policy-link",
                    "launch-screen", "export-compliance", "purpose-quality"]:
            self.assertEqual(st[rid], "PASS", rid)
        self.assertEqual(st["hardcoded-secret"], "N/A")
        self.assertEqual(gs.score(results), 100)

    def test_expo_managed_without_ios_folder_is_manual_not_fail(self):
        st, _ = statuses({"app.json": '{"expo": {"name": "x", "plugins": ["expo-camera"]}}',
                          "package.json": '{"dependencies": {"expo": "1", "expo-camera": "1"}}'})
        self.assertEqual(st["purpose-camera"], "MANUAL")
        self.assertEqual(st["launch-screen"], "MANUAL")
        self.assertEqual(st["app-icon"], "MANUAL")


if __name__ == "__main__":
    unittest.main()
