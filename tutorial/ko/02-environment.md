---
title: 02 환경 설정 (venv, 플래시 도구와 펌웨어)
description: 시작하기 전에 - 프로젝트 .venv를 만들고 활성화하기, 사전 빌드 펌웨어와 공식 플래시 도구(Flash Download Tool / esptool) 받기, 선택 사항인 PlatformIO, 컴퓨터 측 도구와 MuJoCo, 시리얼 포트 확인.
---

# 02 환경 설정 (venv, 플래시 도구와 펌웨어)

> 시작하기 전에 이 페이지를 먼저 하세요. **명령은 저장소 루트** - GitHub에서 내려받은
> **`SR-Support` 폴더**(zip 압축을 풀면 `SR-Support-main`일 수 있음; `firmware/`와 `tools/`가
> 들어 있는 폴더)를 기준으로 합니다. **모든 Python 명령은 `.venv`가 활성화된 터미널에서**
> 실행합니다(2.3). 사전 빌드 펌웨어 플래싱에는 PlatformIO도 컴파일도 필요 없습니다;
> 개발자 환경(2.5)은 코드를 수정할 때만 필요합니다.

## 2.1 요구 사항

- Windows, Linux 또는 macOS(아래 각 명령은 해당되는 경우 세 OS 모두에 대해 안내합니다);
- USB **데이터** 케이블(충전 전용 케이블로는 보드가 인식되지 않습니다);
- ESP32-S3-DevKitC-1(8 MB 플래시).

## 2.2 코드와 사전 빌드 펌웨어 받기

- 저장소를 클론(또는 제공된 압축 파일을 해제)하고 이후 명령은 **저장소 루트**에서
  실행하세요:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (저장소는 비공개입니다 - 먼저 접근 권한을 요청하세요.)

- **사전 빌드 이미지**는 `firmware/releases/`에 있습니다:

  | 파일 | 용도 |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | 메인 펌웨어(0x0에 플래싱; 조립 시 센터링에도 사용: 전원을 켜면 펌웨어 영점, `e`는 선택 사항) |
  | `SHA256SUMS` | 체크섬 |

## 2.3 가상 환경(.venv) 만들기와 활성화

모든 컴퓨터 측 Python 도구(esptool, PlatformIO, MuJoCo 도구)는 **동일한** 프로젝트 로컬
`.venv`에 설치하며, 그 `.venv`는 GitHub에서 내려받은 **`SR-Support` 폴더** 안에 만들어야
합니다(zip 압축을 풀면 `SR-Support-main`일 수 있음; 다시 말하지만 `firmware/`와 `tools/`가
들어 있는 폴더입니다).

먼저 그 폴더로 이동하세요 - 아래 명령은 그곳에서 실행됩니다:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- 올바른 위치에 있는지 확실하지 않나요? `dir`을 실행하세요; `firmware`, `tools`, `tutorial`이
  나열되어야 합니다;
- Python 3.12가 없으면 `py -3 -m venv .venv`를 사용하세요(3.10 이상이면 됩니다);
- PowerShell이 스크립트 실행을 거부하면 이 창에서
  `Set-ExecutionPolicy -Scope Process Bypass`를 실행한 뒤 다시 활성화하세요;
- `.\.venv\Scripts\Activate.ps1`은 venv가 만드는 **PowerShell 활성화 스크립트**입니다:
  앞의 `.\`는 "현재 폴더의 스크립트를 실행하라"는 뜻이며 PowerShell에서는 필수입니다
  (`Activate.ps1`만 입력하면 찾지 못합니다). 다른 셸은 각자의 파일을 사용합니다:
  - **cmd.exe**: `.venv\Scripts\activate.bat`
  - **Git Bash**: `source .venv/Scripts/activate`
  - venv에서 나오려면 `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> 셸 구분법: cmd 프롬프트는 `C:\...>`처럼, PowerShell은 `PS C:\...>`처럼 보입니다.
> 이 튜토리얼은 기본으로 PowerShell을 사용합니다; cmd에서는 활성화 명령만
> `activate.bat`으로 바꾸면 나머지는 동일합니다. 관리자 권한은 필요 없습니다.
>
> **활성화 파일은 셸과 일치해야 합니다**: cmd는 `activate.bat`, PowerShell은
> `Activate.ps1`을 사용합니다. cmd에서 `.ps1`을 실행하면 현재 창은 활성화되지 않습니다
> (보통 아무 일도 일어나지 않거나 별도 창이 열립니다). 또한 `.venv`가 먼저 존재해야
> 합니다(`dir`에 `.venv` 폴더가 나열되어야 함); 없다면 먼저 `py -3.12 -m venv .venv`를
> 실행하세요.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- 올바른 위치에 있는지 확실하지 않나요? `ls`를 실행하세요; `firmware`, `tools`, `tutorial`이
  나열되어야 합니다.

