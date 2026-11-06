---
title: 02 Environment setup (venv, flash tools and firmware)
description: Before starting - create and activate the project .venv, get the prebuilt firmware and an official flash tool (Flash Download Tool / esptool), optional PlatformIO, the computer-side tools and MuJoCo, and the serial port.
---

# 02 Environment setup (venv, flash tools and firmware)

> Do this page before starting. **Commands assume the repository root** - the **`SR-Support`
> folder** you downloaded from GitHub (a zip extract may be named `SR-Support-main`; it is the
> folder that contains `firmware/` and `tools/`). **Every Python command runs in the terminal
> with `.venv` activated** (2.3). Flashing the prebuilt firmware needs no PlatformIO and no
> compilation; the developer environment (2.5) is only for changing the code.

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

- The **prebuilt image** lives in `firmware/releases/`:

  | File | Purpose |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | main firmware (flash at 0x0; also used for assembly centering via serial `e`) |
  | `SHA256SUMS` | checksums |

## 2.3 Create and activate the virtual environment (.venv)

All computer-side Python tools (esptool, PlatformIO, the MuJoCo tools) go into the **same**
project-local `.venv`, and that `.venv` must be created inside the **`SR-Support` folder**
downloaded from GitHub (a zip extract may be named `SR-Support-main`; again, the folder that
contains `firmware/` and `tools/`).

Enter that folder first - the commands below run there:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Not sure you are in the right place? Run `dir`; it must list `firmware`, `tools`, `tutorial`;
- Without Python 3.12, use `py -3 -m venv .venv` (3.10+ works);
- If PowerShell refuses to run scripts, run
  `Set-ExecutionPolicy -Scope Process Bypass` in this window and activate again.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- Not sure you are in the right place? Run `ls`; it must list `firmware`, `tools`, `tutorial`.

After activation the prompt shows **`(.venv)`**. Every command below and on the later
tutorial pages runs in this **activated terminal**; re-activate after opening a new window.
Without activation `pip` / `python` point at the system installation and installs or runs
will fail.

> **Directory requirement (important)**: `.venv` must live in the **`SR-Support` folder (the
> repository root)**, never in a subfolder. The create/activate commands above use **relative
> paths**, so they must be run from that folder - after opening a new terminal, `cd
> D:\Project\SR-Support` (your path) before activating, or use an absolute path such as
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Once activated you can `cd` into any subfolder and `python` / `pip` / `pio` still point at
> that `.venv`; but the tutorial's `tools/...`, `firmware/...` and `hardware/v1/...` paths are
> relative, so **run them from the `SR-Support` folder**. The venv is bound to the path where
> it was created: after moving or renaming the repository, delete `.venv` and recreate it.

## 2.4 Flash tools (all customers - pick one)

A prebuilt image is one bin flashed at 0x0 - **no PlatformIO, no toolchain download**.
Make sure the terminal is in the `SR-Support` folder and the prompt shows `(.venv)`.

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

## 2.5 PlatformIO (developers only - building from source)

> Skip this unless you change the code. **Note**: PlatformIO (including the VS Code
> PlatformIO extension) downloads the espressif32 platform and the Xtensa toolchain on first
> use (~1 GB from the PlatformIO registry and GitHub). On many networks in China this is slow
> or fails and needs a proxy/VPN; the VS Code extension does not avoid the download.

With the terminal in the `SR-Support` folder and `(.venv)` active:

```bash
pip install platformio
```

On Windows you can also run `tools/install_platformio.ps1`, which installs into this same
`.venv`. Verify:

```bash
pio --version
```

## 2.6 Computer-side tools and MuJoCo environment (twin / zeroing / logs)

Not needed for flashing. Install it when you use the arrow-key zero tool, the MuJoCo live twin
(`tools/live_twin.py`), the simulation replay or the log tools. With the terminal in the
`SR-Support` folder and `.venv` active, install the dependencies (pyserial, numpy, MuJoCo 3.1+,
gymnasium):

```bash
pip install -r tools/requirements.txt
```

On Windows you can also run `tools/install_tools_env.ps1` (creates/reuses `.venv` and installs
the same set). On a slow network in China append the Tsinghua mirror
`-i https://pypi.tuna.tsinghua.edu.cn/simple`; the first install downloads a few hundred MB.

**Check: run the environment self-test (it loads and steps MuJoCo, not just imports)**

```bash
python tools/env_check.py
```

The last line must be `env check: PASS`, with output like:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

With no board plugged in, `[--] no serial port found` is informational and does not affect PASS.

> On Linux, a GLFW/OpenGL error when the MuJoCo window opens means missing system libraries:
> install `libgl1` and `libglew-dev` (e.g. `sudo apt install libgl1 libglew-dev`). The
> Windows/macOS MuJoCo wheels bundle what they need. The `training/b_line` simulation and
> replay use the same environment - nothing extra to install.

## 2.7 Connect the board and confirm the serial port

1. Connect over USB-C; on Windows read the COM number in Device Manager, on Linux it is
   usually `/dev/ttyACM0` (add your user to the `dialout` group), on macOS usually
   `/dev/tty.usbmodem*`;
2. Remember the port - every `COM27` in later pages is this value;
3. A serial monitor or `hw_monitor.py` holds the port; close it before flashing.

## 2.8 Checklist

- [ ] the terminal is in the **repository root** and the prompt shows `(.venv)` (check with
      `pwd` / `Get-Location`);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` exists and verifies
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` works, or Flash Download Tool opens;
- [ ] the board's serial port is visible;
- [ ] (developers) `pio --version` works;
- [ ] `python tools/env_check.py` prints `env check: PASS`.

Only continue once the items you need pass.
