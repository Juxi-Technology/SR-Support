---
title: 09 Risoluzione dei problemi
description: Sintomi, cause e soluzioni comuni di SR-Support relativi a IMU, porta seriale, soglia di caduta, timeout dell'esecutore e WiFi.
---

# 09 Risoluzione dei problemi

I comandi seriali si inviano tramite un assistente/monitor seriale: digitali nella casella di
invio e premi Invio (abilita "invia nuova riga" in UartAssist); gli strumenti seriali / il
download di UartAssist per Windows sono alla [pagina 03, sezione 3.3](./03-build-flash.md).

## 9.1 Sintomi comuni

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| `waiting for IMU startup 5000 ms...` poi `IMU not ready` | Avvio lento dell'IMU, cablaggio difettoso, indirizzo errato | Attendi 5–10 s; controlla 3V3, SDA=GPIO6 / SCL=GPIO7, indirizzo 0x23 |
| Ripetuti `IMU lost -> bus reset + re-init` | Fili I²C lunghi o allentati | Accorcia i fili, reinserisci i connettori |
| Il flash fallisce con `could not open port` / `Access is denied` | Porta seriale occupata da monitor/monitor seriale | Chiudi prima `hw_monitor.py` o il monitor seriale |
| Il robot non parte dopo essere stato posato | Corpo non fermo, o una mano lo tocca | Lascialo e tienilo fermo per ≥0.5 s; osserva `getup start` |
| Agitazione immediata / direzione sbagliata | Soglia di caduta attivata a metà rotolamento, classificazione errata | Posiziona e lascia pulitamente; riprova |
| L'esecuzione si ferma e stampa `executor timeout` dopo 14 s | La sequenza di riferimento non è terminata | Fallback normale; nuovo tentativo automatico dopo 1.5 s; conserva il log |
| Occasionali eventi `executor re-plan` | Fallback normale dopo una pressione `roll_neg` fallita | Controlla se termina con `done` |
| Il servomotore ronza / si surriscalda | Stallo o target in blocco | Invia `x` o togli alimentazione; controlla i limiti e il gioco meccanico |
| Il braccio urta il corpo durante l'auto-raddrizzamento | Movimento ampio della spalla | Controlla `Q_SHOULDER_MAX` e il gioco; mantieni l'altezza della base di ~68 mm |
| `up` non corrisponde alla posa reale (inclinazione persistente di 5°+ da sdraiato) | Offset di zero dell'accelerometro non calibrati | Metti il robot in piano e invia `c` (vedi [pagina 06, 6.2](./06-debug-and-calibrate.md)) |
| Il braccio non si ferma al centro visivo dopo la ritrazione | Zero derivato (re-indicizzazione/riassemblaggio senza riazzeramento) | Riazzera con lo [strumento della pagina 05](./05-zero-tool.md) e memorizza |
| Il servomotore ronza/tremola dopo una rialzata | Auto-eccitazione transitoria del servomotore analogico dopo movimenti ampi/stalli (l'uscita è costante) | Si attenua da sola; aggiungi rondelle smorzanti in gomma o usa un servomotore digitale; stringere il braccio la fa tacere subito |
| Pagina di stato / provisioning irraggiungibile | Proxy del browser non escluso, o hotspot spento | Aggiungi `192.168.4.1` alle eccezioni del proxy; invia `w` per attivare il WiFi |

## 9.2 Comandi di sicurezza

| Situazione | Comando |
|---|---|
| Fermare subito il movimento | `s` (mantieni l'ultimo target) o `x` (stacca il PWM, rilascia la coppia) |
| Recuperare dopo `x` | `r` reinizializza il PWM e centra |
| Un giunto si muove nel verso sbagliato | Inversione di segno con `v` (spalla) / `b` (gomito) |

## 9.3 Catturare un guasto

Conserva la parte corrispondente di `logs/hw_monitor.log`. Le righe chiave sono:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```

---

[← Torna all'indice del tutorial](./index.md)
