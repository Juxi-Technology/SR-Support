---
title: 03 메인 펌웨어 플래싱
description: 사전 빌드 bin(Flash Download Tool / esptool) 또는 PlatformIO 빌드로 SR-Support B-line 펌웨어를 플래싱하기; 시리얼 명령과 부팅 로그.
---

# 03 메인 펌웨어 플래싱

> **완성품 사용자는 이 페이지를 건너뛰어도 됩니다**: 공장에서 펌웨어를 플래싱하고
> 검증했습니다. 펌웨어 업그레이드나 코드 수정 후에만 다시 하세요. 고객은 사전 빌드
> 이미지를 사용하고(3.1, PlatformIO 불필요), 개발자는 소스에서 빌드합니다(3.2).

## 3.1 사전 빌드 이미지 플래싱 (고객 권장)

1. `firmware/releases/sr_support_b_ptk_factory.bin`이 있는지 확인하세요(체크섬은 같은 위치의
   `SHA256SUMS`에 있음);
2. 다운로드 모드로 진입하세요: **BOOT**을 누른 채 **RST**를 짧게 누르고 **BOOT**을 놓으세요;
3. 플래싱하세요(도구 설정은 [02 페이지 2.4절](./02-environment.md); 명령은 `.venv`를
   활성화한 상태에서 `SR-Support` 폴더에서 실행):
   - Windows GUI: Flash Download Tool → ESP32-S3 → bin을 `0x0`에 로드 → START;
   - Windows / Linux / macOS 명령줄:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. 완료되면 RST를 누르고 3.3절처럼 로그를 확인하세요.

> 플래싱/시리얼 디버깅 시에는 ESP32를 USB로 전원을 공급하고 5 V 전원은 서보에만
> 연결해도 됩니다(두 가지 전원 옵션은 [04 페이지 4.4절](./04-assembly.md) 참조).

> 이 명령은 **Windows / Linux / macOS에서 동일**합니다; 포트만 바뀝니다:
> Windows는 `COM27`, Linux는 `/dev/ttyACM0`, macOS는 `/dev/tty.usbmodem*`.
> Flash Download Tool은 Windows 전용이므로 다른 OS에서는 esptool 명령줄을 사용하세요.

> 조립 센터링에는 별도의 이미지가 필요 없습니다: 이 이미지를 플래싱한 뒤 전원을 켜면
> 두 서보가 펌웨어 영점(1681 / 1456 µs)으로 구동됩니다 - 그런 다음 전원을 끄고 서보 혼을
> 장착하세요([04 페이지 4.2절](./04-assembly.md)). 선택적으로 `e`를 보내 먼저 1520 µs
> 전기적 중심에 두어도 됩니다(동등함).

## 3.2 소스에서 빌드 및 플래싱 (개발자)

