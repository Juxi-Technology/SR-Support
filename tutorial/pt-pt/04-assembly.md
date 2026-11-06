---
title: 04 Montagem: imprimir, montar, ligar
description: Impressão, reindexação e centragem do horn do servo, tabela de ligações, orientação de montagem da IMU e ordem de ligação do SR-Support.
---

# 04 Montagem: imprimir, montar, ligar

> **Os utilizadores de unidades acabadas podem saltar esta página**: a fábrica já imprimiu,
> montou, ligou e inspecionou a unidade (ver a secção de estado de fábrica no
> [índice](./index.md)). Siga esta página apenas quando construir a partir de peças ou
> substituir componentes.

## 4.1 Impressão e inspeção

1. Imprima a placa inferior, o suporte do servo do ombro, o suporte do servo do cotovelo e o
   montante superior (1 de cada);
2. Verifique o contorno da base (~88 × 82 mm) e a altura total (~68 mm) com um paquímetro;
3. Experimente encaixar os horns de servo 25T nas respetivas ranhuras; fixe com parafusos
   apenas quando não houver bloqueio;
4. Pese cada peça impressa e registe o valor em `hardware/v1/meshes/print_mass_model.json`.

## 4.2 Preparação dos servos (zero do firmware e instalação dos horns)

1. **Ligar e gravar primeiro**: ligue ambos os servos, a IMU, a alimentação dos servos e a massa
   comum conforme a tabela em 4.4 (peças mecânicas ainda não montadas; o firmware principal
   precisa da IMU para arrancar), depois grave o firmware principal conforme a
   [página 03, secção 3.1](./03-build-flash.md);
2. **Ligar até ao zero do firmware**: abra a porta série a 115200 (as ferramentas de série / a
   transferência do UartAssist estão na [página 03, secção 3.3](./03-build-flash.md)) e ligue;
   após o arranque, o firmware leva ambos os servos a q=0 (impulsos centrais 1681 / 1456 µs).
   Quando o registo mostrar `servo start q: 0.00 0.00 rad` e `ready; send g to run` (ou
   `autorun on: ...`), os servos estão no zero;
3. **Desligar**: corte a alimentação dos servos (o USB pode ficar ligado) e confirme que ambos
   os servos estão descarregados;
4. **Instalar os horns**: monte o horn do ombro de modo a que o braço superior fique vertical, e
   o horn do cotovelo de modo a que o antebraço fique alinhado com ele; aperte e verifique todo
   o curso à mão;
5. Convenção de direções (igual à do simulador): `shoulder +q` move o braço grande para **−Y**,
   `elbow +q` move o antebraço para **+X**; os valores por omissão do firmware são
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> Os impulsos centrais 1681 / 1456 µs do firmware já incluem a reindexação do horn feita na
> calibração de fábrica — **não conte os dentes**: monte os horns no zero do firmware com o
> braço na vertical. Em alternativa (equivalente, opcional), escreva `e` na caixa de envio da
> série e prima Enter para colocar ambos os servos no centro elétrico de 1520 µs e monte aí
> (ver a tabela de comandos na [página 03](./03-build-flash.md)); de qualquer forma, o comando
> `z` da [página 05](./05-zero-tool.md) faz o ponto zero preciso final.

> Montar no zero do firmware é apenas uma **centragem grosseira** (a estria do horn é
> discreta). O ponto zero preciso tem de ser definido após a montagem completa e a gravação do
> firmware principal ([página 03](./03-build-flash.md)) com a
> [ferramenta de ponto zero da página 05](./05-zero-tool.md): declare como q=0 a postura
> visualmente vertical (o `z` não usa a IMU e funciona em qualquer postura), depois grave os
> impulsos impressos no `config.h` e volte a gravar o firmware. Mesmo que o horn não tenha sido
> montado na perfeição, este ponto zero corrige-o; só quando um dos lados não tiver curso (o
> impulso satura em 500/2500 µs) é preciso tirar o horn e reindexar. O índice do horn determina
> como o curso se reparte entre os dois lados; os limites manuais do firmware
> (`Q_SHOULDER_MIN/MAX`) têm de corresponder ao curso real — não os alargue. Após o ponto zero,
> desloque todos os waypoints das sequências como descrito na página 05, caso contrário as
> posturas físicas de levantamento desviam-se.

## 4.3 Montagem da base e do braço

1. Fixe a placa inferior e o suporte do servo do ombro com parafusos M3 para formar a base
   (~68 mm de altura);
2. Instale o servo do ombro no suporte do ombro, com o horn voltado para cima;
3. Fixe o suporte do servo do cotovelo ao horn do ombro e aperte (forma o braço superior);
   instale o servo do cotovelo no suporte do cotovelo;
