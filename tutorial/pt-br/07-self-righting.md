---
title: 07 Uso e monitoramento do auto-endireitamento
description: Como operar o SR-Support em cada direção de queda, tempos de movimento esperados, eventos seriais e logs de monitoramento.
---

# 07 Uso e monitoramento do auto-endireitamento

> Cada unidade pronta é testada nas quatro direções antes do envio. No primeiro uso, verifique
> ainda cada direção uma vez conforme a seção 7.2 para garantir que a unidade está saudável após
> o transporte.

## 7.1 Procedimento

1. Energize com o robô em pé e aguarde `autorun on: get-up waits for a fall`;
2. Derrube o robô em qualquer direção, **solte-o e mantenha-o parado por cerca de 0.5 s**;
3. Quando `getup start pose=<pose>` aparecer, o executor inicia automaticamente;
4. Em caso de sucesso, o firmware imprime `standing -> executor done` e retorna ao modo de
   espera;
5. Se uma execução exceder 14 s, o firmware imprime `executor timeout`; após um cooldown de 1.5 s,
   a condição de queda dispara novamente e tenta de novo.

## 7.2 Comportamento esperado por direção

| Pose | Mecanismo | Tempo no robô real |
|---|---|---|
| `pitch_neg` (topo → −X) | O cotovelo se apoia, o curso do ombro alavanca o corpo para cima | ~3 s |
| `pitch_pos` (topo → +X) | Mesma elevação; se tombar durante a retração, o replanejamento de pose executa `pitch_pos` novamente | ~5–6 s |
| `roll_pos` (topo → −Y) | Alavanca direta do ombro usando o lado de curso longo | ~3 s |
| `roll_neg` (topo → +Y) | **Pressão direta de curso total → bombeamentos de cunha com o cotovelo ×2 → nova tentativa de whip-slam se necessário**; sem rolar | ~2–6 s |

> Firmware anteriores rolavam `roll_neg` por cima e replanejavam para uma elevação por pitch
> (5–14 s); o build atual usa o espelhamento da pressão +Y, então as quatro direções são
> simétricas e comparáveis em velocidade. Um eventual `executor re-plan roll_neg -> ...` significa
> apenas que aquela pressão falhou e a nova tentativa de fallback entrou em ação — essa é a rede
> de segurança normal.

## 7.3 Lógica do executor (no firmware)

- 20 ticks (0.4 s) por waypoint de referência, interpolação linear; limite de slew da saída de
  0.08 rad/tick;
- Após os waypoints, retraia o braço para o neutro a 0.033 rad/tick;
- Concluído quando `up_z > 0.95` com o alvo em zero por 50 ticks;
- Se o corpo se estabilizar em outro eixo deitado (`up_z<0.6`, `|ω|<0.8` por 15 ticks), retraia
  para o neutro e mude para a referência da nova pose (até 5 trocas);
- A referência de `roll_neg` usa **esperas adaptativas por estágio**: os estágios de
  pressão/bombeamento seguram enquanto `up_z<0.92`, até um teto de ticks por estágio (pressão
  40 / bombeamento 30 / bombeamento 30 / whip 40 / final 90); se o corpo ficar na vertical no meio
  da sequência, o executor pula direto para a retração, para que os estágios posteriores não
  derrubem o robô já em pé.

## 7.4 Monitoramento e logs

```bash
python tools/hw_monitor.py COM27
```

(Execute na pasta `SR-Support` com o `.venv` ativado — [página 02](./02-environment.md).
Feche antes qualquer assistente/monitor serial; as ferramentas seriais / o download do UartAssist
para Windows estão na [página 03, seção 3.3](./03-build-flash.md).)

- Anexa eventos e resumos de telemetria de 5 segundos a `logs/hw_monitor.log`;
- Registra `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost`, etc.;
- Verifica o envelope dos servos (ombro `[-1.85,+1.82]`, cotovelo `±1.55`) e grava `!! VIOLATION`;
- Enquanto o executor roda, imprime uma trilha a cada 0.2 s:

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Campo | Significado |
|---|---|
| `pose` | Pose de referência atual |
| `ph` / `tick` | Fase do waypoint / tick dentro da fase |
| `tgt` | Ângulos alvo das juntas |
| `up` | Vetor "para cima" atual |
| `q` | Comando atual das juntas |
| `sw` | Número de trocas de pose até agora |

> Abrir o monitor reinicia o ESP32; feche-o antes de gravar.

## 7.5 Registro dos testes

Para cada teste, registre a pose, se terminou com `done`, a duração, o número de trocas e
quaisquer violações. `logs/hw_monitor.log` é o registro oficial.

---

[← Voltar ao índice do tutorial](./index.md)
