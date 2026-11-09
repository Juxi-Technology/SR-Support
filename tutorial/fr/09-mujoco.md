---
title: 09 Simulation MuJoCo et jumeau en direct
description: La fenêtre de simulation MuJoCo locale (relecture du redressement sur quatre poses), le jumeau en direct WiFi du robot réel et la journalisation de la télémétrie.
---

# 09 Simulation MuJoCo et jumeau en direct

MuJoCo est utilisé de deux façons dans ce projet, toujours avec `hardware/v1/robot_v1.xml` (le
modèle de même conception que le robot réel) :

- **Simulation locale** : sans robot connecté, rejouez en boucle les quatre poses couchées et
  leurs redressements sur l'ordinateur pour valider les séquences de référence et observer le
  mouvement ;
- **Jumeau en direct** : le robot réel diffuse son attitude par WiFi et la fenêtre MuJoCo
  reproduit le mouvement réel en temps réel (un jumeau numérique).

La fenêtre se comporte de la même façon dans les deux cas : un glisser avec le bouton gauche fait
tourner la vue, un glisser avec le bouton droit déplace la vue et la molette zoome. Avant la
première utilisation, créez et activez le `.venv` comme sur [page 02](./02-environment.md) et
installez-y les dépendances de l'outil (`pip install -r tools/requirements.txt`, voir page 02).

## 9.1 Fenêtre de simulation locale

Dans le dossier `SR-Support` (`.venv` activé) :

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

La fenêtre s'intitule `MuJoCo : sr_support_v1` (figure 9-1). Le robot est placé successivement
dans les quatre poses couchées (`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`) ; à chaque
fois, l'exécuteur exécute la séquence de référence avec exactement les paramètres du firmware
jusqu'à ce que le robot se redresse, puis la pose suivante est appliquée. La boucle se répète
jusqu'à ce que vous fermiez la fenêtre. Le terminal affiche la pose et le résultat :

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` signifie que la pose s'est redressée en simulation. En cas de `ok=False`, vérifiez la
séquence de référence et les paramètres que vous avez modifiés par rapport à
[page 06](./06-debug-and-calibrate.md).

![Figure 9-1 La fenêtre de simulation MuJoCo (relecture du redressement sur quatre poses)](../images/sr-support/mujoco/01-mujoco-window.png)

*Figure 9-1 : une image de la boucle des quatre poses - l'exécuteur redresse une pose couchée.*

> Différence de modèle connue : avec le modèle à masse 1×, `roll_neg` affiche `ok=False` en
> simulation (la masse/friction du bras du modèle diffère du robot réel, voir
> [page 11](./11-reference.md) 11.4) ; cela n'affecte pas le firmware réel.

## 9.2 Jumeau en direct via WiFi

Prérequis : le robot a rejoint le réseau domestique comme sur [page 08](./08-wifi.md) et
l'ordinateur est sur le même réseau. La page d'état affiche l'adresse du robot sous `Robot IP` ;
copiez-la dans la commande ci-dessous.

1. Sur la page d'état, appuyez sur `Twin ON` (équivalent à `d` en série) ;
2. Dans le dossier `SR-Support` avec `.venv` activé, lancez (remplacez l'adresse par le
   `Robot IP` de la page d'état) :

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

Le modèle reproduit l'attitude réelle en direct (flux de quaternions à 50 Hz) et maintient le
corps sur le sol ; le bras est maintenu à son angle de contact avec le sol comme le servomoteur
bloqué, de sorte qu'il ne pénètre jamais dans le sol.

- Ordinateur directement sur le point d'accès du robot : l'adresse est toujours `192.168.4.1`,
  `python tools/live_twin.py --tcp 192.168.4.1:3333` ;
- Variante filaire : `python tools/live_twin.py --port COM27` (l'outil envoie `d` pour
  activer le flux automatiquement) ;
- Relecture hors ligne : `python tools/live_twin.py --replay logs/hw_fast_xxx.txt` ;
- Le jumeau est en lecture seule, hormis la bascule du flux : il n'envoie jamais de commandes de
  contrôle.

## 9.3 Journalisation de la télémétrie

```bash
python tools/tcp_log.py
```

Enregistre le flux de télémétrie dans `logs/wifi_<time>.txt` pour la relecture hors ligne
(`--replay`) et l'analyse des pannes. Sur le point d'accès, il se connecte par défaut à
`192.168.4.1:3333` ; sur le réseau domestique, passez le `Robot IP` de la page d'état :

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 Référence de simulation et d'entraînement

`training/b_line/` fournit l'exécuteur, les séquences de référence et l'environnement de
simulation - identiques valeur pour valeur au firmware - pour la relecture, la validation et le
réglage des paramètres ; les fichiers du modèle sont décrits sur [page 11](./11-reference.md) 11.1.

---

[← Retour au sommaire du tutoriel](./index.md)
