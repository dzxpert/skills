"""
stream_syslog.py - Real-Time Syslog Streamer with Filtering

Streams live system log messages with optional process/subsystem regex filtering.
"""

import asyncio
import re
import sys
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.os_trace import OsTraceService


async def stream_logs(pattern: str = None, max_lines: int = 50):
    regex = re.compile(pattern, re.IGNORECASE) if pattern else None

    async with await create_using_usbmux() as lockdown:
        print(f"[*] Connected to {lockdown.display_name}. Starting syslog stream...")
        if pattern:
            print(f"[*] Filtering by regex pattern: '{pattern}'")

        trace = OsTraceService(lockdown=lockdown)
        count = 0

        async for entry in trace.syslog():
            log_line = f"[{entry.level.name:7s}] {entry.image_name} [{entry.pid}]: {entry.message}"
            if regex is None or regex.search(log_line):
                print(log_line)
                count += 1
                if max_lines and count >= max_lines:
                    print(f"\n[*] Captured {max_lines} matching lines. Exiting.")
                    break


if __name__ == "__main__":
    filter_pattern = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    try:
        asyncio.run(stream_logs(filter_pattern, limit))
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user.")
