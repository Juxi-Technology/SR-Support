---
title: 07 Utilisation de l'auto-redressement et surveillance
description: Comment utiliser le SR-Support dans chaque direction de chute, temps de mouvement attendus, événements série et journaux de surveillance.
---

# 07 Utilisation de l'auto-redressement et surveillance

> Chaque unité finie est testée dans les quatre directions avant expédition. Pour la première
> utilisation, vérifiez tout de même chaque direction une fois selon la section 7.2 pour vous
> assurer que l'unité est saine après le transport.

## 7.1 Procédure

1. Mettez sous tension avec le robot debout et attendez `autorun on: get-up waits for a fall` ;
2. Faites basculer le robot dans n'importe quelle direction, **relâchez-le et gardez-le immobile
   environ 0.5 s** ;
3. Lorsque `getup start pose=<pose>` apparaît, l'exécuteur démarre automatiquement ;
4. En cas de succès, le firmware affiche `standing -> executor done` et revient en veille ;
5. Si une exécution dépasse 14 s, le firmware affiche `executor timeout` ; après un temps de repos
   de 1.5 s, le seuil de chute se redéclenche et réessaie.

## 7.2 Comportement attendu par direction

| Pose | Mécanisme | Temps sur robot réel |
|---|---|---|
| `pitch_neg` (haut → −X) | Le coude se plante, la course d'épaule fait levier pour soulever le corps | ~3 s |
| `pitch_pos` (haut → +X) | Même levée ; s'il bascule pendant la rétraction, la replanification de pose réexécute `pitch_pos` | ~5–6 s |
| `roll_pos` (haut → −Y) | Levier d'épaule direct utilisant le côté de grande course | ~3 s |
| `roll_neg` (haut → +Y) | **Appui direct sur toute la course → pompes de coin de coude ×2 → nouvelle tentative whip-slam si nécessaire** ; sans culbute | ~2–6 s |

> Les firmwares antérieurs faisaient culbuter `roll_neg` par-dessus le sommet et replanifiaient
> vers une levée de type pitch (5–14 s) ; la version actuelle utilise le miroir de l'appui +Y, de
> sorte que les quatre directions sont symétriques et comparables en vitesse. Un
> `executor re-plan roll_neg -> ...` occasionnel signifie simplement que cet appui a échoué et que
> la nouvelle tentative de repli s'est déclenchée - c'est le filet de sécurité normal.

## 7.3 Logique de l'exécuteur (dans le firmware)

- 20 ticks (0.4 s) par point de passage de référence, interpolation linéaire ; limite de vitesse de
  sortie 0.08 rad/tick ;
- Après les points de passage, rétractez le bras au neutre à 0.033 rad/tick ;
- Terminé lorsque `up_z > 0.95` avec la cible à zéro pendant 50 ticks ;
- Si le corps se stabilise sur un autre axe couché (`up_z<0.6`, `|ω|<0.8` pendant 15 ticks),
  rétractez au neutre et passez à la référence de la nouvelle pose (jusqu'à 5 changements) ;
- La référence `roll_neg` utilise des **maintiens adaptatifs par étape** : les étapes
  d'appui/pompe maintiennent tant que `up_z<0.92` jusqu'à un plafond de ticks par étape (appui 40 /
  pompe 30 / pompe 30 / whip 40 / final 90) ; si le corps se redresse au milieu de la séquence,
  l'exécuteur saute directement à la rétraction pour que les étapes suivantes ne puissent pas
  faire basculer le robot debout.

## 7.4 Surveillance et journaux

```bash
python tools/hw_monitor.py COM27
```

(Exécutez-la dans le dossier `SR-Support` avec `.venv` activé - [page 02](./02-environment.md).
Fermez d'abord tout assistant/moniteur série ; les outils série / le téléchargement UartAssist pour
Windows sont sur [page 03, section 3.3](./03-build-flash.md).)

- Ajoute les événements et des résumés de télémétrie toutes les 5 secondes à `logs/hw_monitor.log` ;
- Enregistre `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost`, etc. ;
- Vérifie l'enveloppe des servomoteurs (épaule `[-1.85,+1.82]`, coude `±1.55`) et écrit
  `!! VIOLATION` ;
- Pendant l'exécution, il affiche une trace toutes les 0.2 s :

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Champ | Signification |
|---|---|
| `pose` | Pose de référence actuelle |
| `ph` / `tick` | Phase du point de passage / tick dans la phase |
| `tgt` | Angles articulaires cibles |
| `up` | Vecteur up actuel |
| `q` | Consigne articulaire actuelle |
| `sw` | Nombre de changements de pose jusqu'ici |

> Ouvrir le moniteur réinitialise l'ESP32 ; fermez-le avant de flasher.

## 7.5 Tenue des registres

Pour chaque test, enregistrez la pose, si cela s'est terminé par `done`, la durée, le nombre de
changements et toute violation. `logs/hw_monitor.log` est le registre de référence.

---

[← Retour au sommaire du tutoriel](./index.md)
