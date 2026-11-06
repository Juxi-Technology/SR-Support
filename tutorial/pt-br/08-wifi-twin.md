---
title: 08 WiFi e o gêmeo de simulação
description: Página de status, provisionamento de WiFi doméstico, o gêmeo MuJoCo ao vivo sem fio e registro de telemetria por WiFi.
---

# 08 WiFi e o gêmeo de simulação

Esta etapa é opcional e não é necessária para o auto-endireitamento em si.

## 8.1 Hotspot e página de status

Hotspot: SSID `SR-Support`, senha `srsupport`, endereço `192.168.4.1` (`w` o alterna; ligado por
padrão na inicialização). `w` é enviado pela serial: digite `w` na caixa de envio do
monitor/assistente serial e pressione Enter; as ferramentas seriais / o download do UartAssist
para Windows estão na [página 03, seção 3.3](./03-build-flash.md).

Conecte-se ao hotspot e abra `http://192.168.4.1` (os celulares geralmente abrem o portal
automaticamente). A página é atualizada a cada 300 ms: estado, vetor "para cima" e barra de
verticalidade, comandos das juntas, pose/fase do endireitamento, estado do WiFi doméstico e o
interruptor do fluxo do gêmeo. Se o navegador usar um proxy, adicione uma exceção para este
endereço.

## 8.2 Provisionamento (entrar no WiFi doméstico)

Na página de status, use o cartão Home WiFi: `Scan` → escolha uma rede → digite a senha →
`Connect`. Em caso de sucesso, o ESP32 opera em AP+STA:

- o hotspot permanece ativo (o trabalho de bancada não é afetado);
- o robô é acessível na LAN doméstica (a página mostra o `Robot IP` dele);
- as credenciais são armazenadas na NVS e a conexão é refeita automaticamente na inicialização.

Somente 2.4 GHz; varreduras/conexões são recusadas enquanto um endireitamento está em execução.

## 8.3 Gêmeo MuJoCo ao vivo sem fio

Pressione `Twin ON` na página de status (o mesmo que `d` na serial) e então:

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(Na pasta `SR-Support`; crie e ative o `.venv` primeiro como na
[página 02](./02-environment.md) — o ambiente das ferramentas também é configurado ali.)

- A janela espelha a atitude real ao vivo e mantém o corpo no chão;
- O braço é mantido no ângulo de contato com o chão, como o servo travado (sem penetração no chão);
- O cabo USB só é necessário para gravação e extração de logs;
- Reproduza um log gravado offline com `--replay <file>`.

## 8.4 Registro de telemetria por WiFi

```bash
python tools/tcp_log.py
```

Salva o fluxo de telemetria do hotspot em `logs/wifi_<time>.txt` para reprodução e análise
offline.

## 8.5 Referência de simulação e treinamento

O repositório inclui o modelo MuJoCo e o código de treinamento (`training/b_line/`) para
reprodução e retreinamento; os arquivos do modelo são descritos na
[página 10](./10-reference.md).

---

[← Voltar ao índice do tutorial](./index.md)
