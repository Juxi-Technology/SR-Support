# Install the computer-side tool dependencies into a project-local venv (Windows).
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\install_tools_env.ps1
#
# This creates .venv next to the repository root and installs tools/requirements.txt
# (pyserial, numpy, mujoco, gymnasium). It does not touch the system Python and does
# not install PlatformIO - see install_platformio.ps1 for that (separate .venv-pio).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Creating venv at $Venv ..."
    py -3.12 -m venv $Venv
}

Write-Host "Upgrading pip ..."
& $Python -m pip install --upgrade pip

Write-Host "Installing tool dependencies ..."
& $Python -m pip install -r (Join-Path $Root "tools\requirements.txt")

Write-Host ""
Write-Host "Done. Run tools with:"
Write-Host "  $Python tools\live_twin.py --tcp <Robot IP>:3333"
