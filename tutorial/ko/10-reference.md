---
title: 10 레퍼런스: 모델, 파라미터 및 라이선스
description: 레퍼런스 모델 파일(MuJoCo XML / STL), 펌웨어 파라미터, 네 가지 레퍼런스 시퀀스, 검증 상태 및 라이선스.
---

# 10 레퍼런스: 모델, 파라미터 및 라이선스

## 10.1 레퍼런스 모델 파일

시뮬레이션은 하드웨어 자체의 설계를 공유하는 MuJoCo MJCF(`.xml` + `.stl` 메시)를
사용합니다:

| 파일 | 설명 |
|---|---|
| `hardware/v1/robot_v1.xml` | 메인 모델(형상/질량이 하드웨어와 일치) |
| `hardware/v1/meshes/*.stl` | 4개의 출력 그룹(베이스 플레이트/셸, 숄더 마운트, 상부 암 브래킷/엘보 마운트, 전완)으로 조립되는 6개의 STL 메시 |
| `hardware/v1/meshes/print_mass_model.json` | 부품별 출력 질량 표(15% 인필) |

URDF는 포함되어 있지 않습니다; ROS에서 사용하려면 위의 CAD/메시에서 내보내세요.

## 10.2 펌웨어 파라미터 (`firmware/sr_support_b_ptk/include/config.h`)

| 파라미터 | 값 | 의미 |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | 50 Hz 제어 주기 |
| `MAX_CMD_RATE` | 0.08 rad/tick | 출력 슬루 제한(4 rad/s) |
| `FALL_UP_Z` | 0.30 | 폴 게이트 up_z 임계값 |
| `FALL_W_QUIET` | 0.9 rad/s | 폴 게이트 각속도 임계값 |
| `FALL_CONFIRM_TICKS` | 25 | 폴 게이트 확인(0.5초) |
| `EXEC_STEPS_PER_WP` | 20 | 레퍼런스 웨이포인트당 틱 수 |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | 수축 속도 |
| `EXEC_DONE_TICKS` | 50 | 완료 판정을 위한 연속 기립 틱 수 |
| `EXEC_TIMEOUT_MS` | 14000 | 레퍼런스별 타임아웃 |
| `EXEC_COOLDOWN_TICKS` | 75 | 완료/타임아웃 후 쿨다운(1.5초) |
| `EXEC_SWITCH_TICKS` | 15 | 자세 전환 확인 틱 수 |
| `EXEC_SWITCH_UP` | 0.60 | 전환을 위한 최대 up_z |
| `EXEC_SWITCH_W` | 0.8 rad/s | 전환을 위한 최대 각속도 |
| `EXEC_MIN_SWITCH_AGE` | 25 | 전환이 가능한 가장 이른 틱 |
| `EXEC_MAX_SWITCHES` | 5 | 실행당 최대 전환 횟수 |
| `EXEC_NEUTRAL_MAX` | 120 | 중립 수축 최대 틱 수 |
| `SERVO_SHOULDER_CENTER_US` | 1681 | 숄더 영점 펄스(2026-11에 구운 눈으로 확인한 중심 값; [05 페이지](./05-zero-tool.md)에 따라 재영점 조정) |
| `SERVO_CENTER_US` | 1456 | 엘보 영점 펄스(동일) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | 숄더 수동 명령 제한 |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | 수동 범위(실행기는 기계적 ±1.55 사용) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | 서보 방향 |
| `IMU_YAW90` | 1 | IMU 90° 회전 장착 |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | 자세 필터: 가속도 보정 이득 / 신뢰 대역 |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | 핫스팟(`w`로 토글; 부팅 시 켜짐) |

## 10.3 레퍼런스 시퀀스 (숄더, 엘보; rad; `training/b_line/getup_reference_b39.py`와 값 단위로 동일)

| 자세 | 시퀀스 |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` 전체 속도 직접 누름(홀드 ≤40틱) → 웨지 펌프 `[-1.80,0.35] → [-1.80,0.05]` ×2(각 홀드 ≤30) → 폴백: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]`(휩-슬램, 홀드 ≤40) → 최종 홀드 ≤90 → 수축 |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 10.4 검증 상태와 공장 검사 (2026-11-06)

- **공장 검사**: 각 완성품은 출하 전에 - 제품별 서보 영점 정의 및 굽기
  ([05 페이지](./05-zero-tool.md)), 자이로 + 가속도 영점 캘리브레이션(NVS), 네 방향 기립
  테스트를 거칩니다;
- 네 방향 모두 실제 로봇에서 검증되었으며, 각각 **직접 기립**(굴러 넘어감 없음)으로
  약 1–6초; 서보 엔벨로프 위반 없음;
- `roll_neg` 최종 레시피: 전체 가동 범위 직접 누름 + 엘보 웨지 펌프 ×2, 폴백으로 휩-슬램
  재시도(이전의 굴러 넘기기 + 재계획 방식은 폐기됨);
- 자세 파이프라인은 가속도 바이어스 캘리브레이션으로 수정되었습니다([06 페이지 6.2절](./06-debug-and-calibrate.md) 참조);
  이제 눕힌 자세가 실제 로봇과 일치합니다;
- `roll_neg`는 1× 질량 시뮬레이션 모델에서는 여전히 재현되지 않습니다(암 질량/마찰이
  다름); 이는 알려진 모델 격차입니다 - 하드웨어 펌웨어는 하드웨어에서 검증됩니다.

## 10.5 라이선스

- B-line 펌웨어/학습 코드: MIT / Apache-2.0;
- B-line CAD/STL: CERN-OHL-S-2.0(강한 상호성 — 상용 사용 전에 의무 사항 확인);
- SelfRisingRobot: 라이선스 없음; 이 튜토리얼에는 해당 코드, 웨이포인트, 모델이 포함되어
  있지 않습니다;
- 특허 CN109693729A/B: 상용 사용 전에 FTO 검토를 수행하세요.

---

[← 튜토리얼 목차로 돌아가기](./index.md)
