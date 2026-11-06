---
title: 04 Montagem: imprimir, montar e ligar
description: Impressão, reindexação e centralização do horn do servo, tabela de fiação, orientação de montagem da IMU e ordem de energização do SR-Support.
---

# 04 Montagem: imprimir, montar e ligar

> **Usuários de unidades prontas podem pular esta página**: a fábrica já imprimiu, montou, fez a
> fiação e inspecionou a unidade (veja a seção de estado de fábrica no [índice](./index.md)). Siga
> esta página apenas ao montar a partir das peças ou substituir componentes.

## 4.1 Impressão e inspeção

1. Imprima a placa inferior, o suporte do servo do ombro, o suporte do servo do cotovelo e a
   travessa superior (1 de cada);
2. Confira o contorno da base (~88 × 82 mm) e a altura total (~68 mm) com um paquímetro;
3. Faça um teste de encaixe dos horns 25T dos servos nos seus alojamentos; fixe com parafusos
   somente quando não houver emperramento;
4. Pese cada peça impressa e registre-a em `hardware/v1/meshes/print_mass_model.json`.

## 4.2 Preparação dos servos (zero do firmware e instalação do horn)

1. **Faça a fiação e grave primeiro**: ligue os dois servos, a IMU, a alimentação dos servos e o
   terra comum conforme a tabela em 4.4 (peças mecânicas ainda não montadas; o firmware principal
   precisa da IMU para inicializar) e depois grave o firmware principal conforme a
   [página 03, seção 3.1](./03-build-flash.md);
2. **Energize até o zero do firmware**: abra a porta serial a 115200 (as ferramentas seriais / o
   download do UartAssist estão na [página 03, seção 3.3](./03-build-flash.md)) e ligue; após a
   inicialização o firmware leva os dois servos a q=0 (pulsos centrais 1681 / 1456 µs). Quando o
   log mostrar `servo start q: 0.00 0.00 rad` e `ready; send g to run` (ou `autorun on: ...`), os
   servos estão no zero;
3. **Desligue**: corte a alimentação dos servos (o USB pode permanecer conectado) e confirme que
   os dois servos estão sem carga;
4. **Instale os horns**: monte o horn do ombro de modo que o braço superior fique vertical, e o
   horn do cotovelo de modo que o antebraço fique alinhado com ele; aperte e verifique o curso
   completo manualmente;
5. Convenção de direção (igual à do simulador): `shoulder +q` move o braço grande na direção
   **−Y**, `elbow +q` move o antebraço na direção **+X**; os padrões do firmware são
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> Os centros de 1681 / 1456 µs do firmware já incluem a reindexação do horn feita na calibração de
> fábrica — **não conte os dentes**: monte os horns no zero do firmware com o braço na vertical.
> Como alternativa (equivalente e opcional), digite `e` na caixa de envio serial e pressione
> Enter para colocar os dois servos no centro elétrico de 1520 µs e monte ali (veja a tabela de
> comandos na [página 03](./03-build-flash.md)); de qualquer forma, o comando `z` da
> [página 05](./05-zero-tool.md) faz o zero preciso final.

> Montar no zero do firmware é apenas uma **centralização grosseira** (a estria do horn é discreta).
> O zero preciso deve ser definido após a montagem completa e a gravação do firmware principal
> ([página 03](./03-build-flash.md)) com a [ferramenta de zero da página 05](./05-zero-tool.md):
> declare a pose visualmente vertical como q=0 (`z` não usa a IMU e funciona em qualquer pose),
> depois grave os pulsos impressos no `config.h` e regrave o firmware. Mesmo que o horn não tenha
> sido montado perfeitamente, esta zeragem corrige isso; só quando um dos lados fica sem curso (o
> pulso satura em 500/2500 µs) você precisa remover o horn e reindexar. O índice do horn define
> como o curso se divide entre os dois lados; os limites manuais do firmware
> (`Q_SHOULDER_MIN/MAX`) devem corresponder ao curso real — não os amplie. Após a zeragem,
> desloque todos os waypoints das sequências conforme descrito na página 05, caso contrário as
> poses físicas de endireitamento derivam.

## 4.3 Montagem da base e do braço

1. Fixe a placa inferior e o suporte do servo do ombro juntos com parafusos M3 para formar a base
   (~68 mm de altura);
2. Instale o servo do ombro no suporte do ombro, com o horn voltado para cima;
3. Prenda o suporte do servo do cotovelo ao horn do ombro e aperte (ele forma o braço superior);
   instale o servo do cotovelo no suporte do cotovelo;
4. Conecte a travessa superior (antebraço) ao horn do cotovelo;
5. Mova o braço manualmente até a vertical (`q≈0`) e confirme que coincide com o centro do servo.

