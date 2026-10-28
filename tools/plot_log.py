#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot a CSV log captured by sr_tune.py.

用法：
  python plot_log.py run1.csv
  python plot_log.py run1.csv --out run1.png
"""

import argparse
import csv
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Plot SR-Support CSV log")
    parser.add_argument("csv", help="sr_tune.py --csv 生成的文件")
    parser.add_argument("--out", help="保存 PNG；不指定则弹窗显示")
    args = parser.parse_args()

    path = Path(args.csv)
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1

    try:
        import matplotlib
        if args.out:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("缺少 matplotlib：pip install -r tools/requirements.txt", file=sys.stderr)
        return 1

    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                rows.append({k: (v if k == "state" else float(v)) for k, v in row.items()})
            except (TypeError, ValueError):
                continue

    if not rows:
        print("没有可绘制的数据", file=sys.stderr)
        return 1

    t = [i * 0.1 for i in range(len(rows))]  # 固件 PRINT_PERIOD_MS=100 -> 10Hz CSV
    states = [r["state"] for r in rows]

    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(10, 7))
    axes[0].plot(t, [r["tilt"] for r in rows], label="tilt")
    axes[0].set_ylabel("tilt (deg)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="upper right")

    axes[1].plot(t, [r["s1_target"] for r in rows], label="s1 target")
    axes[1].plot(t, [r["s1_current"] for r in rows], label="s1 current", alpha=0.7)
    axes[1].set_ylabel("servo 1 (deg)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="upper right")

    axes[2].plot(t, [r["s2_target"] for r in rows], label="s2 target")
    axes[2].plot(t, [r["s2_current"] for r in rows], label="s2 current", alpha=0.7)
    axes[2].set_ylabel("servo 2 (deg)")
    axes[2].set_xlabel("time (s, assumed 10 Hz CSV)")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc="upper right")

    # 状态切换处画竖线
    prev = None
    for i, s in enumerate(states):
        if s != prev:
            for ax in axes:
                ax.axvline(t[i], color="gray", linestyle="--", linewidth=0.6, alpha=0.6)
            prev = s

    fig.suptitle(path.name)
    fig.tight_layout()

    if args.out:
        fig.savefig(args.out, dpi=150)
        print(f"已保存 {args.out}")
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
