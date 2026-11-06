---
title: 06 Depuração e calibração
description: Formato da telemetria, verificações da IMU e dos servos, calibração do giroscópio+acelerómetro, verificação do centro, quatro posturas deitadas e a condição de queda, critérios de conclusão.
---

# 06 Depuração e calibração

> **Os utilizadores de unidades acabadas podem saltar esta página**: a fábrica calibra e
> verifica cada unidade. Repita estes passos apenas após substituir um servo/IMU, remontar um
> horn, ou quando se suspeitar que uma atualização de firmware perturbou a calibração.

Esta é a **verificação funcional e calibração do robô completo** após a montagem, a gravação e o
ponto zero; percorra-a por ordem antes de utilizar o robô.

> **Alimentação durante a depuração**: o USB transporta apenas dados de série. O `c` só precisa
> da IMU (os servos podem ficar sem alimentação); o `t` / `z` / `e` precisam do barramento de
> 5 V dos servos ligado. Se não quiser o ESP32 alimentado por duas fontes, desligue o ramo de
> 5 V para o ESP32, alimente-o apenas por USB e deixe a fonte de 5 V alimentar só os servos —
> uma configuração normal, ver [página 04, secção 4.4](./04-assembly.md).

## 6.1 Abrir a porta série e ler a telemetria

Na pasta `SR-Support` com o `.venv` ativado, abra a porta série (`COM27` é a sua porta):

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(As ferramentas de série / a transferência do UartAssist para Windows estão na
[página 03, secção 3.3](./03-build-flash.md).)

Após abrir a porta, se a placa acabou de ser ligada ou se premiu RST, verá primeiro o registo de
arranque; se não houver registo de arranque, prima RST uma vez. Depois, uma linha de telemetria a
cada 250 ms:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Campo | Significado | Como ler |
|---|---|---|
| `up` | Vetor up do mundo em coordenadas do corpo (x para a frente, y para a esquerda, z para cima) | na vertical `(0,0,1)`, tilt≈0°; posturas deitadas em 6.5 (por exemplo, `(-1,0,0)`=pitch_pos) |
| `w` | Velocidade angular (rad/s) | ≈0 em repouso; não nula durante o levantamento/rolamento; a condição de queda exige `|w|<0.9` |
| `q` | Ângulos de **comando** atuais das juntas (ombro, cotovelo, rad; sem realimentação) | q=0 é o braço vertical; ombro + → braço grande para −Y, cotovelo + → antebraço para +X |
| `qd` | Taxas de comando das juntas | raramente necessário |
| `mode` | Modo de execução | `run` / `hold` / `manual` / `auto` |

Exemplos de leitura (janela do `hw_watch`):

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

O `tilt` é o ângulo entre o vetor up e a vertical (a partir de `up_z`); 0° significa totalmente
vertical.

Se o fluxo contínuo for difícil de ler, use a janela ao vivo de linhas fixas (os comandos
continuam a funcionar):

```bash
python tools/hw_watch.py --port COM27
```

Redesenha no local o up/tilt, a velocidade angular, os ângulos das juntas, o modo e o último
evento; escreva em `cmd>` e prima Enter para enviar um comando, e os eventos também são
acrescentados a `logs/hw_watch.log`. Para uma execução completa de levantamento em que cada
linha em bruto importa, continue a usar o `pio device monitor` ou o `tools/hw_monitor.py` (este
último escreve um resumo no registo a cada 5 s).

**Como enviar comandos série**: mantenha o monitor aberto e escreva o comando seguido de Enter
(os comandos de um único carácter não precisam de aspas). Comandos usados nesta página:

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

A tabela completa de comandos está na [página 03, secção 3.4](./03-build-flash.md).

**Script de autoverificação rápida** (feche primeiro o monitor série para libertar a porta):

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

O primeiro comando lê 0.6 s de telemetria; durante `--tilt 8`, incline o robô à mão e o script
imprime os intervalos de up/giroscópio e o intervalo de tilt, o que revela uma IMU presa ou mal
orientada.

## 6.2 Verificações e calibração da IMU

O `c` faz duas coisas:

1. **Viés zero do giroscópio**: faz a média de 200 amostras em repouso (cerca de 2 s) para o
   offset de taxa zero; é usado no ciclo de alimentação atual e é refeito automaticamente em
   cada arranque;
2. **Zero do acelerómetro**: a partir das mesmas amostras, faz a média do vetor gravidade,
   exigindo que o robô esteja nivelado (gravidade inteiramente em +Z), valida-o e guarda-o na
   NVS (recarregado no arranque).

Procedimento (a alimentação dos servos não é necessária):

1. Faça primeiro a verificação da orientação mecânica da
   [página 04, secção 4.5](./04-assembly.md) (eixo do ombro para o −Y da IMU, eixo do cotovelo
   para o +X da IMU);
2. Coloque o robô na vertical sobre uma mesa NIVELADA, sem mãos, sem cabos a puxar;
3. Escreva `c` e prima Enter no monitor série ou no `cmd>` do `hw_watch`:

   ```text
   c
   ```

