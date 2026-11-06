---
title: 05 Calibração do ponto zero (teclas de seta; obrigatório para montagens DIY)
description: Mova o braço até ao centro visual com as teclas de seta e declare-o q=0; obrigatório para todas as montagens DIY e após reindexar um horn ou remontar.
---

# 05 Calibração do ponto zero (teclas de seta; obrigatório para montagens DIY)

Os zeros dos servos e os zeros do acelerómetro da IMU são calibrados e gravados por unidade na
fábrica, pelo que uma unidade pronta não precisa de nada aqui. Uma **montagem DIY tem de fazer
esta página**: um braço montado à mão quase nunca fica exatamente no centro. Mesmo que o horn
não tenha sido montado exatamente no zero do firmware, pode corrigi-lo aqui — mova o braço até à
vertical visual com as teclas de seta e prima `z` para declarar a postura **atual** como q=0. O
comando `z` não usa a IMU e funciona em qualquer postura ou índice do horn.

Volte aqui quando: um horn foi reindexado, o braço foi desmontado/remontado, um servo foi
substituído, a IMU foi substituída/remontada (recalibre o acelerómetro), ou o braço já não
assenta no centro visual após retrair.

> O `z` apenas desloca o zero de software; **não** altera a forma como o índice do horn reparte o
> curso (PWM 500-2500 µs). Se, após o ponto zero, uma direção ficar sem curso (o impulso satura
> em 500/2500 µs e o braço não alcança um ângulo exigido pela sequência), reindexe o horn (cerca
> de 2 dentes no ombro) e faça o ponto zero de novo.

Momento: depois de o robô estar totalmente montado e o firmware principal gravado (o percurso
DIY segue 03 → 04 → 05).

## 5.1 Princípio

O firmware define q=0 como o centro visual: braço vertical, os dois elos alinhados. O comando `z`
é um zero tipo encoder: torna as posições **atuais** das juntas em q=0 e imprime as larguras de
impulso centrais correspondentes.

## 5.2 Procedimento

1. Ligue tanto a bateria como o USB (servos alimentados) e execute o seguinte na pasta
   `SR-Support` com o `.venv` ativado:

   ```bash
   python tools/hw_shoulder_range.py
   ```

   Feche primeiro qualquer assistente/monitor série (ocupam a porta); as teclas na janela
   abaixo são lidas por esta ferramenta, não é preciso assistente série. As ferramentas de
   série / a transferência do UartAssist para Windows estão na
   [página 03, secção 3.3](./03-build-flash.md).

   Um ecrã persistente de quatro linhas atualiza-se no local:

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Mova com as teclas de seta: `↑`/`↓` = braço grande ±0.05 rad, `←`/`→` = braço pequeno
   ±0.05 rad (Shift = ±0.20) até o braço parecer **vertical e alinhado**;
3. Prima `z`; o firmware imprime:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. Verificação de sanidade: prima `n` (home), mova um pouco, faça home de novo — o braço tem de
   voltar ao centro visual que acabou de definir.

## 5.3 Gravação (obrigatória quando estiver satisfeito)

O `z` só altera a RAM; um reinício restaura o zero antigo. Quando estiver satisfeito:

1. Escreva os dois valores de impulso no `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. Desloque cada waypoint de `EXEC_REF*` e `training/b_line/getup_reference_b39.py` pelos mesmos
   offsets (ombro/cotovelo, cada um −Δ rad);
3. Volte a gravar e teste de novo as quatro direções ([página 07](./07-self-righting.md)).

> Um toque errado é inofensivo: faça o ponto zero de novo para substituir.

## 5.4 Comandos relacionados

| Comando | Função |
|---|---|
| `z` | A postura atual passa a q=0 para ambas as juntas; imprime os novos impulsos centrais (apenas em RAM) |
| `k` | Ler os impulsos centrais atuais (ombro/cotovelo, µs) |
| `o` / `p` | Ajuste fino em tempo real do centro do ombro ±10 µs (repõe no reinício) |

---

[← Voltar ao índice do tutorial](./index.md)
