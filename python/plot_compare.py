"""
Viec 1.3: ve hai do thi canh nhau (dung yen vs cu dong) tu hai file CSV do read_ppg.py luu.

  python plot_compare.py --still ..\\data\\mine\\ppg_dungyen_01.csv --moving ..\\data\\mine\\ppg_nhe_01.csv
Tuy chon: --channel ir|red, --seconds 20 (do dai doan ve), --start 5 (bat dau tu giay thu may)
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ppg_utils import bandpass

FS = 100.0


def load(path, channel):
    df = pd.read_csv(path)
    t = df["t_s"].to_numpy()
    x = df[channel].to_numpy(dtype=float)
    acc = None
    if {"ax", "ay", "az"} <= set(df.columns):
        a = df[["ax", "ay", "az"]].to_numpy(dtype=float)
        a = a - a.mean(axis=0)
        acc = np.linalg.norm(a, axis=1)          # do lon chuyen dong (da bo trong luc)
    return t, x, acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", required=True, help="CSV dung yen")
    ap.add_argument("--moving", required=True, help="CSV cu dong")
    ap.add_argument("--channel", default="ir", choices=["ir", "red"])
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--start", type=float, default=5)
    args = ap.parse_args()

    data = [("Dung yen", *load(args.still, args.channel)),
            ("Cu dong", *load(args.moving, args.channel))]
    has_acc = all(d[3] is not None for d in data)
    rows = 3 if has_acc else 2
    fig, axs = plt.subplots(rows, 2, figsize=(12, 3 * rows), sharex="col")
    for c, (name, t, x, acc) in enumerate(data):
        filt = bandpass(x, FS, 0.5, 5.0)               # loc ca doan dai truoc, roi cat
        m = (t >= args.start) & (t < args.start + args.seconds)
        axs[0, c].plot(t[m], x[m] - np.mean(x[m]))
        axs[0, c].set_title(f"{name}: {args.channel.upper()} tho (bo thanh phan DC)")
        axs[1, c].plot(t[m], filt[m], color="tab:green")
        axs[1, c].set_title("Sau loc 0.5-5 Hz")
        if has_acc:
            axs[2, c].plot(t[m], acc[m], color="tab:red")
            axs[2, c].set_title("Do lon gia toc (chuyen dong)")
        axs[-1, c].set_xlabel("Thoi gian (s)")
    fig.tight_layout()
    fig.savefig("compare.png", dpi=150)
    print("Da luu compare.png")
    plt.show()


if __name__ == "__main__":
    main()