4. Fique imóvel cerca de 2 s; o sucesso imprime:

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

5. `accel cal rejected: |a|=...` significa que o robô não estava nivelado ou não estava imóvel
   (a norma da gravidade afasta-se mais de 1.5 m/s² de 9.8); o viés fica inalterado — coloque-o
   de novo e reenvie `c`.

Verificação:

- Incline lentamente para a esquerda/direita e para a frente/trás: as componentes x/y do `up`
  têm de acompanhar suavemente; se uma direção estiver invertida, envie `i` / `j` para inverter
  o sinal do eixo da IMU e execute `c` de novo;
- Deite o robô e espere 2 s: o `up` tem de corresponder à tabela de posturas deitadas em 6.5
  (por exemplo, `(0,-1,0)` = roll_neg) com a face da base apoiada;
- Um tilt persistente de 5° ou mais com o robô deitado normalmente significa que o zero do
  acelerómetro está errado — repita esta secção.

> As unidades acabadas são calibradas na fábrica (guardado na NVS); repita isto apenas após
> substituir/remontar a IMU ou quando a postura deitada estiver visivelmente inclinada. O `c` só
> calibra a IMU — não altera o zero dos servos (isso é a [página 05](./05-zero-tool.md)).
>
> Se usou comandos manuais antes de calibrar (a telemetria termina em `manual`), o `c` deixa o
> robô em `hold`/`manual` e a condição de queda não iniciará um levantamento; mantenha-o na
> vertical e envie `g` para retomar, ou reinicie a placa.

## 6.3 Verificações dos servos e autoteste de direções

| Verificação | Método | Esperado |
|---|---|---|
| Centros | `k` | `centers: shoulder 1681 us, elbow 1456 us` (valores do centro visual gravados em 2026-11; refaça o ponto zero conforme a [página 05](./05-zero-tool.md)) |
| Ajuste fino do ombro | `o` / `p` (±10 µs) | Braço vertical em `q=0` |
| Direção | `m 0.5 0` / `m 0 0.5` | Ombro + → braço grande para −Y; cotovelo + → antebraço para +X |
| Inversão de sinal | `v` (ombro) / `b` (cotovelo) | Apenas se uma direção estiver invertida |
| Autoteste | `t` | Pequeno movimento nas duas juntas, depois centrar |
| Neutro | `m 0 0` ou `r` | Braço vertical |

Limites das juntas:

- Comandos manuais do ombro `[-1.85, +1.82]` rad; cotovelo mecânico `±1.55` rad (alcançável
  pelo executor);
- Os comandos manuais `m` limitam o cotovelo a `[-0.90, +0.70]` rad;
- Saída PWM de 500–2500 µs a 50 Hz.

Escreva estes comandos um a um na **caixa de envio** do monitor/assistente série (Enter após
cada um):

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Confirme: ombro `q>0` → braço grande para **−Y**; cotovelo `q>0` → antebraço para **+X**.
Direção errada: inverta com `v` / `b`, ou remonte o horn.

## 6.4 Verificação do centro

Gravado na fábrica (ombro 1681 µs / cotovelo 1456 µs) — **pode saltar-se numa unidade pronta**.
Numa montagem DIY isto já foi feito com a
[calibração do ponto zero da página 05](./05-zero-tool.md) e os valores gravados no `config.h`
(volte a gravar se mudaram); aqui basta executar `k` para confirmar que os centros correspondem
aos valores gravados. Volte à página 05 apenas após reindexar um horn, remontar, ou se o braço
já não assentar no centro visual.

## 6.5 As quatro posturas deitadas e a condição de queda

| Postura | `up` no monitor | Significado físico |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | O topo do corpo aponta para +X |
| `pitch_neg` | `(+1, 0, 0)` | O topo do corpo aponta para −X |
| `roll_pos` | `(0, +1, 0)` | O topo do corpo aponta para −Y |
| `roll_neg` | `(0, -1, 0)` | O topo do corpo aponta para +Y |

Condição de queda (firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Só então imprime `getup start pose=...` e começa. Por isso, coloque o robô, largue-o e mantenha-o
imóvel durante ~0.5 s; agitá-lo logo após o colocar normalmente significa que uma mão ainda o
está a tocar ou que o corpo ainda está a rolar.

Verificação: coloque o robô em cada uma das quatro posturas, largue e mantenha imóvel; em 0.5 s
o registo série deve mostrar `getup start pose=<matching pose>`.

## 6.6 Critérios de conclusão

- [ ] `c` imprime `accel bias ... (saved)`;
- [ ] `t` mostra as direções corretas nas duas juntas;
- [ ] `k` corresponde aos centros gravados (ou refez o ponto zero conforme a página 05 e
      gravou-o);
- [ ] as quatro posturas deitadas desencadeiam `getup start`.

---

[← Voltar ao índice do tutorial](./index.md)
