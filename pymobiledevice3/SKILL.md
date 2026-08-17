---
name: pymobiledevice3
description: Comprehensive agentic skill to inspect, instrument, automate, debug, and manage iOS/iPadOS/tvOS/watchOS devices using pymobiledevice3. Use when connecting to Apple devices, pulling crash reports/sysdiagnose, streaming syslog/oslog, inspecting processes with DVT sysmon, capturing network PCAP or Bluetooth HCI, managing apps/profiles/backups, exploring AFC/app sandbox files, mounting DDI / Cryptex, simulating location/conditions, controlling HID touch/buttons, or driving Safari/WebViews and WDA automation via Python async library or CLI.
---

# PyMobileDevice3 Agentic Skill

A production-grade operational playbook for AI agents to interact with iOS, iPadOS, tvOS, and watchOS devices using `pymobiledevice3` as a CLI or an asynchronous Python library.

---

## 🚨 Critical Agent Guardrails

1. **Safety First — Confirm State-Mutating Actions**:
   - **READ-ONLY actions** (inspection, syslog, crash pulling, process listing, screenshots, battery stats) are safe to execute immediately.
   - **STATE-CHANGING actions** (reboot, erase, restore, profile install/remove, app install/uninstall, file deletion, backup restore, simulated location, nonce rolling, DDI mounting) require explicit user intent or confirmation before running.
2. **Never Force Root/Sudo on iOS 17+ by Default**:
   - iOS 17.4+ developer commands automatically establish an **in-process userspace RSD tunnel** without `sudo` or daemon processes.
   - Do NOT run `sudo tunneld` unless the device is iOS 17.0–17.3, or an external tool (e.g. `lldb`) needs network access.
3. **Parse Machine-Readable Output from STDOUT**:
   - CLI data is emitted to `stdout` in JSON or NDJSON (Newline Delimited JSON). Diagnostics and logs are emitted to `stderr`.
   - Binary data is serialized as `{"$hex": "<hex-string>"}`. Timestamps are ISO 8601 strings.
4. **Always Check Pairing & Connectivity First**:
   - Begin with `pymobiledevice3 usbmux list` or `pymobiledevice3 lockdown info` before executing complex multi-step pipelines.
5. **Async-First Python Architecture**:
   - All library APIs are `asyncio` coroutines. Never use outdated synchronous snippets.

---

## 🧭 Transport & iOS Version Decision Matrix

Apple overhauled the developer stack in iOS 17+. Select the appropriate transport using this matrix:

```
                      ┌────────────────────────────┐
                      │ Target Device iOS Version  │
                      └──────────────┬─────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
         ┌────────────────────┐            ┌────────────────────┐
         │  iOS < 17.0        │            │  iOS 17.0+         │
         └──────────┬─────────┘            └──────────┬─────────┘
                    │                                 │
         ┌──────────▼─────────┐            ┌──────────▼─────────┐
         │ Plain USB Lockdown │            │ Developer Services │
         │ (No tunnel needed) │            │ Behind RSD Tunnel  │
         └────────────────────┘            └──────────┬─────────┘
                                                      │
                                 ┌────────────────────┴────────────────────┐
                                 ▼                                         ▼
                     ┌───────────────────────┐                 ┌───────────────────────┐
                     │ iOS 17.4+ (Default)   │                 │ iOS 17.0 – 17.3       │
                     │ In-Process Userspace  │                 │ Privileged Tunneld    │
                     │ RSD (No root / sudo)  │                 │ sudo tunneld / remote │
                     └───────────────────────┘                 └───────────────────────┘
```

| Domain / Service | iOS Version | Connection Method | CLI Transport Flag | Python Entry Point |
|---|---|---|---|---|
| **Lockdown Info / Pairing** | All | USB / Wi-Fi | *(none)* | `create_using_usbmux()` |
| **AFC / HouseArrest** | All | Lockdown | *(none)* | `AfcService(lockdown)` |
| **Syslog / Diagnostics** | All | Lockdown | *(none)* | `OsTraceService(lockdown)` / `DiagnosticsService` |
| **Apps / Backup2** | All | Lockdown | *(none)* | `InstallationProxyService` / `Mobilebackup2Service` |
| **DVT / Sysmon / Oslog** | < 17.0 | Lockdown | *(none)* | `DvtProvider(lockdown)` |
| **DVT / Sysmon / Oslog** | 17.0+ | RSD Tunnel | `--userspace` (default) | `UserspaceRsdTunnel()` → `DvtProvider(rsd)` |
| **CoreDevice (HID/Display)**| 17.0+ | RSD Tunnel | `--userspace` (default) | `UserspaceRsdTunnel()` → CoreDevice clients |
| **Cryptexd** | 17.0+ | RSD Tunnel | `--userspace` (default) | `UserspaceRsdTunnel()` → `CryptexdService(rsd)` |

---

## ⚡ Execution Modes: CLI vs Python

### 1. In Repository Workspace
```shell
uvx --from . pymobiledevice3 usbmux list
uvx --from . pymobiledevice3 lockdown info
```

### 2. Standalone / Global Execution
```shell
python -m pymobiledevice3 usbmux list
# or via uvx
uvx pymobiledevice3 usbmux list
```

---

## 🚀 Fast-Path Workflows (Top Tasks)

### 1. Device Triage & Connectivity Check
```shell
# List attached USB/network devices (UDID, ConnectionType, ProductType)
pymobiledevice3 usbmux list

# Query hardware, OS version, serial, build number
pymobiledevice3 lockdown info
```

