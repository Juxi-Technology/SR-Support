---
title: 08 Página de status WiFi e provisionamento
description: Hotspot, página de status e provisionamento de WiFi doméstico; a simulação MuJoCo e o gêmeo ao vivo são abordados na página 09.
---

# 08 Página de status WiFi e provisionamento

Esta etapa é opcional e não é necessária para o auto-endireitamento em si. A janela de
simulação MuJoCo e o gêmeo ao vivo têm página própria: [página 09](./09-mujoco.md).

## 8.1 Hotspot e página de status

Hotspot: SSID `SR-Support`, senha `srsupport`, endereço `192.168.4.1` (`w` o alterna; ligado por
padrão na inicialização). `w` é enviado pela serial: digite `w` na caixa de envio do
monitor/assistente serial e pressione Enter; as ferramentas seriais / o download do UartAssist
para Windows estão na [página 03, seção 3.3](./03-build-flash.md).

Conecte-se ao hotspot e abra `http://192.168.4.1` (os celulares geralmente abrem o portal
automaticamente). A página é atualizada a cada 300 ms: estado, vetor "para cima" e barra de
verticalidade, comandos das juntas, pose/fase do endireitamento, estado do WiFi doméstico e o
interruptor do fluxo do gêmeo (espelho ao vivo na [página 09](./09-mujoco.md)). Se o navegador
usar um proxy, adicione uma exceção para este endereço.

![Figura 8-1 A página de status do robô](../images/sr-support/wifi/01-status-page.png)

*Figura 8-1: a página de status do robô (aberta no navegador no endereço do robô). Nesta captura o robô entrou na rede WiFi doméstica: o cartão Home WiFi mostra o estado da conexão e o Robot IP, com o interruptor do fluxo do gêmeo logo abaixo (uso em 9.2).*

## 8.2 Provisionamento (entrar no WiFi doméstico)

Na página de status, use o cartão Home WiFi: `Scan` → escolha uma rede → digite a senha →
`Connect`. Em caso de sucesso, o ESP32 opera em AP+STA:

- o hotspot permanece ativo (o trabalho de bancada não é afetado);
- o robô é acessível na LAN doméstica (a página mostra o `Robot IP` dele; use esse endereço no comando do gêmeo da página 09);
- as credenciais são armazenadas na NVS e a conexão é refeita automaticamente na inicialização.

Somente 2.4 GHz; varreduras/conexões são recusadas enquanto um endireitamento está em execução.

---

[← Voltar ao índice do tutorial](./index.md)
