# Python Async Scripting Architecture & Patterns

This reference document provides the definitive guide for writing robust, asynchronous Python code using `pymobiledevice3` as an API library.

---

## 1. Architectural Foundations

1. **Asyncio-First**: All network I/O, service handshakes, and command executions are `asyncio` coroutines.
2. **Service Providers**:
   - `LockdownClient`: Manages classic USB/Wi-Fi lockdown connections on all iOS versions.
   - `RemoteServiceDiscoveryService` (RSD): Manages RemoteXPC developer endpoints on iOS 17+.
3. **Context Managers**: Always use `async with` for service lifecycles to ensure proper socket closure and teardown.

---

## 2. Connection Initialization Patterns

### Pattern A: USB Lockdown Connection (All iOS Versions)

```python
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux

async def main():
    # Pass serial="<udid>" to target a specific device, or None for the first device
    async with await create_using_usbmux() as lockdown:
        print(f"Device: {lockdown.display_name}")
        print(f"Version: {lockdown.product_version}")
        print(f"Hardware: {lockdown.product_type}")
        print(f"UDID: {lockdown.identifier}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Pattern B: In-Process Userspace RSD Tunnel (iOS 17+)

This is the **recommended** path for iOS 17.4+ developer/DVT services. It brings up a full userspace networking stack inside your Python process without requiring root/sudo or a daemon.

```python
import asyncio
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel

async def main():
    # autopair=True automatically exchanges keys and pairs if required
    async with UserspaceRsdTunnel(serial=None, autopair=True) as rsd:
        print(f"Connected to RSD Endpoint: {rsd.peer_address}")
        print(f"Device: {rsd.product_type} ({rsd.product_version})")
        # `rsd` is a connected RemoteServiceDiscoveryService

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. Working with Core Services

### AFC (Apple File Conduit) File Operations

```python
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService

async def main():
    async with await create_using_usbmux() as lockdown:
        afc = AfcService(lockdown=lockdown)

        # List files on the Media partition
        items = await afc.listdir("/")
        print("Root media items:", items)

        # Read file contents into memory
        if await afc.exists("/DCIM/info.txt"):
            data = await afc.get_file_contents("/DCIM/info.txt")
            print("File content:", data.decode("utf-8", errors="ignore"))

        # Write data to a file
        await afc.set_file_contents("/Downloads/agent_marker.txt", b"Antigravity Agent Active")

        # Stat file metadata
        stat = await afc.stat("/Downloads/agent_marker.txt")
        print(f"Size: {stat['st_size']} bytes, Modified: {stat['st_mtime']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Application Lifecycle (InstallationProxy)

```python
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.installation_proxy import InstallationProxyService

async def main():
    async with await create_using_usbmux() as lockdown:
        installer = InstallationProxyService(lockdown=lockdown)

        # Get all user-installed applications
        apps = await installer.get_apps(application_type="User")
        for bundle_id, app_info in apps.items():
            version = app_info.get("CFBundleShortVersionString", "N/A")
            name = app_info.get("CFBundleDisplayName", bundle_id)
            print(f"App: {name} ({bundle_id}) v{version}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Real-Time Syslog Streaming (OsTrace)

```python
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.os_trace import OsTraceService

async def main():
    async with await create_using_usbmux() as lockdown:
        trace = OsTraceService(lockdown=lockdown)

        print("Streaming syslog (Ctrl+C to stop)...")
        count = 0
        async for entry in trace.syslog():
            # entry fields: timestamp, level, pid, image_name, message, label
            print(f"[{entry.level.name:7s}] {entry.image_name} [{entry.pid}]: {entry.message}")
            count += 1
            if count >= 20:
                break

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. DVT Instrumentation & Developer Services (iOS 17+)

```python
import asyncio
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

async def main():
    async with UserspaceRsdTunnel(serial=None, autopair=True) as rsd:
        async with DvtProvider(rsd) as dvt:
            # 1. Launch Process
            pc = ProcessControl(dvt)
            pid = await pc.launch("com.apple.mobilesafari")
            print(f"Launched Safari with PID: {pid}")

            # 2. System Monitoring Metrics
            async with Sysmontap(dvt) as sysmon:
                sample = await sysmon.get_single_system_sample()
                cpu_total = sample.get("systemCPU", {})
                print(f"System CPU Usage: {cpu_total}")

            # 3. Capture Screen
            screenshot_service = Screenshot(dvt)
            png_bytes = await screenshot_service.get_screenshot()
            with open("screenshot.png", "wb") as f:
                f.write(png_bytes)
            print("Saved screenshot.png")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. WebInspector Automation

```python
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.webinspector import WebInspectorService

async def main():
    async with await create_using_usbmux() as lockdown:
        async with WebInspectorService(lockdown=lockdown) as webinspector:
            # Inspect open web pages
            pages = await webinspector.get_open_pages()
            for page in pages:
                print(f"Page ID: {page.page_id}, URL: {page.url}, Title: {page.web_title}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Error Handling & Resilience Patterns

```python
import asyncio
from pymobiledevice3.exceptions import (
    DeviceNotPairedError,
    DeveloperModeDisabledError,
    NoDeviceConnectedError,
    PyMobileDevice3Exception
)
from pymobiledevice3.lockdown import create_using_usbmux

async def safe_device_operation():
    try:
        async with await create_using_usbmux() as lockdown:
            print("Connected to:", lockdown.display_name)
    except NoDeviceConnectedError:
        print("[-] No iOS device detected. Ensure device is plugged in via USB.")
    except DeviceNotPairedError:
        print("[-] Device is not paired. Unlock your device and accept the 'Trust This Computer' prompt.")
    except DeveloperModeDisabledError:
        print("[-] Developer Mode is disabled. Enable it under Settings > Privacy & Security > Developer Mode.")
    except PyMobileDevice3Exception as e:
        print(f"[-] MobileDevice error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(safe_device_operation())
```
