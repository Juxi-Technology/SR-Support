---
title: 06 Depuração e calibração
description: Formato da telemetria, verificações de IMU e servos, calibração do giroscópio + acelerômetro, verificação de centralização, quatro poses deitadas e a condição de queda, critérios de conclusão.
---

# 06 Depuração e calibração

> **Usuários de unidades prontas podem pular esta página**: a fábrica calibra e verifica cada
> unidade. Refaça estes passos apenas após substituir um servo/IMU, remontar um horn, ou quando
> suspeitar que uma atualização de firmware perturbou a calibração.

Esta é a **verificação funcional e calibração do robô completo** após a montagem, a gravação e a
zeragem; percorra-a em ordem antes de usar o robô.

> **Alimentação durante a depuração**: o USB transporta apenas dados seriais. `c` precisa somente
> da IMU (os servos podem ficar sem alimentação); `t` / `z` / `e` precisam do trilho de 5 V dos
> servos ligado. Se você não quiser o ESP32 alimentado por duas fontes, desconecte o ramo de 5 V
> para o ESP32, alimente-o somente pelo USB e deixe a fonte de 5 V alimentar apenas os servos —
> uma configuração normal, veja a [página 04, seção 4.4](./04-assembly.md).

## 6.1 Abra a porta serial e leia a telemetria

Na pasta `SR-Support` com o `.venv` ativado, abra a porta serial (`COM27` é a sua porta):

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(As ferramentas seriais / o download do UartAssist para Windows estão na
[página 03, seção 3.3](./03-build-flash.md).)

Após abrir a porta, se a placa acabou de ser energizada ou você pressionou RST, você verá primeiro
o log de inicialização; se não houver log de inicialização, pressione RST uma vez. Depois, uma
linha de telemetria a cada 250 ms:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Campo | Significado | Como ler |
|---|---|---|
| `up` | Vetor "para cima" do mundo em coordenadas do corpo (x para frente, y para a esquerda, z para cima) | em pé `(0,0,1)`, tilt≈0°; poses deitadas em 6.5 (por exemplo, `(-1,0,0)`=pitch_pos) |
| `w` | Velocidade angular (rad/s) | ≈0 quando parado; diferente de zero ao se levantar/rolar; a condição de queda exige `|w|<0.9` |
| `q` | Ângulos de **comando** atuais das juntas (ombro, cotovelo, rad; sem realimentação) | q=0 é braço vertical; ombro + → braço grande na direção −Y, cotovelo + → antebraço na direção +X |
| `qd` | Taxas de comando das juntas | raramente necessário |
| `mode` | Modo de execução | `run` / `hold` / `manual` / `auto` |

Exemplos de leituras (janela do `hw_watch`):

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

`tilt` é o ângulo entre o vetor "para cima" e a vertical (a partir de `up_z`); 0° significa
totalmente em pé.

Se o fluxo rolante for difícil de ler, use a janela ao vivo de linhas fixas (os comandos
continuam funcionando):

```bash
python tools/hw_watch.py --port COM27
```

Ela redesenha no próprio local o up/tilt, a velocidade angular, os ângulos das juntas, o modo e o
último evento; digite em `cmd>` e pressione Enter para enviar um comando, e os eventos também são
anexados a `logs/hw_watch.log`. Para uma execução completa de endireitamento em que cada linha
bruta importa, continue usando `pio device monitor` ou `tools/hw_monitor.py` (o último grava um
resumo no log a cada 5 s).

**Como enviar comandos seriais**: mantenha o monitor aberto e digite o comando seguido de Enter
(comandos de um único caractere não precisam de aspas). Comandos usados nesta página:

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

A tabela completa de comandos está na [página 03, seção 3.4](./03-build-flash.md).

**Script rápido de autoverificação** (feche primeiro o monitor serial para liberar a porta):

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

O primeiro comando lê 0.6 s de telemetria; durante `--tilt 8`, incline o robô manualmente e ele
imprime as faixas de up/giroscópio e a faixa de tilt, o que revela uma IMU travada ou mal
orientada.

## 6.2 Verificações e calibração da IMU

`c` faz duas coisas:

1. **Bias de zero do giroscópio**: faz a média de 200 amostras paradas (cerca de 2 s) no offset de
   taxa zero; isso é usado no ciclo de energia atual e é refeito automaticamente a cada
   inicialização;
2. **Zero do acelerômetro**: a partir das mesmas amostras, calcula a média do vetor gravidade,
   exigindo que o robô esteja nivelado (gravidade inteiramente em +Z), faz uma verificação de
   sanidade e armazena na NVS (recarregado na inicialização).

Procedimento (a alimentação dos servos não é necessária):

1. Primeiro faça a verificação mecânica da orientação da
   [página 04, seção 4.5](./04-assembly.md) (eixo do ombro para o −Y da IMU, eixo do cotovelo
   para o +X da IMU);
