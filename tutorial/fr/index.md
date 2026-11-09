---
title: Tutoriel du robot auto-redresseur SR-Support
description: Tutoriel complet du dispositif d'auto-redressement SR-Support à 2 DDL, des bases et de la préparation de l'environnement au flashage, à l'assemblage, à la mise à zéro, à la calibration, à l'utilisation de l'auto-redressement et au dépannage.
---

# Tutoriel du robot auto-redresseur SR-Support

[简体中文](../zh-hans/index.md) · [繁體中文](../zh-hant/index.md) · [English](../en/index.md) · [日本語](../ja/index.md) · [한국어](../ko/index.md) · [Deutsch](../de/index.md) · [Français](../fr/index.md) · [Español](../es/index.md) · [Italiano](../it/index.md) · [Português (BR)](../pt-br/index.md) · [Português (PT)](../pt-pt/index.md)


SR-Support est un dispositif actif d'auto-redressement à faible coût basé sur un bras à 2 DDL.
Après avoir basculé dans n'importe quelle direction, il plante son bras à deux articulations sur
le sol, roule et se redresse par effet de levier.
Ce tutoriel est organisé comme un ordre de lecture couvrant tout le parcours, de zéro jusqu'à une
construction vérifiée.

## Ordre de lecture

| # | Page | Contenu | Remarque |
|---|---|---|---|
| 01 | [Bases](./01-basics.md) | Principe de fonctionnement, spécifications, nomenclature (BOM) | à lire en premier |
| 02 | [Préparation de l'environnement](./02-environment.md) | Créer/activer `.venv`, firmware précompilé + outils de flashage (Flash Download Tool / esptool), outils côté ordinateur et environnement MuJoCo, PlatformIO facultatif, port série | **à faire en premier** |
| 03 | [Flasher le firmware principal](./03-build-flash.md) | Binaire précompilé (recommandé pour les clients) ou compilation des sources avec PlatformIO, commandes série, comportement au démarrage | peut être ignoré pour les unités de série |
| 04 | [Assemblage : impression, montage, câblage](./04-assembly.md) | Pièces imprimées, indexation des palonniers, tableau de câblage, montage de l'IMU | peut être ignoré pour les unités de série |
| 05 | [Calibration du point zéro](./05-zero-tool.md) | Déplacement aux flèches + mise à zéro avec `z` (après ré-indexation/ré-assemblage) | **obligatoire pour les montages DIY** ; peut être ignoré pour les unités de série |
| 06 | [Débogage et calibration](./06-debug-and-calibrate.md) | Vérification et calibration de l'ensemble du robot : télémétrie, IMU, servomoteurs, contrôle du centre, quatre poses couchées, seuil de chute | |
| 07 | [Utilisation de l'auto-redressement et surveillance](./07-self-righting.md) | Quatre directions de chute, mouvement attendu, surveillance et journaux | |
| 08 | [Page d'état WiFi et provisionnement](./08-wifi.md) | Point d'accès, page d'état, provisionnement du WiFi domestique | facultatif |
| 09 | [Simulation MuJoCo et jumeau en direct](./09-mujoco.md) | Fenêtre de simulation locale sur quatre poses, jumeau en direct WiFi, journalisation de la télémétrie | facultatif |
| 10 | [Dépannage](./10-troubleshooting.md) | Symptômes courants et correctifs | référence |
| 11 | [Référence : modèle, paramètres, licence](./11-reference.md) | Fichiers du modèle (XML/STL), paramètres, séquences de référence, licence | référence |

## État d'usine d'une unité finie (deux parcours de lecture)

Ce tutoriel s'adresse à deux publics — choisissez le parcours qui vous correspond :

| Lecteur | État d'usine | Parcours recommandé |
|---|---|---|
| **Utilisateur d'une unité finie** | Assemblé et câblé, firmware flashé, **calibré** (points zéro des servomoteurs et zéros d'accéléromètre de l'IMU enregistrés en usine), **testé** (les quatre directions de redressement vérifiées sur chaque unité) | Allez directement à [07 utilisation](./07-self-righting.md), [08 provisionnement WiFi](./08-wifi.md) et [09 simulation MuJoCo et jumeau en direct](./09-mujoco.md) (facultatif) ; gardez [10](./10-troubleshooting.md)/[11](./11-reference.md) comme référence. **Les pages 02/03/04/05/06 ne sont nécessaires que pour une mise à jour du firmware, un remplacement de servomoteur/IMU ou un remontage de palonnier** ; pour utiliser les outils de jumeau/télémétrie de la page 09, installez d'abord les outils côté ordinateur de la page 02. |
| **Monteur de kit / DIY** | Part de pièces détachées | Suivez [01](./01-basics.md) → [02](./02-environment.md) → [03 flash](./03-build-flash.md) → [04 assemblage](./04-assembly.md) → [05 mise à zéro (obligatoire)](./05-zero-tool.md) → [06 débogage/calibration](./06-debug-and-calibrate.md) → [07](./07-self-righting.md) de bout en bout. La mise à zéro (05) et la calibration (06) se font **après l'assemblage complet et le flashage** : `z` n'utilise pas l'IMU et fonctionne dans toute pose ; `c` exige le robot assemblé et debout de niveau. |

> Vérification recommandée à la première utilisation d'une unité finie : mettez sous tension debout → confirmez `up≈(0,0,1)` →
> basculez-la une fois dans chacune des quatre directions selon [la page 07](./07-self-righting.md) et
> confirmez qu'elle se redresse.

## Prérequis

- Pièces mécaniques SR-Support (plaque inférieure, support du servomoteur d'épaule, support du servomoteur de coude, entretoise supérieure ; impression et assemblage sur [la page 04](./04-assembly.md)) ;
- Carte ESP32-S3, IMU Juxi ICM42670P, carte adaptatrice de servomoteur à entraînement direct passif ;
- 2 servomoteurs PTK7452MG (PWM 180°) ;
- Une alimentation de servomoteurs (5 V / ≥5 A) et un câble de données USB-C ;
- Un ordinateur avec l'environnement de [la page 02](./02-environment.md).

## État vérifié (2026-11-06)

Les quatre directions de chute ont été vérifiées sur le robot réel, chacune sous la forme d'un
**redressement direct** (sans culbute nécessaire), en 1 à 6 s environ ; aucune violation
d'enveloppe de servomoteur n'a été enregistrée. Le kit fournit également un outil de calibration du
point zéro aux flèches ([page 05](./05-zero-tool.md)), une page d'état WiFi avec provisionnement
sur le réseau domestique ([page 08](./08-wifi.md)), et la simulation MuJoCo
avec son jumeau en direct sans fil ([page 09](./09-mujoco.md)).

## Sécurité

> - Tenez le robot à la première mise sous tension, gardez une zone dégagée de 30 cm, et envoyez `x` ou coupez l'alimentation des servomoteurs
>   en cas d'anomalie ;
> - Ne bloquez jamais un servomoteur plus de 1 s ; arrêtez lorsque le boîtier dépasse 60 °C ;
> - l'alimentation des servomoteurs **5 V / ≥5 A** (vérifiée pour les quatre directions de redressement) ;
> - tout ce qui dépasse 5 V va uniquement vers le rail des servomoteurs — **jamais** vers le 5V/3V3 de l'ESP32 ;
> - Tout partage une masse commune ; l'ordre de mise sous tension est indiqué sur [la page 04](./04-assembly.md).
