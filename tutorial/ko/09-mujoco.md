---
title: 09 MuJoCo 시뮬레이션과 라이브 트윈
description: 로컬 MuJoCo 시뮬레이션 창(네 자세 기립 리플레이), 실제 로봇의 WiFi 라이브 트윈 및 텔레메트리 로깅.
---

# 09 MuJoCo 시뮬레이션과 라이브 트윈

이 프로젝트에서 MuJoCo는 두 가지 방식으로 사용되며, 둘 다 `hardware/v1/robot_v1.xml`
(실제 로봇과 동일한 소스에서 나온 모델)을 사용합니다:

- **로컬 시뮬레이션**: 로봇을 연결하지 않은 상태에서 컴퓨터에서 네 가지 눕힌 자세와
  각각의 기립 동작을 반복 실행하여 레퍼런스 시퀀스를 검증하고 움직임을 관찰합니다;
- **라이브 트윈**: 실제 로봇이 WiFi로 자세를 스트리밍하고 MuJoCo 창이 실제 움직임을
  실시간으로 반영합니다(디지털 트윈).

창은 두 경우 모두 동일하게 동작합니다: 왼쪽 드래그로 시점을 회전하고, 오른쪽 드래그로
이동하며, 휠로 확대/축소합니다. 처음 사용하기 전에 [02 페이지](./02-environment.md)와
같이 `.venv`를 만들고 활성화한 뒤, 그 안에 도구 의존성을 설치하세요
(`pip install -r tools/requirements.txt`, 02 페이지 참조).

## 9.1 로컬 시뮬레이션 창

`SR-Support` 폴더에서 (`.venv` 활성화 상태):

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

창 제목은 `MuJoCo : sr_support_v1`입니다(그림 9-1). 로봇은 네 가지 눕힌 자세
(`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`)에 차례로 배치됩니다; 매번 실행기가
펌웨어와 정확히 동일한 파라미터로 레퍼런스 시퀀스를 실행하여 로봇이 일어설 때까지
진행한 뒤 다음 자세가 설정됩니다. 창을 닫을 때까지 루프가 반복됩니다. 터미널에는
자세와 결과가 출력됩니다:

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True`는 해당 자세가 시뮬레이션에서 일어섰다는 뜻입니다. `ok=False`이면 레퍼런스
시퀀스와 변경한 파라미터를 [06 페이지](./06-debug-and-calibrate.md)와 대조하여
확인하세요.

![그림 9-1 MuJoCo 시뮬레이션 창(네 자세 기립 리플레이)](../images/sr-support/mujoco/01-mujoco-window.png)

*그림 9-1: 네 자세 루프의 한 장면 — 실행기가 눕힌 자세에서 기립하는 중입니다.*

> 알려진 모델 차이: 1x 질량 모델에서는 `roll_neg`가 시뮬레이션에서 `ok=False`를
> 출력합니다(모델의 암 질량/마찰이 실제 로봇과 다르기 때문, [11 페이지](./11-reference.md)
> 11.4 참조); 실제 펌웨어에는 영향을 주지 않습니다.

## 9.2 WiFi 라이브 트윈

사전 조건: 로봇이 [08 페이지](./08-wifi.md)와 같이 가정용 네트워크에 접속되어 있고,
컴퓨터도 같은 네트워크에 있어야 합니다. 상태 페이지에 로봇의 주소가 `Robot IP`로 표시되면
그 주소를 아래 명령에 복사합니다.

1. 상태 페이지에서 `Twin ON`을 누르세요(시리얼 `d`와 동일);
2. `.venv`를 활성화한 상태에서 `SR-Support` 폴더에서 실행하세요(주소는 상태 페이지의
   `Robot IP`로 바꿉니다):

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

모델은 실제 자세를 실시간으로 반영하며(50 Hz 쿼터니언 스트림), 몸체는 바닥 위에
유지합니다; 암은 스톨된 서보처럼 바닥 접촉 각도에 고정되므로 바닥을 관통하지 않습니다.

- 컴퓨터를 로봇의 핫스팟에 직접 연결하는 경우: 주소는 항상 `192.168.4.1`,
  `python tools/live_twin.py --tcp 192.168.4.1:3333`;
- 유선 대안: `python tools/live_twin.py --port COM27`(도구가 자동으로 `d`를 보내
  스트림을 활성화합니다);
- 오프라인 재생: `python tools/live_twin.py --replay logs/hw_fast_xxx.txt`;
- 트윈은 스트림 토글 외에는 읽기 전용입니다: 제어 명령을 절대 보내지 않습니다.

## 9.3 텔레메트리 로깅

```bash
python tools/tcp_log.py
```

텔레메트리 스트림을 `logs/wifi_<time>.txt`에 저장하여 오프라인 재생(`--replay`)과
장애 분석에 사용합니다. 핫스팟에서는 기본적으로 `192.168.4.1:3333`에 연결하며, 가정용
네트워크에서는 상태 페이지의 `Robot IP`를 인수로 전달하세요:

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 시뮬레이션 및 학습 레퍼런스

`training/b_line/`에는 실행기, 레퍼런스 시퀀스 및 시뮬레이션 환경이 포함되어 있으며 -
펌웨어와 값 하나하나까지 동일합니다 - 재생, 검증, 파라미터 튜닝에 사용합니다; 모델
파일은 [11 페이지](./11-reference.md) 11.1에 설명되어 있습니다.

---

[← 튜토리얼 목차로 돌아가기](./index.md)
