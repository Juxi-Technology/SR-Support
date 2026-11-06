# Install the computer-side tool dependencies into the project .venv (Windows).
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\install_tools_env.ps1
#
# This creates .venv if needed and installs tools/requirements.txt
# (pyserial, numpy, mujoco, gymnasium). It does not touch the system Python
# and does not install PlatformIO - install_platformio.ps1 adds that to the
# same .venv.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"

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

Write-Host "Installing tool dependencies ..."
& $Python -m pip install -r (Join-Path $Root "tools\requirements.txt")

Write-Host ""
Write-Host "Done. Activate the venv, then run tools with plain python:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python tools\live_twin.py --tcp <Robot IP>:3333"
