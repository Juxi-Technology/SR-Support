---
title: 09 Simulação MuJoCo e o gêmeo ao vivo
description: A janela local de simulação MuJoCo (reprodução do endireitamento nas quatro poses), o gêmeo ao vivo do robô real por WiFi e o registro de telemetria.
---

# 09 Simulação MuJoCo e o gêmeo ao vivo

O MuJoCo é usado de duas maneiras neste projeto, ambas com `hardware/v1/robot_v1.xml` (o
modelo do robô real, da mesma fonte de projeto):

- **Simulação local**: sem robô conectado, reproduza em loop as quatro poses deitadas e seus
  endireitamentos no computador para validar as sequências de referência e acompanhar o movimento;
- **Gêmeo ao vivo**: o robô real transmite sua atitude por WiFi e a janela MuJoCo espelha o
  movimento real em tempo real (um gêmeo digital).

A janela funciona da mesma forma nos dois casos: arrastar com o botão esquerdo gira a visão,
arrastar com o botão direito desloca e a roda aplica zoom. Antes do primeiro uso, crie e ative o
`.venv` como na [página 02](./02-environment.md) e instale nele as dependências das ferramentas
(`pip install -r tools/requirements.txt`, veja a página 02).

## 9.1 Janela de simulação local

Na pasta `SR-Support` (com o `.venv` ativado):

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

A janela tem o título `MuJoCo : sr_support_v1` (figura 9-1). O robô é colocado, por vez, nas
quatro poses deitadas (`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`); a cada vez, o
executor executa a sequência de referência com exatamente os parâmetros do firmware até o robô
ficar em pé, e então a próxima pose é definida. O ciclo se repete até você fechar a janela.
O terminal imprime a pose e o resultado:

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` significa que a pose se levantou na simulação. Em `ok=False`, verifique a sequência
de referência e quaisquer parâmetros que você alterou conforme a [página 06](./06-debug-and-calibrate.md).

![Figura 9-1 A janela de simulação MuJoCo (reprodução do endireitamento nas quatro poses)](../images/sr-support/mujoco/01-mujoco-window.png)

*Figura 9-1: um quadro do ciclo das quatro poses - o executor levanta uma pose deitada.*

> Diferença conhecida do modelo: com o modelo de massa 1×, `roll_neg` imprime `ok=False` na
> simulação (massa/atrito do braço do modelo diferem do robô real, veja a
> [página 11](./11-reference.md) 11.4); isso não afeta o firmware do robô real.

## 9.2 Gêmeo ao vivo por WiFi

Pré-requisito: o robô entrou na rede doméstica como na [página 08](./08-wifi.md) e o computador
está na mesma rede. A página de status mostra o endereço do robô como `Robot IP`; copie-o para
o comando abaixo.

1. Na página de status, pressione `Twin ON` (o mesmo que `d` na serial);
2. Na pasta `SR-Support` com o `.venv` ativado, execute (troque o endereço pelo `Robot IP` da
   página de status):

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

O modelo espelha a atitude real ao vivo (fluxo de quatérnios a 50 Hz) e mantém o corpo no
chão; o braço é mantido no ângulo de contato com o chão, como o servo travado, de modo que
nunca penetra o chão.

- Computador ligado diretamente ao hotspot do robô: o endereço é sempre `192.168.4.1`,
  `python tools/live_twin.py --tcp 192.168.4.1:3333`;
- Alternativa com fio: `python tools/live_twin.py --port COM27` (a ferramenta envia `d`
  para habilitar o fluxo automaticamente);
- Reprodução offline: `python tools/live_twin.py --replay logs/hw_fast_xxx.txt`;
- O gêmeo é somente leitura, exceto por alternar o fluxo: ele nunca envia comandos de controle.

## 9.3 Registro de telemetria

```bash
python tools/tcp_log.py
```

Salva o fluxo de telemetria em `logs/wifi_<time>.txt` para reprodução offline (`--replay`) e
análise de falhas. No hotspot conecta-se por padrão a `192.168.4.1:3333`; na rede doméstica,
passe o `Robot IP` da página de status:

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 Referência de simulação e treinamento

`training/b_line/` inclui o executor, as sequências de referência e o ambiente de simulação —
idênticos, valor a valor, aos do firmware — para reprodução, validação e ajuste de parâmetros;
os arquivos do modelo são descritos na [página 11](./11-reference.md) 11.1.

---

[← Voltar ao índice do tutorial](./index.md)