활성화 후 프롬프트에 **`(.venv)`**가 표시됩니다. 아래의 모든 명령과 이후 튜토리얼 페이지의
모든 명령은 이 **활성화된 터미널**에서 실행합니다; 새 창을 열면 다시 활성화하세요.
활성화하지 않으면 `pip` / `python`이 시스템 설치를 가리켜 설치나 실행이 실패합니다.

활성화가 되었는지 확인하세요:

- Windows: `where python` - 첫 줄이 `...\SR-Support\.venv\Scripts\python.exe`여야 합니다;
- Linux / macOS: `which python` - `.../SR-Support/.venv/bin/python`이어야 합니다.

> **cmd에서 활성화 후 화면이 지워졌나요?** 기본 `activate.bat`은 콘솔 코드 페이지를
> 일시적으로 전환(`chcp 65001`)하며 일부 터미널은 화면을 다시 그립니다 - **새 터미널이
> 아닙니다**. 새 프롬프트가 `(.venv)`로 시작하고 `where python`이 `.venv` 안을 가리키면
> 활성화에 성공한 것입니다. 화면 재그리기를 피하려면 PowerShell의 `Activate.ps1`을
> 사용하거나(코드 페이지를 건드리지 않음) 활성화 없이 `.venv\Scripts\python.exe`를 직접
> 호출하세요.

> **디렉터리 요구 사항(중요)**: `.venv`는 반드시 **`SR-Support` 폴더(저장소 루트)**에
> 있어야 하며, 하위 폴더에 두면 안 됩니다. 위의 생성/활성화 명령은 **상대 경로**를
> 사용하므로 반드시 그 폴더에서 실행해야 합니다 - 새 터미널을 연 뒤에는 먼저 그 폴더로
> 이동한 후(PowerShell: `cd D:\Project\SR-Support`; cmd: `cd /d D:\Project\SR-Support`,
> 경로는 본인 것 사용) 활성화하거나,
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate` 같은 절대 경로를 사용하세요.
>
> 활성화한 뒤에는 어느 하위 폴더로 `cd`해도 `python` / `pip` / `pio`가 그 `.venv`를
> 가리킵니다; 하지만 튜토리얼의 `tools/...`, `firmware/...`, `hardware/v1/...` 경로는
> 상대 경로이므로 **`SR-Support` 폴더에서 실행하세요**. venv는 생성된 경로에 묶여
> 있습니다: 저장소를 이동하거나 이름을 바꾼 뒤에는 `.venv`를 삭제하고 다시 만드세요.

## 2.4 플래시 도구 (모든 고객 - 하나 선택)

사전 빌드 이미지는 0x0에 플래싱하는 bin 하나입니다 - **PlatformIO도, 툴체인 다운로드도
필요 없습니다**. 터미널이 `SR-Support` 폴더에 있고 프롬프트에 `(.venv)`가 표시되는지
확인하세요.

**A. Windows GUI: Espressif Flash Download Tool**

1. Espressif 공식 "Other Tools" 페이지를 열고 Flash Download Tools를 다운로드하세요:
   <https://www.espressif.com/en/support/download/other-tools>
2. 실행한 뒤 **ESP32-S3**를 선택하고,
   `firmware/releases/sr_support_b_ptk_factory.bin`을 주소 `0x0`에 로드하고, 포트를 선택한
   뒤 **START**를 클릭하세요.

> Flash Download Tool은 Windows 전용입니다; Linux/macOS에서는 아래 esptool을 사용하세요.

**B. Windows / Linux / macOS: esptool (명령줄)**

```bash
pip install esptool
```

중국에서 네트워크가 느리면 미러를 사용하세요:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

플래싱(`COM27`은 본인의 포트; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

연결에 실패하면 다운로드 모드로 진입하세요: **BOOT**을 누른 채 **RST**를 짧게 누르고,
**BOOT**을 놓으세요.

## 2.5 PlatformIO (개발자 전용 - 소스에서 빌드)

> 코드를 수정하지 않는 한 이 절은 건너뛰세요. **참고**: PlatformIO(VS Code
> PlatformIO 확장 포함)는 처음 사용할 때 espressif32 플랫폼과 Xtensa 툴체인을
> 다운로드합니다(PlatformIO 레지스트리와 GitHub에서 약 1 GB). 중국의 많은 네트워크에서는
> 느리거나 실패하며 프록시/VPN이 필요합니다; VS Code 확장도 다운로드를 피하지 못합니다.

터미널이 `SR-Support` 폴더에 있고 `(.venv)`가 활성화된 상태에서:

```bash
pip install platformio
```

Windows에서는 `tools/install_platformio.ps1`을 실행할 수도 있으며, 같은 `.venv`에
설치합니다. 확인:

```bash
pio --version
```

> 이전 튜토리얼 버전에서는 PlatformIO를 별도의 `.venv-pio`에 설치했지만, 이제는 단일
> `.venv`에 들어갑니다. 업그레이드 후 `pio`를 찾지 못하면 활성화된 `.venv`에서
> `pip install platformio`를 실행하세요(또는 `tools/install_platformio.ps1`을 다시 실행);
> 예전 `.venv-pio`는 삭제해도 됩니다.

## 2.6 컴퓨터 측 도구와 MuJoCo 환경 (트윈 / 영점 조정 / 로그)

플래싱에는 필요 없습니다. 화살표 키 영점 도구, MuJoCo 라이브 트윈(`tools/live_twin.py`),
시뮬레이션 리플레이 또는 로그 도구를 사용할 때 설치하세요. 터미널이 `SR-Support` 폴더에
있고 `.venv`가 활성화된 상태에서 의존성을 설치하세요(pyserial, numpy, MuJoCo 3.1+,
gymnasium):

```bash
pip install -r tools/requirements.txt
```

Windows에서는 `tools/install_tools_env.ps1`을 실행할 수도 있습니다(`.venv`를 생성/재사용하고
같은 패키지 세트를 설치). 중국에서 네트워크가 느리면 칭화대 미러
`-i https://pypi.tuna.tsinghua.edu.cn/simple`를 덧붙이세요; 첫 설치 시 수백 MB를
다운로드합니다.

