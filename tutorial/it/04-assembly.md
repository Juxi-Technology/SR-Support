---
title: 04 Assemblaggio: stampa, montaggio, cablaggio
description: Stampa, re-indicizzazione e centratura delle squadrette dei servomotori, tabella dei collegamenti, orientamento di montaggio dell'IMU e ordine di accensione per SR-Support.
---

# 04 Assemblaggio: stampa, montaggio, cablaggio

> **Gli utenti di un'unità finita possono saltare questa pagina**: la fabbrica ha già stampato,
> assemblato, cablato e ispezionato l'unità (vedi la sezione sullo stato di fabbrica
> nell'[indice](./index.md)). Segui questa pagina solo se costruisci dai componenti o sostituisci
> componenti.

## 4.1 Stampa e ispezione

1. Stampa la piastra inferiore, il supporto del servomotore di spalla, il supporto del
   servomotore di gomito e il montante superiore (1 ciascuno);
2. controlla con un calibro il profilo della base (~88 × 82 mm) e l'altezza totale (~68 mm);
3. prova in sede le squadrette 25T dei servomotori nei loro alloggiamenti; fissale con le viti
   solo se non ci sono impuntamenti;
4. pesa ogni parte stampata e registrala rispetto a `hardware/v1/meshes/print_mass_model.json`.

## 4.2 Preparazione dei servomotori (zero del firmware e installazione delle squadrette)

1. **Collega e scrivi prima il firmware**: collega entrambi i servomotori, l'IMU, l'alimentazione
   dei servomotori e la massa comune secondo la tabella in 4.4 (parti meccaniche non ancora
   montate; il firmware principale richiede l'IMU per avviarsi), poi scrivi in flash il firmware
   principale secondo la [pagina 03, sezione 3.1](./03-build-flash.md);
2. **Accendi fino allo zero del firmware**: apri la porta seriale a 115200 (strumenti seriali / il
   download di UartAssist per Windows sono alla [pagina 03, sezione 3.3](./03-build-flash.md)) e
   accendi; dopo l'avvio il firmware porta entrambi i servomotori a q=0 (impulsi di centratura
   1681 / 1456 µs). Quando il log mostra `servo start q: 0.00 0.00 rad` e
   `ready; send g to run` (o `autorun on: ...`), i servomotori sono allo zero;
3. **Spegni**: togli l'alimentazione ai servomotori (l'USB può restare collegato) e conferma che
   entrambi i servomotori siano scarichi;
4. **Installa le squadrette**: monta la squadretta della spalla in modo che il braccio superiore
   sia verticale, e quella del gomito in modo che l'avambraccio sia in linea con esso; serra e
   verifica la corsa completa a mano;
