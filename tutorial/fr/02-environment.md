---
title: 02 Préparation de l'environnement (venv, outils de flashage et firmware)
description: Avant de commencer - créez et activez le .venv du projet, récupérez le firmware précompilé et un outil de flashage officiel (Flash Download Tool / esptool), PlatformIO facultatif, les outils côté ordinateur et MuJoCo, et le port série.
---

# 02 Préparation de l'environnement (venv, outils de flashage et firmware)

> Faites cette page avant de commencer. **Les commandes supposent la racine du dépôt** - le
> **dossier `SR-Support`** téléchargé depuis GitHub (une extraction de zip peut s'appeler
> `SR-Support-main` ; c'est le dossier qui contient `firmware/` et `tools/`). **Chaque commande
> Python s'exécute dans le terminal avec `.venv` activé** (2.3). Flasher le firmware précompilé
> ne nécessite ni PlatformIO ni compilation ; l'environnement développeur (2.5) ne sert qu'à
> modifier le code.

## 2.1 Prérequis

- Windows, Linux ou macOS (chaque commande ci-dessous est donnée pour les trois systèmes lorsque c'est utile) ;
- un câble USB **de données** (un câble de charge seule ne fera pas apparaître la carte) ;
- ESP32-S3-DevKitC-1 (8 Mo de flash).

## 2.2 Récupérer le code et le firmware précompilé

- Clonez le dépôt (ou décompressez l'archive fournie) et exécutez les commandes suivantes depuis
  la **racine du dépôt** :

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (Le dépôt est privé - demandez d'abord l'accès.)

- L'**image précompilée** se trouve dans `firmware/releases/` :

  | Fichier | Rôle |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | firmware principal (flasher à 0x0 ; sert aussi au centrage lors de l'assemblage : mettez sous tension jusqu'au zéro du firmware, `e` facultatif) |
  | `SHA256SUMS` | sommes de contrôle |

## 2.3 Créer et activer l'environnement virtuel (.venv)

Tous les outils Python côté ordinateur (esptool, PlatformIO, les outils MuJoCo) vont dans le
**même** `.venv` local au projet, et ce `.venv` doit être créé dans le **dossier `SR-Support`**
téléchargé depuis GitHub (une extraction de zip peut s'appeler `SR-Support-main` ; là encore, le
dossier qui contient `firmware/` et `tools/`).

Entrez d'abord dans ce dossier - les commandes ci-dessous s'y exécutent :

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Vous n'êtes pas sûr d'être au bon endroit ? Lancez `dir` ; il doit lister `firmware`, `tools`, `tutorial` ;
- Sans Python 3.12, utilisez `py -3 -m venv .venv` (3.10+ fonctionne) ;
- Si PowerShell refuse d'exécuter des scripts, lancez
  `Set-ExecutionPolicy -Scope Process Bypass` dans cette fenêtre et activez à nouveau ;
- `.\.venv\Scripts\Activate.ps1` est le **script d'activation PowerShell** créé par venv :
  le `.\` initial signifie « exécute le script dans le dossier courant » et est obligatoire dans
  PowerShell (`Activate.ps1` seul ne sera pas trouvé). Les autres shells utilisent leur propre fichier :
  - **cmd.exe** : `.venv\Scripts\activate.bat`
  - **Git Bash** : `source .venv/Scripts/activate`
  - Quittez le venv avec `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> Distinguer les shells : l'invite de cmd ressemble à `C:\...>`, celle de PowerShell à `PS C:\...>`.
> Le tutoriel utilise PowerShell par défaut ; sous cmd, remplacez simplement la commande d'activation
> par `activate.bat`, tout le reste est identique. Les droits administrateur ne sont pas nécessaires.
>
> **Le fichier d'activation doit correspondre au shell** : cmd utilise `activate.bat`, PowerShell
> utilise `Activate.ps1`. Lancer le `.ps1` depuis cmd n'active pas la fenêtre courante (généralement
> rien ne se passe, ou une fenêtre séparée s'ouvre). Vérifiez aussi que `.venv` existe d'abord (`dir`
> doit lister le dossier `.venv`) ; sinon, lancez d'abord `py -3.12 -m venv .venv`.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- Vous n'êtes pas sûr d'être au bon endroit ? Lancez `ls` ; il doit lister `firmware`, `tools`, `tutorial`.

Après activation, l'invite affiche **`(.venv)`**. Toutes les commandes ci-dessous et des pages
suivantes du tutoriel s'exécutent dans ce **terminal activé** ; réactivez après avoir ouvert une
nouvelle fenêtre. Sans activation, `pip` / `python` pointent vers l'installation système et les
installations ou exécutions échoueront.

Confirmez que l'activation a fonctionné :

- Windows : `where python` - la première ligne doit être `...\SR-Support\.venv\Scripts\python.exe` ;
- Linux / macOS : `which python` - doit être `.../SR-Support/.venv/bin/python`.

> **Écran effacé après l'activation sous cmd ?** Le fichier `activate.bat` standard bascule
> temporairement la page de code de la console (`chcp 65001`) et certains terminaux redessinent
> l'écran - ce n'est **pas un nouveau terminal**. Si la nouvelle invite commence par `(.venv)` et
> que `where python` pointe vers `.venv`, l'activation a réussi. Pour éviter le redessin, utilisez
> `Activate.ps1` de PowerShell (il ne touche pas à la page de code) ou appelez
> `.venv\Scripts\python.exe` sans activer.

> **Exigence de répertoire (important)** : `.venv` doit se trouver dans le **dossier `SR-Support`
> (la racine du dépôt)**, jamais dans un sous-dossier. Les commandes de création/activation
> ci-dessus utilisent des **chemins relatifs**, elles doivent donc être exécutées depuis ce
> dossier - après avoir ouvert un nouveau terminal, entrez-y d'abord
> (PowerShell : `cd D:\Project\SR-Support` ; cmd : `cd /d D:\Project\SR-Support`, avec votre chemin)
> avant d'activer, ou utilisez un chemin absolu comme
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Une fois activé, vous pouvez `cd` dans n'importe quel sous-dossier et `python` / `pip` / `pio`
> pointent toujours vers ce `.venv` ; mais les chemins `tools/...`, `firmware/...` et
> `hardware/v1/...` du tutoriel sont relatifs, donc **exécutez-les depuis le dossier
> `SR-Support`**. Le venv est lié au chemin où il a été créé : après avoir déplacé ou renommé le
> dépôt, supprimez `.venv` et recréez-le.

## 2.4 Outils de flashage (tous les clients - choisissez-en un)

Une image précompilée est un seul bin à flasher à 0x0 - **pas de PlatformIO, pas de
téléchargement de chaîne d'outils**. Assurez-vous que le terminal est dans le dossier `SR-Support`
et que l'invite affiche `(.venv)`.

**A. Interface graphique Windows : Espressif Flash Download Tool**

1. Ouvrez la page officielle « Other Tools » d'Espressif et téléchargez Flash Download Tools :
   <https://www.espressif.com/en/support/download/other-tools>
2. Lancez-le ; sélectionnez **ESP32-S3**, chargez
   `firmware/releases/sr_support_b_ptk_factory.bin` à l'adresse `0x0`, choisissez le port et
   cliquez sur **START**.

> Flash Download Tool est réservé à Windows ; sous Linux/macOS, utilisez esptool ci-dessous.

**B. Windows / Linux / macOS : esptool (ligne de commande)**

```bash
pip install esptool
```

Réseau lent en Chine - utilisez un miroir :

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Flashez (`COM27` est votre port ; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`) :

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

Si la connexion échoue, passez en mode téléchargement : maintenez **BOOT**, appuyez sur **RST**, relâchez **BOOT**.

## 2.5 PlatformIO (développeurs uniquement - compilation depuis les sources)

> Ignorez cette section sauf si vous modifiez le code. **Remarque** : PlatformIO (y compris
> l'extension PlatformIO de VS Code) télécharge la plateforme espressif32 et la chaîne d'outils
> Xtensa à la première utilisation (~1 GB depuis le registre PlatformIO et GitHub). Sur de
> nombreux réseaux en Chine, c'est lent ou échoue et nécessite un proxy/VPN ; l'extension VS Code
> n'évite pas le téléchargement.

Le terminal étant dans le dossier `SR-Support` et `(.venv)` actif :

```bash
pip install platformio
```

Sous Windows, vous pouvez aussi lancer `tools/install_platformio.ps1`, qui installe dans ce même
`.venv`. Vérifiez :

```bash
pio --version
```

> Les anciennes versions du tutoriel installaient PlatformIO dans un `.venv-pio` séparé ; il vit
> désormais dans l'unique `.venv`. Si `pio` est introuvable après une mise à jour, lancez
> `pip install platformio` dans le `.venv` activé (ou relancez `tools/install_platformio.ps1`) ;
> l'ancien `.venv-pio` peut être supprimé.

## 2.6 Outils côté ordinateur et environnement MuJoCo (jumeau / mise à zéro / journaux)

Pas nécessaire pour le flashage. Installez-le lorsque vous utilisez l'outil de mise à zéro aux
flèches, le jumeau en direct MuJoCo (`tools/live_twin.py`), la relecture de simulation ou les
outils de journaux. Le terminal étant dans le dossier `SR-Support` et `.venv` actif, installez les
dépendances (pyserial, numpy, MuJoCo 3.1+, gymnasium) :

```bash
pip install -r tools/requirements.txt
```

Sous Windows, vous pouvez aussi lancer `tools/install_tools_env.ps1` (crée/réutilise `.venv` et
installe le même ensemble). Sur un réseau lent en Chine, ajoutez le miroir Tsinghua
`-i https://pypi.tuna.tsinghua.edu.cn/simple` ; la première installation télécharge quelques
centaines de Mo.

**Vérification : lancez l'auto-test de l'environnement (il charge et fait avancer MuJoCo, pas seulement les imports)**

```bash
python tools/env_check.py
```

La dernière ligne doit être `env check: PASS`, avec une sortie comme :

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Sans carte branchée, `[--] no serial port found` est informatif et n'affecte pas le PASS.

> Sous Linux, une erreur GLFW/OpenGL à l'ouverture de la fenêtre MuJoCo signifie des bibliothèques
> système manquantes : installez `libgl1` et `libglew-dev` (par ex. `sudo apt install libgl1 libglew-dev`).
> Les wheels MuJoCo Windows/macOS embarquent ce qu'il faut. La simulation et la relecture
> `training/b_line` utilisent le même environnement - rien de plus à installer.

## 2.7 Connecter la carte et confirmer le port série

1. Connectez la carte en USB-C ; sous Windows, lisez le numéro COM dans le Gestionnaire de
   périphériques, sous Linux c'est généralement `/dev/ttyACM0` (ajoutez votre utilisateur au
   groupe `dialout`), sous macOS généralement `/dev/tty.usbmodem*` ;
2. Retenez le port - chaque `COM27` des pages suivantes correspond à cette valeur ;
3. Un moniteur série ou `hw_monitor.py` occupe le port ; fermez-le avant de flasher.

## 2.8 Liste de vérification

- [ ] le terminal est à la **racine du dépôt** et l'invite affiche `(.venv)` (vérifiez avec
      `pwd` / `Get-Location`) ;
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` existe et se vérifie
      (`sha256sum -c firmware/releases/SHA256SUMS`) ;
- [ ] `python -m esptool version` fonctionne, ou Flash Download Tool s'ouvre ;
- [ ] le port série de la carte est visible ;
- [ ] (développeurs) `pio --version` fonctionne ;
- [ ] `python tools/env_check.py` affiche `env check: PASS`.

Ne continuez que lorsque les éléments dont vous avez besoin passent.

---

[← Retour au sommaire du tutoriel](./index.md)
