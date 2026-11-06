# firmware/releases — 预编译固件（客户直接烧录）

| 文件 | 用途 | 烧录地址 |
|---|---|---|
| `sr_support_b_ptk_factory.bin` | 主固件（SR-Support B 线，PTK7452MG） | **0x0** |
| `servo_center_ptk.bin` | 装配找中辅助（两只舵机输出 1520 µs） | **0x0** |
| `SHA256SUMS` | 文件校验和 | — |

- 目标硬件：ESP32-S3-DevKitC-1（8 MB Flash），espressif32 8.0.0 / Arduino core 3.3.12；
- 版本：v0.1.0（2026-11-06，对应源码提交 `fc51a07`）；
- 合并镜像已包含 bootloader（0x0）、分区表（0x8000）、boot_app0（0xe000）、应用（0x10000），
  所以只需要在 **0x0** 烧一个文件，不需要 PlatformIO。

## 烧录方式

**Windows（图形界面）**

1. 从乐鑫官方 "Other Tools" 页下载 Flash Download Tool：
   <https://www.espressif.com/zh-hans/support/download/other-tools>
2. 打开工具选 **ESP32-S3**；在地址 `0x0` 处加载 `sr_support_b_ptk_factory.bin`；
   选择串口，点击 **START**。

**Windows / Linux / macOS（命令行，推荐）**

```bash
pip install esptool
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 sr_support_b_ptk_factory.bin
```

Linux/macOS 把 `COM27` 换成 `/dev/ttyACM0` 或 `/dev/tty.usbmodem*`。
国内网络装不上时可用镜像：`pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple`。

进入下载模式：按住 **BOOT**，点按一下 **RST**，松开 **BOOT**；烧录完成后按 RST 启动。

## 校验

```bash
sha256sum -c SHA256SUMS
```

## 版本与再生成

- 用 PlatformIO 构建 `firmware/sr_support_b_ptk` 与 `firmware/servo_center_ptk`，再用
  esptool `merge-bin` 按 `0x0 bootloader / 0x8000 partitions / 0xe000 boot_app0 /
  0x10000 firmware` 合并；
- 推送 `v*` 标签时，GitHub Actions（`.github/workflows/firmware-release.yml`）会自动
  重新构建并把同样的资产名附到 Release，教程中的 `releases/latest/download/...` 链接始终有效；
- 许可：固件基于 MIT/Apache-2.0，见根目录 `LICENSE` 与 `third_party/juxi-2dof/`。
