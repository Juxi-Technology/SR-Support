---
title: 09 Dépannage
description: Symptômes, causes et correctifs courants du SR-Support couvrant l'IMU, le port série, le seuil de chute, les délais d'expiration de l'exécuteur et le WiFi.
---

# 09 Dépannage

Les commandes série s'envoient via un assistant/moniteur série : tapez-les dans la zone d'envoi et
appuyez sur Entrée (activez « send newline » dans UartAssist) ; les outils série / le téléchargement
UartAssist pour Windows sont sur [page 03, section 3.3](./03-build-flash.md).

## 9.1 Symptômes courants

| Symptôme | Cause probable | Correctif |
|---|---|---|
| `waiting for IMU startup 5000 ms...` puis `IMU not ready` | Démarrage lent de l'IMU, câblage défectueux, mauvaise adresse | Attendez 5–10 s ; vérifiez 3V3, SDA=GPIO6 / SCL=GPIO7, adresse 0x23 |
| Répétition de `IMU lost -> bus reset + re-init` | Fils I²C longs ou desserrés | Raccourcissez les fils, réinsérez les connecteurs |
| Échec du flashage avec `could not open port` / `Access is denied` | Port série occupé par le moniteur/assistant série | Fermez d'abord `hw_monitor.py` ou le moniteur série |
| Le robot ne démarre pas après avoir été posé | Corps pas immobile, ou une main le touche | Relâchez et gardez immobile ≥0.5 s ; surveillez `getup start` |
| Agitation immédiate / mauvaise direction | Seuil de chute déclenché en plein roulis, mauvaise classification | Posez et relâchez proprement ; réessayez |
| L'exécution s'arrête et affiche `executor timeout` après 14 s | La référence ne s'est pas terminée | Repli normal ; nouvelle tentative automatique après 1.5 s ; conservez le journal |
| Événements `executor re-plan` occasionnels | Repli normal après un appui `roll_neg` raté | Vérifiez si cela se termine par `done` |
| Le servomoteur bourdonne / chauffe | Blocage ou cible contraignante | Envoyez `x` ou coupez l'alimentation ; vérifiez les limites et le dégagement mécanique |
| Le bras heurte le corps pendant l'auto-redressement | Mouvement d'épaule trop grand | Vérifiez `Q_SHOULDER_MAX` et le dégagement ; conservez la hauteur de base d'environ 68 mm |
| `up` ne correspond pas à la pose réelle (inclinaison persistante de 5°+ en position couchée) | Offsets de zéro de l'accéléromètre non calibrés | Placez le robot de niveau et envoyez `c` (voir [page 06, 6.2](./06-debug-and-calibrate.md)) |
| Le bras ne repose pas au centre visuel après la rétraction | Zéro dérivé (ré-indexé/ré-assemblé sans refaire la mise à zéro) | Refaites la mise à zéro avec [l'outil de la page 05](./05-zero-tool.md) et intégrez-la |
| Le servomoteur bourdonne/claque après un redressement | Auto-excitation transitoire du servomoteur analogique après un mouvement ample/des blocages (la sortie est constante) | Se dissipe seul ; ajoutez des rondelles amortisseuses en caoutchouc ou utilisez un servomoteur numérique ; pincer le bras le fait taire instantanément |
| Page d'état / provisionnement inaccessible | Proxy du navigateur non contourné, ou point d'accès désactivé | Ajoutez `192.168.4.1` aux exceptions du proxy ; envoyez `w` pour activer le WiFi |

## 9.2 Commandes de sécurité

| Situation | Commande |
|---|---|
| Arrêt immédiat du mouvement | `s` (maintenir la dernière cible) ou `x` (détacher le PWM, libérer le couple) |
| Récupération après `x` | `r` réinitialise le PWM et centre |
| Une articulation va dans le mauvais sens | inversion de signe `v` (épaule) / `b` (coude) |

## 9.3 Capturer une panne

Conservez la partie correspondante de `logs/hw_monitor.log`. Les lignes clés sont :

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```

---

[← Retour au sommaire du tutoriel](./index.md)
