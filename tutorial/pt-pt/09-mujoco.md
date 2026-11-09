---
title: 09 Simulação MuJoCo e o gémeo ao vivo
description: A janela de simulação MuJoCo local (repetição do levantamento nas quatro posturas), o gémeo ao vivo por WiFi do robô real e o registo de telemetria.
---

# 09 Simulação MuJoCo e o gémeo ao vivo

O MuJoCo é usado de duas formas neste projeto, ambas com `hardware/v1/robot_v1.xml` (o modelo
do robô real a partir da mesma fonte):

- **Simulação local**: sem robô ligado, repita em ciclo as quatro posturas deitadas e os
  respetivos levantamentos no computador, para validar as sequências de referência e observar o
  movimento;
- **Gémeo ao vivo**: o robô real transmite a sua atitude por WiFi e a janela do MuJoCo espelha o
  movimento real em tempo real (um gémeo digital).

A janela funciona da mesma forma nos dois casos: arrastar com o botão esquerdo roda a vista,
arrastar com o botão direito desloca e a roda faz zoom. Antes da primeira utilização, crie e
ative o `.venv` como na [página 02](./02-environment.md) e instale nele as dependências das
ferramentas (`pip install -r tools/requirements.txt`, ver página 02).

## 9.1 Janela de simulação local

Na pasta `SR-Support` (`.venv` ativado):

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

A janela tem o título `MuJoCo : sr_support_v1` (figura 9-1). O robô é colocado sucessivamente
nas quatro posturas deitadas (`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`); de cada vez,
o executor executa a sequência de referência com exatamente os parâmetros do firmware até o
robô se levantar, e em seguida é definida a postura seguinte. O ciclo repete-se até fechar a
janela. O terminal imprime a postura e o resultado:

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` significa que a postura se levantou em simulação. Se obtiver `ok=False`, verifique a
sequência de referência e quaisquer parâmetros que tenha alterado face à
[página 06](./06-debug-and-calibrate.md).

![Figura 9-1 A janela de simulação MuJoCo (repetição do levantamento nas quatro posturas)](../images/sr-support/mujoco/01-mujoco-window.png)

*Figura 9-1: um fotograma do ciclo das quatro posturas - o executor levanta uma postura deitada.*

> Diferença conhecida do modelo: com o modelo de massa 1×, o `roll_neg` imprime `ok=False` em
> simulação (a massa/atrito do braço do modelo difere do robô real, ver
> [página 11](./11-reference.md) 11.4); isto não afeta o firmware real.

## 9.2 Gémeo ao vivo por WiFi

Pré-requisito: o robô aderiu à rede doméstica como na [página 08](./08-wifi.md) e o computador
está na mesma rede. A página de estado mostra o endereço do robô como `Robot IP`; copie-o para
o comando abaixo.

1. Na página de estado, prima `Twin ON` (o mesmo que `d` na série);
2. Na pasta `SR-Support` com o `.venv` ativado, execute (substitua o endereço pelo `Robot IP`
   da página de estado):

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

O modelo espelha a atitude real ao vivo (fluxo de quaterniões a 50 Hz) e mantém o corpo no
chão; o braço é mantido no seu ângulo de contacto com o chão como o servo bloqueado, pelo que
nunca penetra o chão.

- Computador ligado diretamente ao hotspot do robô: o endereço é sempre `192.168.4.1`,
  `python tools/live_twin.py --tcp 192.168.4.1:3333`;
- Alternativa com fios: `python tools/live_twin.py --port COM27` (a ferramenta envia `d` para
  ativar o fluxo automaticamente);
- Reprodução offline: `python tools/live_twin.py --replay logs/hw_fast_xxx.txt`;
- O gémeo é apenas de leitura, com exceção de alternar o fluxo: nunca envia comandos de
  controlo.

## 9.3 Registo de telemetria

```bash
python tools/tcp_log.py
```

Guarda o fluxo de telemetria em `logs/wifi_<time>.txt` para reprodução offline (`--replay`) e
análise de falhas. No hotspot liga-se por omissão a `192.168.4.1:3333`; na rede doméstica,
passe o `Robot IP` da página de estado:

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 Referência de simulação e treino

`training/b_line/` inclui o executor, as sequências de referência e o ambiente de simulação —
idênticos valor a valor ao firmware — para reprodução, validação e afinação de parâmetros; os
ficheiros de modelo estão descritos na [página 11](./11-reference.md) 11.1.

---

[← Voltar ao índice do tutorial](./index.md)
