---
title: 04 Assemblage : impression, montage, câblage
description: Impression, ré-indexation et centrage des palonniers, tableau de câblage, orientation de montage de l'IMU et ordre de mise sous tension du SR-Support.
---

# 04 Assemblage : impression, montage, câblage

> **Les utilisateurs d'une unité finie peuvent ignorer cette page** : l'usine a déjà imprimé,
> assemblé, câblé et inspecté l'unité (voir la section sur l'état d'usine dans
> [l'index](./index.md)). Ne suivez cette page que pour construire à partir de pièces ou
> remplacer des composants.

## 4.1 Impression et inspection

1. Imprimez la plaque inférieure, le support de servomoteur d'épaule, le support de servomoteur
   de coude et l'entretoise supérieure (1 de chaque) ;
2. Vérifiez le contour de la base (~88 × 82 mm) et la hauteur totale (~68 mm) au pied à coulisse ;
3. Essayez les palonniers 25T dans leurs logements ; fixez-les avec des vis seulement en
   l'absence de point dur ;
4. Pesez chaque pièce imprimée et enregistrez-la par rapport à `hardware/v1/meshes/print_mass_model.json`.

## 4.2 Préparation des servomoteurs (zéro du firmware et installation des palonniers)

1. **Câblez et flashez d'abord** : câblez les deux servomoteurs, l'IMU, l'alimentation des
   servomoteurs et la masse commune selon le tableau du 4.4 (pièces mécaniques pas encore
   montées ; le firmware principal a besoin de l'IMU pour démarrer), puis flashez le firmware
   principal selon [page 03, section 3.1](./03-build-flash.md) ;
2. **Mettez sous tension jusqu'au zéro du firmware** : ouvrez le port série à 115200 (les outils
   série / le téléchargement UartAssist sont sur [page 03, section 3.3](./03-build-flash.md)) et
   mettez sous tension ; après le démarrage, le firmware amène les deux servomoteurs à q=0
   (impulsions de centre 1681 / 1456 µs). Lorsque le journal affiche
   `servo start q: 0.00 0.00 rad` et `ready; send g to run` (ou `autorun on: ...`), les
   servomoteurs sont au zéro ;
3. **Mettez hors tension** : coupez l'alimentation des servomoteurs (l'USB peut rester connecté)
   et confirmez que les deux servomoteurs ne sont plus en charge ;
4. **Installez les palonniers** : montez le palonnier d'épaule de sorte que le bras supérieur
   soit vertical, et le palonnier de coude de sorte que l'avant-bras soit aligné avec lui ;
   serrez et vérifiez la course complète à la main ;
5. Convention de direction (identique au simulateur) : `shoulder +q` déplace le grand bras vers
   **−Y**, `elbow +q` déplace l'avant-bras vers **+X** ; les valeurs par défaut du firmware sont
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> Les impulsions de centre 1681 / 1456 µs du firmware incluent déjà la ré-indexation du palonnier
> issue de la calibration d'usine - **ne comptez pas les dents** : montez les palonniers au zéro
> du firmware avec le bras vertical. Autre possibilité (équivalente, facultative) : tapez `e`
> dans la zone d'envoi série et appuyez sur Entrée pour placer les deux servomoteurs au centre
> électrique de 1520 µs et montez là (voir le tableau des commandes sur
> [page 03](./03-build-flash.md)) ; dans les deux cas, la commande `z` de
> [la page 05](./05-zero-tool.md) fait la mise à zéro précise finale.

