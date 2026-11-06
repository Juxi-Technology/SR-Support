---
title: 02 Environment setup (software and tools)
description: Prepare everything before starting - get the code, install PlatformIO and the computer-side Python tools, confirm the USB serial port.
---

# 02 Environment setup (software and tools)

> Do this page **first**, before printing or assembly. Everything after this page uses the
> commands installed here; no later page repeats the installation steps.

## 2.1 Requirements

- Windows 10/11 (the commands use PowerShell and Windows paths; on macOS/Linux substitute the
  equivalent shell and paths);
- Python 3.10+ with the `py` launcher (3.12 recommended; `py -3.12 --version` or
  `py -3 --version` must print a version);
- a USB **data** cable (a charge-only cable will not enumerate the board).

## 2.2 Get the code

Clone the repository (or unzip the supplied archive) and run every later command from the
**repository root**:

```bash
git clone https://github.com/Juxi-Technology/SR-Support.git
cd SR-Support
```

(The repository is private - request access first, or simply unzip the archive you received.)

Layout: `firmware/` (the code flashed to the ESP32), `tools/` (computer-side tools),
`hardware/v1/` (model and printable parts), `tutorial/` (this tutorial).

## 2.3 Install PlatformIO (build and flashing)

```bash
powershell -ExecutionPolicy Bypass -File tools/install_platformio.ps1
```

The script creates `.venv-pio` inside the repository and installs PlatformIO there; it does not
touch the system Python. Verify:

```bash
.venv-pio/Scripts/pio.exe --version
```

> Do not want the project-local environment? Use the VS Code PlatformIO extension or a global
> `pip install platformio`, and replace `.venv-pio\Scripts\pio.exe` in later commands with the
> matching command.

## 2.4 Install the computer-side tool environment (monitor / zeroing / twin)

```bash
powershell -ExecutionPolicy Bypass -File tools/install_tools_env.ps1
```

Creates `.venv` and installs pyserial/numpy/mujoco/gymnasium (the first run downloads a few
hundred MB and takes a few minutes). Verify:

```bash
.venv/Scripts/python.exe -c "import serial, numpy, mujoco, gymnasium; print('tools env ok')"
```

> A virtual environment is not mandatory: in any Python 3.10+ run
> `pip install -r tools/requirements.txt` and replace `.venv\Scripts\python.exe` in later
> commands with `python`.

## 2.5 Connect the board and confirm the serial port

1. Connect the ESP32-S3 over USB-C (the on-board USB serial is usually driver-free; if Windows
   shows an unknown serial device, install the CP210x or CH340 driver that matches your board);
2. List the ports:

```bash
.venv-pio/Scripts/pio.exe device list
```

A line like `COM27` must appear. Remember it - every `COM27` in the following pages is this
port. A serial monitor or `hw_monitor.py` holds the port; close it before flashing.

## 2.6 Checklist

- [ ] `.venv-pio/Scripts/pio.exe --version` prints a PlatformIO version;
- [ ] `.venv/Scripts/python.exe -c "import serial, numpy, mujoco, gymnasium"` runs without error;
- [ ] `pio device list` shows the board port (e.g. `COM27`);
- [ ] you know where the repository root is (all commands run from there).

Only continue once every item passes.
