---
title: 07 Utilização e monitorização do auto-endireitamento
description: Como operar o SR-Support em cada direção de queda, tempos de movimento esperados, eventos série e registos de monitorização.
---

# 07 Utilização e monitorização do auto-endireitamento

> Cada unidade acabada é testada nas quatro direções antes do envio. Na primeira utilização,
> verifique ainda cada direção uma vez conforme a secção 7.2, para garantir que a unidade está
> saudável após o transporte.

## 7.1 Procedimento

1. Ligue com o robô na vertical e aguarde `autorun on: get-up waits for a fall`;
2. Derrube o robô em qualquer direção, **largue-o e mantenha-o imóvel durante cerca de 0.5 s**;
3. Quando aparecer `getup start pose=<pose>`, o executor arranca automaticamente;
4. Em caso de sucesso, o firmware imprime `standing -> executor done` e volta ao estado de
   espera;
5. Se uma execução exceder 14 s, o firmware imprime `executor timeout`; após 1.5 s de
   arrefecimento, a condição de queda volta a disparar e tenta de novo.

## 7.2 Comportamento esperado por direção

| Postura | Mecanismo | Tempo no robô real |
|---|---|---|
| `pitch_neg` (topo → −X) | O cotovelo apoia-se, o curso do ombro alavanca o corpo para cima | ~3 s |
| `pitch_pos` (topo → +X) | O mesmo levantamento; se tombar durante a retração, o replaneamento da postura executa `pitch_pos` de novo | ~5–6 s |
| `roll_pos` (topo → −Y) | Alavanca direta do ombro usando o lado de maior curso | ~3 s |
| `roll_neg` (topo → +Y) | **Pressão direta a todo o curso → bombeamentos de cunha do cotovelo ×2 → nova tentativa whip-slam se necessário**; sem rolamento | ~2–6 s |

> O firmware anterior rolava o `roll_neg` por cima e replaneava para um levantamento de pitch
> (5–14 s); a compilação atual usa o espelho da pressão de +Y, pelo que as quatro direções são
> simétricas e de velocidade comparável. Um `executor re-plan roll_neg -> ...` ocasional
> significa apenas que essa pressão falhou e que o mecanismo de recurso entrou em ação — é a
> rede de segurança normal.

## 7.3 Lógica do executor (no firmware)

- 20 ticks (0.4 s) por waypoint de referência, interpolação linear; limite de slew da saída
  0.08 rad/tick;
- Após os waypoints, retrair o braço para o neutro a 0.033 rad/tick;
- Concluído quando `up_z > 0.95` com o alvo em zero durante 50 ticks;
- Se o corpo assentar noutro eixo deitado (`up_z<0.6`, `|ω|<0.8` durante 15 ticks), retrair para
  o neutro e mudar para a referência da nova postura (até 5 mudanças);
- A referência do `roll_neg` usa **esperas adaptativas por etapa**: as etapas de
  pressão/bombeamento esperam enquanto `up_z<0.92`, até um limite de ticks por etapa (pressão
  40 / bombeamento 30 / bombeamento 30 / whip 40 / final 90); se o corpo ficar na vertical a
  meio da sequência, o executor salta diretamente para a retração, para que as etapas seguintes
  não possam derrubar o robô já de pé.

## 7.4 Monitorização e registos

```bash
python tools/hw_monitor.py COM27
```

(Execute-o na pasta `SR-Support` com o `.venv` ativado — [página 02](./02-environment.md). Feche
primeiro qualquer assistente/monitor série; as ferramentas de série / a transferência do
UartAssist para Windows estão na [página 03, secção 3.3](./03-build-flash.md).)

- Acrescenta eventos e resumos de telemetria de 5 segundos a `logs/hw_monitor.log`;
- Regista `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost`, etc.;
- Verifica o envelope dos servos (ombro `[-1.85,+1.82]`, cotovelo `±1.55`) e escreve
  `!! VIOLATION`;
- Enquanto o executor corre, imprime uma linha de traço a cada 0.2 s:

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Campo | Significado |
|---|---|
| `pose` | Postura de referência atual |
| `ph` / `tick` | Fase do waypoint / tick dentro da fase |
| `tgt` | Ângulos-alvo das juntas |
| `up` | Vetor up atual |
| `q` | Comando atual das juntas |
| `sw` | Número de mudanças de postura até ao momento |

> Abrir o monitor reinicia o ESP32; feche-o antes de gravar.

## 7.5 Registo dos testes

Para cada teste, registe a postura, se terminou com `done`, a duração, o número de mudanças e
quaisquer violações. `logs/hw_monitor.log` é o registo de referência.

---

[← Voltar ao índice do tutorial](./index.md)
