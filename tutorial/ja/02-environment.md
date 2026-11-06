---
title: 02 環境構築（venv、書き込みツール、ファームウェア）
description: 作業開始前の準備 - プロジェクトの .venv を作成・有効化し、ビルド済みファームウェアと公式書き込みツール（Flash Download Tool / esptool）、任意の PlatformIO、PC 側ツールと MuJoCo、シリアルポートを用意します。
---

# 02 環境構築（venv、書き込みツール、ファームウェア）

> 作業を始める前にこのページを済ませてください。**コマンドはリポジトリのルート**を前提とします。
> つまり GitHub からダウンロードした **`SR-Support` フォルダ**（zip を展開すると `SR-Support-main`
> という名前になる場合がありますが、`firmware/` と `tools/` を含むフォルダのことです）です。
> **すべての Python コマンドは `.venv` を有効化したターミナルで実行**します（2.3）。
> ビルド済みファームウェアの書き込みには PlatformIO もコンパイルも不要です。開発者向け環境（2.5）は
> コードを変更する場合にのみ必要です。

## 2.1 必要環境

- Windows、Linux、macOS（以下の各コマンドは、必要な箇所では 3 環境すべてについて記載しています）。
- USB **データ**ケーブル（充電専用ケーブルではボードが認識されません）。
- ESP32-S3-DevKitC-1（8 MB フラッシュ）。

## 2.2 コードとビルド済みファームウェアの入手

- リポジトリをクローン（または配布アーカイブを展開）し、以降のコマンドは**リポジトリのルート**で実行します。

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  （リポジトリはプライベートです。先にアクセス権を申請してください。）

- **ビルド済みイメージ**は `firmware/releases/` にあります。

  | ファイル | 用途 |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | メインファームウェア（0x0 に書き込み。組立時のセンター合わせにも使用：ファームウェアのゼロ点まで通電し、`e` は任意） |
  | `SHA256SUMS` | チェックサム |

## 2.3 仮想環境（.venv）の作成と有効化

PC 側のすべての Python ツール（esptool、PlatformIO、MuJoCo ツール）は**同じ**プロジェクト内の `.venv` に入れます。その `.venv` は、GitHub からダウンロードした **`SR-Support` フォルダ**の中に作成する必要があります（zip を展開すると `SR-Support-main` という名前になる場合がありますが、これも `firmware/` と `tools/` を含むフォルダのことです）。

まずそのフォルダに移動します。以下のコマンドはそこで実行します。

**Windows（PowerShell）**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- 正しい場所にいるか分からないときは `dir` を実行してください。`firmware`、`tools`、`tutorial` が表示される必要があります。
- Python 3.12 がない場合は `py -3 -m venv .venv` を使用してください（3.10 以上で動作します）。
- PowerShell がスクリプトの実行を拒否する場合は、このウィンドウで
  `Set-ExecutionPolicy -Scope Process Bypass` を実行してから再度有効化してください。
