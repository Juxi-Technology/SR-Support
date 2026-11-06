---
title: 05 Calibration du point zéro (flèches ; obligatoire pour les montages DIY)
description: Déplacez le bras jusqu'au centre visuel avec les flèches et déclarez-le q=0 ; obligatoire pour chaque montage DIY, et après une ré-indexation de palonnier ou un ré-assemblage.
---

# 05 Calibration du point zéro (flèches ; obligatoire pour les montages DIY)

Les zéros des servomoteurs et les zéros d'accéléromètre de l'IMU sont calibrés et enregistrés par
unité en usine, donc une unité de série n'a rien à faire ici. Un **montage DIY doit faire cette
page** : un bras assemblé à la main ne se placera presque jamais exactement au centre. Même si le
palonnier n'a pas été monté exactement au zéro du firmware, vous pouvez corriger ici - amenez le
bras à la verticale visuelle avec les flèches et appuyez sur `z` pour déclarer la pose
**actuelle** q=0. La commande `z` n'utilise pas l'IMU et fonctionne dans toute pose ou index de
palonnier.

Revenez ici lorsque : un palonnier a été ré-indexé, le bras a été démonté/ré-assemblé, un
servomoteur a été remplacé, l'IMU a été remplacée/remontée (recalibrez l'accéléromètre), ou le
bras ne repose plus au centre visuel après la rétraction.

> `z` ne décale que le zéro logiciel ; il ne change **pas** la façon dont l'index du palonnier
> répartit la course (PWM 500-2500 µs). Si après la mise à zéro une direction sort de plage
> (l'impulsion sature à 500/2500 µs et le bras ne peut pas atteindre un angle de séquence
> requis), ré-indexez le palonnier (environ 2 dents sur l'épaule) et refaites la mise à zéro.

Chronologie : une fois le robot complètement assemblé et le firmware principal flashé (le
parcours DIY suit 03 → 04 → 05).

## 5.1 Principe

Le firmware définit q=0 comme le centre visuel : bras vertical, les deux segments alignés. La
commande `z` est une mise à zéro façon codeur : elle rend les positions articulaires **actuelles**
q=0 et affiche les largeurs d'impulsion de centre correspondantes.

## 5.2 Procédure

1. Connectez à la fois la batterie et l'USB (servomoteurs alimentés) et exécutez ceci dans le
   dossier `SR-Support` avec `.venv` activé :

   ```bash
   python tools/hw_shoulder_range.py
   ```

   Fermez d'abord tout assistant/moniteur série (ils occupent le port) ; les touches dans la
   fenêtre ci-dessous sont lues par cet outil, aucun assistant série n'est nécessaire. Les outils
   série / le téléchargement UartAssist pour Windows sont sur
   [page 03, section 3.3](./03-build-flash.md).

   Un affichage persistant de quatre lignes se met à jour sur place :

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Déplacez avec les flèches : `↑`/`↓` = grand bras ±0.05 rad, `←`/`→` = petit bras ±0.05 rad
   (Maj = ±0.20) jusqu'à ce que le bras paraisse **vertical et aligné** ;
3. Appuyez sur `z` ; le firmware affiche :

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. Contrôle de cohérence : appuyez sur `n` (position de repos), déplacez un peu, revenez au
   repos - le bras doit revenir au centre visuel que vous venez de définir.

## 5.3 Intégration définitive (obligatoire une fois satisfait)

`z` ne touche que la RAM ; un redémarrage restaure l'ancien zéro. Quand tout vous convient :

1. Écrivez les deux valeurs d'impulsion dans `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`) ;
2. Décalez chaque point de passage de `EXEC_REF*` et de `training/b_line/getup_reference_b39.py`
   des mêmes offsets (épaule/coude chacun −Δ rad) ;
3. Reflashez et retestez les quatre directions ([page 07](./07-self-righting.md)).

> Une fausse manipulation est sans conséquence : refaites la mise à zéro pour l'écraser.

## 5.4 Commandes associées

| Commande | Fonction |
|---|---|
| `z` | La pose actuelle devient q=0 pour les deux articulations ; affiche les nouvelles impulsions de centre (RAM seulement) |
| `k` | Lire les impulsions de centre actuelles (épaule/coude, µs) |
| `o` / `p` | Ajustement fin en direct du centre d'épaule ±10 µs (réinitialisé au redémarrage) |

---

[← Retour au sommaire du tutoriel](./index.md)
