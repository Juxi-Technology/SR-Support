# SR-Support 教程（wiki 目录格式）

> **中文教程入口：[zh-hans/index.md](zh-hans/index.md)** · 繁體中文：[zh-hant/index.md](zh-hant/index.md) · English: [en/index.md](en/index.md) · 日本語: [ja/index.md](ja/index.md) · 한국어: [ko/index.md](ko/index.md) · Deutsch: [de/index.md](de/index.md) · Français: [fr/index.md](fr/index.md) · Español: [es/index.md](es/index.md) · Italiano: [it/index.md](it/index.md) · Português (BR): [pt-br/index.md](pt-br/index.md) · Português (PT): [pt-pt/index.md](pt-pt/index.md)

本目录按 Juxi Technology Wiki（wiki.juxitech.com）教程的目录规范组织：
`tutorial/<语言>/<章节>`，语言目录在前，章节文件直接放在对应语言目录下。
教程先保存在本项目路径下，发布时再复制到 `wiki-documents` 仓库。

## 目录格式

```text
tutorial/
├─ zh-hans/                     # 简体中文（11 页正文 + 目录）
│  ├─ index.md                  # 目录
│  ├─ 01-basics.md              # 基础知识
│  ├─ 02-environment.md         # 环境准备（虚拟环境、烧录工具与固件）
│  ├─ 03-build-flash.md         # 烧录主固件
│  ├─ 04-assembly.md            # 散件组装：打印、装配与接线
│  ├─ 05-zero-tool.md           # 中位零点校准（DIY 必做）
│  ├─ 06-debug-and-calibrate.md # 调试与标定
│  ├─ 07-self-righting.md       # 自扶正使用与监控
│  ├─ 08-wifi.md                # WiFi 状态页与配网
│  ├─ 09-mujoco.md              # MuJoCo 仿真与实机实时镜像
│  ├─ 10-troubleshooting.md     # 故障排查
│  └─ 11-reference.md           # 参考：模型、参数与许可
├─ zh-hant/                     # 繁體中文（11 页正文 + 目录）
├─ en/                          # English（11 页正文 + 目录）
├─ ja/                          # 日本語（11 页正文 + 目录）
├─ ko/                          # 한국어（11 页正文 + 目录）
├─ de/                          # Deutsch（11 页正文 + 目录）
├─ fr/                          # Français（11 页正文 + 目录）
├─ es/                          # Español（11 页正文 + 目录）
├─ it/                          # Italiano（11 页正文 + 目录）
├─ pt-br/                       # Português (Brasil)（11 页正文 + 目录）
├─ pt-pt/                       # Português (Portugal)（11 页正文 + 目录）
└─ images/sr-support/           # 教程图片（各语言共用；self-righting/ 与 mujoco/）
```

## 发布

把 `tutorial/` 下的语言目录与 `images/` 按 wiki-documents 仓库的既有教程结构复制过去，
保持 `tutorial/<语言>/<章节>` 的相对路径不变；然后在 wiki-documents 仓库中：

```bash
npm ci
npm run docs:dev      # 本地预览 http://localhost:5173
npm run docs:build    # 提交前验证构建
```

新教程需先在 GitHub Issues 提交教程提案，再提交 PR；合并后由 GitHub Actions 自动部署。

## 格式约定

- 每个 `.md` 必须带 `title`、`description` frontmatter；文件名使用英文 kebab-case，
  章节带两位序号；
- 每个语种目录下需要有一一对应的章节文件；当前提供简体中文、繁體中文、英文、日本語、
  한국어、Deutsch、Français、Español、Italiano、Português (BR/PT)，其余语言可继续补充，
  但不要放入空章节文件，避免发布空页面；
- 代码块必须标注语言（`bash`、`c`、`text` 等）。

## 教程配图

图片放在 `tutorial/images/sr-support/` 下，按小节分子目录。`self-righting/` 建议文件名：
`01-printed-parts.png`（打印件全家福）、`02-base-40mm.png`（40 mm 底座）、
`03-wiring.png`（接线总览）、`04-poses.png`（四种躺姿与 up 值）、
`05-trace.png`（串口执行轨迹截图）。`wifi/01-status-page.png` 为 08 页图 8-1（实机状态页
截图），`mujoco/01-mujoco-window.png` 为 09 页图 9-1（MuJoCo 仿真运行窗口截图）。
发布时按 wiki 的图片路径约定放置，并用相对路径引用。

## 来源与许可

- B 线固件/代码：MIT / Apache-2.0；
- B 线 CAD/STL：CERN-OHL-S-2.0；
- SelfRisingRobot 无许可证，本教程不包含其代码、waypoint 或模型文件；
- 专利 CN109693729A/B 需在商用前完成 FTO 评估。