5. convenzione di direzione (coerente con il simulatore): `shoulder +q` muove il braccio grande
   verso **−Y**, `elbow +q` muove l'avambraccio verso **+X**; i valori predefiniti del firmware
   sono `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> Gli impulsi di centratura 1681 / 1456 µs del firmware includono già la re-indicizzazione delle
> squadrette della calibrazione di fabbrica - **non contare i denti**: monta le squadrette allo
> zero del firmware con il braccio verticale. In alternativa (equivalente, opzionale) digita `e`
> nella casella di invio seriale e premi Invio per portare entrambi i servomotori al centro
> elettrico di 1520 µs e montare lì (vedi la tabella dei comandi alla [pagina 03](./03-build-flash.md));
> in ogni caso il comando `z` della [pagina 05](./05-zero-tool.md) esegue lo zero preciso finale.

> Il montaggio allo zero del firmware è solo una **centratura grossolana** (la dentatura della
> squadretta è discreta). Lo zero preciso va impostato dopo l'assemblaggio completo e il flash
> del firmware principale ([pagina 03](./03-build-flash.md)) con lo
> [strumento di azzeramento della pagina 05](./05-zero-tool.md): dichiara la posa visivamente
> verticale come q=0 (`z` non usa l'IMU e funziona in qualsiasi posa), poi incorpora gli impulsi
> stampati in `config.h` e riscrivi il firmware. Anche se la squadretta non è stata montata
> perfettamente, questo azzeramento lo corregge; solo se un lato è a corto di corsa (l'impulso si
> blocca a 500/2500 µs) devi estrarre la squadretta e re-indicizzarla. L'indicizzazione della
> squadretta determina come la corsa si divide tra i due lati; i limiti manuali del firmware
> (`Q_SHOULDER_MIN/MAX`) devono corrispondere alla corsa reale - non allargarli. Dopo
> l'azzeramento, sposta tutti i waypoint delle sequenze come descritto alla pagina 05, altrimenti
> le pose di rialzata fisiche derivano.

## 4.3 Assemblaggio di base e braccio

1. Fissa la piastra inferiore e il supporto del servomotore di spalla insieme con viti M3 per
   formare la base (~68 mm di altezza);
2. installa il servomotore di spalla nel supporto della spalla, con la squadretta verso l'alto;
3. fissa il supporto del servomotore di gomito alla squadretta della spalla e serra (forma il
   braccio superiore); installa il servomotore di gomito nel supporto del gomito;
4. collega il montante superiore (avambraccio) alla squadretta del gomito;
5. porta il braccio in verticale a mano (`q≈0`) e conferma che coincida con il centro del
   servomotore.

## 4.4 Cablaggio

| Dispositivo | Pin ESP32-S3 | Adattatore | Note |
|---|---|---|---|
| Adattatore 3V3 | 3V3 | Pin di segnale S1 | altro capo a VCC dell'IMU (3.3 V) |
| Segnale spalla | GPIO4 | S4 | PWM a 50 Hz |
| Segnale gomito | GPIO5 | S5 | PWM a 50 Hz |
| SDA IMU | GPIO6 | Pin di segnale S6 | altro capo a SDA dell'IMU; I²C 0x23, 100 kHz |
| SCL IMU | GPIO7 | Pin di segnale S7 | altro capo a SCL dell'IMU; I²C 0x23, 100 kHz |
| GND IMU | GND | — (diretto) | massa comune |
| LED (opzionale) | GPIO2 | — | LED di stato |
| Ingresso alimentazione 5 V | 5V / GND | — | cavo a 1→2: un ramo all'ESP32, uno a V+/GND dell'adattatore per i servomotori |
| Alimentazione servomotori | — | Morsetto V+/GND | 5 V / ≥5 A; **le tensioni più alte devono usare solo questo morsetto, mai il 5V dell'ESP32** |
| S2 / S3 | — | — | non collegati |

Note:

- L'adattatore è un pass-through passivo: S1/S6/S7 portano 3V3 / SDA / SCL sui rispettivi pin di
  segnale, S4/S5 portano i segnali dei servomotori; conferma l'ordine V+/GND/segnale di ogni
  connettore - una polarità invertita distrugge i servomotori o la scheda;
- tieni i fili I²C corti e lontani dai fili dei servomotori; i pull-up del modulo sono a 3.3 V;
- con un'alimentazione a **5 V** puoi alimentare i pin 5V/GND dell'ESP32 e derivare la stessa
  alimentazione al V+/GND dell'adattatore per i servomotori; le tensioni più alte (6 V / 7.4 V)
  devono alimentare solo il V+/GND dell'adattatore e l'ESP32 deve essere alimentato da USB;
- **con una batteria a 5 V che alimenta l'ESP32 puoi lasciare il Type-C collegato**: nello schema
  ufficiale della DevKitC-1 ogni VBUS USB raggiunge la rete 5V attraverso un diodo Schottky,
  quindi non c'è controalimentazione e l'USB funziona come dati (più alimentazione ausiliaria).
  Su una scheda clone che omette il diodo, o se non puoi verificarlo, scollega il ramo 5 V verso
  l'ESP32 durante il flash e alimentalo da USB (opzione 2);
- **alimentazione durante il debug / flash (entrambe sono normali; scegline una)**:
  1. l'alimentatore 5 V alimenta l'ESP32 e i servomotori tramite il ripartitore, l'USB porta solo
     i dati;
  2. più semplice da ragionare: scollega il ramo 5 V verso l'ESP32, alimenta l'ESP32 solo da USB
     e lascia che l'alimentatore 5 V alimenti solo i servomotori.
  Usa l'opzione 2 per il flash, il monitoraggio seriale e la calibrazione `c`; l'opzione 1 per il
  funzionamento autonomo;
- alla prima accensione lascia i servomotori scollegati, verifica con un multimetro la polarità e
  la tensione di V+, poi prova un servomotore, poi entrambi;
- ordine di cablaggio: massa e segnali → alimentazione 5 V (ESP32 e servomotori insieme) → USB
  per la porta seriale quando serve. In ordine inverso allo spegnimento.

## 4.5 Orientamento di montaggio dell'IMU

L'IMU è fissata alla base con viti (il suo orientamento non è regolabile), quindi il firmware
abilita `IMU_YAW90` e converte il vettore up dal sistema di riferimento dell'IMU alle coordinate
del corpo:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Verifica dell'orientamento meccanico** (possibile una volta montati i servomotori, prima
dell'accensione): usando gli assi stampati su / documentati per il modulo IMU,

- l'**albero di uscita** del servomotore di spalla (l'albero su cui si monta la squadretta; detto
  anche albero della squadretta o albero degli ingranaggi) punta verso **−Y** dell'IMU;
- l'albero di uscita del servomotore di gomito punta verso **+X** dell'IMU.

Dal basso verso l'alto i due servomotori sono **spalla (inferiore) → gomito (superiore)**; non
scambiarli quando monti le squadrette o fai il cablaggio.

Queste due direzioni sono gli assi di spalla e gomito del corpo; se non corrispondono
all'hardware, l'IMU o un supporto del servomotore è installato al rovescio - correggi prima di
accendere.

Dopo l'accensione, riverifica alla [pagina 06](./06-debug-and-calibrate.md): in posizione eretta
si ha `up≈(0, 0, 1)`; le quattro pose sdraiate sono elencate nella tabella del 6.5.

---

[← Torna all'indice del tutorial](./index.md)
