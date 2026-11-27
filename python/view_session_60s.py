"""
Nhan du lieu phien do 60 giay tu STM32 qua UART, luu CSV va hien thi do thi
kem danh gia SQI + nhan xet ngay tren hinh trong VSCode.

Cach dung:
  1) Chay truc tiep tu cong COM/USB-TTL (tu dong tim cong neu bo trong --port):
     python3 view_session_60s.py
     python3 view_session_60s.py --port /dev/cu.usbserial-0001

  2) Hoac xem lai 1 file CSV 60s da luu:
     python3 view_session_60s.py --csv ../data/mine/KhiemHungMinh/ppg_dungyen_lan1_Khiem.csv
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from nlms import clean_ppg
from nlms_csv import fix_repeated_acc
from ppg_utils import fix_stale, hr_fft
from train_sqi import FEATURE_COLS, extract_window_features

FS = 100.0


def auto_detect_port():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    for p in ports:
        desc = (p.description or "").lower()
        dev = (p.device or "").lower()
        if any(k in desc or k in dev for k in ("usb", "cp210", "ch340", "ftdi", "uart", "com")):
            return p.device
    return ports[0].device


def read_serial_60s(port, baud, out_csv):
    import serial

    ser = serial.Serial(port, baud, timeout=1)
    print(f"Da mo {port} @ {baud}. Cho STM32 bat dau phien do 60s (dat tay hoac bam nut)...")
    rows = []
    stm_summary = ""
    recording = False
    first_idx = None
    t_start = None

    try:
        while True:
            raw = ser.readline().decode("ascii", errors="ignore").strip()
            if not raw:
                if recording and t_start and (time.time() - t_start > 68.0):
                    break
                continue

            if "CHUAN BI" in raw or "BAT DAU DO 60S" in raw:
                print(raw)
                if "BAT DAU DO 60S" in raw:
                    recording = True
                    t_start = time.time()
                    rows.clear()
                    first_idx = None
                continue

            if "KET QUA 60S:" in raw:
                stm_summary = raw
                print(raw)
                break

            parts = raw.split(",")
            if len(parts) == 6:
                try:
                    idx, red, ir, ax, ay, az = [int(x) for x in parts]
                except ValueError:
                    continue
                if not recording:
                    recording = True
                    t_start = time.time()
                if first_idx is None:
                    first_idx = idx
                rows.append((idx - first_idx, red, ir, ax, ay, az))
                if len(rows) % 500 == 0:
                    print(f"  Da nhan {len(rows)}/6000 mau ({len(rows)/FS:.0f}s)...")
                if len(rows) >= 6000:
                    # Cho them toi da 1s de nhan dong KET QUA 60S tu STM32
                    time.sleep(0.2)
                    while ser.in_waiting:
                        tail = ser.readline().decode("ascii", errors="ignore").strip()
                        if "KET QUA 60S:" in tail:
                            stm_summary = tail
                            print(tail)
                    break
    finally:
        ser.close()

    if not rows:
        sys.exit("Khong nhan duoc du lieu nao tu STM32.")

    os.makedirs(os.path.dirname(os.path.abspath(out_csv)), exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sample", "t_s", "red", "ir", "ax", "ay", "az"])
        for s, red, ir, ax, ay, az in rows:
            w.writerow([s, f"{s / FS:.2f}", red, ir, ax, ay, az])
    print(f"Da luu CSV: {out_csv} ({len(rows)} mau)")
    return out_csv, stm_summary


def analyze_and_plot(csv_path, features_csv, out_png, stm_summary=""):
    df = pd.read_csv(csv_path)
    _, ir, _ = fix_stale(df["red"].to_numpy(float), df["ir"].to_numpy(float))
    acc, _ = fix_repeated_acc(df[["ax", "ay", "az"]].to_numpy(float))
    acc_g = acc / 8192.0
    d, e = clean_ppg(ir, acc_g, FS, taps=32, mu=0.02, eps_rel=1.0)

    # Load model SQI da train de danh gia va ve timeline tung cua so 10s
    feat_df = pd.read_csv(features_csv)
    clf = RandomForestClassifier(n_estimators=15, max_depth=4, random_state=42)
    clf.fit(feat_df[FEATURE_COLS].to_numpy(float), feat_df["label"].to_numpy(int))

    w = int(10.0 * FS)
    step = int(2.0 * FS)
    win_t, win_label, win_prob, win_hr = [], [], [], []
    for start in range(0, len(e) - w + 1, step):
        end = start + w
        f = extract_window_features(ir[start:end], d[start:end], e[start:end], acc_g[start:end])
        x_vec = np.array([[f[c] for c in FEATURE_COLS]], dtype=float)
        prob = float(clf.predict_proba(x_vec)[0, 1])
        pred = 1 if prob >= 0.5 else 0
        hr_w = float(hr_fft(e[start:end], FS))
        win_t.append((start + end) / (2.0 * FS))
        win_label.append(pred)
        win_prob.append(prob)
        win_hr.append(hr_w)

    win_t = np.array(win_t)
    win_label = np.array(win_label)
    win_hr = np.array(win_hr)

    n_tot = len(win_label)
    n_good = int(win_label.sum()) if n_tot else 0
    good_pct = (100.0 * n_good / n_tot) if n_tot else 0.0
    if n_good > 0:
        hr_avg = float(np.mean(win_hr[win_label == 1]))
    elif n_tot > 0:
        hr_avg = float(np.mean(win_hr))
    else:
        hr_avg = 0.0

    if good_pct >= 70.0:
        comment = "NHAN XET: Tin hieu 60s RAT TOT - On dinh, du tin cay de uoc luong HR."
        status_color = "#1b7837"
    elif good_pct >= 50.0:
        comment = "NHAN XET: Tin hieu TRUNG BINH - Co nhieu nhe mot so doan, HR lay tu vung GOOD."
        status_color = "#d95f02"
    else:
        comment = "NHAN XET: Tin hieu NHIEU CAO - Giu tay yen hon / giam luc ep ngon tay roi do lai."
        status_color = "#b2182b"

    t = np.arange(len(ir)) / FS
    acc_dyn = np.linalg.norm(acc_g - acc_g.mean(axis=0), axis=1)

    fig, axes = plt.subplots(3, 1, figsize=(12, 8.5), sharex=True)

    # Panel 1: IR tho + gia toc dong
    ax0 = axes[0]
    ax0.plot(t, ir, color="steelblue", lw=0.8, label="IR tho")
    ax0.set_ylabel("PPG IR (ADC)", color="steelblue")
    ax0_r = ax0.twinx()
    ax0_r.plot(t, acc_dyn, color="gray", alpha=0.55, lw=0.8, label="|Acc| dong (g)")
    ax0_r.set_ylabel("Gia toc (g)", color="gray")
    ax0.set_title("1. Tin hieu tho MAX30102 & Chuyen dong MPU6050")

    # Panel 2: Bandpass vs NLMS
    ax1 = axes[1]
    ax1.plot(t, d, color="silver", lw=0.9, label="Truoc NLMS (Bandpass)")
    ax1.plot(t, e, color="teal", lw=1.0, label="Sau NLMS (Da khu nhieu)")
    ax1.set_ylabel("Bien do (AC)")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.set_title("2. Ket qua loc thich nghi NLMS (taps=32, mu=0.02)")

    # Panel 3: SQI & HR theo thoi gian
    ax2 = axes[2]
    if n_tot:
        good_m = win_label == 1
        ax2.scatter(win_t[good_m], win_hr[good_m], color="green", s=45, label="Cua so GOOD", zorder=3)
        ax2.scatter(win_t[~good_m], win_hr[~good_m], color="red", marker="x", s=50, label="Cua so BAD", zorder=3)
        ax2.plot(win_t, win_hr, color="black", alpha=0.35, lw=1.0)
        for wt, wl in zip(win_t, win_label):
            ax2.axvspan(wt - 1.0, wt + 1.0, color=("green" if wl == 1 else "red"), alpha=0.08)
    ax2.set_ylabel("HR (bpm)")
    ax2.set_xlabel("Thoi gian (s)")
    ax2.set_ylim(40, 180)
    ax2.legend(loc="upper right", fontsize=8)
    ax2.set_title("3. Danh gia chat luong SQI & Nhip tim tung cua so 10s")

    summary_line = (
        f"TONG KET 60S: HR_avg = {hr_avg:.1f} bpm  |  SQI = {n_good}/{n_tot} ({good_pct:.0f}% GOOD)\n"
        f"{comment}"
    )
    if stm_summary:
        summary_line += f"\nSTM32: {stm_summary}"

    fig.suptitle(
        f"Phien do PPG 60s - {os.path.basename(csv_path)}",
        fontsize=12, fontweight="bold", y=0.98
    )
    fig.text(
        0.5, 0.015, summary_line,
        ha="center", va="bottom", fontsize=9.5, fontweight="bold",
        color=status_color,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f8f9fa", edgecolor=status_color, lw=1.2)
    )
    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    fig.savefig(out_png, dpi=150)
    print(f"Da luu anh phien do 60s: {out_png}")
    plt.show()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="", help="Cong COM/USB-TTL (bo trong de tu dong tim)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--csv", default="", help="Xem lai file CSV co san (khong can cam STM32)")
    ap.add_argument("--features-csv", default="../report/sqi_features.csv")
    ap.add_argument("--out", default="", help="File CSV dau ra khi doc tu STM32")
    ap.add_argument("--out-png", default="../report/session_60s_latest.png")
    args = ap.parse_args()

    stm_summary = ""
    if args.csv:
        csv_path = args.csv
    else:
        port = args.port or auto_detect_port()
        if not port:
            sys.exit("Khong tim thay cong COM/USB-TTL. Hay cam mach hoac truyen --port.")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_csv = args.out or f"../data/session_60s_{ts}.csv"
        csv_path, stm_summary = read_serial_60s(port, args.baud, out_csv)

    analyze_and_plot(csv_path, args.features_csv, args.out_png, stm_summary=stm_summary)


if __name__ == "__main__":
    main()
