# Troubleshooting & Diagnostics Matrix

This guide details error signatures, root causes, and deterministic remediation steps for issues encountered while interacting with iOS devices.

---

## 1. Fast Diagnostics Flowchart

```
                 [Command / API Call Fails]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [Connectivity / Pairing]        [Developer / DVT Services]
            │                                 │
     1. usbmux list                    1. amfi enable-developer-mode
     2. lockdown info                  2. mounter auto-mount / cryptex auto-install
     3. Check trust prompt             3. Verify iOS version & tunnel mode
```

---

## 2. Common Errors & Resolution Matrix

| Error Signature | Underlying Root Cause | Deterministic Fix |
|---|---|---|
| `NoDeviceConnectedError` / empty `usbmux list` | USB cable loose, device off, or Usbmux daemon not running. | 1. Re-plug USB.<br>2. On Windows, ensure *Apple Mobile Device Service* is running in `services.msc`.<br>3. Run `pymobiledevice3 usbmux list`. |
| `DeviceNotPairedError` | Device does not have a valid pairing record for this host. | 1. Unlock device passcode.<br>2. Run `pymobiledevice3 lockdown pair`.<br>3. Tap **Trust** and enter passcode on the device screen. |
| `PasswordProtectedError` | Device screen is locked with passcode. | Unlock device screen with PIN/passcode and re-run command. |
| `DeveloperModeDisabledError` | iOS 16+ requires Developer Mode to run DVT/developer services. | 1. Run `pymobiledevice3 amfi enable-developer-mode`.<br>2. On device, confirm restart.<br>3. After reboot, unlock and confirm "Turn On". |
| `MounterError` / `DeveloperImageUnavailable` | DDI is not mounted for current iOS build. | 1. Run `pymobiledevice3 mounter auto-mount`.<br>2. On iOS 17+, run `pymobiledevice3 cryptex auto-install`. |
| `RemoteServiceDiscoveryError` / Tunnel timeout | Tunnel failed to handshake or CoreDeviceProxy crashed. | 1. Verify device is paired and unlocked.<br>2. Try forcing userspace tunnel explicitly: `--userspace`.<br>3. If using iOS 17.0–17.3, start privileged `sudo tunneld` first. |
| `AfcError` (`AFC_E_OBJECT_NOT_FOUND` / Permission denied) | Sandboxed app container does not permit AFC access. | Application must have `UIFileSharingEnabled` set to true in `Info.plist` or be developer-signed with debugging entitlements. |
| `SessionActiveError` | Another service session is holding exclusive lock. | Close competing processes or recreate service connection. |

---

## 3. Syslog-First Troubleshooting Technique

When an error message returned by `pymobiledevice3` is opaque, iOS daemons almost always write the exact reason into the system log.

### Step 1: Start Syslog Filter in Background / Terminal
```shell
# Filter for relevant daemons (e.g. mobileactivationd, amfid, lockdownd, installd, SpringBoard)
pymobiledevice3 syslog live -m "lockdownd|installd|amfid|cryptexd"
```

### Step 2: Reproduce the Failing Action
In another terminal or command step, run the failing command (e.g., app install or profile provision).

### Step 3: Inspect Daemon Output
Look for security denials (e.g., `MIS: ... failed code signing verification`, `AMFI: entitlement denied`, or `installd: Package inspection failed`).