4. Ligue o montante superior (antebraço) ao horn do cotovelo;
5. Mova o braço para a vertical à mão (`q≈0`) e confirme que corresponde ao centro do servo.

## 4.4 Ligações

| Dispositivo | Pino do ESP32-S3 | Adaptador | Notas |
|---|---|---|---|
| Adaptador 3V3 | 3V3 | Pino de sinal S1 | outra extremidade no VCC da IMU (3.3 V) |
| Sinal do ombro | GPIO4 | S4 | PWM de 50 Hz |
| Sinal do cotovelo | GPIO5 | S5 | PWM de 50 Hz |
| SDA da IMU | GPIO6 | Pino de sinal S6 | outra extremidade no SDA da IMU; I²C 0x23, 100 kHz |
| SCL da IMU | GPIO7 | Pino de sinal S7 | outra extremidade no SCL da IMU; I²C 0x23, 100 kHz |
| GND da IMU | GND | — (direto) | massa comum |
| LED (opcional) | GPIO2 | — | LED de estado |
| Entrada de alimentação 5 V | 5V / GND | — | cabo 1-para-2: um ramo para o ESP32, outro para o V+/GND do adaptador para os servos |
| Alimentação dos servos | — | Terminal V+/GND | 5 V / ≥5 A; **tensões superiores têm de usar apenas este terminal, nunca o 5V do ESP32** |
| S2 / S3 | — | — | não ligados |

Notas:

- O adaptador é um pass-through passivo: S1/S6/S7 transportam 3V3 / SDA / SCL nos respetivos
  pinos de sinal, S4/S5 transportam os sinais dos servos; confirme a ordem V+/GND/sinal de cada
  conector — a polaridade invertida destrói os servos ou a placa;
- Mantenha os fios I²C curtos e afastados dos fios dos servos; as pull-ups do módulo são de
  3.3 V;
- Com uma fonte de **5 V** pode alimentar o 5V/GND do ESP32 e derivar a mesma fonte para o V+/GND
  do adaptador para os servos; tensões superiores (6 V / 7.4 V) só podem alimentar o V+/GND do
  adaptador e o ESP32 tem de ser alimentado por USB;
- **Com uma bateria de 5 V a alimentar o ESP32, pode manter o Type-C ligado**: no esquema
  oficial do DevKitC-1, cada VBUS do USB chega à rede de 5V através de um díodo Schottky, pelo
  que não há realimentação e o USB funciona como dados (mais alimentação auxiliar). Numa placa
  clonada que omita o díodo, ou se não o puder confirmar, desligue o ramo de 5 V para o ESP32
  durante a gravação e alimente-o por USB (opção 2);
- **Alimentação durante a depuração / gravação (ambas são normais; escolha uma)**:
  1. a fonte de 5 V alimenta o ESP32 e os servos através do repartidor, o USB transporta apenas
     dados;
  2. mais simples de raciocinar: desligue o ramo de 5 V para o ESP32, alimente o ESP32 apenas
     por USB e deixe a fonte de 5 V alimentar só os servos.
  Use a opção 2 para gravar, monitorizar a série e calibrar com `c`; a opção 1 para
  funcionamento autónomo;
- Na primeira ligação, deixe os servos desligados, verifique a polaridade e a tensão de V+ com
  um multímetro, depois teste um servo e só depois ambos;
- Ordem de ligação: massa e sinais → fonte de 5 V (ESP32 e servos em conjunto) → USB para a
  porta série quando necessário. Inverta a ordem ao desligar.

## 4.5 Orientação de montagem da IMU

A IMU é fixa à base com parafusos (a sua orientação não é ajustável), pelo que o firmware ativa
`IMU_YAW90` e converte o vetor up no referencial da IMU para coordenadas do corpo:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Verificação da orientação mecânica** (possível depois de montar os servos, antes de ligar):
usando os eixos impressos no módulo IMU / documentados para ele,

- o **eixo de saída** do servo do ombro (o eixo onde monta o horn; também chamado eixo do horn
  ou eixo da engrenagem) aponta para o **−Y** da IMU;
- o eixo de saída do servo do cotovelo aponta para o **+X** da IMU.

De baixo para cima, os dois servos são **ombro (inferior) → cotovelo (superior)**; não os troque
ao montar os horns nem ao ligar.

Estas duas direções são os eixos do ombro e do cotovelo do corpo; se não corresponderem ao
hardware, a IMU ou um suporte de servo está montado ao contrário — corrija antes de ligar.

Após a ligação, verifique de novo na [página 06](./06-debug-and-calibrate.md): na vertical obtém
`up≈(0, 0, 1)`; as quatro posturas deitadas estão listadas na tabela em 6.5.

---

[← Voltar ao índice do tutorial](./index.md)
