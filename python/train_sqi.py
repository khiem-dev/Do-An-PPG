"""
Trich xuat dac trung cua so 10s va train model SQI (Tot=1 / Xau=0) tren data/mine.
Tu dong nhan tat ca file dang ppg_<trangthai>_lan<x>_<Ten>.csv trong data/mine.

Chay thu:
  python3 train_sqi.py
"""
import argparse
import glob
import os
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from nlms import clean_ppg
from nlms_csv import fix_repeated_acc
from ppg_utils import detect_peaks, fix_stale, hr_spectrum, ibi_hr

FS = 100.0
FILE_RE = re.compile(r"^ppg_(dungyen|nhe|epchat|manh)_lan\d+_([A-Za-z0-9]+).*\.csv$")
FEATURE_COLS = [
    "pi_pct",
    "ppg_std",
    "ibi_std",
    "valid_ibi_ratio",
    "spec_purity",
    "acc_mean_g",
    "acc_max_g",
]


def extract_window_features(ir_raw_win, d_win, e_win, acc_win):
    """Tinh 7 dac trung nhe cho 1 cua so 10s (de de chuyen sang C tren F407)."""
    ir_dc = np.mean(ir_raw_win) + 1e-9
    pi_pct = 100.0 * (2.0 * np.sqrt(2.0) * np.std(d_win)) / ir_dc
    ppg_std = float(np.std(e_win))

    peaks = detect_peaks(e_win, FS, max_bpm=180, prom_ratio=0.3)
    _, ibi, _ = ibi_hr(peaks, FS, min_bpm=40, max_bpm=180)
    n_intervals = max(len(peaks) - 1, 1)
    valid_ibi_ratio = float(len(ibi) / n_intervals)
    ibi_std = float(np.std(ibi)) if len(ibi) >= 2 else 1.0

    bpm_ax, spec = hr_spectrum(e_win, FS, lo=0.7, hi=3.5)
    p2 = spec ** 2
    f_dom = bpm_ax[np.argmax(p2)]
    m_peak = np.abs(bpm_ax - f_dom) <= 12.0  # +-0.2 Hz = +-12 bpm
    spec_purity = float(p2[m_peak].sum() / (p2.sum() + 1e-12))

    acc_mag = np.linalg.norm(acc_win - acc_win.mean(axis=0), axis=1)
    acc_mean_g = float(np.mean(acc_mag))
    acc_max_g = float(np.max(acc_mag))

    return {
        "pi_pct": pi_pct,
        "ppg_std": ppg_std,
        "ibi_std": ibi_std,
        "valid_ibi_ratio": valid_ibi_ratio,
        "spec_purity": spec_purity,
        "acc_mean_g": acc_mean_g,
        "acc_max_g": acc_max_g,
    }


def build_dataset(data_dir, win_s=10.0, shift_s=2.0, skip_s=10.0, taps=32, mu=0.02, eps=1.0):
    rows = []
    for fpath in sorted(glob.glob(os.path.join(data_dir, "**", "ppg_*.csv"), recursive=True)):
        fname = os.path.basename(fpath)
        m = FILE_RE.match(fname)
        if not m:
            continue
        cond, subject = m.group(1), m.group(2)
        label = 1 if cond in ("dungyen", "nhe") else 0

        df = pd.read_csv(fpath)
        if not {"red", "ir", "ax", "ay", "az"} <= set(df.columns):
            continue
        _, ir, _ = fix_stale(df["red"].to_numpy(float), df["ir"].to_numpy(float))
        acc, _ = fix_repeated_acc(df[["ax", "ay", "az"]].to_numpy(float))
        acc_g = acc / 8192.0

        d, e = clean_ppg(ir, acc_g, FS, taps=taps, mu=mu, eps_rel=eps)

        s0 = int(skip_s * FS)
        w = int(win_s * FS)
        step = int(shift_s * FS)
        for start in range(s0, len(e) - w + 1, step):
            end = start + w
            feats = extract_window_features(ir[start:end], d[start:end], e[start:end], acc_g[start:end])
            feats.update({"file": fname, "subject": subject, "condition": cond, "label": label})
            rows.append(feats)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="../data/mine")
    ap.add_argument("--out-csv", default="../report/sqi_features.csv")
    ap.add_argument("--out-fig", default="../report/sqi_confusion.png")
    args = ap.parse_args()

    df = build_dataset(args.data_dir)
    if df.empty:
        raise SystemExit("Khong tim thay file phu hop trong data/mine.")

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    df.to_csv(args.out_csv, index=False)

    subjects = sorted(df["subject"].unique())
    print(f"Tong so cua so 10s: {len(df)} | So nguoi: {len(subjects)} ({', '.join(subjects)})")
    print(f"Phan bo nhan: Tot(1)={(df['label'] == 1).sum()}, Xau(0)={(df['label'] == 0).sum()}")
    print("\nTrung binh dac trung theo trang thai:")
    print(df.groupby("condition")[FEATURE_COLS].mean().round(3).to_string())
    print(f"\nDa luu bang dac trung: {args.out_csv}")

    if len(subjects) < 2:
        print("Can it nhat 2 nguoi de chay kiem thu cheo theo nguoi.")
        return

    X = df[FEATURE_COLS].to_numpy(float)
    y = df["label"].to_numpy(int)
    groups = df["subject"].to_numpy()
    logo = LeaveOneGroupOut()

    models = {
        "DecisionTree (d=4)": DecisionTreeClassifier(max_depth=4, random_state=42),
        "RandomForest (15x4)": RandomForestClassifier(n_estimators=15, max_depth=4, random_state=42),
        "MLP (16,8)": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=600, random_state=42)),
    }

    best_name, best_acc, best_pred = None, -1.0, None
    print("\n=== Danh gia Leave-One-Subject-Out (tach theo nguoi) ===")
    for name, clf in models.items():
        y_pred = np.zeros_like(y)
        for tr, te in logo.split(X, y, groups):
            clf.fit(X[tr], y[tr])
            y_pred[te] = clf.predict(X[te])
        acc = accuracy_score(y, y_pred)
        print(f"\n--- {name}: Accuracy = {acc * 100:.1f}% ---")
        print(classification_report(y, y_pred, target_names=["Xau (0)", "Tot (1)"], digits=3))
        if acc > best_acc:
            best_name, best_acc, best_pred = name, acc, y_pred

    cm = confusion_matrix(y, best_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=["Xau (0)", "Tot (1)"])
    fig, ax = plt.subplots(figsize=(5, 4))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"SQI ({best_name}, Acc={best_acc * 100:.1f}%)")
    fig.tight_layout()
    fig.savefig(args.out_fig, dpi=150)
    print(f"Da luu ma tran nham lan: {args.out_fig}")


if __name__ == "__main__":
    main()
