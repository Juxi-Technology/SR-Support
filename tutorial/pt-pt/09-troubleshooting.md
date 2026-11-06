---
title: 09 Resolução de problemas
description: Sintomas, causas e soluções comuns do SR-Support, abrangendo IMU, porta série, condição de queda, timeouts do executor e WiFi.
---

# 09 Resolução de problemas

Os comandos série são enviados através de um assistente/monitor série: escreva-os na caixa de
envio e prima Enter (ative «send newline» no UartAssist); as ferramentas de série / a
transferência do UartAssist para Windows estão na
[página 03, secção 3.3](./03-build-flash.md).

## 9.1 Sintomas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `waiting for IMU startup 5000 ms...` e depois `IMU not ready` | Arranque lento da IMU, cablagem defeituosa, endereço errado | Aguarde 5–10 s; verifique 3V3, SDA=GPIO6 / SCL=GPIO7, endereço 0x23 |
| `IMU lost -> bus reset + re-init` repetido | Fios I²C longos ou soltos | Encurte os fios, volte a assentar as ligações |
| A gravação falha com `could not open port` / `Access is denied` | Porta série ocupada pelo monitor/monitor série | Feche primeiro o `hw_monitor.py` ou o monitor série |
| O robô não arranca depois de colocado | Corpo não está imóvel, ou uma mão está a tocá-lo | Largue e mantenha imóvel ≥0.5 s; observe `getup start` |
| Agitação imediata / direção errada | Condição de queda disparada a meio do rolamento, classificação errada | Coloque e largue com cuidado; tente de novo |
| A execução para e imprime `executor timeout` após 14 s | A referência não terminou | Recurso normal; nova tentativa automática após 1.5 s; guarde o registo |
| Eventos `executor re-plan` ocasionais | Recurso normal após uma pressão `roll_neg` falhada | Verifique se termina com `done` |
| O servo zumbe / aquece | Bloqueio ou alvo que prende | Envie `x` ou corte a alimentação; verifique os limites e a folga mecânica |
| O braço bate no corpo durante o auto-endireitamento | Movimento grande do ombro | Verifique `Q_SHOULDER_MAX` e a folga; mantenha a altura da base de ~68 mm |
| O `up` não corresponde à postura real (tilt persistente de 5° ou mais com o robô deitado) | Offsets de zero do acelerómetro não calibrados | Coloque o robô nivelado e envie `c` (ver [página 06, 6.2](./06-debug-and-calibrate.md)) |
| O braço não assenta no centro visual após retrair | Zero desviado (reindexado/remontado sem refazer o ponto zero) | Refaça o ponto zero com a [ferramenta da página 05](./05-zero-tool.md) e grave-o |
| O servo zumbe/vibra após um levantamento | Autoexcitação transitória do servo analógico após grandes movimentos/bloqueios (a saída é constante) | Desaparece por si; adicione anilhas de amortecimento em borracha ou use um servo digital; apertar o braço silencia-o de imediato |
| Página de estado / aprovisionamento inacessível | Proxy do navegador não contornado, ou hotspot desligado | Adicione `192.168.4.1` às exceções do proxy; envie `w` para ativar o WiFi |

## 9.2 Comandos de segurança

| Situação | Comando |
|---|---|
| Parar o movimento imediatamente | `s` (manter o último alvo) ou `x` (desativar PWM, libertar o torque) |
| Recuperar após `x` | `r` reinicializa o PWM e centra |
| Uma junta move-se no sentido errado | inversão de sinal `v` (ombro) / `b` (cotovelo) |

## 9.3 Capturar uma falha

Guarde a parte correspondente de `logs/hw_monitor.log`. As linhas-chave são:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```

---

[← Voltar ao índice do tutorial](./index.md)
