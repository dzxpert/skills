---
name: ipsw-extract-component
description: Extract specific components, daemons, frameworks, or dyld shared cache from encrypted iOS IPSW restore packages on Windows using ipsw and apfs-fuse. Use when extracting specific files like mobileactivationd, amfid, SpringBoard, system frameworks, or dyld shared cache.
---

# IPSW Component & Binary Extraction (Windows)

This skill provides step-by-step instructions for extracting target system components, binaries, daemons, frameworks, or DYLD shared caches from encrypted iOS IPSW restore images on Windows.

---

## 1. Environment Requirements & Configuration

Before running `ipsw` extraction commands on Windows, ensure the `apfs-fuse` helper path (`ApfsUtil.exe`) is exported into the environment.

```powershell
$env:IPSW_APFS_FUSE_PATH = "C:\Users\xWantedStore\Documents\GitHub\apfs-fuse\x64\Release\ApfsUtil.exe"
```

### Path References
- **APFS Util Path**: `C:\Users\xWantedStore\Documents\GitHub\apfs-fuse\x64\Release\ApfsUtil.exe`
- **Default Output Dir**: `D:\iFirmware\extracted_binaries`
- **7-Zip Executable**: `C:\Program Files\7-Zip\7z.exe`

---

## 2. Core Workflows

### Workflow A: Extract a Specific Component / Binary by Name (Recommended)

Use this workflow to locate and extract any target file (e.g. `mobileactivationd`, `amfid`, `SpringBoard`, etc.) directly from an IPSW image.

#### Step 1: Set Variables & Extract AEA Encryption Keys
Modern iOS IPSWs use AEA encryption. Extract the key database (`.pem` files) first:

```powershell
$ipswPath  = "D:\iFirmware\iPhone16,2_26.5.2_23F84_Restore.ipsw"
$outputDir = "D:\iFirmware\extracted_binaries"

# Extract FCS/AEA decryption keys
ipsw extract --fcs-key "$ipswPath" -o "$outputDir"
```
*This produces a key directory inside `$outputDir` (e.g., `D:\iFirmware\extracted_binaries\23F84__iPhone16,2`).*

#### Step 2: Dynamically Locate the Key Database Directory
```powershell
$pemDb = (Get-ChildItem -Path "$outputDir\*__*" -Directory | Select-Object -First 1).FullName
```

#### Step 3: Extract Target Component via Regex Pattern
Ensure `IPSW_APFS_FUSE_PATH` is set and run `ipsw extract --files` with your target pattern (e.g., `mobileactivationd`):

```powershell
$env:IPSW_APFS_FUSE_PATH = "C:\Users\xWantedStore\Documents\GitHub\apfs-fuse\x64\Release\ApfsUtil.exe"
$targetPattern = ".*mobileactivationd.*"  # Replace with target regex pattern

ipsw extract --files --pattern "$targetPattern" "$ipswPath" --pem-db "$pemDb" -o "$outputDir"
```

#### Step 4: Verify Extracted Binary
```powershell
Get-ChildItem -Path "$outputDir" -Recurse -Include "*mobileactivationd*" | Select-Object FullName, Length, LastWriteTime
```

---

### Workflow B: Decrypt AEA DMG & Inspect via 7-Zip

Use this workflow to decrypt an individual AEA encrypted DMG (`.dmg.aea`) and inspect its files manually.

```powershell
# 1. Decrypt AEA image
$pemKey       = "$pemDb\094-55051-109.dmg.aea.pem"
$encryptedDmg = "D:\iFirmware\iPhone16,2_26.5.2_23F84_Restore\094-55051-109.dmg.aea"

ipsw fw aea -p "$pemKey" -o "$outputDir" "$encryptedDmg"

# 2. List contents of decrypted DMG using 7-Zip
$decryptedDmg = "$outputDir\094-55051-109.dmg"
& "C:\Program Files\7-Zip\7z.exe" l "$decryptedDmg" | Select-String -SimpleMatch "mobileactivationd"
```

---

### Workflow C: Extract DYLD Shared Cache

Use this workflow to extract the ARM64e DYLD shared cache from an IPSW:

```powershell
$env:IPSW_APFS_FUSE_PATH = "C:\Users\xWantedStore\Documents\GitHub\apfs-fuse\x64\Release\ApfsUtil.exe"
ipsw extract --dyld --dyld-arch arm64e "$ipswPath" --pem-db "$pemDb" -o "$outputDir"
```

---

## 3. Common Component Patterns Reference

| Target Component | Regex Pattern (`--pattern`) |
|---|---|
| **Mobile Activation Daemon** | `.*mobileactivationd.*` |
| **MobileActivation Framework** | `.*MobileActivation\.framework.*` |
| **SpringBoard Daemon** | `.*SpringBoard.*` |
| **AMFI Daemon** | `.*amfid.*` |
| **Security Framework** | `.*Security\.framework.*` |
| **Kernelcache** | `.*kernelcache.*` |

---

## 4. Verification Checklist for Agents

Upon execution:
1. Run `Get-ChildItem` to verify that the extracted binary exists and has a non-zero byte size (`Length > 0`).
2. Output the extracted file's absolute path, byte size, and last modified date to the user.
