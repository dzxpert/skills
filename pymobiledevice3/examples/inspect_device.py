"""
inspect_device.py - Safe Read-Only Device Triage Script

Queries and displays connected iOS device properties, battery statistics,
and installed user applications.
"""

import asyncio
import json
import sys
from pymobiledevice3.exceptions import (
    DeviceNotPairedError,
    NoDeviceConnectedError,
    PasswordProtectedError,
    PyMobileDevice3Exception,
)
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.services.installation_proxy import InstallationProxyService


async def inspect_device(serial: str = None):
    try:
        async with await create_using_usbmux(serial=serial) as lockdown:
            print("=" * 60)
            print(f"Device Name:     {lockdown.display_name}")
            print(f"Product Type:    {lockdown.product_type}")
            print(f"iOS Version:     {lockdown.product_version} (Build: {lockdown.build_version})")
            print(f"UDID:            {lockdown.identifier}")
            print(f"Serial Number:   {lockdown.get_value(key='SerialNumber')}")
            print(f"Wi-Fi Address:   {lockdown.get_value(key='WiFiAddress')}")
            print("=" * 60)

            # Battery & Diagnostics Info
            try:
                diag = DiagnosticsService(lockdown=lockdown)
                battery = await diag.get_battery()
                print("\n[+] Battery Status:")
                print(f"    Current Capacity: {battery.get('CurrentCapacity')}%")
                print(f"    Is Charging:      {battery.get('IsCharging')}")
                print(f"    Cycle Count:      {battery.get('CycleCount', 'N/A')}")
            except Exception as e:
                print(f"[-] Battery diagnostics skipped: {e}")

            # Installed User Apps
            try:
                installer = InstallationProxyService(lockdown=lockdown)
                user_apps = await installer.get_apps(application_type="User")
                print(f"\n[+] User Applications ({len(user_apps)} installed):")
                for bundle_id, info in sorted(user_apps.items())[:15]:
                    name = info.get("CFBundleDisplayName", bundle_id)
                    version = info.get("CFBundleShortVersionString", "N/A")
                    print(f"    - {name} ({bundle_id}) v{version}")
                if len(user_apps) > 15:
                    print(f"    ... and {len(user_apps) - 15} more.")
            except Exception as e:
                print(f"[-] Application listing skipped: {e}")

    except NoDeviceConnectedError:
        print("[-] Error: No iOS device connected via USB/Wi-Fi.")
        sys.exit(1)
    except PasswordProtectedError:
        print("[-] Error: Device is locked with passcode. Please unlock your device.")
        sys.exit(1)
    except DeviceNotPairedError:
        print("[-] Error: Device is not paired with this computer. Tap 'Trust' on device screen.")
        sys.exit(1)
    except PyMobileDevice3Exception as e:
        print(f"[-] PyMobileDevice3 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    target_serial = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(inspect_device(target_serial))
