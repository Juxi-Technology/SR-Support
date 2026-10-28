#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SR-Support serial tuner

用途：
  - 连接 ESP32-S3 固件，手动移动舵机；
  - 从 CSV 状态流里捕获 s1/s2 目标角，生成 getup_sequence.h 的 waypoint 片段；
  - 记录日志，供 plot_log.py 画图。

依赖：pyserial
用法：
  python sr_tune.py --list
  python sr_tune.py --port COM5
  python sr_tune.py --port /dev/ttyUSB0 --csv run1.csv

本地命令（以冒号开头，不会发给固件）：
  :w [name]     捕获当前 s1/s2 目标角为一个 waypoint
  :l            列出已捕获 waypoint
  :c            清空
  :s <pose>     输出 C 片段到 waypoints_<pose>.txt（pose=front/back/left/right）
  :q            退出
  :h            帮助

其余输入原样发给固件（例如 g、x、m、a、d、1-8、p、s）。
"""

import argparse
import math
import queue
import sys
import threading
import time
from pathlib import Path

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("缺少 pyserial：pip install -r tools/requirements.txt", file=sys.stderr)
    raise

CSV_FIELDS = [
    "state", "tilt", "roll", "pitch",
    "s1_target", "s1_current", "s2_target", "s2_current",
    "attempts", "imu_valid",
]
CSV_HEADER = ",".join(CSV_FIELDS)


def parse_csv(line: str):
    parts = line.strip().split(",")
    if len(parts) != len(CSV_FIELDS):
        return None
    row = {"state": parts[0]}
    try:
        for i, name in enumerate(CSV_FIELDS[1:], start=1):
            row[name] = float(parts[i])
    except ValueError:
        return None
    return row


class SerialReader(threading.Thread):
    def __init__(self, ser: "serial.Serial", out_queue: queue.Queue):
        super().__init__(daemon=True)
        self.ser = ser
        self.out_queue = out_queue
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            try:
                raw = self.ser.readline()
            except serial.SerialException as exc:
                self.out_queue.put(("error", f"串口读取失败: {exc}"))
                return
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if line:
                self.out_queue.put(("line", line))


class InputReader(threading.Thread):
    def __init__(self, out_queue: queue.Queue):
        super().__init__(daemon=True)
        self.out_queue = out_queue

    def run(self):
        while True:
            try:
                line = input()
            except EOFError:
                return
            self.out_queue.put(("input", line))


def list_serial_ports():
    ports = list(list_ports.comports())
    if not ports:
        print("没有找到串口。检查 USB 线/驱动。")
        return
    for p in ports:
        print(f"{p.device}\t{p.description}")


def save_snippet(path: Path, pose: str, waypoints):
    lines = []
    lines.append(f"// Captured waypoints for pose {pose.upper()}")
    lines.append("// Paste into firmware/sr_support_2dof/getup_sequence.h")
    lines.append("// values are radians (0 = center, +/-1.55 = +/-89 deg)")
    lines.append("{")
    for i, (s1, s2) in enumerate(waypoints):
        lines.append(f"  {{ {s1:.4f}f, {s2:.4f}f }},  // #{i + 1}")
    lines.append("}")
    lines.append("")
    lines.append(f"// length = {len(waypoints)}")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"已写入 {path}（{len(waypoints)} 个 waypoint）")


def print_local_help():
    print("本地命令: :w [name] 捕获  :l 列表  :c 清空  :s <pose> 保存  :q 退出")
    print("固件命令: g 起立  x 急停  m 手动/自动  a/d 选中舵机 -/+5°  j/l 舵机2")
    print("          1-8 选择舵机  c 回中  p 状态  s 舵机状态  v 详细  ? 帮助")


def main():
    parser = argparse.ArgumentParser(description="SR-Support serial tuner")
    parser.add_argument("--port", help="串口，例如 COM5 或 /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--csv", help="把 CSV 状态流写入这个文件")
    parser.add_argument("--out-dir", default=".", help="waypoint 片段输出目录")
    parser.add_argument("--raw", action="store_true", help="打印所有串口行（默认 2Hz 摘要）")
    parser.add_argument("--list", action="store_true", help="列出串口后退出")
    args = parser.parse_args()

    if args.list:
        list_serial_ports()
        return
    if not args.port:
        list_serial_ports()
        parser.error("需要 --port；或先用 --list 查看串口")

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
    except serial.SerialException as exc:
        print(f"打开串口失败: {exc}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_file = None
    if args.csv:
        csv_file = open(args.csv, "w", encoding="utf-8", newline="")
        csv_file.write(CSV_HEADER + "\n")
        csv_file.flush()

    serial_q = queue.Queue()
    input_q = queue.Queue()
    reader = SerialReader(ser, serial_q)
    reader.start()
    InputReader(input_q).start()

    waypoints = []
    last_row = None
    last_status = 0.0

    print(f"已连接 {args.port} @ {args.baud}")
    print_local_help()

    try:
        while True:
            did_work = False

            # 串口输出
            while True:
                try:
                    kind, payload = serial_q.get_nowait()
                except queue.Empty:
                    break
                did_work = True
                if kind == "error":
                    print(payload, file=sys.stderr)
                    continue
                line = payload
                if csv_file and parse_csv(line):
                    csv_file.write(line + "\n")
                    csv_file.flush()

                row = parse_csv(line)
                if row:
                    last_row = row
                    now = time.time()
                    if args.raw:
                        print(line)
                    elif now - last_status >= 0.5:
                        last_status = now
                        print(
                            f"[{row['state']:>14}] tilt={row['tilt']:6.1f}° "
                            f"s1={row['s1_target']:6.1f}°/{row['s1_current']:6.1f}° "
                            f"s2={row['s2_target']:6.1f}°/{row['s2_current']:6.1f}°"
                        )
                else:
                    print(line)

            # 键盘输入
            while True:
                try:
                    kind, payload = input_q.get_nowait()
                except queue.Empty:
                    break
                did_work = True
                cmd = payload.strip()
                if not cmd:
                    continue
                if cmd.startswith(":"):
                    parts = cmd.split()
                    op = parts[0]
                    if op == ":q":
                        raise KeyboardInterrupt
                    if op == ":h":
                        print_local_help()
                    elif op == ":w":
                        if last_row is None:
                            print("还没有收到 CSV 状态；确认固件 v=开、串口 115200")
                            continue
                        s1 = math.radians(last_row["s1_target"])
                        s2 = math.radians(last_row["s2_target"])
                        name = parts[1] if len(parts) > 1 else f"wp{len(waypoints) + 1}"
                        waypoints.append((s1, s2))
                        print(f"捕获 {name}: s1={last_row['s1_target']:.1f}° "
                              f"s2={last_row['s2_target']:.1f}° "
                              f"-> ({s1:.4f}, {s2:.4f}) rad")
                    elif op == ":l":
                        if not waypoints:
                            print("还没有 waypoint")
                        for i, (s1, s2) in enumerate(waypoints):
                            print(f"  #{i + 1}: {math.degrees(s1):7.1f}°, "
                                  f"{math.degrees(s2):7.1f}°  ({s1:.4f}, {s2:.4f}) rad")
                    elif op == ":c":
                        waypoints.clear()
                        print("已清空")
                    elif op == ":s":
                        if not waypoints:
                            print("还没有 waypoint")
                            continue
                        pose = parts[1] if len(parts) > 1 else "front"
                        save_snippet(out_dir / f"waypoints_{pose}.txt", pose, waypoints)
                    else:
                        print(f"未知本地命令: {op}（:h 查看帮助）")
                else:
                    ser.write((cmd + "\n").encode("utf-8"))
                    ser.flush()

            if not did_work:
                time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n退出")
    finally:
        reader.stop_event.set()
        try:
            ser.close()
        except Exception:
            pass
        if csv_file:
            csv_file.close()
        reader.join(timeout=1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
