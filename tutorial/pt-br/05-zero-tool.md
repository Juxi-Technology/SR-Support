---
title: 05 Calibração de zero (teclas de seta; obrigatório para builds DIY)
description: Mova o braço até o centro visual com as teclas de seta e declare-o q=0; obrigatório para todo build DIY, e após reindexar um horn ou remontar.
---

# 05 Calibração de zero (teclas de seta; obrigatório para builds DIY)

Os zeros dos servos e os zeros do acelerômetro da IMU são calibrados e gravados por unidade na
fábrica, então uma unidade pronta não precisa de nada aqui. Um **build DIY precisa fazer esta
página**: um braço montado à mão quase nunca fica exatamente no centro. Mesmo que o horn não
tenha sido montado exatamente no zero do firmware, você pode corrigir aqui — mova o braço até a
vertical visual com as teclas de seta e pressione `z` para declarar a pose **atual** como q=0. O
comando `z` não usa a IMU e funciona em qualquer pose ou índice de horn.

Volte a esta página quando: um horn for reindexado, o braço for desmontado/remontado, um servo for
substituído, a IMU for substituída/remontada (recalibre o acelerômetro), ou o braço deixar de
repousar no centro visual após retrair.

> `z` apenas desloca o zero de software; ele **não** muda como o índice do horn divide o curso
> (PWM 500-2500 µs). Se, após a zeragem, uma direção ficar sem faixa (o pulso satura em
> 500/2500 µs e o braço não alcança um ângulo exigido pela sequência), reindexe o horn (cerca de
> 2 dentes no ombro) e zere novamente.

Momento: após o robô estar totalmente montado e o firmware principal gravado (o caminho DIY segue
03 → 04 → 05).

## 5.1 Princípio

O firmware define q=0 como o centro visual: braço vertical, ambos os elos em uma mesma linha. O
comando `z` é um zero estilo encoder: ele torna as posições **atuais** das juntas q=0 e imprime as
larguras de pulso centrais correspondentes.

## 5.2 Procedimento

1. Conecte tanto a bateria quanto o USB (servos alimentados) e execute isto na pasta `SR-Support`
   com o `.venv` ativado:

   ```bash
   python tools/hw_shoulder_range.py
   ```

   Feche antes qualquer assistente/monitor serial (eles ocupam a porta); as teclas na janela
   abaixo são lidas por esta ferramenta, nenhum assistente serial é necessário. As ferramentas
   seriais / o download do UartAssist para Windows estão na
   [página 03, seção 3.3](./03-build-flash.md).

   Um visor persistente de quatro linhas é atualizado no próprio local:

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Mova com as teclas de seta: `↑`/`↓` = braço grande ±0.05 rad, `←`/`→` = braço pequeno
   ±0.05 rad (Shift = ±0.20) até o braço parecer **vertical e alinhado**;
3. Pressione `z`; o firmware imprime:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. Verificação de sanidade: pressione `n` (home), mova um pouco, vá para home de novo — o braço
   deve voltar ao centro visual que você acabou de definir.

## 5.3 Gravação permanente (obrigatória quando estiver satisfeito)

`z` só altera a RAM; um reboot restaura o zero antigo. Quando estiver satisfeito:

1. Escreva os dois valores de pulso no `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. Desloque todos os waypoints de `EXEC_REF*` e de `training/b_line/getup_reference_b39.py` pelos
   mesmos offsets (ombro/cotovelo, cada um −Δ rad);
3. Regrave o firmware e reteste as quatro direções ([página 07](./07-self-righting.md)).

> Um toque errado é inofensivo: zere novamente para sobrescrever.

## 5.4 Comandos relacionados

| Comando | Função |
|---|---|
| `z` | A pose atual vira q=0 para as duas juntas; imprime os novos pulsos centrais (apenas na RAM) |
| `k` | Lê os pulsos centrais atuais (ombro/cotovelo, µs) |
| `o` / `p` | Ajuste ao vivo de ±10 µs no centro do ombro (redefinido no reboot) |

---

[← Voltar ao índice do tutorial](./index.md)
