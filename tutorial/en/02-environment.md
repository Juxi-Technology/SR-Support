---
title: 02 Environment setup (flash tools and firmware)
description: Before starting - get the prebuilt firmware and an official flash tool (Flash Download Tool / esptool), optionally PlatformIO and the computer-side tools, confirm the serial port.
---

# 02 Environment setup (flash tools and firmware)

> Do this page before starting. Flashing the prebuilt firmware needs **no PlatformIO and no
> compilation**; the developer environment (2.4) is only for changing or rebuilding the code.

## 2.1 Requirements

- Windows, Linux or macOS (each command below is given for all three where it matters);
- a USB **data** cable (a charge-only cable will not enumerate the board);
- ESP32-S3-DevKitC-1 (8 MB flash).

## 2.2 Get the code and the prebuilt firmware

- Clone the repository (or unzip the supplied archive) and run later commands from the
  **repository root**:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (The repository is private - request access first.)

- The **prebuilt images** live in `firmware/releases/` (also attached to GitHub Releases;
  repository access required):

  | File | Purpose |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | main firmware (flash at 0x0; also used for assembly centering via serial `e`) |
  | `SHA256SUMS` | checksums |

  GitHub Releases: <https://github.com/Juxi-Technology/SR-Support/releases> (repository
  access required; the same files are mirrored on the company drive/Feishu).

## 2.3 Flash tools (all customers - pick one)

A prebuilt image is one bin flashed at 0x0 - **no PlatformIO, no toolchain download**.

**A. Windows GUI: Espressif Flash Download Tool**

1. Open Espressif's official "Other Tools" page and download Flash Download Tools:
   <https://www.espressif.com/en/support/download/other-tools>
2. Run it; select **ESP32-S3**, load
   `firmware/releases/sr_support_b_ptk_factory.bin` at address `0x0`, choose the port and
   click **START**.

> Flash Download Tool is Windows-only; on Linux/macOS use esptool below.

**B. Windows / Linux / macOS: esptool (command line)**

```bash
pip install esptool
```

Slow network in China - use a mirror:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Flash (`COM27` is your port; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

If connecting fails, enter download mode: hold **BOOT**, tap **RST**, release **BOOT**.

## 2.4 PlatformIO (developers only - building from source)

> Skip this unless you change the code. **Note**: PlatformIO (including the VS Code
> PlatformIO extension) downloads the espressif32 platform and the Xtensa toolchain on first
> use (~1 GB from the PlatformIO registry and GitHub). On many networks in China this is slow
> or fails and needs a proxy/VPN; the VS Code extension does not avoid the download.

- Windows: `powershell -ExecutionPolicy Bypass -File tools/install_platformio.ps1`
  (needs Python 3.10+ and the `py` launcher; the script tries 3.12, then falls back to `py -3`);
- Linux/macOS: `pip install platformio`, and replace `.venv-pio/Scripts/pio.exe` below with `pio`;
- Verify: `pio --version`.

## 2.5 Computer-side tool environment (optional: zeroing / twin / logs)

Not needed for flashing. Install it when you use the arrow-key zero tool, the MuJoCo twin or
the log tools:

```bash
powershell -ExecutionPolicy Bypass -File tools/install_tools_env.ps1
```

Creates `.venv` with pyserial/numpy/mujoco/gymnasium (a few hundred MB). On Linux/macOS:

```bash
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
```

Replace `.venv/Scripts/python.exe` in later commands with `.venv/bin/python` on Linux/macOS,
or with plain `python` if you skip the venv.

## 2.6 Connect the board and confirm the serial port

1. Connect over USB-C; on Windows read the COM number in Device Manager, on Linux it is
   usually `/dev/ttyACM0` (add your user to the `dialout` group), on macOS usually
   `/dev/tty.usbmodem*`;
2. Remember the port - every `COM27` in later pages is this value;
3. A serial monitor or `hw_monitor.py` holds the port; close it before flashing.

## 2.7 Checklist

- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` exists and verifies
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` works, or Flash Download Tool opens;
- [ ] the board's serial port is visible;
- [ ] (developers) `pio --version` works;
- [ ] (optional) the `.venv` tool imports succeed.

Only continue once the items you need pass.
