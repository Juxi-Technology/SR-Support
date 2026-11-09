---
title: 03 メインファームウェアの書き込み
description: ビルド済み bin（Flash Download Tool / esptool）または PlatformIO によるビルドで SR-Support B ラインのファームウェアを書き込みます。シリアルコマンドと起動ログについても説明します。
---

# 03 メインファームウェアの書き込み

> **完成品ユーザーはこのページをスキップできます**：工場出荷時点でファームウェアは書き込み・検証済みです。
> やり直しが必要なのはファームウェア更新時またはコード変更後のみです。お客様はビルド済みイメージ
> （3.1、PlatformIO 不要）を使用し、開発者はソースからビルドします（3.2）。

## 3.1 ビルド済みイメージの書き込み（お客様に推奨）

1. `firmware/releases/sr_support_b_ptk_factory.bin` があることを確認します（チェックサムは隣の
   `SHA256SUMS`）。
2. ダウンロードモードに入ります：**BOOT** を押したまま **RST** をタップし、**BOOT** を離します。
3. 書き込みます（ツールの準備は [02 ページ 2.4 節](./02-environment.md)。以下のコマンドは
   `SR-Support` フォルダで `.venv` を有効化して実行します）：
   - Windows GUI：Flash Download Tool → ESP32-S3 → bin を `0x0` に読み込む → START
   - Windows / Linux / macOS コマンドライン：

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. 完了したら RST を押し、3.3 の要領でログを確認します。

> 書き込みやシリアルデバッグの際は、ESP32 を USB から給電し、5 V 電源はサーボ専用にしておくことが
> できます（2 つの給電方法は [04 ページ 4.4 節](./04-assembly.md)を参照）。

> コマンドは **Windows / Linux / macOS で同一**です。変わるのはポートだけです：
> Windows は `COM27`、Linux は `/dev/ttyACM0`、macOS は `/dev/tty.usbmodem*`。
> Flash Download Tool は Windows 専用です。それ以外では esptool のコマンドラインを使用してください。

> 組立時のセンター合わせに 2 つ目のイメージは不要です：このイメージを書き込んだあと電源を入れると、
> 両サーボがファームウェアのゼロ点（1681 / 1456 µs）まで動くので、電源を切ってサーボホーンを取り付けます
> （[04 ページ 4.2 節](./04-assembly.md)）。必要なら先に `e` を送って 1520 µs の電気的中立位置に
> 合わせることもできます（結果は同等です）。

## 3.2 ソースからのビルドと書き込み（開発者）

環境：[02 ページ 2.5 節](./02-environment.md)。プロジェクト：
`firmware/sr_support_b_ptk/`（環境 `ptk7452`）。

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> `.venv` を有効化した `SR-Support` フォルダで実行してください（02 ページ 2.3 節）。3 プラットフォームで
> 同一で、`--upload-port` の `COM27` をご自身のポートに置き換えるだけです。書き込み前にシリアルポートを
> 占有しているもの（シリアルモニタ、`tools/hw_monitor.py`）を閉じてください。閉じないと
> `could not open port` / `Access is denied` になります。

ビルド成功時は RAM 約 56%、Flash 約 30% を使用します（WiFi + Web サーバー込み。WiFi なしの旧ビルドは約 7% / 12% でした）。

## 3.3 シリアルモニタ

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

（3 プラットフォーム共通。`COM27` をご自身のポートに置き換えてください。）

> **Windows GUI シリアルアシスタント（任意）**：野人家園の UartAssist（無料、単体 exe、
> Windows 専用）。公式ページ <https://cmsoft.cn/resource/101.html>、公式ダウンロード
> 入口 <https://cmsoft.cn/resource/download/101>。COM ポートを選択し、**115200、8N1、フロー制御なし**
> を設定して「改行送信」を有効にします。受信ペインで起動ログ/テレメトリを確認し、送信ボックスで
> コマンドを入力します。ダウンロードは公式リンクのみから行ってください（サードパーティサイトは
> アドウェアを同梱していることがよくあります）。exe をこのリポジトリにコミットしないでください。

