---
title: 03 Flasher le firmware principal
description: Flasher le firmware SR-Support de la ligne B à partir du bin précompilé (Flash Download Tool / esptool) ou le compiler avec PlatformIO ; commandes série et journal de démarrage.
---

# 03 Flasher le firmware principal

> **Les utilisateurs d'une unité finie peuvent ignorer cette page** : l'usine a flashé et vérifié
> le firmware. Ne refaites cette étape que pour une mise à jour du firmware ou après avoir modifié
> le code. Les clients utilisent l'image précompilée (3.1, sans PlatformIO) ; les développeurs
> compilent depuis les sources (3.2).

## 3.1 Flasher l'image précompilée (recommandé pour les clients)

1. Assurez-vous de disposer de `firmware/releases/sr_support_b_ptk_factory.bin` (sommes de
   contrôle dans `SHA256SUMS` à côté) ;
2. Passez en mode téléchargement : maintenez **BOOT**, appuyez sur **RST**, relâchez **BOOT** ;
3. Flashez-le (configuration de l'outil sur [page 02, section 2.4](./02-environment.md) ; exécutez
   ces commandes dans le dossier `SR-Support` avec `.venv` activé) :
   - Interface graphique Windows : Flash Download Tool → ESP32-S3 → chargez le bin à `0x0` → START ;
   - Ligne de commande Windows / Linux / macOS :

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Appuyez sur RST une fois terminé et lisez le journal comme en 3.3.

