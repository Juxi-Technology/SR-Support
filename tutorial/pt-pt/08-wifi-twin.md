---
title: 08 WiFi e o gémeo de simulação
description: Página de estado, aprovisionamento da rede doméstica, o gémeo MuJoCo ao vivo sem fios e o registo de telemetria por WiFi.
---

# 08 WiFi e o gémeo de simulação

Este passo é opcional e não é necessário para o auto-endireitamento em si.

## 8.1 Hotspot e página de estado

Hotspot: SSID `SR-Support`, palavra-passe `srsupport`, endereço `192.168.4.1` (o `w` alterna-o;
ativo por omissão no arranque). O `w` é enviado por série: escreva `w` na caixa de envio do
monitor/assistente série e prima Enter; as ferramentas de série / a transferência do UartAssist
para Windows estão na [página 03, secção 3.3](./03-build-flash.md).

Ligue-se ao hotspot e abra `http://192.168.4.1` (os telemóveis normalmente abrem o portal
automaticamente). A página atualiza-se a cada 300 ms: estado, vetor up e barra de verticalidade,
comandos das juntas, postura/fase do levantamento, estado do WiFi doméstico e o interruptor do
fluxo do gémeo. Se o navegador usar um proxy, adicione uma exceção para este endereço.

## 8.2 Aprovisionamento (aderir ao WiFi doméstico)

Na página de estado, use o cartão Home WiFi: `Scan` → escolha uma rede → introduza a
palavra-passe → `Connect`. Em caso de sucesso, o ESP32 passa a AP+STA:

- o hotspot mantém-se ativo (o trabalho de bancada não é afetado);
- o robô fica acessível na LAN doméstica (a página mostra o `Robot IP`);
- as credenciais são guardadas na NVS e a ligação é refeita automaticamente no arranque.

Apenas 2.4 GHz; as pesquisas/ligações são recusadas enquanto um levantamento está em curso.

## 8.3 Gémeo MuJoCo ao vivo sem fios

Prima `Twin ON` na página de estado (o mesmo que `d` na série), depois:

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(Na pasta `SR-Support`; crie e ative primeiro o `.venv` como na
[página 02](./02-environment.md) — o ambiente das ferramentas também é preparado aí.)

- A janela espelha a atitude real ao vivo e mantém o corpo no chão;
- O braço é mantido no seu ângulo de contacto com o chão como o servo bloqueado (sem penetração
  no chão);
- O cabo USB só é necessário para gravar e extrair registos;
- Reproduza um registo gravado offline com `--replay <file>`.

## 8.4 Registo de telemetria por WiFi

```bash
python tools/tcp_log.py
```

Guarda o fluxo de telemetria do hotspot em `logs/wifi_<time>.txt` para reprodução e análise
offline.

## 8.5 Referência de simulação e treino

O repositório inclui o modelo MuJoCo e o código de treino (`training/b_line/`) para reprodução e
novo treino; os ficheiros de modelo estão descritos na [página 10](./10-reference.md).

---

[← Voltar ao índice do tutorial](./index.md)
