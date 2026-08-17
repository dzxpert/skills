"""
dvt_sysmon_profiler.py - iOS DVT System & Process Profiler

Connects via in-process userspace RSD tunnel (iOS 17+) and samples system
metrics and high-CPU processes using DvtProvider and Sysmontap.
"""

import asyncio
import sys
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap


async def profile_system():
    print("[*] Establishing Userspace RSD Tunnel...")
    async with UserspaceRsdTunnel(serial=None, autopair=True) as rsd:
        print(f"[+] Connected to RSD: {rsd.product_type} on iOS {rsd.product_version}")

        print("[*] Initializing DVT Instrument Provider...")
        async with DvtProvider(rsd) as dvt:
            async with Sysmontap(dvt) as sysmon:
                print("[*] Capturing system resource sample...")
                sample = await sysmon.get_single_system_sample()

                sys_cpu = sample.get("systemCPU", {})
                print("\n" + "=" * 50)
                print("SYSTEM RESOURCE SUMMARY")
                print("=" * 50)
                print(f"Total CPU Usage:   {sys_cpu.get('total', 'N/A')}%")
                print(f"User Space CPU:    {sys_cpu.get('user', 'N/A')}%")
                print(f"System Kernel CPU: {sys_cpu.get('system', 'N/A')}%")
                print("=" * 50)

                # Query process listing
                proc_sample = await sysmon.get_single_process_sample()
                processes = proc_sample.get("processes", [])
                print(f"\n[+] Active Processes ({len(processes)} sampled):")
                print(f"{'PID':<8} {'CPU %':<10} {'Memory (MB)':<14} {'Process Name'}")
                print("-" * 50)

                # Sort by CPU usage descending
                sorted_procs = sorted(
                    processes,
                    key=lambda p: float(p.get("cpuUsage", 0) or 0),
                    reverse=True,
                )

                for proc in sorted_procs[:15]:
                    pid = proc.get("pid", "?")
                    name = proc.get("name", "unknown")
                    cpu = f"{float(proc.get('cpuUsage', 0)):.1f}%"
                    mem_bytes = proc.get("physFootprint", 0) or 0
                    mem_mb = f"{mem_bytes / (1024 * 1024):.2f}"
                    print(f"{pid:<8} {cpu:<10} {mem_mb:<14} {name}")


if __name__ == "__main__":
    asyncio.run(profile_system())