**Linux / macOS のシリアルビューア（いずれか 1 つ）**：

- 推奨：上記の `pio device monitor` コマンド（プロジェクトと一緒にインストールされ、クロスプラットフォーム）；
- 軽量 CLI：`python -m serial.tools.miniterm /dev/ttyACM0 115200`
  （macOS では `/dev/tty.usbmodem*`。終了は `Ctrl-]`）。標準の
  `screen /dev/ttyACM0 115200` も使えます（終了は `Ctrl-A` のあと `K`）。
- GUI：**CoolTerm**（無料、Windows/macOS/Linux、公式サイト
  <https://freeware.the-meiers.org>）。Linux では `sudo apt install cutecom` も利用できます。

> Linux ではユーザーを `dialout` グループに追加してください：`sudo usermod -aG dialout $USER`。
> その後ログアウトして再ログインします。

ポートを開いたあと、ボードの電源を入れた直後か RST を押した直後なら起動ログが最初に表示されます。表示されない場合は RST を 1 回押してください。リセット後は次のように表示されるはずです。

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 シリアルコマンド（115200）

各コマンドはシリアルモニタ/アシスタントの**送信ボックス**に入力して Enter を押します（UartAssist では「改行送信」を有効にします）。`m` コマンドはスペースと 2 つの値が必要です（例：`m 0.5 0`）。

| コマンド | 機能 |
|---|---|
| `g` | 実行の開始/継続（このビルドは自動実行のため通常は不要） |
| `s` | 実行器を停止し、最後の目標値を保持 |
| `x` | 緊急解除：PWM をデタッチ；`r` で再アーム |
| `r` | PWM を再初期化してセンタリング |
| `t` | サーボセルフテスト（小さな動き） |
| `c` | ジャイロ + **加速度ゼロオフセット**をキャリブレーション（ロボットは水平に静止させた状態で行うこと。NVS に保存） |
| `m <q1> <q2>` | 手動関節目標値（rad） |
| `1/2` | 肩を手動で ±0.5 rad |
| `3/4` | 肘を手動で ±0.5 rad |
| `0` | 手動中立 |
| `l` | 3 秒間 50 Hz の高速ログ |
| `k` | 両サーボのセンターパルス幅を表示 |
| `o` / `p` | 肩センターを ±10 µs トリム |
| `z` | エンコーダ式ゼロ点：現在の姿勢を両関節の q=0 にする；新しいパルス幅を表示（RAM のみ。[05 ページ](./05-zero-tool.md)参照） |
| `e` | 電気的中立位置（任意）：両サーボを 1520 µs にしてサーボホーンを電気的中立位置に取り付けるためのもの。通常はファームウェアのゼロ点まで通電してそこで取り付けます（[04 ページ 4.2 節](./04-assembly.md)参照） |
| `d` | 50 Hz ツインストリームの切り替え（MuJoCo ツイン。ステータスページにも同じスイッチあり） |
| `w` | WiFi の切り替え（ホットスポット + ステータスページ/プロビジョニング。[08 ページ](./08-wifi.md)参照） |
| `v` / `b` | 肩 / 肘の符号反転 |
| `i` / `j` | IMU X / Y の符号反転 |
| `h` | スタンドホーミングの切り替え（レガシーポリシー経路） |
| `a` | レガシーのスクリプト式起き上がりテストモード |

## 3.5 電源投入時の動作

ファームウェアは `AUTORUN_ON_BOOT` を定義しています。電源投入後、実行器はロボットが**完全に倒れて静止**した状態が 0.5 秒続くのを待ってから自動的に開始します（`g` は不要）。ロボットを直立させた状態で電源を入れてください。

---

[← チュートリアル目次に戻る](./index.md)
