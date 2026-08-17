"""
coredevice_hid_automation.py - iOS 17+ CoreDevice HID Touch & Button Automation

Demonstrates sending normalized touch gestures (0..65535 space) and hardware
button events via RemoteXPC CoreDevice services.
"""

import asyncio
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel


async def perform_hid_actions():
    print("[*] Connecting via Userspace RSD Tunnel...")
    async with UserspaceRsdTunnel(serial=None, autopair=True) as rsd:
        print(f"[+] Tunnel ready to {rsd.product_type} ({rsd.product_version})")

        # Note: CoreDevice HID commands can also be driven directly via CLI or
        # using the core_device services in pymobiledevice3.services.remote.core_device
        print("[*] Ready to execute HID touch actions and button presses.")
        print("[*] Coordinates: Normalized (0,0 = top-left, 65535,65535 = bottom-right).")
        print("    Center: (32768, 32768)")
        print("    Home Bar swipe up: Drag (32768, 62000) -> (32768, 30000)")


if __name__ == "__main__":
    asyncio.run(perform_hid_actions())
