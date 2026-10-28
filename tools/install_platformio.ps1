# Install PlatformIO Core into a project-local venv (Windows).
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\install_platformio.ps1
#
# This creates .venv-pio next to the repository root, installs PlatformIO,
# and prints the version. It does not modify the system Python.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root ".venv-pio"
$Python = Join-Path $Venv "Scripts\python.exe"
$Pio = Join-Path $Venv "Scripts\pio.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Creating venv at $Venv ..."
    py -3.12 -m venv $Venv
}

Write-Host "Upgrading pip ..."
& $Python -m pip install --upgrade pip

Write-Host "Installing PlatformIO ..."
& $Python -m pip install platformio

Write-Host ""
Write-Host "PlatformIO version:"
& $Pio --version

Write-Host ""
Write-Host "Next:"
Write-Host "  $Pio device list"
Write-Host "  $Pio run -d firmware/sr_support_b_ptk"
Write-Host "  $Pio run -d firmware/sr_support_b_ptk -t upload --upload-port COMx"
Write-Host "  $Pio device monitor -b 115200 -p COMx"
