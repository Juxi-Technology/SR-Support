---
title: 03 Gravar o firmware principal
description: Grave o firmware da linha B do SR-Support a partir do bin pré-compilado (Flash Download Tool / esptool) ou compile-o com PlatformIO; comandos seriais e log de inicialização.
---

# 03 Gravar o firmware principal

> **Usuários de unidades prontas podem pular esta página**: a fábrica já gravou e verificou o
> firmware. Só refaça isto para atualizações de firmware ou após modificar o código. Clientes usam
> a imagem pré-compilada (3.1, sem PlatformIO); desenvolvedores compilam a partir do código-fonte (3.2).

## 3.1 Gravar a imagem pré-compilada (recomendado para clientes)

1. Certifique-se de ter `firmware/releases/sr_support_b_ptk_factory.bin` (checksums em
   `SHA256SUMS`, ao lado);
2. Entre no modo de download: segure **BOOT**, toque em **RST**, solte **BOOT**;
3. Grave-o (configuração da ferramenta na [página 02, seção 2.4](./02-environment.md); execute
   estes comandos na pasta `SR-Support` com o `.venv` ativado):
   - Interface gráfica no Windows: Flash Download Tool → ESP32-S3 → carregue o bin em `0x0` → START;
   - Linha de comando no Windows / Linux / macOS:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Pressione RST ao terminar e leia o log como em 3.3.

> Para gravação / depuração serial, você pode alimentar o ESP32 pelo USB e deixar a fonte de 5 V
> apenas para os servos (as duas opções de alimentação estão na [página 04, seção 4.4](./04-assembly.md)).

> O comando é **idêntico no Windows / Linux / macOS**; só a porta muda:
> `COM27` no Windows, `/dev/ttyACM0` no Linux, `/dev/tty.usbmodem*` no macOS.
> O Flash Download Tool existe apenas para Windows; nos demais sistemas use a linha de comando do esptool.

> A centralização na montagem não precisa de uma segunda imagem: após gravar esta, ligue — os dois
> servos vão para o zero do firmware (1681 / 1456 µs) — depois desligue e instale os horns
> ([página 04, seção 4.2](./04-assembly.md)). Opcionalmente, envie `e` para colocá-los primeiro no
> centro elétrico de 1520 µs (equivalente).

## 3.2 Compilar e gravar a partir do código-fonte (desenvolvedores)

Ambiente: [página 02, seção 2.5](./02-environment.md). Projeto:
`firmware/sr_support_b_ptk/` (ambiente `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Execute-os na pasta `SR-Support` com o `.venv` ativado (página 02, seção 2.3); eles são
> idênticos nas três plataformas — substitua `COM27` em `--upload-port` pela sua porta. Feche
> qualquer coisa que ocupe a porta serial (monitor serial, `tools/hw_monitor.py`) antes de gravar,
> caso contrário você verá `could not open port` / `Access is denied`.

Um build bem-sucedido usa cerca de 56% da RAM e 30% da Flash (WiFi + servidor web incluídos;
builds anteriores sem WiFi ficavam em cerca de 7% / 12%).

## 3.3 Monitor serial

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(O mesmo nas três plataformas; substitua `COM27` pela sua porta.)

> **Assistente serial com interface gráfica no Windows (opcional)**: UartAssist, do 野人家园
> (gratuito, um único exe, apenas Windows). Página oficial
> <https://cmsoft.cn/resource/101.html>, entrada oficial de download
> <https://cmsoft.cn/resource/download/101>. Selecione a porta COM, **115200, 8N1, sem
> controle de fluxo**, habilite "send newline"; acompanhe o log de inicialização/telemetria no
> painel de recepção e digite os comandos na caixa de envio. Baixe apenas pelo link oficial (sites
> de terceiros frequentemente incluem adware); não faça commit do exe neste repositório.

**Visualizadores seriais para Linux / macOS (escolha um)**:

- Preferido: o comando `pio device monitor` acima (instalado com o projeto, multiplataforma);
- CLI leve: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` no macOS; saia com `Ctrl-]`); o `screen /dev/ttyACM0 115200` embutido
  também funciona (saia com `Ctrl-A`, depois `K`);
- Interface gráfica: **CoolTerm** (gratuito, Windows/macOS/Linux, site oficial
  <https://freeware.the-meiers.org>); no Linux você também pode usar `sudo apt install cutecom`.

> No Linux, adicione seu usuário ao grupo `dialout`: `sudo usermod -aG dialout $USER`, depois saia
> e entre novamente.

Após abrir a porta, se a placa acabou de ser energizada ou você pressionou RST, você verá primeiro
o log de inicialização; se não, pressione RST uma vez. Após o reset, você deve ver:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Comandos seriais (115200)

Digite cada comando na **caixa de envio** do monitor/assistente serial e pressione Enter
(habilite "send newline" no UartAssist); o comando `m` precisa de um espaço e dois valores, por
exemplo `m 0.5 0`.

| Comando | Função |
|---|---|
| `g` | Inicia/continua a execução (este build executa automaticamente; geralmente não é necessário) |
| `s` | Para o executor, mantém o último alvo |
| `x` | Liberação de emergência: desacopla o PWM; rearme com `r` |
| `r` | Reinicializa o PWM e centraliza |
| `t` | Autoteste dos servos (movimento pequeno) |
| `c` | Calibra o giroscópio + **offsets de zero do acelerômetro** (o robô deve estar EM PÉ, NIVELADO e parado; armazenado na NVS) |
| `m <q1> <q2>` | Alvos manuais das juntas em rad |
| `1/2` | Ombro manual ±0.5 rad |
| `3/4` | Cotovelo manual ±0.5 rad |
| `0` | Neutro manual |
| `l` | Log rápido de 3 s a 50 Hz |
| `k` | Imprime as larguras de pulso centrais dos dois servos |
| `o` / `p` | Ajuste fino de ±10 µs no centro do ombro |
| `z` | Zero estilo encoder: a pose atual vira q=0 para as duas juntas; imprime os novos pulsos (apenas na RAM; veja a [página 05](./05-zero-tool.md)) |
| `e` | Centro elétrico (opcional): ambos os servos em 1520 µs para montar os horns no centro elétrico; o modo usual é energizar até o zero do firmware e montar ali (veja a [página 04, 4.2](./04-assembly.md)) |
| `d` | Alterna o fluxo do gêmeo a 50 Hz (gêmeo MuJoCo; mesmo interruptor na página de status) |
| `w` | Alterna o WiFi (hotspot + página de status/provisionamento, veja a [página 08](./08-wifi-twin.md)) |
| `v` / `b` | Inverte o sinal do ombro / cotovelo |
| `i` / `j` | Inverte o sinal X / Y da IMU |
| `h` | Alterna o stand-homing (caminho de política legado) |
| `a` | Modo de teste legado de endireitamento por script |

## 3.5 Comportamento na energização

O firmware define `AUTORUN_ON_BOOT`: após a energização, o executor espera o robô ficar
**completamente deitado e parado** por 0.5 s e então inicia automaticamente — sem necessidade de
`g`. Energize com o robô em pé.

---

[← Voltar ao índice do tutorial](./index.md)
