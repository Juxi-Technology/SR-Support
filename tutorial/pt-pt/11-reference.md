---
title: 11 Referência: modelo, parâmetros e licenciamento
description: Ficheiros de modelo de referência (MuJoCo XML / STL), parâmetros do firmware, as quatro sequências de referência, estado verificado e licenciamento.
---

# 11 Referência: modelo, parâmetros e licenciamento

## 11.1 Ficheiros de modelo de referência

A simulação usa MuJoCo MJCF (`.xml` + malhas `.stl`), partilhando o próprio design do hardware:

| Ficheiro | Descrição |
|---|---|
| `hardware/v1/robot_v1.xml` | Modelo principal (geometria/massa correspondentes ao hardware) |
| `hardware/v1/meshes/*.stl` | 6 malhas STL que se agrupam em 4 grupos impressos (placa/carcaça da base, suporte do ombro, suporte do braço superior/suporte do cotovelo, antebraço) |
| `hardware/v1/meshes/print_mass_model.json` | Tabela de massa impressa por peça (15% de preenchimento) |

Não é incluído nenhum URDF; para utilização com ROS, exporte um a partir do CAD/malhas acima.

## 11.2 Parâmetros do firmware (`firmware/sr_support_b_ptk/include/config.h`)

| Parâmetro | Valor | Significado |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | Período de controlo de 50 Hz |
| `MAX_CMD_RATE` | 0.08 rad/tick | Limite de slew da saída (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Limiar de up_z da condição de queda |
| `FALL_W_QUIET` | 0.9 rad/s | Limiar de velocidade angular da condição de queda |
| `FALL_CONFIRM_TICKS` | 25 | Confirmação da condição de queda (0.5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Ticks por waypoint de referência |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Taxa de retração |
| `EXEC_DONE_TICKS` | 50 | Ticks consecutivos de pé para concluir |
| `EXEC_TIMEOUT_MS` | 14000 | Timeout por referência |
| `EXEC_COOLDOWN_TICKS` | 75 | Arrefecimento após conclusão/timeout (1.5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Ticks de confirmação da mudança de postura |
| `EXEC_SWITCH_UP` | 0.60 | up_z máximo para uma mudança |
| `EXEC_SWITCH_W` | 0.8 rad/s | Velocidade angular máxima para uma mudança |
| `EXEC_MIN_SWITCH_AGE` | 25 | Tick mais cedo para uma mudança |
| `EXEC_MAX_SWITCHES` | 5 | Máximo de mudanças por execução |
| `EXEC_NEUTRAL_MAX` | 120 | Máximo de ticks de retração para o neutro |
| `SERVO_SHOULDER_CENTER_US` | 1681 | Impulso do zero do ombro (valor do centro visual gravado em 2026-11; refaça o ponto zero conforme a [página 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Impulso do zero do cotovelo (idem) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Limites dos comandos manuais do ombro |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Curso manual (o executor usa ±1.55 mecanicamente) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Direção do servo |
| `IMU_YAW90` | 1 | IMU montada rodada 90° |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Filtro de atitude: ganho de correção do acelerómetro / banda de confiança |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Hotspot (o `w` alterna-o; ativo no arranque) |

## 11.3 Sequências de referência (ombro, cotovelo; rad; valor a valor com `training/b_line/getup_reference_b39.py`)

| Postura | Sequência |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` pressão direta a toda a velocidade (manter ≤40 ticks) → bombeamentos de cunha `[-1.80,0.35] → [-1.80,0.05]` ×2 (manter ≤30 cada) → recurso: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (whip-slam, manter ≤40) → espera final ≤90 → retrair |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 11.4 Estado verificado e inspeção de fábrica (2026-11-06)

- **Inspeção de fábrica**: cada unidade acabada recebe — zeros dos servos definidos e gravados
  por unidade ([página 05](./05-zero-tool.md)), calibração do zero do giroscópio + acelerómetro
  (NVS) e um teste de levantamento nas quatro direções antes do envio;
- As quatro direções verificadas no robô real, cada uma como um **levantamento direto** (sem
  rolamento), cerca de 1–6 s; sem violações do envelope dos servos;
- Receita final do `roll_neg`: pressão direta a todo o curso + bombeamentos de cunha do
  cotovelo ×2, nova tentativa whip-slam como recurso (o esquema anterior de rolamento +
  replaneamento foi retirado);
- O pipeline de atitude foi corrigido com a calibração do viés do acelerómetro (ver
  [página 06, 6.2](./06-debug-and-calibrate.md)); as posturas deitadas agora correspondem ao
  robô real;
- O `roll_neg` ainda não se reproduz no modelo de simulação com massa 1× (massa/atrito do braço
  diferem); é uma lacuna conhecida do modelo — o firmware do hardware é validado no hardware.

## 11.5 Licenciamento

- Código de firmware/treino da linha B: MIT / Apache-2.0;
- CAD/STL da linha B: CERN-OHL-S-2.0 (reciprocidade forte — verifique as obrigações antes de uso
  comercial);
- SelfRisingRobot: sem licença; este tutorial não contém nenhum do seu código, waypoints ou
  modelos;
- Patente CN109693729A/B: faça uma revisão FTO antes de uso comercial.

---

[← Voltar ao índice do tutorial](./index.md)
