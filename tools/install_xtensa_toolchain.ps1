# Install the ESP32-S3 Xtensa toolchain used by espressif32@8.0.0.
#
# Preferred: reuse the ESP-IDF 14.2.0 toolchain already on this machine
# (C:\Espressif\tools\xtensa-esp-elf\esp-14.2.0_20241119\xtensa-esp-elf).
# Fallback: download the official PlatformIO package with resume + SHA256.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\install_xtensa_toolchain.ps1
#
# Safe to re-run: an existing complete package is skipped.

$ErrorActionPreference = "Stop"

$Version = "14.2.0+20260121"
$Url = "https://dl.registry.platformio.org/download/platformio/tool/toolchain-xtensa-esp-elf/$Version/toolchain-xtensa-esp-elf-windows_amd64-$Version.tar.gz"
$Sha256 = "41db60c7308fe0bd15f2b843069735586509dba4e206b1b632ddc07ff4059c56"

$PioHome = Join-Path $env:USERPROFILE ".platformio"
$Pkg = Join-Path $PioHome "packages\toolchain-xtensa-esp-elf"
$CacheDir = Join-Path $PioHome ".cache\downloads"
$Cache = Join-Path $CacheDir "toolchain-xtensa-esp-elf-$Version.tar.gz"
$Gcc = Join-Path $Pkg "bin\xtensa-esp32s3-elf-gcc.exe"

New-Item -ItemType Directory -Force $CacheDir | Out-Null
New-Item -ItemType Directory -Force $Pkg | Out-Null

function Write-Meta {
    $piopm = '{"type": "tool", "name": "toolchain-xtensa-esp-elf", "version": "' + $Version + '", "spec": {"owner": "platformio", "id": 17066, "name": "toolchain-xtensa-esp-elf", "requirements": null, "uri": null}}'
    Set-Content -Encoding ascii -Path (Join-Path $Pkg ".piopm") -Value $piopm

    $pkgJson = @'
{
  "name": "toolchain-xtensa-esp-elf",
  "version": "14.2.0+20260121",
  "description": "GCC Toolchain for Espressif ESP32 Xtensa MCUs",
  "keywords": ["build tools", "compiler", "assembler", "linker", "preprocessor", "espressif", "esp32", "esp32s2", "esp32s3"],
  "license": "GPL-2.0-or-later",
  "repository": {"type": "git", "url": "https://github.com/espressif/crosstool-NG"},
  "system": ["windows_amd64", "windows_arm64"]
}
'@
    Set-Content -Encoding ascii -Path (Join-Path $Pkg "package.json") -Value $pkgJson
}

if (Test-Path $Gcc) {
    Write-Host "Already installed: $Gcc"
    exit 0
}

# ------------------------------------------------------------------
# 1) Reuse ESP-IDF 14.2.0 toolchain if present (no 401 MB download).
# ------------------------------------------------------------------
$IdfCandidates = @(
    "C:\Espressif\tools\xtensa-esp-elf\esp-14.2.0_20241119\xtensa-esp-elf",
    (Join-Path $env:USERPROFILE "esp\tools\xtensa-esp-elf\esp-14.2.0_20241119\xtensa-esp-elf")
)
foreach ($Idf in $IdfCandidates) {
    $IdfGcc = Join-Path $Idf "bin\xtensa-esp32s3-elf-gcc.exe"
    if (Test-Path $IdfGcc) {
        Write-Host "Reusing ESP-IDF toolchain:"
        Write-Host "  $Idf"
        robocopy $Idf $Pkg /E /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -gt 7) { throw "robocopy failed with exit code $LASTEXITCODE" }
        Write-Meta
        if (-not (Test-Path $Gcc)) { throw "Copy finished but $Gcc is missing." }
        Write-Host "Installed: $Gcc"
        Write-Host "Next: pio run -d firmware/sr_support_b_ptk"
        exit 0
    }
}

# ------------------------------------------------------------------
# 2) Fallback: download the official PlatformIO package.
# ------------------------------------------------------------------
Write-Host "No local ESP-IDF 14.2.0 toolchain found; downloading/resuming:"
Write-Host "  $Url"
curl.exe -L -C - --retry 3 --retry-delay 2 -o $Cache $Url
if ($LASTEXITCODE -ne 0) { throw "curl failed with exit code $LASTEXITCODE" }

Write-Host "Verifying SHA256 ..."
$Actual = (Get-FileHash $Cache -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Actual -ne $Sha256) {
    throw "SHA256 mismatch: expected $Sha256, got $Actual. Delete $Cache and retry."
}

Write-Host "Extracting to $Pkg ..."
tar -xzf $Cache -C $Pkg
if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }

Write-Meta

if (-not (Test-Path $Gcc)) {
    throw "Extraction finished but $Gcc is missing."
}

Write-Host ""
Write-Host "Installed: $Gcc"
Write-Host "Next: pio run -d firmware/sr_support_b_ptk"
