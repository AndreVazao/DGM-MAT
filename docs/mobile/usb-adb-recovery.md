# USB + ADB automatic recovery

## Behavior
The DGM-MAT PC API starts a low-frequency USB/ADB monitor by default. It checks for Android devices, reports device / offline / unauthorized state, and automatically runs only the reversible "adb reconnect offline" action for offline devices. ADB itself may start its local server when queried.

The monitor never attempts to bypass the Android RSA authorization prompt, unlock the device, clear application data, or execute arbitrary shell commands. If Android reports unauthorized, unlock the phone and accept the USB debugging prompt. If the DGM-MAT package is missing, the monitor reports it; it does not silently install software.

## Explicit recovery actions
Authenticated operator API:
- GET /mobile/usb-recovery/state — current background monitor status.
- GET /mobile/usb-recovery/diagnose — read-only ADB and package diagnostic.
- POST /mobile/usb-recovery/repair — allowlisted action: restart-adb-server, reconnect-offline, or install-apk.

APK reinstall requires {"action":"install-apk","confirm_install":true}, exactly one authorized ADB device, and an APK at DGM_MOBILE_APK_PATH or the known local build/artifact path. It uses adb install -r to preserve application data. It never uses pm clear or adb uninstall.

## Configuration
- DGM_USB_AUTO_RECOVERY_ENABLED=0 — disable the background monitor.
- DGM_USB_AUTO_RECOVERY_INTERVAL_SECONDS=30 — polling interval, clamped to 15–300 seconds.
- DGM_ADB_PATH — optional full path to adb.exe if it is not discoverable through PATH or the standard Android SDK locations.
- DGM_MOBILE_APK_PATH — optional full path to the validated APK for an explicitly confirmed reinstall.

## Security and current limitation
All recovery endpoints require a valid DGM-MAT operator session. The mobile app never embeds the PC bootstrap secret. To pair, open http://127.0.0.1:8181/auth/pairing-code in a browser on the PC itself, then enter the one-time code in the mobile app. The code expires after five minutes and is consumed on first successful use; the issued bearer session expires after 30 minutes. The pairing-code endpoint is loopback-only and the pairing endpoint is rate-limited. The PC-side background monitor does not depend on mobile API authentication and still performs safe transient ADB reconnection.

## Validation
Tests in tests/api/test_usb_recovery.py cover device-state parsing, missing ADB, blocked arbitrary actions, confirmation before APK reinstall, and route security classification. On a Windows PC with an authorized Android device, validate:
1. API starts and monitor state appears.
2. Plug/unplug USB and check the monitor's last_report and status.
3. Test offline recovery and verify data remains intact.
4. Test APK installation only after an explicit confirmation.
