---
title: 11 Référence : modèle, paramètres et licence
description: Fichiers du modèle de référence (XML MuJoCo / STL), paramètres du firmware, les quatre séquences de référence, état vérifié et licence.
---

# 11 Référence : modèle, paramètres et licence

## 11.1 Fichiers du modèle de référence

La simulation utilise MuJoCo MJCF (`.xml` + maillages `.stl`), partageant la conception du matériel
lui-même :

| Fichier | Description |
|---|---|
| `hardware/v1/robot_v1.xml` | Modèle principal (géométrie/masse alignées sur le matériel) |
| `hardware/v1/meshes/*.stl` | 6 maillages STL qui s'assemblent en 4 groupes imprimés (plaque/coque de base, support d'épaule, support de bras supérieur/support de coude, avant-bras) |
| `hardware/v1/meshes/print_mass_model.json` | Table des masses imprimées par pièce (15 % de remplissage) |

Aucun URDF n'est fourni ; pour une utilisation avec ROS, exportez-en un depuis la CAO/les maillages
ci-dessus.

## 11.2 Paramètres du firmware (`firmware/sr_support_b_ptk/include/config.h`)

| Paramètre | Valeur | Signification |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | Période de commande de 50 Hz |
| `MAX_CMD_RATE` | 0.08 rad/tick | Limite de vitesse de sortie (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Seuil up_z du seuil de chute |
| `FALL_W_QUIET` | 0.9 rad/s | Seuil de vitesse angulaire du seuil de chute |
| `FALL_CONFIRM_TICKS` | 25 | Confirmation du seuil de chute (0.5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Ticks par point de passage de référence |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Vitesse de rétraction |
| `EXEC_DONE_TICKS` | 50 | Ticks debout consécutifs pour terminer |
| `EXEC_TIMEOUT_MS` | 14000 | Délai d'expiration par référence |
| `EXEC_COOLDOWN_TICKS` | 75 | Temps de repos après done/timeout (1.5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Ticks de confirmation du changement de pose |
| `EXEC_SWITCH_UP` | 0.60 | up_z max pour un changement |
| `EXEC_SWITCH_W` | 0.8 rad/s | Vitesse angulaire max pour un changement |
| `EXEC_MIN_SWITCH_AGE` | 25 | Tick le plus précoce pour un changement |
| `EXEC_MAX_SWITCHES` | 5 | Changements max par exécution |
| `EXEC_NEUTRAL_MAX` | 120 | Ticks max de rétraction au neutre |
| `SERVO_SHOULDER_CENTER_US` | 1681 | Impulsion de zéro de l'épaule (valeur de centre visuel intégrée en 2026-11 ; refaites la mise à zéro selon [la page 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Impulsion de zéro du coude (idem) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Limites de commande manuelle de l'épaule |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Plage manuelle (l'exécuteur utilise ±1.55 en mécanique) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Sens des servomoteurs |
| `IMU_YAW90` | 1 | IMU montée avec une rotation de 90° |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Filtre d'attitude : gain de correction accélérométrique / bande de confiance |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Point d'accès (`w` l'active/désactive ; actif au démarrage) |

## 11.3 Séquences de référence (épaule, coude ; rad ; identiques valeur pour valeur à `training/b_line/getup_reference_b39.py`)

| Pose | Séquence |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` appui direct pleine vitesse (maintien ≤40 ticks) → pompes de coin `[-1.80,0.35] → [-1.80,0.05]` ×2 (maintien ≤30 chacune) → repli : `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (whip-slam, maintien ≤40) → maintien final ≤90 → rétraction |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 11.4 État vérifié et inspection d'usine (2026-11-06)

- **Inspection d'usine** : chaque unité finie reçoit - zéros des servomoteurs définis et intégrés
  par unité ([page 05](./05-zero-tool.md)), calibration du zéro gyroscope + accéléromètre (NVS), et
  un test de redressement dans les quatre directions avant expédition ;
- Les quatre directions vérifiées sur le robot réel, chacune sous la forme d'un **redressement
  direct** (sans culbute), environ 1–6 s ; aucune violation d'enveloppe de servomoteur ;
- Recette finale de `roll_neg` : appui direct sur toute la course + pompes de coin de coude ×2,
  nouvelle tentative whip-slam en repli (l'ancien schéma culbute + replanification est retiré) ;
- La chaîne d'attitude a été corrigée avec la calibration du biais d'accéléromètre (voir
  [page 06, 6.2](./06-debug-and-calibrate.md)) ; les poses couchées correspondent désormais au
  robot réel ;
- `roll_neg` ne se reproduit toujours pas dans le modèle de simulation à masse 1× (masse/friction
  du bras différentes) ; c'est une lacune connue du modèle - le firmware matériel est validé sur
  le matériel.

## 11.5 Licence

- Firmware/code d'entraînement de la ligne B : MIT / Apache-2.0 ;
- CAO/STL de la ligne B : CERN-OHL-S-2.0 (forte réciprocité - vérifiez les obligations avant toute
  utilisation commerciale) ;
- SelfRisingRobot : aucune licence ; ce tutoriel ne contient aucun de ses codes, points de passage
  ou modèles ;
- Brevet CN109693729A/B : effectuez une revue FTO avant toute utilisation commerciale.

---

[← Retour au sommaire du tutoriel](./index.md)
