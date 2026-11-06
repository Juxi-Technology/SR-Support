---
title: Tutorial del robot auto-raddrizzante SR-Support
description: Tutorial completo per il dispositivo auto-raddrizzante a 2-DOF SR-Support, dalle nozioni di base e dalla preparazione dell'ambiente al flash, all'assemblaggio, all'azzeramento, alla calibrazione, all'uso dell'auto-raddrizzamento e alla risoluzione dei problemi.
---

# Tutorial del robot auto-raddrizzante SR-Support

[简体中文](../zh-hans/index.md) · [繁體中文](../zh-hant/index.md) · [English](../en/index.md) · [日本語](../ja/index.md) · [한국어](../ko/index.md) · [Deutsch](../de/index.md) · [Français](../fr/index.md) · [Español](../es/index.md) · [Italiano](../it/index.md) · [Português (BR)](../pt-br/index.md) · [Português (PT)](../pt-pt/index.md)


SR-Support è un dispositivo auto-raddrizzante attivo a basso costo basato su un braccio a
2-DOF. Dopo essere caduto in qualsiasi direzione, pianta il suo braccio a due giunti sul
terreno, rotola e si fa leva per tornare in posizione eretta. Questo tutorial è organizzato
come un ordine di lettura che copre l'intero percorso da zero a una build verificata.

## Ordine di lettura

| # | Pagina | Contenuto | Nota |
|---|---|---|---|
| 01 | [Nozioni di base](./01-basics.md) | Principio di funzionamento, specifiche, BOM | leggi prima |
| 02 | [Preparazione dell'ambiente](./02-environment.md) | Creare/attivare `.venv`, firmware precompilato + strumenti di flash (Flash Download Tool / esptool), strumenti lato computer e ambiente MuJoCo, PlatformIO opzionale, porta seriale | **da fare per primo** |
| 03 | [Flash del firmware principale](./03-build-flash.md) | Bin precompilato (consigliato ai clienti) o build da sorgente con PlatformIO, comandi seriali, comportamento all'avvio | saltabile per le unità di serie |
| 04 | [Assemblaggio: stampa, montaggio, cablaggio](./04-assembly.md) | Parti stampate, indicizzazione delle squadrette, tabella dei collegamenti, montaggio dell'IMU | saltabile per le unità di serie |
| 05 | [Azzeramento](./05-zero-tool.md) | Spostamento con i tasti freccia + azzeramento con `z` (dopo re-indicizzazione/riassemblaggio) | **obbligatorio per le build fai-da-te**; saltabile per le unità di serie |
| 06 | [Debug e calibrazione](./06-debug-and-calibrate.md) | Verifica e calibrazione dell'intero robot: telemetria, IMU, servomotori, controllo della centratura, quattro pose sdraiate, soglia di caduta | |
| 07 | [Uso dell'auto-raddrizzamento e monitoraggio](./07-self-righting.md) | Quattro direzioni di caduta, movimento previsto, monitoraggio e log | |
| 08 | [WiFi e il gemello della simulazione](./08-wifi-twin.md) | Pagina di stato, provisioning del WiFi domestico, gemello MuJoCo wireless | opzionale |
| 09 | [Risoluzione dei problemi](./09-troubleshooting.md) | Sintomi comuni e soluzioni | consultazione |
| 10 | [Riferimenti: modello, parametri e licenze](./10-reference.md) | File del modello (XML/STL), parametri, sequenze di riferimento, licenze | consultazione |

## Stato di fabbrica di un'unità finita (due percorsi di lettura)

Questo tutorial si rivolge a due tipi di lettori: scegli il percorso che ti corrisponde:

| Lettore | Stato di fabbrica | Percorso consigliato |
|---|---|---|
| **Utente di un'unità finita** | Assemblata e cablata, firmware caricato, **calibrata** (zeri dei servomotori e zeri dell'accelerometro IMU memorizzati), **collaudata** (tutte e quattro le direzioni di rialzata verificate su ogni unità) | Vai direttamente alla [07 uso](./07-self-righting.md) e alla [08 WiFi/gemello](./08-wifi-twin.md) (opzionale); tieni la [09](./09-troubleshooting.md)/[10](./10-reference.md) per consultazione. **Le pagine 02/03/04/05/06 servono solo per aggiornamenti del firmware, sostituzione di servomotori/IMU o rimontaggio delle squadrette**; per usare gli strumenti gemello/telemetria della pagina 08, installa prima gli strumenti lato computer della pagina 02. |
| **Costruttore di kit / fai-da-te** | Parte dai componenti | Segui [01](./01-basics.md) → [02](./02-environment.md) → [03 flash](./03-build-flash.md) → [04 assemblaggio](./04-assembly.md) → [05 azzeramento (obbligatorio)](./05-zero-tool.md) → [06 debug/calibrazione](./06-debug-and-calibrate.md) → [07](./07-self-righting.md) dall'inizio alla fine. Sia l'azzeramento (05) sia la calibrazione (06) avvengono **dopo l'assemblaggio completo e il flash**: `z` non usa l'IMU e funziona in qualsiasi posa; `c` richiede il robot assemblato, in piedi e in piano. |

> Controllo consigliato al primo uso di un'unità finita: accendi in posizione eretta → conferma
> `up≈(0,0,1)` → rovesciala una volta in ciascuna delle quattro direzioni secondo la
> [pagina 07](./07-self-righting.md) e conferma che si rialzi.

## Prerequisiti

- Parti meccaniche SR-Support (piastra inferiore, supporto del servomotore di spalla, supporto
  del servomotore di gomito, montante superiore; stampa e assemblaggio alla
  [pagina 04](./04-assembly.md));
- scheda ESP32-S3, IMU Juxi ICM42670P, scheda adattatrice passiva per servomotori a comando diretto;
- 2× servomotori PTK7452MG (PWM 180°);
- un alimentatore per servomotori (5 V / ≥5 A) e un cavo dati USB-C;
- un computer con l'ambiente della [pagina 02](./02-environment.md).

## Stato verificato (2026-11-06)

Tutte e quattro le direzioni di caduta sono state verificate sul robot reale, ciascuna come
**rialzata diretta** (senza bisogno di ribaltamento), in circa 1–6 s; non sono state registrate
violazioni dell'inviluppo dei servomotori. Il kit include anche uno strumento di calibrazione
del punto zero con i tasti freccia ([pagina 05](./05-zero-tool.md)), una pagina di stato WiFi
con provisioning della rete domestica e un gemello digitale MuJoCo wireless in tempo reale
([pagina 08](./08-wifi-twin.md)).

## Sicurezza

> - Tieni fermo il robot alla prima accensione, lascia un'area libera di 30 cm e invia `x` o
>   togli l'alimentazione ai servomotori in caso di qualsiasi anomalia;
> - non tenere mai un servomotore in stallo per più di 1 s; fermati quando la carcassa supera i 60 °C;
> - l'alimentazione dei servomotori **5 V / ≥5 A** (verificata per tutte e quattro le direzioni di rialzata);
> - qualsiasi tensione superiore a 5 V va solo alla linea di alimentazione dei servomotori -
>   **mai** ai pin 5V/3V3 dell'ESP32;
> - tutto condivide un'unica massa; l'ordine di accensione è nella [pagina 04](./04-assembly.md).
