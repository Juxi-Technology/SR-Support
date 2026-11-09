---
title: 08 Página de estado WiFi e aprovisionamento
description: Hotspot, página de estado e aprovisionamento da rede doméstica; a simulação MuJoCo e o gémeo ao vivo são abordados na página 09.
---

# 08 Página de estado WiFi e aprovisionamento

Este passo é opcional e não é necessário para o auto-endireitamento em si. A janela de
simulação MuJoCo e o gémeo ao vivo têm a sua própria página: [página 09](./09-mujoco.md).

## 8.1 Hotspot e página de estado

Hotspot: SSID `SR-Support`, palavra-passe `srsupport`, endereço `192.168.4.1` (o `w` alterna-o;
ativo por omissão no arranque). O `w` é enviado por série: escreva `w` na caixa de envio do
monitor/assistente série e prima Enter; as ferramentas de série / a transferência do UartAssist
para Windows estão na [página 03, secção 3.3](./03-build-flash.md).

Ligue-se ao hotspot e abra `http://192.168.4.1` (os telemóveis normalmente abrem o portal
automaticamente). A página atualiza-se a cada 300 ms: estado, vetor up e barra de verticalidade,
comandos das juntas, postura/fase do levantamento, estado do WiFi doméstico e o interruptor do
fluxo do gémeo (espelho ao vivo na [página 09](./09-mujoco.md)). Se o navegador usar um proxy,
adicione uma exceção para este endereço.

![Figura 8-1 A página de estado do robô](../images/sr-support/wifi/01-status-page.png)

*Figura 8-1: a página de estado do robô (aberta no navegador no endereço do robô). Nesta captura o robô aderiu à rede WiFi doméstica: o cartão Home WiFi mostra o estado da ligação e o Robot IP, com o interruptor do fluxo do gémeo por baixo (utilização em 9.2).*

## 8.2 Aprovisionamento (aderir ao WiFi doméstico)

Na página de estado, use o cartão Home WiFi: `Scan` → escolha uma rede → introduza a
palavra-passe → `Connect`. Em caso de sucesso, o ESP32 passa a AP+STA:

- o hotspot mantém-se ativo (o trabalho de bancada não é afetado);
- o robô fica acessível na LAN doméstica (a página mostra o `Robot IP`; use esse endereço no comando do gémeo da página 09);
- as credenciais são guardadas na NVS e a ligação é refeita automaticamente no arranque.

Apenas 2.4 GHz; as pesquisas/ligações são recusadas enquanto um levantamento está em curso.

---

[← Voltar ao índice do tutorial](./index.md)