2. Coloque o robô em pé sobre uma mesa NIVELADA, sem tocá-lo, com os cabos sem tração;
3. Digite `c` e pressione Enter no monitor serial ou no `cmd>` do `hw_watch`:

   ```text
   c
   ```

4. Fique imóvel por cerca de 2 s; em caso de sucesso, imprime:

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

5. `accel cal rejected: |a|=...` significa que o robô não estava nivelado ou não estava parado (a
   norma da gravidade está a mais de 1.5 m/s² de 9.8); o bias é mantido inalterado — reposicione e
   envie `c` novamente.

Verificação:

- Incline lentamente para a esquerda/direita e para frente/trás: os componentes x/y de `up` devem
  acompanhar suavemente; se uma direção estiver invertida, envie `i` / `j` para inverter o sinal
  do eixo da IMU e execute `c` novamente;
- Deite o robô e espere 2 s: `up` deve corresponder à tabela de poses deitadas em 6.5 (por
  exemplo, `(0,-1,0)` = roll_neg) com a face da base plana;
- Um tilt persistente de 5°+ enquanto deitado geralmente indica que o zero do acelerômetro está
  errado — refaça esta seção.

> Unidades prontas são calibradas na fábrica (valores armazenados na NVS); refaça isto apenas após
> substituir/remontar a IMU ou quando a pose deitada estiver visivelmente inclinada. `c` calibra
> apenas a IMU — ele não altera o zero dos servos (isso é a [página 05](./05-zero-tool.md)).
>
> Se você usou comandos manuais antes de calibrar (a telemetria termina em `manual`), `c` deixa o
> robô em `hold`/`manual` e a condição de queda não iniciará um endireitamento; mantenha-o em pé
> e envie `g` para retomar, ou reinicie a placa.

## 6.3 Verificações dos servos e autoteste de direção

| Verificação | Método | Esperado |
|---|---|---|
| Centros | `k` | `centers: shoulder 1681 us, elbow 1456 us` (valores do centro visual gravados em 2026-11; rezerar conforme a [página 05](./05-zero-tool.md)) |
| Ajuste do ombro | `o` / `p` (±10 µs) | Braço vertical em `q=0` |
| Direção | `m 0.5 0` / `m 0 0.5` | Ombro + → braço grande na direção −Y; cotovelo + → antebraço na direção +X |
| Inversão de sinal | `v` (ombro) / `b` (cotovelo) | Apenas se uma direção estiver invertida |
| Autoteste | `t` | Movimento pequeno nas duas juntas, depois centraliza |
| Neutro | `m 0 0` ou `r` | Braço vertical |

Limites das juntas:

- Comandos manuais do ombro `[-1.85, +1.82]` rad; cotovelo mecânico `±1.55` rad (alcançável pelo
  executor);
- Comandos manuais `m` limitam o cotovelo a `[-0.90, +0.70]` rad;
- Saída PWM de 500–2500 µs a 50 Hz.

Digite estes comandos um a um na **caixa de envio** do monitor/assistente serial (Enter após cada
um):

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Confirme: ombro `q>0` → braço grande na direção **−Y**; cotovelo `q>0` → antebraço na direção
**+X**. Direção errada: inverta com `v` / `b`, ou remonte o horn.

## 6.4 Verificação de centralização

Gravado na fábrica (ombro 1681 µs / cotovelo 1456 µs) — **dispensável para uma unidade pronta**.
Em um build DIY isso já foi feito com a [calibração de zero da página 05](./05-zero-tool.md) e os
valores gravados no `config.h` (regrave se mudaram); aqui basta executar `k` para confirmar que os
centros correspondem aos valores gravados. Volte à página 05 apenas após reindexar um horn,
remontar, ou se o braço deixar de repousar no centro visual.

## 6.5 As quatro poses deitadas e a condição de queda

| Pose | `up` no monitor | Significado físico |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | O topo do corpo aponta para +X |
| `pitch_neg` | `(+1, 0, 0)` | O topo do corpo aponta para −X |
| `roll_pos` | `(0, +1, 0)` | O topo do corpo aponta para −Y |
| `roll_neg` | `(0, -1, 0)` | O topo do corpo aponta para +Y |

Condição de queda (firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Só então ele imprime `getup start pose=...` e começa. Portanto, posicione o robô, solte-o e
mantenha-o parado por ~0.5 s; balançá-lo logo após posicionar geralmente significa que uma mão
ainda o está tocando ou que o corpo ainda está rolando.

Verificação: coloque o robô em cada uma das quatro poses, solte e mantenha parado; em até 0.5 s o
log serial deve mostrar `getup start pose=<matching pose>`.

## 6.6 Critérios de conclusão

- [ ] `c` imprime `accel bias ... (saved)`;
- [ ] `t` mostra as direções corretas nas duas juntas;
- [ ] `k` corresponde aos centros gravados (ou você rezerou conforme a página 05 e gravou);
- [ ] as quatro poses deitadas acionam `getup start`.

---

[← Voltar ao índice do tutorial](./index.md)
