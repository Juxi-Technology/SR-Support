# SR-Support 教程（wiki 目录格式）

本目录按 Juxi Technology Wiki（wiki.juxitech.com）教程的目录规范组织：
`tutorial/<语言>/<章节>`，语言目录在前，章节文件直接放在对应语言目录下。
教程先保存在本项目路径下，发布时再复制到 `wiki-documents` 仓库。

## 目录格式

```text
tutorial/
├─ zh-hans/                     # 简体中文（11 页正文 + 目录）
│  ├─ index.md                  # 目录
│  ├─ 01-basics.md              # 基础知识
│  ├─ 02-environment.md         # 环境准备（软件与工具）
│  ├─ 03-assembly.md            # 散件组装：打印、装配与接线
│  ├─ 04-build-flash.md         # 第一步：构建与烧录
│  ├─ 05-debug-and-checks.md    # 调试与检查
│  ├─ 06-zero-tool.md           # 中位零点校准（DIY 必做）
│  ├─ 07-calibrate.md           # 第二步：标定
│  ├─ 08-self-righting.md       # 第三步：自扶正使用与监控
│  ├─ 09-wifi-twin.md           # 第四步：WiFi 与仿真镜像
│  ├─ 10-troubleshooting.md     # 故障排查
│  └─ 11-reference.md           # 参考：模型、参数与许可
├─ en/                          # 英文（与中文逐文件对应，11 页正文 + 目录）
├─ de/                          # 其余语言目录已建好，待翻译（当前为占位）
├─ zh-hant/  ja/  ko/  fr/  es/  it/  pt-br/  pt-pt/
└─ images/sr-support/self-righting/   # 教程图片（各语言共用）
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
- 每个语种目录下需要有一一对应的章节文件；当前提供简体中文与英文，其余语言待翻译，
  翻译完成前不放入空章节文件，避免发布空页面；
- 代码块必须标注语言（`bash`、`c`、`text` 等）。

## 教程配图

图片放在 `tutorial/images/sr-support/self-righting/`，建议文件名：
`01-printed-parts.png`（打印件全家福）、`02-base-40mm.png`（40 mm 底座）、
`03-wiring.png`（接线总览）、`04-poses.png`（四种躺姿与 up 值）、
`05-trace.png`（串口执行轨迹截图）。发布时按 wiki 的图片路径约定放置，并用相对路径引用。

## 来源与许可

- B 线固件/代码：MIT / Apache-2.0；
- B 线 CAD/STL：CERN-OHL-S-2.0；
- SelfRisingRobot 无许可证，本教程不包含其代码、waypoint 或模型文件；
- 专利 CN109693729A/B 需在商用前完成 FTO 评估。