> Pour le flashage/débogage série, vous pouvez alimenter l'ESP32 par USB et réserver l'alimentation
> 5 V aux servomoteurs (les deux options d'alimentation sont sur [page 04, section 4.4](./04-assembly.md)).

> La commande est **identique sous Windows / Linux / macOS** ; seul le port change :
> `COM27` sous Windows, `/dev/ttyACM0` sous Linux, `/dev/tty.usbmodem*` sous macOS.
> Flash Download Tool est réservé à Windows ; ailleurs, utilisez la ligne de commande esptool.

> Le centrage lors de l'assemblage ne nécessite pas de seconde image : après avoir flashé celle-ci,
> mettez sous tension - les deux servomoteurs vont au zéro du firmware (1681 / 1456 µs) - puis
> mettez hors tension et installez les palonniers
> ([page 04, section 4.2](./04-assembly.md)). Vous pouvez éventuellement envoyer `e` pour les
> placer d'abord au centre électrique de 1520 µs (équivalent).

## 3.2 Compiler et flasher depuis les sources (développeurs)

Environnement : [page 02, section 2.5](./02-environment.md). Projet :
`firmware/sr_support_b_ptk/` (environnement `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Exécutez ces commandes dans le dossier `SR-Support` avec `.venv` activé (page 02, section 2.3) ;
> elles sont identiques sur les trois plateformes - remplacez `COM27` dans `--upload-port` par votre
> port. Fermez tout ce qui occupe le port série (moniteur série, `tools/hw_monitor.py`) avant de
> flasher, sinon vous obtiendrez `could not open port` / `Access is denied`.

Une compilation réussie utilise environ 56 % de RAM et 30 % de Flash (WiFi + serveur web inclus ;
les compilations antérieures sans WiFi étaient d'environ 7 % / 12 %).

## 3.3 Moniteur série

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Identique sur les trois plateformes ; remplacez `COM27` par votre port.)

> **Assistant série graphique Windows (facultatif)** : UartAssist de 野人家园 (gratuit, exe unique,
> Windows uniquement). Page officielle <https://cmsoft.cn/resource/101.html>, entrée de
> téléchargement officielle <https://cmsoft.cn/resource/download/101>. Sélectionnez le port COM,
> **115200, 8N1, sans contrôle de flux**, activez « send newline » ; observez le journal de
> démarrage/la télémétrie dans le volet de réception et tapez les commandes dans la zone d'envoi.
> Téléchargez-le uniquement depuis le lien officiel (les sites tiers y joignent souvent des
> logiciels publicitaires) ; ne committez pas l'exe dans ce dépôt.

**Visionneuses série Linux / macOS (choisissez-en une)** :

- Préféré : la commande `pio device monitor` ci-dessus (installée avec le projet, multiplateforme) ;
- CLI léger : `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` sous macOS ; quittez avec `Ctrl-]`) ; le `screen /dev/ttyACM0 115200`
  intégré fonctionne aussi (quittez avec `Ctrl-A`, puis `K`) ;
- Interface graphique : **CoolTerm** (gratuit, Windows/macOS/Linux, site officiel
  <https://freeware.the-meiers.org>) ; sous Linux, vous pouvez aussi `sudo apt install cutecom`.

> Sous Linux, ajoutez votre utilisateur au groupe `dialout` : `sudo usermod -aG dialout $USER`, puis
> déconnectez-vous et reconnectez-vous.

Après avoir ouvert le port, si la carte vient d'être alimentée ou si vous avez appuyé sur RST, vous
verrez d'abord le journal de démarrage ; sinon, appuyez une fois sur RST. Après la réinitialisation,
vous devriez voir :

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Commandes série (115200)

Tapez chaque commande dans la **zone d'envoi** du moniteur/assistant série et appuyez sur Entrée
(activez « send newline » dans UartAssist) ; la commande `m` nécessite un espace et deux valeurs,
par ex. `m 0.5 0`.

| Commande | Fonction |
|---|---|
| `g` | Démarrer/continuer l'exécution (cette compilation démarre automatiquement ; généralement pas nécessaire) |
| `s` | Arrêter l'exécuteur, maintenir la dernière cible |
| `x` | Relâchement d'urgence : détache le PWM ; réarmez avec `r` |
| `r` | Réinitialiser le PWM et centrer |
| `t` | Auto-test des servomoteurs (petit mouvement) |
| `c` | Calibrer le gyroscope + les **offsets de zéro de l'accéléromètre** (le robot doit être DEBOUT DE NIVEAU et immobile ; stockés en NVS) |
| `m <q1> <q2>` | Cibles articulaires manuelles en rad |
| `1/2` | Épaule manuelle ±0.5 rad |
| `3/4` | Coude manuel ±0.5 rad |
| `0` | Neutre manuel |
| `l` | Journal rapide de 3 s à 50 Hz |
| `k` | Afficher les largeurs d'impulsion de centre des deux servomoteurs |
| `o` / `p` | Ajustement fin du centre d'épaule ±10 µs |
| `z` | Zéro façon codeur : la pose actuelle devient q=0 pour les deux articulations ; affiche les nouvelles impulsions (RAM seulement ; voir [page 05](./05-zero-tool.md)) |
| `e` | Centre électrique (facultatif) : les deux servomoteurs à 1520 µs pour monter les palonniers au centre électrique ; la méthode habituelle est de mettre sous tension jusqu'au zéro du firmware et de monter là (voir [page 04, 4.2](./04-assembly.md)) |
| `d` | Basculer le flux jumeau à 50 Hz (jumeau MuJoCo ; même interrupteur sur la page d'état) |
| `w` | Basculer le WiFi (point d'accès + page d'état/provisionnement, voir [page 08](./08-wifi-twin.md)) |
| `v` / `b` | Inverser le signe de l'épaule / du coude |
| `i` / `j` | Inverser le signe X / Y de l'IMU |
| `h` | Bascule du retour en position debout (ancien chemin de politique) |
| `a` | Ancien mode de test de redressement scripté |

## 3.5 Comportement à la mise sous tension

Le firmware définit `AUTORUN_ON_BOOT` : après la mise sous tension, l'exécuteur attend que le robot
soit **complètement couché et immobile** pendant 0.5 s, puis démarre automatiquement - pas besoin de
`g`. Mettez sous tension avec le robot debout.

---

[← Retour au sommaire du tutoriel](./index.md)
