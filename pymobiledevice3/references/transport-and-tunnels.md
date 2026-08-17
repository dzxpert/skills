# Transports, RemoteXPC, & iOS 17+ RSD Tunnels

This reference explains the transport mechanisms, network stacks, and tunnel architectures used across different iOS versions and services in `pymobiledevice3`.

---

## 1. Transport Evolution Overview

Historically (iOS ≤ 16), all communication between host computers and iOS devices flowed through **usbmuxd** (USB multiplexer). Lockdown and developer services (DVT instruments, debugserver) were straightforward TCP streams multiplexed over USB.

Beginning in **iOS 17**, Apple refactored developer services behind **RemoteXPC** and **Remote Service Discovery (RSD)**, encapsulating connections within encrypted IPv6 tunnels (using QUIC, WireGuard, and CoreDeviceProxy).

```
                      ┌──────────────────────────────────────────────┐
                      │              Host Application                │
                      │         (pymobiledevice3 CLI/API)            │
                      └───────┬──────────────────────────────┬───────┘
                              │                              │
               (Classic Lockdown Services)       (iOS 17+ Developer Services)
                              │                              │
                              ▼                              ▼
                 ┌─────────────────────────┐   ┌───────────────────────────┐
                 │         usbmuxd         │   │   Userspace RSD Tunnel    │
                 │   (USB / TCP 27015)     │   │   (Pure-Python NetStack)  │
                 └────────────┬────────────┘   └─────────────┬─────────────┘
                              │                              │
                              ▼                              ▼
                 ┌─────────────────────────┐   ┌───────────────────────────┐
                 │   lockdownd (Port 62078)│   │   RemoteXPC / RSD Daemon  │
                 │   - AFC, Syslog, Apps   │   │   - DVT, Sysmon, CoreDev  │
                 └─────────────────────────┘   └───────────────────────────┘
```

---

## 2. Transport Mechanisms Explained

### A. Classic Usbmux Lockdown (All iOS Versions)
- **Host Transport**: Connects to the local usbmux daemon (`127.0.0.1:27015` on Windows, `/var/run/usbmuxd` on macOS/Linux).
- **Protocol**: Exchanging plist messages over TCP. Upon pairing, an SSL/TLS session is negotiated using pair records saved on the host (`~/.pymobiledevice3/pair_records` or Apple's `Lockdown` directory).
- **Target Services**: AFC, Installation Proxy, MobileBackup2, OsTrace/Syslog, CrashReports, Diagnostics, Profiles.

### B. In-Process Userspace RSD Tunnel (iOS 17.4+ Default)
- **Architecture**: A pure-Python user-space networking stack implementing the tunnel handshake directly inside the running process.
- **Root/Sudo**: **None required**. Runs entirely in unprivileged user space.
- **Port Isolation**: The virtual IPv6 address created by the tunnel is visible **only inside this Python process**. External tools (e.g. standard system `lldb`) cannot connect directly to it.
- **When to Use**: Default for all developer and DVT commands executed from scripts, CLI, or agent workflows.

### C. Privileged `tunneld` Daemon (iOS 17.0–17.3 or Multi-Process Tooling)
- **Architecture**: A background daemon that sets up a system-level TUN/TAP virtual network interface (`utun` on macOS, `wintun` on Windows).
- **Root/Sudo**: Requires elevated/administrator privileges to create network adapters and modify routing tables.
- **When to Use**:
  1. Legacy iOS 17.0–17.3 devices (which lack CoreDeviceProxy userspace tunnel endpoints).
  2. High-throughput DDI flashing or massive file transfers where user-space Python network overhead is noticeable.
  3. Sharing a single persistent tunnel across multiple independent processes (e.g., standard Xcode LLDB + CLI tools).

---

## 3. CLI Transport Flags & Resolution

When executing commands, `pymobiledevice3`'s dependency injector (`ServiceProviderDep`) automatically resolves transport:

| Flag | Purpose | Mutually Exclusive With |
|---|---|---|
| *(none)* | Automatically selects best transport (USB lockdown for classic; in-process userspace tunnel for iOS 17+ developer services). | — |
| `--userspace` | Forces the in-process userspace RSD tunnel explicitly. | `--rsd`, `--tunnel` |
| `--tunnel <UDID>` | Directs command to use an existing RSD tunnel published by a running `tunneld` daemon. | `--userspace`, `--rsd` |
| `--rsd <HOST> <PORT>` | Directly connects to a specified RSD hostname/IP and port. | `--userspace`, `--tunnel` |
| `--udid <UDID>` | Selects specific device when multiple are connected. | — |

---

## 4. Environment Variable Configuration

Agents and automated scripts can control transport behavior via environment variables:

| Variable | Values | Description |
|---|---|---|
| `PYMOBILEDEVICE3_USERSPACE` | `1` / `0` | Set `1` to force userspace tunnel mode for developer services. |
| `PYMOBILEDEVICE3_PREFER_TUNNELD` | `1` / `0` | Set `1` to opt out of userspace tunnels and force `tunneld` lookup. |
| `PYMOBILEDEVICE3_UDID` | `<UDID-string>` | Target specific device UDID across all commands. |
| `PYMOBILEDEVICE3_PAIRING_RECORDS_CACHE_FOLDER` | `<path>` | Custom directory path for device pairing records. |

---

## 5. Port Forwarding via Usbmux

To bridge a local TCP port to a listening port on the iOS device (e.g. custom debug servers or local proxies):

```shell
# Forwards local localhost:5000 to device port 5000
pymobiledevice3 usbmux forward 5000 5000
```