**점검: 환경 자체 테스트 실행(단순 import가 아니라 MuJoCo를 로드하고 스텝까지 실행)**

```bash
python tools/env_check.py
```

마지막 줄이 `env check: PASS`여야 하며, 출력은 다음과 비슷합니다:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

보드를 연결하지 않은 경우 `[--] no serial port found`는 안내일 뿐이며 PASS에 영향을 주지
않습니다.

> Linux에서 MuJoCo 창이 열릴 때 GLFW/OpenGL 오류가 나면 시스템 라이브러리가 없는
> 것입니다: `libgl1`과 `libglew-dev`를 설치하세요(예: `sudo apt install libgl1 libglew-dev`).
> Windows/macOS용 MuJoCo 휠에는 필요한 것이 포함되어 있습니다. `training/b_line` 시뮬레이션과
> 리플레이도 같은 환경을 사용합니다 - 추가로 설치할 것은 없습니다.

## 2.7 보드 연결 및 시리얼 포트 확인

1. USB-C로 연결하세요; Windows에서는 장치 관리자에서 COM 번호를 확인하고, Linux에서는
   보통 `/dev/ttyACM0`(사용자를 `dialout` 그룹에 추가), macOS에서는 보통
   `/dev/tty.usbmodem*`입니다;
2. 포트를 기억하세요 - 이후 페이지의 모든 `COM27`이 이 값입니다;
3. 시리얼 모니터나 `hw_monitor.py`가 포트를 점유합니다; 플래싱 전에 닫으세요.

## 2.8 체크리스트

- [ ] 터미널이 **저장소 루트**에 있고 프롬프트에 `(.venv)`가 표시됨
      (`pwd` / `Get-Location`으로 확인);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin`이 존재하고 검증됨
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version`이 동작하거나 Flash Download Tool이 열림;
- [ ] 보드의 시리얼 포트가 보임;
- [ ] (개발자) `pio --version`이 동작함;
- [ ] `python tools/env_check.py`가 `env check: PASS`를 출력함.

필요한 항목이 모두 통과된 후에만 계속 진행하세요.

---

[← 튜토리얼 목차로 돌아가기](./index.md)
