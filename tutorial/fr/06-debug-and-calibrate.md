---
title: 06 Débogage et calibration
description: Format de télémétrie, contrôles IMU et servomoteurs, calibration gyroscope+accéléromètre, contrôle du centre, quatre poses couchées et seuil de chute, critères de réussite.
---

# 06 Débogage et calibration

> **Les utilisateurs d'une unité finie peuvent ignorer cette page** : l'usine calibre et vérifie
> chaque unité. Ne refaites ces étapes qu'après avoir remplacé un servomoteur/IMU, remonté un
> palonnier, ou lorsqu'une mise à jour du firmware est soupçonnée d'avoir perturbé la calibration.

Il s'agit du **contrôle fonctionnel et de la calibration de l'ensemble du robot** après
l'assemblage, le flashage et la mise à zéro ; parcourez-la dans l'ordre avant d'utiliser le robot.

> **Alimentation pendant le débogage** : l'USB ne transporte que les données série. `c` n'a besoin
> que de l'IMU (les servomoteurs peuvent rester hors tension) ; `t` / `z` / `e` nécessitent le rail
> 5 V des servomoteurs sous tension. Si vous ne voulez pas que l'ESP32 soit alimenté par deux
> sources, débranchez la branche 5 V vers l'ESP32, alimentez-le uniquement par USB et laissez
> l'alimentation 5 V alimenter seulement les servomoteurs - une configuration normale, voir
> [page 04, section 4.4](./04-assembly.md).

## 6.1 Ouvrir le port série et lire la télémétrie

Dans le dossier `SR-Support` avec `.venv` activé, ouvrez le port série (`COM27` est votre port) :

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Les outils série / le téléchargement UartAssist pour Windows sont sur
[page 03, section 3.3](./03-build-flash.md).)

Après avoir ouvert le port, si la carte vient d'être alimentée ou si vous avez appuyé sur RST, vous
verrez d'abord le journal de démarrage ; s'il n'y a pas de journal de démarrage, appuyez une fois
sur RST. Ensuite, une ligne de télémétrie toutes les 250 ms :

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Champ | Signification | Comment le lire |
|---|---|---|
| `up` | Vecteur up du monde en coordonnées du corps (x avant, y gauche, z haut) | debout `(0,0,1)`, inclinaison≈0° ; poses couchées en 6.5 (par ex. `(-1,0,0)`=pitch_pos) |
| `w` | Vitesse angulaire (rad/s) | ≈0 à l'arrêt ; non nulle pendant le redressement/roulis ; le seuil de chute exige `|w|<0.9` |
| `q` | Angles de **consigne** articulaires actuels (épaule, coude, rad ; sans retour capteur) | q=0 est le bras vertical ; épaule + → grand bras vers −Y, coude + → avant-bras vers +X |
| `qd` | Vitesses de consigne articulaires | rarement nécessaire |
| `mode` | Mode d'exécution | `run` / `hold` / `manual` / `auto` |

Exemples de lecture (fenêtre `hw_watch`) :

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

`tilt` est l'angle entre le vecteur up et la verticale (à partir de `up_z`) ; 0° signifie
parfaitement debout.

Si le flux défilant est difficile à lire, utilisez la fenêtre en direct à lignes fixes (les
commandes fonctionnent toujours) :

```bash
python tools/hw_watch.py --port COM27
```

Elle redessine sur place up/tilt, la vitesse angulaire, les angles articulaires, le mode et le
dernier événement ; tapez à `cmd>` et appuyez sur Entrée pour envoyer une commande, et les
événements sont aussi ajoutés à `logs/hw_watch.log`. Pour une exécution complète de redressement
où chaque ligne brute compte, continuez avec `pio device monitor` ou `tools/hw_monitor.py` (ce
dernier écrit un résumé dans le journal toutes les 5 s).

**Comment envoyer les commandes série** : gardez le moniteur ouvert et tapez la commande suivie
d'Entrée (les commandes à un seul caractère n'ont pas besoin de guillemets). Commandes utilisées
sur cette page :

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

Le tableau complet des commandes est sur [page 03, section 3.4](./03-build-flash.md).

**Script d'auto-vérification rapide** (fermez d'abord le moniteur série pour libérer le port) :

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

La première commande lit 0.6 s de télémétrie ; pendant `--tilt 8`, inclinez le robot à la main et
elle affiche les plages up/gyro et la plage d'inclinaison, ce qui révèle une IMU bloquée ou mal
orientée.

## 6.2 Contrôles et calibration de l'IMU

`c` fait deux choses :

1. **Biais zéro du gyroscope** : moyenne de 200 échantillons immobiles (environ 2 s) pour obtenir
   l'offset de vitesse nulle ; il est utilisé pour le cycle d'alimentation en cours et refait
   automatiquement à chaque démarrage ;
2. **Zéro de l'accéléromètre** : à partir des mêmes échantillons, il moyenne le vecteur gravité,
   exige que le robot soit debout de niveau (gravité entièrement sur +Z), le contrôle de
   cohérence et le stocke en NVS (rechargé au démarrage).

Procédure (l'alimentation des servomoteurs n'est pas nécessaire) :

