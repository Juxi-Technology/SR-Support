---
title: 01 Fundamentos
description: Princípio de funcionamento, especificações e lista de materiais do SR-Support.
---

# 01 Fundamentos

## 1.1 Princípio de funcionamento

O SR-Support é um dispositivo ativo de auto-endireitamento de 2 GDL (ombro + cotovelo):

- **Mecanismo**: um braço de duas articulações montado numa base quadrada; o ombro oscila em
  torno do eixo longitudinal do corpo e o cotovelo dobra o antebraço;
- **Sensorização**: uma IMU de 6 eixos fornece o quaternião de atitude; o firmware classifica
  cada queda numa de quatro posturas (`pitch_pos/neg`, `roll_pos/neg`, ver
  [página 06](./06-debug-and-calibrate.md) 6.5) a partir do vetor up no referencial do corpo;
- **Atuação**: um executor de sequências de referência — cada postura tem um esquema de
  waypoints (20 ticks por waypoint, 0.08 rad/tick de slew) que apoia/alavanca o braço para rolar
  o corpo de volta à vertical; o `roll_neg` usa ainda bombeamentos de cunha com o cotovelo e um
  mecanismo de recurso *whip-slam*;
- **Mecanismos de reserva**: tempo limite de 14 s, replaneamento da postura e nova tentativa
  automática após a condição de queda; o `roll_neg` usa esperas adaptativas por etapa e sai para
  retrair assim que está na vertical;
- **Verificado**: as quatro direções levantam-se diretamente em cerca de 1–6 s; o mesmo modelo
  alimenta a simulação MuJoCo e o gémeo do hardware ao vivo
  ([página 09](./09-mujoco.md)).

## 1.2 Visão geral

| Item | Especificação |
|---|---|
| Base | ~88 × 82 mm, 68 mm de altura (placa inferior + suporte do servo do ombro, impressos em 3D) |
| Braço | Eixo do ombro a 56 mm acima da base, cotovelo a 40.1 mm acima do ombro; montante do antebraço ~17 cm (tubo de 12 mm) |
| Massa | ~133 g (tabela de massas do modelo: pé 92.1 / arm1 20.7 / arm2 20.1 g, incluindo ambos os servos) |
| Ombro | PTK7452MG; limites manuais `[-1.85, +1.82]` rad (curso da junta na simulação `[-1.07, +2.07]`) |
| Cotovelo | PTK7452MG; limites manuais `[-0.90, +0.70]` rad (mecânicos ~±1.55 rad) |
| Controlador | ESP32-S3-DevKitC-1 (framework Arduino / PlatformIO) |
| Atitude | IMU Juxi ICM42670P de 6 eixos (endereço I²C 0x23, 100 kHz) |
| Acionamento dos servos | LEDC do ESP32, 50 Hz, 14 bits, largura de impulso 500–2500 µs |

## 1.3 Lista de materiais (BOM)

| Categoria | Peça | Quantidade | Notas |
|---|---|---|---|
| Estrutura | Impressos em 3D: placa inferior, suporte do servo do ombro, suporte do servo do cotovelo, montante superior | 1 de cada | PETG ou PLA, 15% de preenchimento; os horns são os fornecidos com os servos |
| Acionamento | Servo PTK7452MG PWM de 180° | 2 | Engrenagem metálica, 25T, ~12.2 g, ~3.4 kg·cm a 6 V |
| Controlador | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Sensor | Módulo IMU Juxi ICM42670P | 1 | Alimentação 3.3 V |
| Adaptador | Placa adaptadora passiva de servos | 1 | GPIO → conectores de 3 pinos, V+/GND comuns, sem PCA9685 |
| Cablagem | Cabo de dados USB-C, fios Dupont, extensões de servo | vários | — |
| Alimentação | Fonte dos servos 5 V / ≥5 A | 1 | Uma fonte de 5 V alimenta o ESP32 e os servos através de um cabo 1-para-2 (massa comum); **verificada para as quatro direções de levantamento** |

---

[← Voltar ao índice do tutorial](./index.md)