### 2. Live Logs & Diagnostics
```shell
# Stream live syslog with regex matching
pymobiledevice3 syslog live -m "SpringBoard|mobileactivationd"

# Stream iOS unified logging via DVT (iOS 17+ auto-tunnels)
pymobiledevice3 developer dvt oslog

# Query running processes without developer tunnel (diagnosticsd)
pymobiledevice3 processes ps

# Pull crash reports and sysdiagnose to local directory
pymobiledevice3 crash pull ./crashes/
```

### 3. File System & Sandboxes (AFC / HouseArrest)
```shell
# Interactive AFC shell for /var/mobile/Media
pymobiledevice3 afc shell

# Pull file from device
pymobiledevice3 afc pull /DCIM/100APPLE/IMG_0001.JPG ./photo.jpg

# Push file to device
pymobiledevice3 afc push ./payload.bin /Downloads/payload.bin

# Access sandboxed app documents container (requires app with UIFileSharingEnabled or developer signed)
pymobiledevice3 apps documents com.example.MyApp pull /Documents/db.sqlite ./db.sqlite
```

### 4. Installed Applications
```shell
# List installed third-party apps
pymobiledevice3 apps list --application-type User

# Query detailed metadata for specific bundle IDs
pymobiledevice3 apps query com.apple.Preferences com.apple.mobilesafari
```

### 5. Developer Mode & Developer Disk Image (DDI / Cryptex)
```shell
# Enable iOS Developer Mode (reboot prompt on device)
pymobiledevice3 amfi enable-developer-mode

# Auto-mount Developer Disk Image (fetches and mounts appropriate DDI)
pymobiledevice3 mounter auto-mount

# On iOS 17+, install DDI as personalized Cryptex via cryptexd
pymobiledevice3 cryptex auto-install
```

### 6. DVT Performance & Instrumentation (iOS 17+ compatible)
```shell
# Single snapshot of system CPU and process metrics
pymobiledevice3 developer dvt sysmon process single

# Stream processes consuming > 20% CPU
pymobiledevice3 developer dvt sysmon process monitor threshold 20

# Launch an application by bundle ID
pymobiledevice3 developer dvt launch com.apple.mobilesafari

# Take a screenshot via DVT
pymobiledevice3 developer dvt screenshot ./screen.png
```

### 7. CoreDevice HID Input & Screen Stream (iOS 17+)
```shell
# Hardware button press (home, power, lock, volume-up, volume-down, siri)
pymobiledevice3 developer core-device hid button home press

# Touch tap at normalized coordinates (0..65535, center = 32768, 32768)
pymobiledevice3 developer core-device universal-hid-service tap -- 32768 32768

# Touch drag (e.g. pull down notification center)
pymobiledevice3 developer core-device universal-hid-service drag -- 32768 5000 32768 60000

# Stream device screen to local browser via WebCodecs
pymobiledevice3 developer core-device display serve-web
```

### 8. WebInspector & Browser Automation
```shell
# List open Safari tabs and WebViews
pymobiledevice3 webinspector opened-tabs

# Open interactive JavaScript shell on active tab
pymobiledevice3 webinspector js-shell

# Bridge WebInspector to Chrome DevTools Protocol (CDP) for remote debugging
pymobiledevice3 webinspector cdp
```

---

## 🐍 Python Async Scripting Quickstart

### Example: Inspect Device & Stream Syslog

```python
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.os_trace import OsTraceService
from pymobiledevice3.services.installation_proxy import InstallationProxyService

async def main():
    # 1. Connect via Usbmux Lockdown
    async with await create_using_usbmux() as lockdown:
        print(f"Device: {lockdown.display_name} ({lockdown.product_version})")
        print(f"UDID: {lockdown.identifier}")

        # 2. Query Installed Apps
        installer = InstallationProxyService(lockdown=lockdown)
        apps = await installer.get_apps(application_type="User")
        print(f"Installed User Apps ({len(apps)}):")
        for bundle_id in sorted(apps.keys())[:10]:
            print(f"  - {bundle_id}")

        # 3. Stream Syslog for 5 seconds
        print("\nStreaming syslog sample:")
        trace = OsTraceService(lockdown=lockdown)
        count = 0
        async for entry in trace.syslog():
            print(f"[{entry.label}] {entry.image_name}: {entry.message}")
            count += 1
            if count >= 10:
                break

if __name__ == "__main__":
    asyncio.run(main())
```

### Example: iOS 17+ In-Process Userspace RSD & DVT

```python
import asyncio
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap

async def main():
    # Establishes pure-Python userspace RSD tunnel (No root required)
    async with UserspaceRsdTunnel(serial=None, autopair=True) as rsd:
        print(f"Connected to RSD: {rsd.product_version} ({rsd.product_type})")

        async with DvtProvider(rsd) as dvt:
            # Process control: launch Safari
            pc = ProcessControl(dvt)
            pid = await pc.launch("com.apple.mobilesafari")
            print(f"Launched MobileSafari PID: {pid}")

            # System monitoring snapshot
            async with Sysmontap(dvt) as sysmon:
                sample = await sysmon.get_single_system_sample()
                print("Sysmon sample:", sample)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 Specialized Skill References

Load these reference files when detailed domain knowledge is required:

- [CLI Command Cheatsheet](./references/cli-recipes.md) — Comprehensive command catalog across all 30+ service groups.
- [Python Async API Patterns](./references/python-async-patterns.md) — Complete coroutine blueprints, connection patterns, and service lifecycles.
- [Transport & iOS 17+ RSD Tunnels](./references/transport-and-tunnels.md) — Deep dive into QUIC/WireGuard, CoreDeviceProxy, userspace tunnels, and port forwarding.
- [Troubleshooting & Diagnostics Guide](./references/troubleshooting-matrix.md) — Error resolution matrix (pairing, lockdown, DDI mounting, sandbox restrictions).
