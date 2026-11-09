---
title: Tutorial do robô auto-endireitador SR-Support
description: Tutorial completo do dispositivo de auto-endireitamento SR-Support de 2 GDL, desde os fundamentos e a preparação do ambiente até à gravação, montagem, ponto zero, calibração, utilização do auto-endireitamento e resolução de problemas.
---

# Tutorial do robô auto-endireitador SR-Support

[简体中文](../zh-hans/index.md) · [繁體中文](../zh-hant/index.md) · [English](../en/index.md) · [日本語](../ja/index.md) · [한국어](../ko/index.md) · [Deutsch](../de/index.md) · [Français](../fr/index.md) · [Español](../es/index.md) · [Italiano](../it/index.md) · [Português (BR)](../pt-br/index.md) · [Português (PT)](../pt-pt/index.md)


O SR-Support é um dispositivo ativo de auto-endireitamento de baixo custo baseado num braço de
2 GDL. Depois de tombar em qualquer direção, apoia o seu braço de duas articulações no solo, rola
e alavanca-se de volta à posição vertical. Este tutorial está organizado como uma ordem de
leitura que cobre todo o percurso, do zero até uma montagem verificada.

## Ordem de leitura

| # | Página | Conteúdo | Nota |
|---|---|---|---|
| 01 | [Fundamentos](./01-basics.md) | Princípio de funcionamento, especificações, lista de materiais | ler primeiro |
| 02 | [Preparação do ambiente](./02-environment.md) | Criar/ativar o `.venv`, firmware pré-compilado + ferramentas de gravação (Flash Download Tool / esptool), ferramentas do lado do computador e ambiente MuJoCo, PlatformIO opcional, porta série | **fazer isto primeiro** |
| 03 | [Gravar o firmware principal](./03-build-flash.md) | Bin pré-compilado (recomendado para clientes) ou compilação a partir do código-fonte com PlatformIO, comandos série, comportamento no arranque | pode saltar-se em unidades prontas |
| 04 | [Montagem: imprimir, montar, ligar](./04-assembly.md) | Peças impressas, índice do horn, tabela de ligações, montagem da IMU | pode saltar-se em unidades prontas |
| 05 | [Calibração do ponto zero](./05-zero-tool.md) | Jog com teclas de seta + ponto zero com `z` (após reindexação/remontagem) | **obrigatório para montagens DIY**; pode saltar-se em unidades prontas |
| 06 | [Depuração e calibração](./06-debug-and-calibrate.md) | Verificação e calibração do robô completo: telemetria, IMU, servos, verificação do centro, quatro posturas deitadas, condição de queda | |
| 07 | [Utilização e monitorização do auto-endireitamento](./07-self-righting.md) | As quatro direções de queda, movimento esperado, monitorização e registos | |
| 08 | [Página de estado WiFi e aprovisionamento](./08-wifi.md) | Hotspot, página de estado, aprovisionamento do WiFi doméstico | opcional |
| 09 | [Simulação MuJoCo e o gémeo ao vivo](./09-mujoco.md) | Janela de simulação local nas quatro posturas, gémeo ao vivo por WiFi, registo de telemetria | opcional |
| 10 | [Resolução de problemas](./10-troubleshooting.md) | Sintomas comuns e soluções | referência |
| 11 | [Referência: modelo, parâmetros, licenciamento](./11-reference.md) | Ficheiros de modelo (XML/STL), parâmetros, sequências de referência, licenciamento | referência |

## Estado de fábrica de uma unidade acabada (dois percursos de leitura)

Este tutorial serve dois públicos — escolha o percurso que se aplica ao seu caso:

| Leitor | Estado de fábrica | Percurso recomendado |
|---|---|---|
| **Utilizador de unidade acabada** | Montada e ligada, firmware gravado, **calibrada** (zeros dos servos e zeros do acelerómetro da IMU gravados), **testada** (as quatro direções de levantamento verificadas em cada unidade) | Vá diretamente para [07 utilização](./07-self-righting.md), [08 aprovisionamento WiFi](./08-wifi.md) e [09 simulação MuJoCo e gémeo ao vivo](./09-mujoco.md) (opcional); guarde [10](./10-troubleshooting.md)/[11](./11-reference.md) para referência. **As páginas 02/03/04/05/06 só são necessárias para atualizações de firmware, substituição de servos/IMU ou remontagem do horn**; para usar as ferramentas de gémeo/telemetria da página 09, instale primeiro as ferramentas do lado do computador da página 02. |
| **Construtor de kit / DIY** | Parte das peças | Siga [01](./01-basics.md) → [02](./02-environment.md) → [03 gravação](./03-build-flash.md) → [04 montagem](./04-assembly.md) → [05 ponto zero (obrigatório)](./05-zero-tool.md) → [06 depuração/calibração](./06-debug-and-calibrate.md) → [07](./07-self-righting.md) do início ao fim. Tanto o ponto zero (05) como a calibração (06) acontecem **depois da montagem completa e da gravação do firmware**: o `z` não usa a IMU e funciona em qualquer postura; o `c` requer o robô montado e nivelado. |

> Verificação recomendada na primeira utilização de uma unidade acabada: ligue-a na vertical →
> confirme `up≈(0,0,1)` → incline-a uma vez em cada uma das quatro direções conforme a
> [página 07](./07-self-righting.md) e confirme que se levanta.

## Pré-requisitos

- Peças mecânicas do SR-Support (placa inferior, suporte do servo do ombro, suporte do servo do
  cotovelo, montante superior; impressão e montagem na [página 04](./04-assembly.md));
- Placa ESP32-S3, IMU Juxi ICM42670P, placa adaptadora passiva para servos de acionamento direto;
- 2× servos PTK7452MG (PWM de 180°);
- Uma fonte de alimentação dos servos (5 V / ≥5 A) e um cabo de dados USB-C;
- Um computador com o ambiente da [página 02](./02-environment.md).

## Estado verificado (2026-11-06)

As quatro direções de queda foram verificadas no robô real, cada uma como um **levantamento
direto** (sem necessidade de rolamento), demorando cerca de 1–6 s; não foi registada qualquer
violação do envelope dos servos. O kit inclui também uma ferramenta de calibração do ponto zero
com teclas de seta ([página 05](./05-zero-tool.md)), uma página de estado WiFi com
aprovisionamento da rede doméstica ([página 08](./08-wifi.md)) e a simulação MuJoCo com o seu
gémeo ao vivo sem fios ([página 09](./09-mujoco.md)).

## Segurança

> - Segure o robô na primeira ligação, mantenha uma área livre de 30 cm e envie `x` ou corte a
>   alimentação dos servos perante qualquer anomalia;
> - Nunca bloqueie um servo durante mais de 1 s; pare quando a carcaça exceder 60 °C;
> - a alimentação dos servos **5 V / ≥5 A** (verificada para as quatro direções de levantamento);
> - qualquer tensão acima de 5 V vai apenas para o barramento dos servos — **nunca** para o
>   5V/3V3 do ESP32;
> - Tudo partilha a mesma massa; a ordem de ligação está na [página 04](./04-assembly.md).