> Le montage au zéro du firmware n'est qu'un **centrage grossier** (les cannelures du palonnier
> sont discrètes). Le zéro précis doit être réglé après l'assemblage complet et le flashage du
> firmware principal ([page 03](./03-build-flash.md)) avec
> [l'outil de mise à zéro de la page 05](./05-zero-tool.md) : déclarez la pose visuellement
> verticale comme q=0 (`z` n'utilise pas l'IMU et fonctionne dans toute pose), puis intégrez les
> impulsions affichées dans `config.h` et reflashez. Même si le palonnier n'a pas été monté
> parfaitement, cette mise à zéro le corrige ; ce n'est que lorsqu'un côté manque de course
> (l'impulsion sature à 500/2500 µs) qu'il faut retirer le palonnier et le ré-indexer.
> L'indexation du palonnier détermine la répartition de la course entre les deux côtés ; les
> limites logicielles du firmware (`Q_SHOULDER_MIN/MAX`) doivent correspondre à la course réelle -
> ne les élargissez pas. Après la mise à zéro, décalez tous les points de passage des séquences
> comme décrit à la page 05, sinon les poses physiques de redressement dérivent.

## 4.3 Assemblage de la base et du bras

1. Fixez la plaque inférieure et le support de servomoteur d'épaule ensemble avec des vis M3 pour
   former la base (~68 mm de haut) ;
2. Installez le servomoteur d'épaule dans le support d'épaule, palonnier vers le haut ;
3. Fixez le support de servomoteur de coude au palonnier d'épaule et serrez (il forme le bras
   supérieur) ; installez le servomoteur de coude dans le support de coude ;
4. Reliez l'entretoise supérieure (avant-bras) au palonnier de coude ;
5. Amenez le bras à la verticale à la main (`q≈0`) et confirmez qu'il correspond au centre du
   servomoteur.

## 4.4 Câblage

| Dispositif | Broche ESP32-S3 | Adaptateur | Remarques |
|---|---|---|---|
| Adaptateur 3V3 | 3V3 | Broche signal S1 | autre extrémité vers VCC de l'IMU (3.3 V) |
| Signal épaule | GPIO4 | S4 | PWM 50 Hz |
| Signal coude | GPIO5 | S5 | PWM 50 Hz |
| IMU SDA | GPIO6 | Broche signal S6 | autre extrémité vers SDA de l'IMU ; I²C 0x23, 100 kHz |
| IMU SCL | GPIO7 | Broche signal S7 | autre extrémité vers SCL de l'IMU ; I²C 0x23, 100 kHz |
| IMU GND | GND | — (direct) | masse commune |
| LED (facultatif) | GPIO2 | — | LED d'état |
| Entrée d'alimentation 5 V | 5V / GND | — | câble 1 vers 2 : une branche vers l'ESP32, une vers V+/GND de l'adaptateur pour les servomoteurs |
| Alimentation des servomoteurs | — | Borne V+/GND | 5 V / ≥5 A ; **les tensions supérieures doivent utiliser uniquement cette borne, jamais le 5V de l'ESP32** |
| S2 / S3 | — | — | non connectés |

Remarques :

- L'adaptateur est purement passif et se contente de recopier les signaux : S1/S6/S7 transportent 3V3 / SDA / SCL sur leurs
  broches signal, S4/S5 transportent les signaux des servomoteurs ; vérifiez l'ordre
  V+/GND/signal de chaque connecteur - une polarité inversée détruit les servomoteurs ou la carte ;
- Gardez les fils I²C courts et à l'écart des fils des servomoteurs ; les résistances de tirage du
  module sont à 3.3 V ;
- Avec une alimentation **5 V**, vous pouvez alimenter le 5V/GND de l'ESP32 et dériver la même
  alimentation vers V+/GND de l'adaptateur pour les servomoteurs ; les tensions supérieures
  (6 V / 7.4 V) doivent alimenter uniquement V+/GND de l'adaptateur et l'ESP32 doit être alimenté
  par USB ;
- **Avec une batterie 5 V alimentant l'ESP32, vous pouvez laisser le Type-C branché** : dans le
  schéma officiel du DevKitC-1, chaque VBUS USB atteint le réseau 5V à travers une diode Schottky,
  il n'y a donc pas de retour d'alimentation et l'USB fonctionne comme données (plus alimentation
  auxiliaire). Sur une carte clone qui omet la diode, ou si vous ne pouvez pas le confirmer,
  débranchez la branche 5 V vers l'ESP32 pendant le flashage et alimentez-le par USB (option 2) ;
- **Alimentation pendant le débogage / le flashage (les deux sont normaux ; choisissez-en une)** :
  1. l'alimentation 5 V alimente l'ESP32 et les servomoteurs via le répartiteur, l'USB ne
     transporte que les données ;
  2. plus simple à raisonner : débranchez la branche 5 V vers l'ESP32, alimentez l'ESP32
     uniquement par USB et laissez l'alimentation 5 V alimenter seulement les servomoteurs.
  Utilisez l'option 2 pour le flashage, la surveillance série et la calibration `c` ; l'option 1
  pour le fonctionnement autonome ;
- À la première mise sous tension, laissez les servomoteurs débranchés, vérifiez la polarité et la
  tension de V+ au multimètre, puis testez un servomoteur, puis les deux ;
- Ordre de câblage : masse et signaux → alimentation 5 V (ESP32 et servomoteurs ensemble) → USB
  pour le port série si nécessaire. Inversez au moment de la mise hors tension.

## 4.5 Orientation de montage de l'IMU

L'IMU est fixée à la base par des vis (son orientation n'est pas réglable), donc le firmware
active `IMU_YAW90` et convertit le vecteur up du repère IMU en coordonnées du corps :

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Contrôle de l'orientation mécanique** (possible une fois les servomoteurs montés, avant la mise
sous tension) : en utilisant les axes imprimés sur le module IMU / documentés pour celui-ci,

- l'**arbre de sortie** du servomoteur d'épaule (l'arbre sur lequel se monte le palonnier ; aussi
  appelé arbre de palonnier ou arbre de pignon) pointe vers **−Y** de l'IMU ;
- l'arbre de sortie du servomoteur de coude pointe vers **+X** de l'IMU.

De bas en haut, les deux servomoteurs sont **épaule (inférieur) → coude (supérieur)** ; ne les
intervertissez pas lors du montage des palonniers ou du câblage.

Ces deux directions sont les axes d'épaule et de coude du corps ; si elles ne correspondent pas au
matériel, l'IMU ou un support de servomoteur est installé dans le mauvais sens - corrigez avant la
mise sous tension.

Après la mise sous tension, revérifiez sur [la page 06](./06-debug-and-calibrate.md) : debout,
`up≈(0, 0, 1)` ; les quatre poses couchées sont listées dans le tableau du 6.5.

---

[← Retour au sommaire du tutoriel](./index.md)
