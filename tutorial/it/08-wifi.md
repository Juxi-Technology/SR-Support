---
title: 08 Pagina di stato WiFi e provisioning
description: Hotspot, pagina di stato e provisioning della rete domestica; la simulazione MuJoCo e il gemello in tempo reale sono trattati alla pagina 09.
---

# 08 Pagina di stato WiFi e provisioning

Questo passo è opzionale e non necessario per l'auto-raddrizzamento in sé. La finestra di
simulazione MuJoCo e il gemello in tempo reale hanno una pagina dedicata:
[pagina 09](./09-mujoco.md).

## 8.1 Hotspot e pagina di stato

Hotspot: SSID `SR-Support`, password `srsupport`, indirizzo `192.168.4.1` (`w` lo attiva/disattiva;
attivo per impostazione predefinita all'avvio). `w` si invia via seriale: digita `w` nella casella
di invio del monitor/assistente seriale e premi Invio; gli strumenti seriali / il download di
UartAssist per Windows sono alla [pagina 03, sezione 3.3](./03-build-flash.md).

Unisciti all'hotspot e apri `http://192.168.4.1` (i telefoni di solito aprono il portale
automaticamente). La pagina si aggiorna ogni 300 ms: stato, vettore up e barra di verticalità,
comandi dei giunti, posa/fase di rialzata, stato del WiFi domestico e interruttore del flusso del
gemello (specchio in tempo reale alla [pagina 09](./09-mujoco.md)). Se il browser usa un proxy,
aggiungi un'eccezione per questo indirizzo.

![Figura 8-1 La pagina di stato del robot](../images/sr-support/wifi/01-status-page.png)

*Figura 8-1: la pagina di stato del robot (aperta nel browser all'indirizzo del robot). In questa cattura il robot si è unito al WiFi domestico: la scheda Home WiFi mostra lo stato della connessione e il Robot IP, con sotto l'interruttore del flusso del gemello (uso in 9.2).*

## 8.2 Provisioning (unirsi al WiFi domestico)

Nella pagina di stato usa la scheda Home WiFi: `Scan` → scegli una rete → inserisci la password →
`Connect`. In caso di successo l'ESP32 funziona in AP+STA:

- l'hotspot resta attivo (il lavoro in banco non è influenzato);
- il robot è raggiungibile sulla LAN domestica (la pagina mostra il suo `Robot IP`; usa questo indirizzo nel comando del gemello a pagina 09);
- le credenziali sono memorizzate in NVS e la connessione viene ripristinata automaticamente
  all'avvio.

Solo 2.4 GHz; scansioni/connessioni vengono rifiutate mentre è in corso una rialzata.

---

[← Torna all'indice del tutorial](./index.md)