환경: [02 페이지 2.5절](./02-environment.md). 프로젝트:
`firmware/sr_support_b_ptk/`(환경 `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> `.venv`를 활성화한 상태에서 `SR-Support` 폴더에서 실행하세요(02 페이지 2.3절); 세
> 플랫폼 모두 동일합니다 - `--upload-port`의 `COM27`을 본인 포트로 바꾸세요. 플래싱 전에
> 시리얼 포트를 점유한 것(시리얼 모니터, `tools/hw_monitor.py`)을 닫으세요. 그렇지 않으면
> `could not open port` / `Access is denied`가 발생합니다.

성공적인 빌드는 RAM 약 56%, 플래시 약 30%를 사용합니다(WiFi + 웹 서버 포함; WiFi가 없던
이전 빌드는 약 7% / 12%였습니다).

## 3.3 시리얼 모니터

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(세 플랫폼 모두 동일; `COM27`을 본인 포트로 바꾸세요.)

> **Windows GUI 시리얼 어시스턴트(선택 사항)**: 野人家园의 UartAssist(무료, 단일 exe,
> Windows 전용). 공식 페이지 <https://cmsoft.cn/resource/101.html>, 공식 다운로드
> 링크 <https://cmsoft.cn/resource/download/101>. COM 포트를 선택하고 **115200, 8N1,
> 흐름 제어 없음**으로 설정한 뒤 "send newline"을 켜세요; 수신 창에서 부팅 로그/텔레메트리를
> 보고 송신 상자에 명령을 입력하세요. 반드시 공식 링크에서만 다운로드하세요(제3자 사이트는
> 애드웨어를 묶어 배포하는 경우가 많음); exe를 이 저장소에 커밋하지 마세요.

**Linux / macOS 시리얼 뷰어(하나 선택)**:

- 권장: 위의 `pio device monitor` 명령(프로젝트와 함께 설치되며 크로스 플랫폼);
- 경량 CLI: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (macOS에서는 `/dev/tty.usbmodem*`; `Ctrl-]`로 종료); 내장
  `screen /dev/ttyACM0 115200`도 동작합니다(`Ctrl-A` 후 `K`로 종료);
- GUI: **CoolTerm**(무료, Windows/macOS/Linux, 공식 사이트
  <https://freeware.the-meiers.org>); Linux에서는 `sudo apt install cutecom`도 가능합니다.

> Linux에서는 사용자를 `dialout` 그룹에 추가하세요: `sudo usermod -aG dialout $USER`,
> 그런 다음 로그아웃했다가 다시 로그인하세요.

포트를 연 뒤 보드에 방금 전원이 들어왔거나 RST를 눌렀다면 부팅 로그가 먼저 보입니다;
그렇지 않으면 RST를 한 번 누르세요. 리셋 후에는 다음이 보여야 합니다:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 시리얼 명령 (115200)

모든 명령은 시리얼 모니터/어시스턴트의 **송신 상자**에 입력하고 Enter를 누르세요
(UartAssist에서는 "send newline"을 켜세요); `m` 명령은 공백과 값 두 개가 필요합니다, 예:
`m 0.5 0`.

| 명령 | 기능 |
|---|---|
| `g` | 실행 시작/계속(이 빌드는 자동 실행되므로 보통 불필요) |
| `s` | 실행기 정지, 마지막 목표 유지 |
| `x` | 비상 해제: PWM 해제; `r`로 재무장 |
| `r` | PWM 재초기화 및 센터 |
| `t` | 서보 자체 테스트(작은 움직임) |
| `c` | 자이로 + **가속도 영점 오프셋** 캘리브레이션(로봇이 수평으로 서 있고 정지 상태여야 함; NVS에 저장) |
| `m <q1> <q2>` | 수동 관절 목표(rad) |
| `1/2` | 수동 숄더 ±0.5 rad |
| `3/4` | 수동 엘보 ±0.5 rad |
| `0` | 수동 중립 |
| `l` | 3초 50 Hz 고속 로그 |
| `k` | 두 서보의 센터 펄스 폭 출력 |
| `o` / `p` | 숄더 센터 ±10 µs 트림 |
| `z` | 엔코더식 영점: 현재 자세가 두 관절 모두 q=0이 됨; 새 펄스 폭 출력(RAM에만 적용; [05 페이지](./05-zero-tool.md) 참조) |
| `e` | 전기적 중심(선택 사항): 서보 혼을 전기적 중심에 장착하기 위해 두 서보를 1520 µs로 이동; 일반적인 방법은 펌웨어 영점으로 전원을 켜고 그 위치에 장착하는 것([04 페이지 4.2절](./04-assembly.md) 참조) |
| `d` | 50 Hz 트윈 스트림 토글(MuJoCo 트윈; 상태 페이지의 스위치와 동일) |
| `w` | WiFi 토글(핫스팟 + 상태 페이지/프로비저닝, [08 페이지](./08-wifi.md) 참조) |
| `v` / `b` | 숄더 / 엘보 부호 반전 |
| `i` / `j` | IMU X / Y 부호 반전 |
| `h` | 기립 홈잉 토글(레거시 정책 경로) |
| `a` | 레거시 스크립트 기립 테스트 모드 |

## 3.5 전원 투입 동작

펌웨어는 `AUTORUN_ON_BOOT`를 정의합니다: 전원이 들어오면 실행기는 로봇이 **완전히 눕고
정지**한 상태가 0.5초 지속되기를 기다린 뒤 자동으로 시작합니다 - `g`가 필요 없습니다.
로봇을 세운 상태로 전원을 켜세요.

---

[← 튜토리얼 목차로 돌아가기](./index.md)
