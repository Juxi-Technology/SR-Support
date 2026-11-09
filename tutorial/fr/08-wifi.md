---
title: 08 Page d'état WiFi et provisionnement
description: Point d'accès, page d'état et provisionnement sur le réseau domestique ; la simulation MuJoCo et le jumeau en direct sont couverts à la page 09.
---

# 08 Page d'état WiFi et provisionnement

Cette étape est facultative et n'est pas nécessaire à l'auto-redressement proprement dit. La
fenêtre de simulation MuJoCo et le jumeau en direct ont leur propre page :
[page 09](./09-mujoco.md).

## 8.1 Point d'accès et page d'état

Point d'accès : SSID `SR-Support`, mot de passe `srsupport`, adresse `192.168.4.1` (`w` l'active et
le désactive ; activé par défaut au démarrage). `w` s'envoie par série : tapez `w` dans la zone
d'envoi du moniteur/assistant série et appuyez sur Entrée ; les outils série / le téléchargement
UartAssist pour Windows sont sur [page 03, section 3.3](./03-build-flash.md).

Rejoignez le point d'accès et ouvrez `http://192.168.4.1` (les téléphones affichent généralement le
portail automatiquement). La page se rafraîchit toutes les 300 ms : état, vecteur up et barre de
verticalité, consignes articulaires, pose/phase de redressement, état du WiFi domestique et
interrupteur du flux jumeau (miroir en direct sur [page 09](./09-mujoco.md)). Si le navigateur
utilise un proxy, ajoutez une exception pour cette adresse.

![Figure 8-1 La page d'état du robot](../images/sr-support/wifi/01-status-page.png)

*Figure 8-1 : la page d'état du robot (ouverte dans un navigateur à l'adresse du robot). Ici le robot a rejoint le WiFi domestique : la carte Home WiFi affiche l'état de connexion et la Robot IP, avec l'interrupteur du flux jumeau en dessous (utilisation en 9.2).*

## 8.2 Provisionnement (rejoindre le WiFi domestique)

Sur la page d'état, utilisez la carte Home WiFi : `Scan` → choisissez un réseau → saisissez le mot
de passe → `Connect`. En cas de succès, l'ESP32 fonctionne en AP+STA :

- le point d'accès reste actif (le travail sur banc n'est pas affecté) ;
- le robot est joignable sur le réseau local domestique (la page affiche son `Robot IP` ; utilisez cette adresse dans la commande du jumeau page 09) ;
- les identifiants sont stockés en NVS et la connexion est rétablie automatiquement au démarrage.

2.4 GHz uniquement ; les scans/connexions sont refusés pendant qu'un redressement est en cours.

---

[← Retour au sommaire du tutoriel](./index.md)
