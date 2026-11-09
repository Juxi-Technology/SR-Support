---
title: 10 Solução de problemas
description: Sintomas, causas e correções comuns do SR-Support, cobrindo IMU, porta serial, condição de queda, timeouts do executor e WiFi.
---

# 10 Solução de problemas

Os comandos seriais são enviados por um assistente/monitor serial: digite-os na caixa de envio e
pressione Enter (habilite "send newline" no UartAssist); as ferramentas seriais / o download do
UartAssist para Windows estão na [página 03, seção 3.3](./03-build-flash.md).

## 10.1 Sintomas comuns

| Sintoma | Causa provável | Correção |
|---|---|---|
| `waiting for IMU startup 5000 ms...` e depois `IMU not ready` | Inicialização lenta da IMU, fiação ruim, endereço errado | Espere 5–10 s; verifique 3V3, SDA=GPIO6 / SCL=GPIO7, endereço 0x23 |
| `IMU lost -> bus reset + re-init` repetido | Fios I²C longos ou soltos | Encurte os fios, reassente os conectores |
| A gravação falha com `could not open port` / `Access is denied` | Porta serial ocupada por um monitor serial | Feche o `hw_monitor.py` ou o monitor serial primeiro |
| O robô não inicia após ser posicionado | Corpo não está parado, ou uma mão o está tocando | Solte e mantenha parado por ≥0.5 s; observe `getup start` |
| Movimento descontrolado imediato / direção errada | Condição de queda disparada no meio de um rolamento, classificação incorreta | Posicione e solte de forma limpa; tente novamente |
| A execução para e imprime `executor timeout` após 14 s | A referência não terminou | Fallback normal; nova tentativa automática após 1.5 s; guarde o log |
| Eventos ocasionais de `executor re-plan` | Fallback normal após uma pressão de `roll_neg` que falhou | Verifique se termina com `done` |
| O servo zumbe / esquenta | Travamento ou alvo com emperramento | Envie `x` ou corte a alimentação; verifique limites e folga mecânica |
| O braço bate no corpo durante o auto-endireitamento | Movimento grande do ombro | Verifique `Q_SHOULDER_MAX` e a folga; mantenha a altura da base de ~68 mm |
| `up` não corresponde à pose real (tilt persistente de 5°+ enquanto deitado) | Offsets de zero do acelerômetro não calibrados | Coloque o robô nivelado e envie `c` (veja a [página 06, 6.2](./06-debug-and-calibrate.md)) |
| O braço não repousa no centro visual após retrair | Zero desviou (reindexado/remontado sem rezerar) | Rezere com a [ferramenta da página 05](./05-zero-tool.md) e grave o zero |
| O servo zumbe/vibra após um endireitamento | Autoexcitação transitória do servo analógico após movimentos grandes/travamentos (a saída é constante) | Desaparece sozinho; adicione arruelas de borracha para amortecimento ou use um servo digital; apertar o braço com os dedos silencia na hora |
| Página de status / provisionamento inacessível | Proxy do navegador não contornado, ou hotspot desligado | Adicione `192.168.4.1` às exceções do proxy; envie `w` para ativar o WiFi |

## 10.2 Comandos de segurança

| Situação | Comando |
|---|---|
| Parar o movimento imediatamente | `s` (mantém o último alvo) ou `x` (desacopla o PWM, libera o torque) |
| Recuperar após `x` | `r` reinicializa o PWM e centraliza |
| Uma junta se move na direção errada | inversão de sinal com `v` (ombro) / `b` (cotovelo) |

## 10.3 Capturando uma falha

Guarde a parte correspondente de `logs/hw_monitor.log`. As linhas principais são:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```

---

[← Voltar ao índice do tutorial](./index.md)