- `.\.venv\Scripts\Activate.ps1` は venv が生成する **PowerShell 用の有効化スクリプト**です。
  先頭の `.\` は「現在のフォルダにあるスクリプトを実行する」という意味で、PowerShell では
  必須です（`Activate.ps1` だけでは見つかりません）。他のシェルではそれぞれのファイルを使います。
  - **cmd.exe**：`.venv\Scripts\activate.bat`
  - **Git Bash**：`source .venv/Scripts/activate`
  - venv から抜けるには `deactivate`

**Windows（cmd.exe）**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> シェルの見分け方：cmd のプロンプトは `C:\...>`、PowerShell は `PS C:\...>` のような形です。
> 本チュートリアルは既定で PowerShell を使用します。cmd では有効化コマンドを
> `activate.bat` に置き換えるだけで、それ以外はすべて同じです。管理者権限は不要です。
>
> **有効化ファイルはシェルに合わせる必要があります**：cmd は `activate.bat`、PowerShell は
> `Activate.ps1` です。cmd から `.ps1` を実行しても現在のウィンドウは有効化されません
> （通常は何も起こらないか、別のウィンドウが開きます）。また、先に `.venv` が存在することを
> 確認してください（`dir` に `.venv` フォルダが表示される必要があります）。なければ先に
> `py -3.12 -m venv .venv` を実行してください。

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- 正しい場所にいるか分からないときは `ls` を実行してください。`firmware`、`tools`、`tutorial` が表示される必要があります。

有効化すると、プロンプトに **`(.venv)`** が表示されます。以降のすべてのコマンド、および後続のチュートリアルページのコマンドは、この**有効化済みのターミナル**で実行します。新しいウィンドウを開いたら再度有効化してください。有効化しないと `pip` / `python` はシステムのインストール先を指すため、インストールや実行に失敗します。

有効化できたか確認します。

- Windows：`where python` — 先頭の行が `...\SR-Support\.venv\Scripts\python.exe` である必要があります。
- Linux / macOS：`which python` — `.../SR-Support/.venv/bin/python` である必要があります。

> **cmd で有効化したら画面が消えた？** 標準の `activate.bat` は一時的にコンソールのコードページを
> 切り替える（`chcp 65001`）ため、一部のターミナルでは画面が再描画されます。これは**新しいターミナル
> ではありません**。新しいプロンプトが `(.venv)` で始まり、`where python` が `.venv` 内を指していれば
> 有効化は成功しています。再描画を避けるには、PowerShell の `Activate.ps1`（コードページを変更しません）
> を使うか、有効化せずに `.venv\Scripts\python.exe` を直接呼び出してください。

> **ディレクトリ要件（重要）**：`.venv` は必ず **`SR-Support` フォルダ（リポジトリのルート）** に置き、
> サブフォルダには置かないでください。上記の作成/有効化コマンドは**相対パス**を使うため、
> そのフォルダから実行する必要があります。新しいターミナルを開いたら、まずそのフォルダに移動して
> （PowerShell：`cd D:\Project\SR-Support`、cmd：`cd /d D:\Project\SR-Support`、パスはご自身の環境に
> 合わせてください）から有効化するか、`C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate` のような絶対パスを使用してください。
>
> 有効化後は任意のサブフォルダに `cd` しても `python` / `pip` / `pio` はその `.venv` を指したままです。
> ただしチュートリアルの `tools/...`、`firmware/...`、`hardware/v1/...` のパスは相対パスなので、
> **`SR-Support` フォルダから実行してください**。venv は作成したパスに紐づきます。リポジトリを移動
> または名前変更した場合は、`.venv` を削除して作り直してください。

## 2.4 書き込みツール（すべてのお客様 — いずれか 1 つを選択）

ビルド済みイメージは 0x0 に書き込む 1 つの bin です。**PlatformIO もツールチェーンのダウンロードも不要**です。
ターミナルが `SR-Support` フォルダにあり、プロンプトに `(.venv)` が表示されていることを確認してください。

**A. Windows GUI：Espressif Flash Download Tool**

1. Espressif 公式の「Other Tools」ページを開き、Flash Download Tools をダウンロードします。
   <https://www.espressif.com/en/support/download/other-tools>
2. 起動し、**ESP32-S3** を選択して、
   `firmware/releases/sr_support_b_ptk_factory.bin` をアドレス `0x0` に読み込み、ポートを選んで
   **START** をクリックします。

> Flash Download Tool は Windows 専用です。Linux/macOS では下記の esptool を使用してください。

**B. Windows / Linux / macOS：esptool（コマンドライン）**

```bash
pip install esptool
```

中国国内でネットワークが遅い場合はミラーを使用します。

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

書き込み（`COM27` はご自身のポート。Linux は `/dev/ttyACM0`、macOS は `/dev/tty.usbmodem*`）：

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

接続に失敗する場合はダウンロードモードに入ります：**BOOT** を押したまま **RST** をタップし、**BOOT** を離します。

## 2.5 PlatformIO（開発者専用 — ソースからのビルド）

> コードを変更しない限りスキップしてください。**注意**：PlatformIO（VS Code の PlatformIO 拡張を含む）は
> 初回使用時に espressif32 プラットフォームと Xtensa ツールチェーンをダウンロードします（PlatformIO
> レジストリと GitHub から約 1 GB）。中国国内の多くのネットワークでは遅いか失敗し、プロキシ/VPN が
> 必要になります。VS Code 拡張を使ってもダウンロードは避けられません。

ターミナルが `SR-Support` フォルダにあり、`(.venv)` が有効な状態で：

```bash
pip install platformio
```

Windows では `tools/install_platformio.ps1` を実行することもできます。これは同じ `.venv` にインストールします。確認：

```bash
pio --version
```

> 古いチュートリアルでは PlatformIO を別の `.venv-pio` にインストールしていましたが、現在は単一の
> `.venv` に入ります。アップグレード後に `pio` が見つからない場合は、有効化した `.venv` で
> `pip install platformio` を実行する（または `tools/install_platformio.ps1` を再実行する）と解決します。
> 古い `.venv-pio` は削除して構いません。

## 2.6 PC 側ツールと MuJoCo 環境（ツイン / ゼロ点校正 / ログ）

書き込みには不要です。矢印キー式ゼロ点ツール、MuJoCo ライブツイン（`tools/live_twin.py`）、シミュレーションリプレイ、ログツールを使うときにインストールしてください。ターミナルが `SR-Support` フォルダにあり、`.venv` が有効な状態で、依存関係（pyserial、numpy、MuJoCo 3.1+、gymnasium）をインストールします。

```bash
pip install -r tools/requirements.txt
```

Windows では `tools/install_tools_env.ps1` を実行することもできます（`.venv` を作成または再利用し、同じセットをインストールします）。中国国内でネットワークが遅い場合は、Tsinghua ミラー `-i https://pypi.tuna.tsinghua.edu.cn/simple` を末尾に追加してください。初回インストールでは数百 MB をダウンロードします。

