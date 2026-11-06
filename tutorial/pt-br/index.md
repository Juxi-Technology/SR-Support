---
title: Tutorial do Robô de Auto-Endireitamento SR-Support
description: Tutorial completo do dispositivo de auto-endireitamento SR-Support de 2 GDL, dos fundamentos e da configuração do ambiente à gravação, montagem, zeragem, calibração, uso do auto-endireitamento e solução de problemas.
---

# Tutorial do Robô de Auto-Endireitamento SR-Support

[简体中文](../zh-hans/index.md) · [繁體中文](../zh-hant/index.md) · [English](../en/index.md) · [日本語](../ja/index.md) · [한국어](../ko/index.md) · [Deutsch](../de/index.md) · [Français](../fr/index.md) · [Español](../es/index.md) · [Italiano](../it/index.md) · [Português (BR)](../pt-br/index.md) · [Português (PT)](../pt-pt/index.md)


O SR-Support é um dispositivo ativo de auto-endireitamento de baixo custo baseado em um braço
de 2 GDL. Após tombar em qualquer direção, ele apoia seu braço de duas juntas no chão, rola e
se alavanca de volta para a posição vertical. Este tutorial está organizado como uma ordem de
leitura que cobre o caminho completo, do zero a uma montagem verificada.

## Ordem de leitura

| # | Página | Conteúdo | Observação |
|---|---|---|---|
| 01 | [Fundamentos](./01-basics.md) | Princípio de funcionamento, especificações, BOM | leia primeiro |
| 02 | [Configuração do ambiente](./02-environment.md) | Criar/ativar `.venv`, firmware pré-compilado + ferramentas de gravação (Flash Download Tool / esptool), ferramentas do lado do computador e ambiente MuJoCo, PlatformIO opcional, porta serial | **faça isto primeiro** |
| 03 | [Gravar o firmware principal](./03-build-flash.md) | Binário pré-compilado (recomendado para clientes) ou build a partir do código-fonte com PlatformIO, comandos seriais, comportamento de inicialização | dispensável para unidades prontas |
| 04 | [Montagem: imprimir, montar e ligar](./04-assembly.md) | Peças impressas, índice do horn, tabela de fiação, montagem da IMU | dispensável para unidades prontas |
| 05 | [Calibração de zero](./05-zero-tool.md) | Movimentação com as teclas de seta + zeragem com `z` (após reindexação/remontagem) | **obrigatório para builds DIY**; dispensável para unidades prontas |
| 06 | [Depuração e calibração](./06-debug-and-calibrate.md) | Verificação e calibração do robô completo: telemetria, IMU, servos, verificação de centralização, quatro poses deitadas, condição de queda | |
| 07 | [Uso e monitoramento do auto-endireitamento](./07-self-righting.md) | Quatro direções de queda, movimento esperado, monitoramento e logs | |
| 08 | [WiFi e o gêmeo de simulação](./08-wifi-twin.md) | Página de status, provisionamento de WiFi doméstico, gêmeo MuJoCo sem fio | opcional |
| 09 | [Solução de problemas](./09-troubleshooting.md) | Sintomas comuns e correções | referência |
| 10 | [Referência: modelo, parâmetros, licenciamento](./10-reference.md) | Arquivos do modelo (XML/STL), parâmetros, sequências de referência, licenciamento | referência |

## Estado de fábrica de uma unidade pronta (dois caminhos de leitura)

Este tutorial atende a dois públicos — escolha o caminho que corresponde ao seu:

| Leitor | Estado de fábrica | Caminho recomendado |
|---|---|---|
| **Usuário de unidade pronta** | Montada e cabeada, firmware gravado, **calibrada** (zeros dos servos e zeros do acelerômetro da IMU já gravados), **testada** (todas as quatro direções de endireitamento verificadas em cada unidade) | Vá direto para [07 uso](./07-self-righting.md) e [08 WiFi/gêmeo](./08-wifi-twin.md) (opcional); guarde [09](./09-troubleshooting.md)/[10](./10-reference.md) para referência. **As páginas 02/03/04/05/06 só são necessárias para atualizações de firmware, substituição de servo/IMU ou remontagem do horn**; para usar as ferramentas de gêmeo/telemetria da página 08, primeiro instale as ferramentas do computador da página 02. |
| **Montador de kit / DIY** | Começa a partir das peças | Siga [01](./01-basics.md) → [02](./02-environment.md) → [03 gravação](./03-build-flash.md) → [04 montagem](./04-assembly.md) → [05 zeragem (obrigatória)](./05-zero-tool.md) → [06 depuração/calibração](./06-debug-and-calibrate.md) → [07](./07-self-righting.md) do início ao fim. Tanto a zeragem (05) quanto a calibração (06) acontecem **após a montagem completa e a gravação**: `z` não usa a IMU e funciona em qualquer pose; `c` exige o robô montado em pé e nivelado. |

> Verificação recomendada na primeira utilização de uma unidade pronta: ligue em pé → confirme `up≈(0,0,1)` →
> tombe-a uma vez em cada uma das quatro direções conforme a [página 07](./07-self-righting.md) e
> confirme que ela se levanta.

## Pré-requisitos

- Peças mecânicas do SR-Support (placa inferior, suporte do servo do ombro, suporte do servo do cotovelo, travessa superior; impressão e montagem na [página 04](./04-assembly.md));
- Placa ESP32-S3, IMU Juxi ICM42670P, placa adaptadora de servo de acionamento direto passiva;
- 2× servos PTK7452MG (PWM de 180°);
- Uma fonte de alimentação para os servos (5 V / ≥5 A) e um cabo de dados USB-C;
- Um computador com o ambiente da [página 02](./02-environment.md).

## Status verificado (2026-11-06)

As quatro direções de queda foram verificadas no robô real, cada uma como **endireitamento
direto** (sem necessidade de rolar), levando cerca de 1–6 s; nenhuma violação do envelope dos
servos foi registrada. O kit também inclui uma ferramenta de calibração de zero com teclas de
seta ([página 05](./05-zero-tool.md)), uma página de status WiFi com provisionamento para a
rede doméstica e um gêmeo MuJoCo ao vivo sem fio
([página 08](./08-wifi-twin.md)).

## Segurança

> - Segure o robô na primeira energização, mantenha uma área livre de 30 cm e envie `x` ou corte
>   a alimentação dos servos diante de qualquer anormalidade;
> - Nunca trave um servo por mais de 1 s; pare quando a carcaça ultrapassar 60 °C;
> - a alimentação dos servos **5 V / ≥5 A** (verificada para as quatro direções de endireitamento);
> - qualquer coisa acima de 5 V vai apenas para o trilho dos servos — **nunca** para o 5V/3V3 do ESP32;
> - Tudo compartilha um único terra; a ordem de energização está na [página 04](./04-assembly.md).
