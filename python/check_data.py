"""
Bao cao chat luong nhanh cho mot file CSV thu tu board.
  python check_data.py ..\\data\\mine\\ppg_dungyen_01.csv
"""
import sys

import numpy as np
import pandas as pd

from ppg_utils import fix_stale

FS = 100.0


def dominant(x, lo=0.5, hi=5.0):
    x = np.asarray(x, float) - np.mean(x)
    n = 16384
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)), n))
    f = np.fft.rfftfreq(n, 1.0 / FS)
    m = (f >= lo) & (f <= hi)
    return f[m][np.argmax(spec[m])]


def main():
    df = pd.read_csv(sys.argv[1])
    n = len(df)
    print(f"File: {sys.argv[1]}")
    print(f"So mau: {n} ({n / FS:.1f} s)")
    print(f"Mau lien tuc, khong mat: {bool((np.diff(df['sample']) == 1).all())}")
    for c in ("ir", "red"):
        mx = df[c].max()
        pp = mx - df[c].min()
        print(f"{c.upper():3s}: trung binh {int(df[c].mean())}, max {mx}"
              f"{'  <-- GAN BAO HOA (262143), giam dong LED' if mx > 250000 else ''}, bien do {pp} ({100 * pp / df[c].mean():.1f}% DC)")
    _, _, bad = fix_stale(df["red"], df["ir"])
    print(f"Mau PPG bi doc nham tu FIFO cu: {len(bad)} ({100 * len(bad) / n:.1f}%)")
    print(f"Tan so manh nhat cua IR: {dominant(df['ir']):.2f} Hz = {60 * dominant(df['ir']):.0f} bpm")
    if {"ax", "ay", "az"} <= set(df.columns):
        a = df[["ax", "ay", "az"]].to_numpy(float)
        same = (np.diff(a, axis=0) == 0).all(axis=1).mean()
        mag = np.linalg.norm(a - a.mean(axis=0), axis=1)
        print(f"Gia toc: |chuyen dong| trung binh {mag.mean() / 8192:.2f} g, max {mag.max() / 8192:.2f} g (8192 don vi = 1 g)")
        print(f"Tan so manh nhat cua gia toc: {dominant(mag):.2f} Hz")
        print(f"Mau co gia toc lap lai y het mau truoc: {100 * same:.0f}%")


if __name__ == "__main__":
    main()
