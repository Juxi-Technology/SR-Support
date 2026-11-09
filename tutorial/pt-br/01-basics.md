---
title: 01 Fundamentos
description: Princípio de funcionamento, especificações e BOM do SR-Support.
---

# 01 Fundamentos

## 1.1 Princípio de funcionamento

O SR-Support é um dispositivo ativo de auto-endireitamento de 2 GDL (ombro + cotovelo):

- **Mecanismo**: um braço de duas juntas montado sobre uma base quadrada; o ombro gira em torno
  do eixo longitudinal do corpo e o cotovelo dobra o antebraço;
- **Sensoriamento**: uma IMU de 6 eixos fornece o quatérnio de atitude; o firmware classifica
  cada queda em uma de quatro poses (`pitch_pos/neg`, `roll_pos/neg`, veja a
  [página 06](./06-debug-and-calibrate.md) 6.5) a partir do vetor "para cima" no referencial do corpo;
- **Atuação**: um executor de sequências de referência — cada pose tem uma programação de
  waypoints (20 ticks por waypoint, slew de 0.08 rad/tick) que apoia/alavanca o braço para rolar
  o corpo de volta à posição vertical; `roll_neg` usa ainda bombeamentos de cunha com o cotovelo e um
  fallback de whip-slam;
- **Fallbacks**: timeout de 14 s, replanejamento de pose e nova tentativa automática após a
  condição de queda; `roll_neg` usa esperas adaptativas por estágio e passa para a retração
  assim que está na vertical;
- **Verificado**: as quatro direções se levantam diretamente em cerca de 1–6 s; o mesmo modelo
  alimenta a simulação MuJoCo e o gêmeo ao vivo do hardware ([página 09](./09-mujoco.md)).

## 1.2 Visão geral

| Item | Especificação |
|---|---|
| Base | ~88 × 82 mm, 68 mm de altura (placa inferior + suporte do servo do ombro, impressos em 3D) |
| Braço | Eixo do ombro 56 mm acima da base, cotovelo 40.1 mm acima do ombro; haste do antebraço ~17 cm (tubo de 12 mm) |
| Massa | ~133 g (tabela de massas do modelo: foot 92.1 / arm1 20.7 / arm2 20.1 g, incluindo os dois servos) |
| Ombro | PTK7452MG; limites manuais `[-1.85, +1.82]` rad (faixa da junta na simulação `[-1.07, +2.07]`) |
| Cotovelo | PTK7452MG; limites manuais `[-0.90, +0.70]` rad (mecânico ~±1.55 rad) |
| Controlador | ESP32-S3-DevKitC-1 (framework Arduino / PlatformIO) |
| Atitude | IMU de 6 eixos Juxi ICM42670P (endereço I²C 0x23, 100 kHz) |
| Acionamento dos servos | ESP32 LEDC, 50 Hz, 14 bits, largura de pulso 500–2500 µs |

## 1.3 BOM

| Categoria | Peça | Qtd | Observações |
|---|---|---|---|
| Estrutura | Impressas em 3D: placa inferior, suporte do servo do ombro, suporte do servo do cotovelo, travessa superior | 1 de cada | PETG ou PLA, 15% de preenchimento; os horns são os inclusos com os servos |
| Atuação | Servo PTK7452MG 180° PWM | 2 | Engrenagens metálicas, 25T, ~12.2 g, ~3.4 kg·cm a 6 V |
| Controlador | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Sensor | Módulo IMU Juxi ICM42670P | 1 | Alimentação de 3.3 V |
| Adaptador | Placa adaptadora de servo passiva | 1 | GPIO → conectores de 3 pinos, V+/GND compartilhados, sem PCA9685 |
| Cabeamento | Cabo de dados USB-C, fios Dupont, extensões de servo | vários | — |
| Alimentação | Fonte para servos 5 V / ≥5 A | 1 | Uma fonte de 5 V alimenta o ESP32 e os servos por meio de um cabo 1-para-2 (terra comum); **verificada para as quatro direções de endireitamento** |

---

[← Voltar ao índice do tutorial](./index.md)
