---
title: 11 Referência: modelo, parâmetros e licenciamento
description: Arquivos de modelo de referência (XML / STL do MuJoCo), parâmetros do firmware, as quatro sequências de referência, status verificado e licenciamento.
---

# 11 Referência: modelo, parâmetros e licenciamento

## 11.1 Arquivos de modelo de referência

A simulação usa MuJoCo MJCF (`.xml` + malhas `.stl`), compartilhando o próprio design do hardware:

| Arquivo | Descrição |
|---|---|
| `hardware/v1/robot_v1.xml` | Modelo principal (geometria/massa correspondentes ao hardware) |
| `hardware/v1/meshes/*.stl` | 6 malhas STL que se agrupam em 4 grupos impressos (placa/casca da base, suporte do ombro, suporte do braço superior/suporte do cotovelo, antebraço) |
| `hardware/v1/meshes/print_mass_model.json` | Tabela de massa impressa por peça (15% de preenchimento) |

Nenhum URDF é incluído; para uso com ROS, exporte um a partir do CAD/malhas acima.

## 11.2 Parâmetros do firmware (`firmware/sr_support_b_ptk/include/config.h`)

| Parâmetro | Valor | Significado |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | Período de controle de 50 Hz |
| `MAX_CMD_RATE` | 0.08 rad/tick | Limite de slew da saída (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Limiar de up_z da condição de queda |
| `FALL_W_QUIET` | 0.9 rad/s | Limiar de taxa angular da condição de queda |
| `FALL_CONFIRM_TICKS` | 25 | Confirmação da condição de queda (0.5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Ticks por waypoint de referência |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Taxa de retração |
| `EXEC_DONE_TICKS` | 50 | Ticks consecutivos em pé para concluir |
| `EXEC_TIMEOUT_MS` | 14000 | Timeout por referência |
| `EXEC_COOLDOWN_TICKS` | 75 | Cooldown após done/timeout (1.5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Ticks de confirmação da troca de pose |
| `EXEC_SWITCH_UP` | 0.60 | up_z máximo para uma troca |
| `EXEC_SWITCH_W` | 0.8 rad/s | Taxa angular máxima para uma troca |
| `EXEC_MIN_SWITCH_AGE` | 25 | Tick mínimo para uma troca |
| `EXEC_MAX_SWITCHES` | 5 | Máximo de trocas por execução |
| `EXEC_NEUTRAL_MAX` | 120 | Máximo de ticks na retração ao neutro |
| `SERVO_SHOULDER_CENTER_US` | 1681 | Pulso de zero do ombro (valor do centro visual gravado em 2026-11; rezerar conforme a [página 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Pulso de zero do cotovelo (idem) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Limites de comando manual do ombro |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Faixa manual (o executor usa ±1.55 mecanicamente) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Direção dos servos |
| `IMU_YAW90` | 1 | IMU montada com rotação de 90° |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Filtro de atitude: ganho de correção do acelerômetro / faixa de confiança |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Hotspot (`w` o alterna; ligado na inicialização) |

## 11.3 Sequências de referência (ombro, cotovelo; rad; idênticas, valor a valor, às de `training/b_line/getup_reference_b39.py`)

| Pose | Sequência |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` pressão direta em velocidade total (espera ≤40 ticks) → bombeamentos de cunha `[-1.80,0.35] → [-1.80,0.05]` ×2 (espera ≤30 cada) → fallback: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (whip-slam, espera ≤40) → espera final ≤90 → retrair |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 11.4 Status verificado e inspeção de fábrica (2026-11-06)

- **Inspeção de fábrica**: cada unidade pronta recebe — zeros dos servos definidos e gravados por
  unidade ([página 05](./05-zero-tool.md)), calibração de zero do giroscópio + acelerômetro (NVS),
  e um teste de endireitamento nas quatro direções antes do envio;
- As quatro direções verificadas no robô real, cada uma como **endireitamento direto** (sem
  rolar), cerca de 1–6 s; nenhuma violação do envelope dos servos;
- Receita final de `roll_neg`: pressão direta de curso total + bombeamentos de cunha com o cotovelo ×2,
  nova tentativa de whip-slam como fallback (o esquema anterior de rolar + replanejar foi
  aposentado);
- O pipeline de atitude foi corrigido com calibração do bias do acelerômetro (veja a
  [página 06, 6.2](./06-debug-and-calibrate.md)); as poses deitadas agora correspondem ao robô real;
- `roll_neg` ainda não é reproduzido no modelo de simulação com massa 1× (massa/atrito do braço
  diferem); essa é uma lacuna conhecida do modelo — o firmware do hardware é validado no hardware.

## 11.5 Licenciamento

- Código de firmware/treinamento da linha B: MIT / Apache-2.0;
- CAD/STL da linha B: CERN-OHL-S-2.0 (reciprocidade forte — verifique as obrigações antes do uso comercial);
- SelfRisingRobot: sem licença; este tutorial não contém nenhum código, waypoint ou modelo dele;
- Patente CN109693729A/B: faça uma revisão de FTO antes do uso comercial.

---

[← Voltar ao índice do tutorial](./index.md)
