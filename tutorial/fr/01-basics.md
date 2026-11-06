---
title: 01 Bases
description: Principe de fonctionnement, spécifications et nomenclature (BOM) du SR-Support.
---

# 01 Bases

## 1.1 Principe de fonctionnement

SR-Support est un dispositif actif d'auto-redressement à 2 DDL (épaule + coude) :

- **Mécanisme** : un bras à deux articulations monté sur une base carrée ; l'épaule pivote autour
  de l'axe longitudinal du corps et le coude replie l'avant-bras ;
- **Acquisition** : une IMU 6 axes fournit le quaternion d'attitude ; le firmware classe chaque
  chute dans l'une de quatre poses (`pitch_pos/neg`, `roll_pos/neg`, voir
  [page 06](./06-debug-and-calibrate.md) 6.5) à partir du vecteur up exprimé dans le repère du corps ;
- **Actionnement** : un exécuteur de séquences de référence — chaque pose possède une suite de
  points de passage (20 ticks par point de passage, 0.08 rad/tick de vitesse) qui plante/fait
  levier avec le bras pour faire rouler le corps et le redresser ; `roll_neg` utilise en plus des
  pompes de coin de coude et un repli de type coup de fouet (whip-slam) ;
- **Replis** : délai d'expiration de 14 s, replanification de pose et nouvelle tentative
  automatique après le seuil de chute ; `roll_neg` utilise des maintiens adaptatifs par étape et
  sort vers la rétraction dès qu'il est redressé ;
- **Vérifié** : les quatre directions se redressent directement en 1 à 6 s environ ; le même
  modèle pilote la simulation MuJoCo et le jumeau matériel en direct ([page 08](./08-wifi-twin.md)).

## 1.2 Vue d'ensemble

| Élément | Spécification |
|---|---|
| Base | ~88 × 82 mm, 68 mm de haut (plaque inférieure + support de servomoteur d'épaule, imprimés en 3D) |
| Bras | Axe d'épaule à 56 mm au-dessus de la base, coude à 40.1 mm au-dessus de l'épaule ; entretoise de l'avant-bras ~17 cm (tube de 12 mm) |
| Masse | ~133 g (table des masses du modèle : pied 92.1 / bras1 20.7 / bras2 20.1 g, servomoteurs inclus) |
| Épaule | PTK7452MG ; limites logicielles `[-1.85, +1.82]` rad (plage articulaire en simulation `[-1.07, +2.07]`) |
| Coude | PTK7452MG ; limites logicielles `[-0.90, +0.70]` rad (~±1.55 rad mécanique) |
| Contrôleur | ESP32-S3-DevKitC-1 (framework Arduino / PlatformIO) |
| Attitude | IMU 6 axes Juxi ICM42670P (adresse I²C 0x23, 100 kHz) |
| Commande servomoteur | LEDC de l'ESP32, 50 Hz, 14 bits, largeur d'impulsion 500–2500 µs |

## 1.3 Nomenclature (BOM)

| Catégorie | Pièce | Qté | Remarques |
|---|---|---|---|
| Structure | Imprimés 3D : plaque inférieure, support de servomoteur d'épaule, support de servomoteur de coude, entretoise supérieure | 1 de chaque | PETG ou PLA, 15 % de remplissage ; les palonniers sont ceux fournis avec les servomoteurs |
| Actionnement | Servomoteur PTK7452MG PWM 180° | 2 | Pignons métal, 25T, ~12.2 g, ~3.4 kg·cm à 6 V |
| Contrôleur | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Capteur | Module IMU Juxi ICM42670P | 1 | Alimentation 3.3 V |
| Adaptateur | Carte adaptatrice de servomoteur passive | 1 | GPIO → connecteurs 3 broches, V+/GND communs, pas de PCA9685 |
| Câblage | Câble de données USB-C, fils Dupont, rallonges de servomoteur | plusieurs | — |
| Alimentation | Alimentation de servomoteurs 5 V / ≥5 A | 1 | Une seule alimentation 5 V alimente l'ESP32 et les servomoteurs via un câble 1 vers 2 (masse commune) ; **vérifiée pour les quatre directions de redressement** |

---

[← Retour au sommaire du tutoriel](./index.md)