1. Effectuez d'abord le contrôle d'orientation mécanique de
   [page 04, section 4.5](./04-assembly.md) (arbre d'épaule vers −Y de l'IMU, arbre de coude vers
   +X de l'IMU) ;
2. Placez le robot debout sur une table DE NIVEAU, sans y toucher, câbles sans tension ;
3. Tapez `c` et appuyez sur Entrée dans le moniteur série ou dans le `cmd>` de `hw_watch` :

   ```text
   c
   ```

4. Restez immobile environ 2 s ; en cas de succès, il affiche :

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

5. `accel cal rejected: |a|=...` signifie que le robot n'était pas de niveau ou pas immobile (la
   norme de gravité s'écarte de plus de 1.5 m/s² de 9.8) ; le biais reste inchangé - replacez-le
   et renvoyez `c`.

Vérification :

- Inclinez lentement à gauche/droite et avant/arrière : les composantes x/y de `up` doivent suivre
  en douceur ; si une direction est inversée, envoyez `i` / `j` pour inverser le signe de l'axe
  IMU et relancez `c` ;
- Posez le robot et attendez 2 s : `up` doit correspondre au tableau des poses couchées du 6.5
  (par ex. `(0,-1,0)` = roll_neg) avec la face de la base à plat ;
- Une inclinaison persistante de 5°+ en position couchée signifie généralement que le zéro de
  l'accéléromètre est décalé - refaites cette section.

> Les unités finies sont calibrées en usine (stockées en NVS) ; ne refaites ceci qu'après avoir
> remplacé/remonté l'IMU ou lorsque la pose couchée est visiblement inclinée. `c` ne calibre que
> l'IMU - il ne change pas le zéro des servomoteurs (c'est [la page 05](./05-zero-tool.md)).
>
> Si vous avez utilisé des commandes manuelles avant la calibration (la télémétrie se termine par
> `manual`), `c` laisse le robot en `hold`/`manual` et le seuil de chute ne déclenchera pas de
> redressement ; maintenez-le debout et envoyez `g` pour reprendre, ou réinitialisez la carte.

## 6.3 Contrôles des servomoteurs et auto-test des directions

| Contrôle | Méthode | Attendu |
|---|---|---|
| Centres | `k` | `centers: shoulder 1681 us, elbow 1456 us` (valeurs de centre visuel intégrées en 2026-11 ; refaites la mise à zéro selon [la page 05](./05-zero-tool.md)) |
| Ajustement d'épaule | `o` / `p` (±10 µs) | Bras vertical à `q=0` |
| Direction | `m 0.5 0` / `m 0 0.5` | Épaule + → grand bras vers −Y ; coude + → avant-bras vers +X |
| Inversion de signe | `v` (épaule) / `b` (coude) | Uniquement si une direction est inversée |
| Auto-test | `t` | Petit mouvement sur les deux articulations, puis centrage |
| Neutre | `m 0 0` ou `r` | Bras vertical |

Limites articulaires :

- Commandes manuelles d'épaule `[-1.85, +1.82]` rad ; coude mécanique `±1.55` rad (atteignable par
  l'exécuteur) ;
- Les commandes manuelles `m` limitent le coude à `[-0.90, +0.70]` rad ;
- Sortie PWM 500–2500 µs à 50 Hz.

Tapez-les une par une dans la **zone d'envoi** du moniteur/assistant série (Entrée après chacune) :

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Confirmez : épaule `q>0` → grand bras vers **−Y** ; coude `q>0` → avant-bras vers **+X**.
Mauvaise direction : inversez avec `v` / `b`, ou remontez le palonnier.

## 6.4 Contrôle du centre

Intégré en usine (épaule 1681 µs / coude 1456 µs) - **peut être ignoré pour une unité de série**.
Dans un montage DIY, cela a déjà été fait avec la
[calibration du point zéro de la page 05](./05-zero-tool.md) et les valeurs intégrées dans
`config.h` (reflashez si elles ont changé) ; ici, lancez simplement `k` pour confirmer que les
centres correspondent aux valeurs intégrées. Ne revenez à la page 05 qu'après avoir ré-indexé un
palonnier, ré-assemblé, ou si le bras ne repose plus au centre visuel.

## 6.5 Quatre poses couchées et seuil de chute

| Pose | `up` au moniteur | Signification physique |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | Le haut du corps pointe vers +X |
| `pitch_neg` | `(+1, 0, 0)` | Le haut du corps pointe vers −X |
| `roll_pos` | `(0, +1, 0)` | Le haut du corps pointe vers −Y |
| `roll_neg` | `(0, -1, 0)` | Le haut du corps pointe vers +Y |

Condition du seuil de chute (firmware) :

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

C'est seulement alors qu'il affiche `getup start pose=...` et commence. Placez donc le robot,
relâchez-le et gardez-le immobile ~0.5 s ; l'agiter juste après l'avoir posé signifie généralement
qu'une main le touche encore ou que le corps roule encore.

Contrôle : placez le robot dans chacune des quatre poses, relâchez et gardez immobile ; en 0.5 s le
journal série doit afficher `getup start pose=<matching pose>`.

## 6.6 Critères de réussite

- [ ] `c` affiche `accel bias ... (saved)` ;
- [ ] `t` montre des directions correctes sur les deux articulations ;
- [ ] `k` correspond aux centres intégrés (ou vous avez refait la mise à zéro selon la page 05 et
      l'avez intégrée) ;
- [ ] les quatre poses couchées déclenchent `getup start`.

---

[← Retour au sommaire du tutoriel](./index.md)
