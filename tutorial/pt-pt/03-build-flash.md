---
title: 03 Gravar o firmware principal
description: Gravar o firmware SR-Support B-line a partir do bin pré-compilado (Flash Download Tool / esptool) ou compilá-lo com PlatformIO; comandos série e registo de arranque.
---

# 03 Gravar o firmware principal

> **Os utilizadores de unidades acabadas podem saltar esta página**: a fábrica já gravou e
> verificou o firmware. Só precisa de repetir isto para atualizações de firmware ou após
> alterar o código. Os clientes usam a imagem pré-compilada (3.1, sem PlatformIO); os
> programadores compilam a partir do código-fonte (3.2).

## 3.1 Gravar a imagem pré-compilada (recomendado para clientes)

1. Certifique-se de que tem `firmware/releases/sr_support_b_ptk_factory.bin` (somas de
   verificação em `SHA256SUMS`, ao lado);
2. Entre no modo de transferência: mantenha **BOOT** premido, toque em **RST**, liberte
   **BOOT**;
3. Grave-o (preparação das ferramentas na [página 02, secção 2.4](./02-environment.md); execute
   estes comandos na pasta `SR-Support` com o `.venv` ativado):
   - Windows com interface gráfica: Flash Download Tool → ESP32-S3 → carregue o bin em `0x0` → START;
   - Linha de comandos em Windows / Linux / macOS:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Prima RST quando terminar e leia o registo como em 3.3.

> Para gravação / depuração série pode alimentar o ESP32 por USB e deixar a fonte de 5 V apenas
> para os servos (as duas opções de alimentação estão na [página 04, secção 4.4](./04-assembly.md)).

> O comando é **idêntico em Windows / Linux / macOS**; só muda a porta:
> `COM27` no Windows, `/dev/ttyACM0` no Linux, `/dev/tty.usbmodem*` no macOS.
> O Flash Download Tool só existe para Windows; nas outras plataformas use a linha de comandos
> do esptool.

> A centragem na montagem não precisa de uma segunda imagem: após gravar esta, ligue — ambos os
> servos vão para o zero do firmware (1681 / 1456 µs) — depois desligue e instale os horns
> ([página 04, secção 4.2](./04-assembly.md)). Opcionalmente, envie `e` para os colocar primeiro
> no centro elétrico de 1520 µs (equivalente).

## 3.2 Compilar e gravar a partir do código-fonte (programadores)

Ambiente: [página 02, secção 2.5](./02-environment.md). Projeto:
`firmware/sr_support_b_ptk/` (ambiente `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Execute estes comandos na pasta `SR-Support` com o `.venv` ativado (página 02, secção 2.3);
> são idênticos nas três plataformas — substitua `COM27` em `--upload-port` pela sua porta.
> Feche tudo o que estiver a ocupar a porta série (monitor série, `tools/hw_monitor.py`) antes
> de gravar, caso contrário obtém `could not open port` / `Access is denied`.

Uma compilação bem-sucedida usa cerca de 56% de RAM e 30% de Flash (WiFi + servidor web
incluídos; compilações anteriores sem WiFi usavam cerca de 7% / 12%).

## 3.3 Monitor série

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Igual nas três plataformas; substitua `COM27` pela sua porta.)

> **Assistente série com interface gráfica para Windows (opcional)**: o UartAssist do 野人家园
> (gratuito, um único exe, apenas Windows). Página oficial
> <https://cmsoft.cn/resource/101.html>, entrada oficial de transferência
> <https://cmsoft.cn/resource/download/101>. Selecione a porta COM, **115200, 8N1, sem
> controlo de fluxo**, ative «send newline»; observe o registo de arranque/telemetria no painel
> de receção e escreva comandos na caixa de envio. Transfira-o apenas a partir da ligação
> oficial (os sites de terceiros incluem frequentemente adware); não faça commit do exe neste
> repositório.

**Visualizadores de porta série para Linux / macOS (escolha um)**:

- Preferido: o comando `pio device monitor` acima (instalado com o projeto, multiplataforma);
- CLI leve: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` no macOS; sair com `Ctrl-]`); o `screen /dev/ttyACM0 115200`
  integrado também funciona (sair com `Ctrl-A`, depois `K`);
- Interface gráfica: **CoolTerm** (gratuito, Windows/macOS/Linux, site oficial
  <https://freeware.the-meiers.org>); no Linux também pode usar `sudo apt install cutecom`.

> No Linux, adicione o seu utilizador ao grupo `dialout`: `sudo usermod -aG dialout $USER`,
> depois termine sessão e volte a entrar.

Após abrir a porta, se a placa acabou de ser ligada ou se premiu RST, verá primeiro o registo de
arranque; caso contrário, prima RST uma vez. Após o reset deverá ver:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Comandos série (115200)

Escreva cada comando na **caixa de envio** do monitor/assistente série e prima Enter (ative
«send newline» no UartAssist); o comando `m` precisa de um espaço e dois valores, por exemplo
`m 0.5 0`.

| Comando | Função |
|---|---|
| `g` | Iniciar/continuar a execução (esta compilação arranca automaticamente; normalmente não é necessário) |
| `s` | Parar o executor, manter o último alvo |
| `x` | Libertação de emergência: desativa o PWM; rearma com `r` |
| `r` | Reinicializar o PWM e centrar |
| `t` | Autoteste dos servos (movimento pequeno) |
| `c` | Calibrar o giroscópio + **offsets de zero do acelerómetro** (o robô tem de estar NA HORIZONTAL e imóvel; guardado na NVS) |
| `m <q1> <q2>` | Alvos manuais das juntas em rad |
| `1/2` | Ombro manual ±0.5 rad |
| `3/4` | Cotovelo manual ±0.5 rad |
| `0` | Neutro manual |
| `l` | Registo rápido de 3 s a 50 Hz |
| `k` | Imprimir as larguras de impulso centrais dos dois servos |
| `o` / `p` | Ajuste fino do centro do ombro ±10 µs |
| `z` | Zero tipo encoder: a postura atual passa a q=0 para ambas as juntas; imprime os novos impulsos (apenas em RAM; ver [página 05](./05-zero-tool.md)) |
| `e` | Centro elétrico (opcional): ambos os servos a 1520 µs para montar os horns no centro elétrico; o habitual é ligar até ao zero do firmware e montar aí (ver [página 04, 4.2](./04-assembly.md)) |
| `d` | Alternar o fluxo do gémeo a 50 Hz (gémeo MuJoCo; o mesmo interruptor na página de estado) |
| `w` | Alternar o WiFi (hotspot + página de estado/aprovisionamento, ver [página 08](./08-wifi.md)) |
| `v` / `b` | Inverter o sinal do ombro / do cotovelo |
| `i` / `j` | Inverter o sinal X / Y da IMU |
| `h` | Alternar a homing vertical (caminho de política legado) |
| `a` | Modo de teste de levantamento com script legado |

## 3.5 Comportamento na ligação

O firmware define `AUTORUN_ON_BOOT`: após a ligação, o executor espera que o robô esteja
**completamente caído e imóvel** durante 0.5 s e depois arranca automaticamente — não é preciso
`g`. Ligue com o robô na vertical.

---

[← Voltar ao índice do tutorial](./index.md)
