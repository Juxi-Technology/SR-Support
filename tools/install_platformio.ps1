# Install PlatformIO Core into the project .venv (Windows).
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\install_platformio.ps1
#
# This creates .venv if needed (the same venv used by the computer-side
# tools), installs PlatformIO there and prints the version. It does not
# modify the system Python.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$Pio = Join-Path $Venv "Scripts\pio.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Creating venv at $Venv ..."
    py -3.12 -m venv $Venv
    if (-not (Test-Path $Python)) {
        Write-Host "Python 3.12 not found; falling back to py -3 ..."
        py -3 -m venv $Venv
    }
}
if (-not (Test-Path $Python)) {
    Write-Error "Could not create the venv. Install Python 3.10+ from python.org (keep the 'py' launcher) and retry."
}

Write-Host "Upgrading pip ..."
& $Python -m pip install --upgrade pip

Write-Host "Installing PlatformIO ..."
& $Python -m pip install platformio

Write-Host ""
Write-Host "PlatformIO version:"
& $Pio --version

Write-Host ""
Write-Host "Next (activate the venv first: .\.venv\Scripts\Activate.ps1):"
Write-Host "  pio device list"
Write-Host "  pio run -d firmware/sr_support_b_ptk"
Write-Host "  pio run -d firmware/sr_support_b_ptk -t upload --upload-port COMx"
Write-Host "  pio device monitor -b 115200 -p COMx"
