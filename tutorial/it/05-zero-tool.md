---
title: 05 Azzeramento (tasti freccia; obbligatorio per le build fai-da-te)
description: Sposta il braccio al centro visivo con i tasti freccia e dichiaralo q=0; obbligatorio per ogni build fai-da-te e dopo aver re-indicizzato una squadretta o riassemblato.
---

# 05 Azzeramento (tasti freccia; obbligatorio per le build fai-da-te)

Gli zeri dei servomotori e gli zeri dell'accelerometro dell'IMU vengono calibrati e memorizzati
per unità in fabbrica, quindi un'unità di serie non richiede nulla qui. Una **build fai-da-te
deve seguire questa pagina**: un braccio assemblato a mano quasi mai si trova esattamente al
centro. Anche se la squadretta non è stata montata esattamente allo zero del firmware, puoi
correggere qui - sposta il braccio fino alla verticale visiva con i tasti freccia e premi `z` per
dichiarare la posa **attuale** q=0. Il comando `z` non usa l'IMU e funziona con qualsiasi posa o
indicizzazione della squadretta.

Torna qui quando: una squadretta è stata re-indicizzata, il braccio è stato
smontato/riassemblato, un servomotore è stato sostituito, l'IMU è stata sostituita/rimontata
(ricalibra l'accelerometro), oppure il braccio non si ferma più al centro visivo dopo la
ritrazione.

> `z` sposta solo lo zero software; **non** cambia come l'indicizzazione della squadretta divide
> la corsa (PWM 500-2500 µs). Se dopo l'azzeramento una direzione esaurisce la corsa (l'impulso si
> blocca a 500/2500 µs e il braccio non raggiunge un angolo richiesto dalla sequenza), re-indicizza
> la squadretta (circa 2 denti sulla spalla) e azzera di nuovo.

Momento: dopo che il robot è completamente assemblato e il firmware principale è stato scritto in
flash (il percorso fai-da-te segue 03 → 04 → 05).

## 5.1 Principio

Il firmware definisce q=0 come centro visivo: braccio verticale, entrambi i segmenti in linea. Il
comando `z` è uno zero in stile encoder: rende q=0 le posizioni **attuali** dei giunti e stampa le
corrispondenti larghezze d'impulso di centratura.

## 5.2 Procedura

1. Collega sia la batteria sia l'USB (servomotori alimentati) ed esegui questo nella cartella
   `SR-Support` con `.venv` attivata:

   ```bash
   python tools/hw_shoulder_range.py
   ```

   Chiudi prima qualsiasi assistente/monitor seriale (occupano la porta); i tasti nella finestra
   qui sotto sono letti da questo strumento, non serve alcun assistente seriale. Gli strumenti
   seriali / il download di UartAssist per Windows sono alla [pagina 03, sezione 3.3](./03-build-flash.md).

   Un display persistente a quattro righe si aggiorna sul posto:

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Sposta con i tasti freccia: `↑`/`↓` = braccio grande ±0.05 rad, `←`/`→` = braccio piccolo
   ±0.05 rad (Shift = ±0.20) finché il braccio non appare **verticale e allineato**;
3. premi `z`; il firmware stampa:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. verifica di coerenza: premi `n` (home), sposta un po', home di nuovo - il braccio deve tornare
   al centro visivo appena definito.

## 5.3 Memorizzazione (obbligatoria una volta soddisfatti)

`z` tocca solo la RAM; un riavvio ripristina lo zero precedente. Quando sei soddisfatto:

1. scrivi i due valori di impulso in `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. sposta ogni waypoint di `EXEC_REF*` e `training/b_line/getup_reference_b39.py` degli stessi
   offset (spalla/gomito ciascuno −Δ rad);
3. riscrivi il firmware e ritesta tutte e quattro le direzioni ([pagina 07](./07-self-righting.md)).

> Una pressione errata è innocua: azzera di nuovo per sovrascrivere.

## 5.4 Comandi correlati

| Comando | Funzione |
|---|---|
| `z` | La posa attuale diventa q=0 per entrambi i giunti; stampa i nuovi impulsi di centratura (solo RAM) |
| `k` | Legge le larghezze d'impulso di centratura attuali (spalla/gomito, µs) |
| `o` / `p` | Trim dal vivo del centro della spalla ±10 µs (azzerato al riavvio) |

---

[← Torna all'indice del tutorial](./index.md)