## 4.4 Fiação

| Dispositivo | Pino do ESP32-S3 | Adaptador | Observações |
|---|---|---|---|
| Adaptador 3V3 | 3V3 | Pino de sinal S1 | outra ponta no VCC da IMU (3.3 V) |
| Sinal do ombro | GPIO4 | S4 | PWM de 50 Hz |
| Sinal do cotovelo | GPIO5 | S5 | PWM de 50 Hz |
| SDA da IMU | GPIO6 | Pino de sinal S6 | outra ponta no SDA da IMU; I²C 0x23, 100 kHz |
| SCL da IMU | GPIO7 | Pino de sinal S7 | outra ponta no SCL da IMU; I²C 0x23, 100 kHz |
| GND da IMU | GND | — (direto) | terra comum |
| LED (opcional) | GPIO2 | — | LED de status |
| Entrada de alimentação 5 V | 5V / GND | — | cabo 1-para-2: um ramo para o ESP32, outro para o V+/GND do adaptador para os servos |
| Alimentação dos servos | — | Terminal V+/GND | 5 V / ≥5 A; **tensões mais altas devem usar apenas este terminal, nunca o 5V do ESP32** |
| S2 / S3 | — | — | não conectados |

Notas:

- O adaptador é uma passagem passiva: S1/S6/S7 carregam 3V3 / SDA / SCL nos seus pinos de
  sinal, S4/S5 carregam os sinais dos servos; confirme a ordem V+/GND/sinal de cada conector —
  polaridade invertida destrói servos ou a placa;
- Mantenha os fios I²C curtos e longe dos fios dos servos; os pull-ups do módulo são de 3.3 V;
- Com uma fonte de **5 V**, você pode alimentar o 5V/GND do ESP32 e derivar a mesma fonte para o
  V+/GND do adaptador para os servos; tensões mais altas (6 V / 7.4 V) devem alimentar apenas o
  V+/GND do adaptador, e o ESP32 deve ser alimentado pelo USB;
- **Com uma bateria de 5 V alimentando o ESP32, você pode manter o Type-C conectado**: no
  esquemático oficial do DevKitC-1, cada VBUS do USB chega à rede 5V através de um diodo Schottky,
  então não há realimentação e o USB funciona como dados (mais alimentação auxiliar). Em uma placa
  clone que omite o diodo, ou se você não puder confirmá-lo, desconecte o ramo de 5 V para o ESP32
  durante a gravação e alimente-o pelo USB (opção 2);
- **Alimentação durante depuração / gravação (ambas são normais; escolha uma)**:
  1. a fonte de 5 V alimenta o ESP32 e os servos pelo divisor, e o USB transporta apenas dados;
  2. mais fácil de entender: desconecte o ramo de 5 V para o ESP32, alimente o ESP32 somente pelo
     USB e deixe a fonte de 5 V alimentar apenas os servos.
  Use a opção 2 para gravação, monitoramento serial e calibração `c`; a opção 1 para operação
  autônoma;
- Na primeira energização, deixe os servos desconectados, verifique a polaridade e a tensão de V+
  com um multímetro, depois teste um servo e em seguida os dois;
- Ordem de fiação: terra e sinais → fonte de 5 V (ESP32 e servos juntos) → USB para a porta serial
  quando necessário. Inverta a ordem ao desligar.

## 4.5 Orientação de montagem da IMU

A IMU é fixada à base com parafusos (sua orientação não é ajustável), então o firmware habilita
`IMU_YAW90` e converte o vetor "para cima" do referencial da IMU para as coordenadas do corpo:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Verificação mecânica da orientação** (possível após montar os servos, antes de energizar):
usando os eixos impressos no módulo IMU ou documentados para ele,

- o **eixo de saída** do servo do ombro (o eixo no qual o horn é montado; também chamado de eixo
  do horn ou eixo da engrenagem) aponta para o **−Y** da IMU;
- o eixo de saída do servo do cotovelo aponta para o **+X** da IMU.

De baixo para cima, os dois servos são **ombro (inferior) → cotovelo (superior)**; não os troque
ao montar os horns ou fazer a fiação.

Essas duas direções são os eixos de ombro e cotovelo do corpo; se não corresponderem ao hardware,
a IMU ou um suporte de servo está instalado ao contrário — corrija antes de energizar.

Após a energização, verifique novamente na [página 06](./06-debug-and-calibrate.md): em pé
fornece `up≈(0, 0, 1)`; as quatro poses deitadas estão na tabela em 6.5.

---

[← Voltar ao índice do tutorial](./index.md)