**確認：環境セルフテストを実行する（import だけでなく、MuJoCo を読み込んでステップ実行します）**

```bash
python tools/env_check.py
```

最後の行が `env check: PASS` である必要があります。出力は次のような形です。

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

ボードを接続していない場合、`[--] no serial port found` は情報表示であり、PASS には影響しません。

> Linux で MuJoCo ウィンドウを開くときに GLFW/OpenGL エラーが出る場合は、システムライブラリが不足して
> います。`libgl1` と `libglew-dev` をインストールしてください（例：`sudo apt install libgl1 libglew-dev`）。
> Windows/macOS の MuJoCo ホイールには必要なものが同梱されています。`training/b_line` のシミュレーションと
> リプレイも同じ環境を使います。追加インストールは不要です。

## 2.7 ボードの接続とシリアルポートの確認

1. USB-C で接続します。Windows ではデバイスマネージャーで COM 番号を確認します。Linux では通常 `/dev/ttyACM0`（ユーザーを `dialout` グループに追加してください）、macOS では通常 `/dev/tty.usbmodem*` です。
2. そのポートを覚えてください。以降のページに出てくる `COM27` はすべてこの値です。
3. シリアルモニタや `hw_monitor.py` はポートを占有します。書き込み前に閉じてください。

## 2.8 チェックリスト

- [ ] ターミナルが**リポジトリのルート**にあり、プロンプトに `(.venv)` が表示されている（`pwd` / `Get-Location` で確認）。
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` が存在し、検証が通る（`sha256sum -c firmware/releases/SHA256SUMS`）。
- [ ] `python -m esptool version` が動作する、または Flash Download Tool が起動する。
- [ ] ボードのシリアルポートが見えている。
- [ ] （開発者）`pio --version` が動作する。
- [ ] `python tools/env_check.py` が `env check: PASS` を出力する。

必要な項目がすべて通ってから先に進んでください。

---

[← チュートリアル目次に戻る](./index.md)
