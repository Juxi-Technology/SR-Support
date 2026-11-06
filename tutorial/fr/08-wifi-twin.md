---
title: 08 WiFi et le jumeau de simulation
description: Page d'état, provisionnement sur le réseau domestique, jumeau en direct MuJoCo sans fil et journalisation de la télémétrie WiFi.
---

# 08 WiFi et le jumeau de simulation

Cette étape est facultative et n'est pas nécessaire à l'auto-redressement proprement dit.

## 8.1 Point d'accès et page d'état

Point d'accès : SSID `SR-Support`, mot de passe `srsupport`, adresse `192.168.4.1` (`w` l'active et
le désactive ; activé par défaut au démarrage). `w` s'envoie par série : tapez `w` dans la zone
d'envoi du moniteur/assistant série et appuyez sur Entrée ; les outils série / le téléchargement
UartAssist pour Windows sont sur [page 03, section 3.3](./03-build-flash.md).

Rejoignez le point d'accès et ouvrez `http://192.168.4.1` (les téléphones affichent généralement le
portail automatiquement). La page se rafraîchit toutes les 300 ms : état, vecteur up et barre de
verticalité, consignes articulaires, pose/phase de redressement, état du WiFi domestique et
interrupteur du flux jumeau. Si le navigateur utilise un proxy, ajoutez une exception pour cette
adresse.

## 8.2 Provisionnement (rejoindre le WiFi domestique)

Sur la page d'état, utilisez la carte Home WiFi : `Scan` → choisissez un réseau → saisissez le mot
de passe → `Connect`. En cas de succès, l'ESP32 fonctionne en AP+STA :

- le point d'accès reste actif (le travail sur banc n'est pas affecté) ;
- le robot est joignable sur le réseau local domestique (la page affiche son `Robot IP`) ;
- les identifiants sont stockés en NVS et la connexion est rétablie automatiquement au démarrage.

2.4 GHz uniquement ; les scans/connexions sont refusés pendant qu'un redressement est en cours.

## 8.3 Jumeau en direct MuJoCo sans fil

Appuyez sur `Twin ON` sur la page d'état (équivalent à `d` en série), puis :

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(Dans le dossier `SR-Support` ; créez et activez d'abord `.venv` comme sur
[page 02](./02-environment.md) - l'environnement de l'outil y est aussi installé.)

- La fenêtre reproduit l'attitude réelle en direct et maintient le corps sur le sol ;
- Le bras est maintenu à son angle de contact avec le sol comme le servomoteur bloqué (pas de
  pénétration du sol) ;
- Le câble USB n'est nécessaire que pour le flashage et l'export des journaux ;
- Rejouez un journal enregistré hors ligne avec `--replay <file>`.

## 8.4 Journalisation de la télémétrie WiFi

```bash
python tools/tcp_log.py
```

Enregistre le flux de télémétrie du point d'accès dans `logs/wifi_<time>.txt` pour une relecture et
une analyse hors ligne.

## 8.5 Référence de simulation et d'entraînement

Le dépôt fournit le modèle MuJoCo et le code d'entraînement (`training/b_line/`) pour la relecture
et le ré-entraînement ; les fichiers du modèle sont décrits sur [la page 10](./10-reference.md).

---

[← Retour au sommaire du tutoriel](./index.md)
