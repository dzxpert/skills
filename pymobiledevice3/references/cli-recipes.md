# PyMobileDevice3 CLI Command Catalog & Recipes

This reference provides a complete index of `pymobiledevice3` command-line interfaces organized by functional domain.

---

## 1. Device Discovery & Basic Lockdown

```shell
# List all attached devices with UDID, ConnectionType, and ProductType
pymobiledevice3 usbmux list

# Forward local host port to device port over usbmux
pymobiledevice3 usbmux forward 8080 8080

# Query complete lockdown dictionary (all device properties)
pymobiledevice3 lockdown info

# Query specific domain or key
pymobiledevice3 lockdown info --domain com.apple.disk_usage
pymobiledevice3 lockdown get-value --key UniqueDeviceID

# Query battery state & cycle count (via Diagnostics domain)
pymobiledevice3 diagnostics battery info
pymobiledevice3 diagnostics battery monitor --format json

# Pair device (prompts for trust on device screen)
pymobiledevice3 lockdown pair

# Set device language/locale
pymobiledevice3 lockdown set-locale en_US
```

---

## 2. Diagnostics, Logs, & System Monitoring

```shell
# Live syslog stream with regex filter
pymobiledevice3 syslog live -m "SpringBoard"

# Live syslog stream excluding noisy daemons
pymobiledevice3 syslog live -v "mediaserverd"

# Stream unified logging over DVT (iOS 17+ auto-tunnels)
pymobiledevice3 developer dvt oslog

# Query process list without developer tunnel (diagnosticsd API)
pymobiledevice3 processes ps

# Find process ID by name pattern
pymobiledevice3 processes pgrep backboardd

# Pull all crash reports and diagnostic archives (.ips, .synced, .ips.synced)
pymobiledevice3 crash pull ./crash_logs/

# Watch for new crash logs in real time
pymobiledevice3 crash watch --format json

# Capture Bluetooth HCI traffic to PacketLogger format (.pklg) or pcapng
pymobiledevice3 btlogger ./trace.pklg
pymobiledevice3 btlogger -f pcapng ./trace.pcapng

# Remote packet capture (sniff device network interfaces)
pymobiledevice3 pcap --out ./capture.pcap
pymobiledevice3 pcap --process backboardd -c 100
```

---

## 3. Files, App Containers, & AFC

```shell
# Interactive AFC shell for /var/mobile/Media
pymobiledevice3 afc shell

# List directory contents on media partition
pymobiledevice3 afc ls /DCIM

# Pull file or directory from device
pymobiledevice3 afc pull /DCIM/100APPLE/IMG_0001.JPG ./IMG_0001.JPG

# Push local file to device
pymobiledevice3 afc push ./config.json /Downloads/config.json

# Remove file or directory on device
pymobiledevice3 afc rm /Downloads/config.json

# Access sandboxed application container (Documents/Library)
pymobiledevice3 apps documents <bundle_id> ls /
pymobiledevice3 apps documents <bundle_id> pull /Documents/database.sqlite ./database.sqlite
pymobiledevice3 apps documents <bundle_id> push ./modified.plist /Library/Preferences/com.app.plist
```

---

## 4. Application Management & Provisioning

```shell
# List installed User applications
pymobiledevice3 apps list --application-type User

# List System / Hidden / Internal applications
pymobiledevice3 apps list --application-type System
pymobiledevice3 apps list --application-type Internal

# Query app metadata for one or more bundle IDs
pymobiledevice3 apps query com.apple.Preferences com.apple.mobilesafari

# Install an iOS application package (.ipa)
pymobiledevice3 apps install ./MyApp.ipa

# Uninstall an application by bundle ID
pymobiledevice3 apps uninstall com.example.MyApp

# List installed configuration profiles (.mobileconfig)
pymobiledevice3 profile list

# Install a configuration profile
pymobiledevice3 profile install ./payload.mobileconfig

# Remove a configuration profile by identifier
pymobiledevice3 profile remove com.example.profile

# List provisioning profiles
pymobiledevice3 provision list
```

---

## 5. Developer Mode, DDI, & Cryptex (iOS 17+)

```shell
# Enable iOS Developer Mode (triggers confirmation/reboot on iOS 16+)
pymobiledevice3 amfi enable-developer-mode

# Automatically download and mount Developer Disk Image (DDI)
pymobiledevice3 mounter auto-mount

# Install personalized DDI as Cryptex over cryptexd (iOS 17+, needs RSD)
pymobiledevice3 cryptex auto-install

# List mounted Cryptexes
pymobiledevice3 cryptex list

# Inspect device personalization identifiers (ECID, ChipID, BoardId, Nonce)
pymobiledevice3 cryptex personalization-identifiers
pymobiledevice3 cryptex nonce
```

---

## 6. DVT Instruments & Developer Subsystems

```shell
# Detailed snapshot of CPU, memory, and thread usage
pymobiledevice3 developer dvt sysmon process single

# Stream processes exceeding CPU threshold
pymobiledevice3 developer dvt sysmon process monitor threshold 50

# Filter sysmon stream to a specific process name with selected fields
pymobiledevice3 developer dvt sysmon process monitor process --filter name=SpringBoard --key name --key cpuUsage --key physFootprint --human

# Launch application and obtain spawned PID
pymobiledevice3 developer dvt launch com.apple.mobilesafari

# Terminate running process by PID
pymobiledevice3 developer dvt kill <PID>

# Disable jetsam memory limit for a process
pymobiledevice3 developer dvt memlimitoff <PID>

# Take a screenshot via DVT instruments
pymobiledevice3 developer dvt screenshot ./screen.png

# Simulate GPS location (iOS 17+)
pymobiledevice3 developer dvt simulate-location set -- 37.7749 -122.4194

# Clear simulated GPS location
pymobiledevice3 developer dvt simulate-location clear

# Play a GPX route with optional jitter (ms)
pymobiledevice3 developer dvt simulate-location play ./route.gpx 200

# Live KDebug kernel event tracing (strace-equivalent for iOS)
pymobiledevice3 developer dvt core-profile-session parse-live
```

---

## 7. CoreDevice (iOS 17+ RSD Services)

```shell
# Capture screenshot via CoreDevice
pymobiledevice3 developer core-device screen-capture screenshot ./screen.png

# Fetch high-resolution application icon
pymobiledevice3 developer core-device fetch-app-icon com.apple.Preferences ./PreferencesIcon.png --width 176 --height 176 --scale 2

# Hardware button triggers: home, power, lock, volume-up, volume-down, siri
pymobiledevice3 developer core-device hid button home press
pymobiledevice3 developer core-device hid button volume-up down
pymobiledevice3 developer core-device hid button volume-up up

# Normalized touch tap (0..65535 screen coordinate space)
pymobiledevice3 developer core-device universal-hid-service tap -- 32768 32768

# Normalized touch drag (e.g. top pull-down)
pymobiledevice3 developer core-device universal-hid-service drag -- 32768 5000 32768 60000

# Serve live device display to browser via WebCodecs
pymobiledevice3 developer core-device display serve-web

# Serve live device display as VNC server (macOS only)
pymobiledevice3 developer core-device display serve-vnc
```

---

## 8. WebInspector & Browser Automation

```shell
# List opened tabs across Safari and app WebViews
pymobiledevice3 webinspector opened-tabs

# Open interactive JavaScript shell attached to first open tab
pymobiledevice3 webinspector js-shell

# Open JavaScript shell filtered to specific application's WebViews
pymobiledevice3 webinspector js-shell --bundle-id com.example.MyApp

# Launch Safari directly to a URL
pymobiledevice3 webinspector launch https://apple.com

# Start Chrome DevTools Protocol (CDP) bridge for remote debugging
pymobiledevice3 webinspector cdp
```

---

## 9. Backups & Restores

```shell
# Full device backup
pymobiledevice3 backup2 backup --full ./Backups/

# Selective backup (extract only messages / SMS without saving entire media)
pymobiledevice3 backup2 backup --only messages ./Backups/

# Selective backup for specific data domains
pymobiledevice3 backup2 backup --only sms ./Backups/
pymobiledevice3 backup2 backup --only whatsapp ./Backups/
pymobiledevice3 backup2 backup --only contacts ./Backups/
pymobiledevice3 backup2 backup --only call_history ./Backups/

# Restore backup to device
pymobiledevice3 backup2 restore ./Backups/
```
