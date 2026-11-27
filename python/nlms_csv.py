"""
Thu NLMS tren FILE CSV TU DO (khong can dataset cong khai).
  python nlms_csv.py --csv ../data/mine/ppg_nhe_lan1_Hung.csv
  python nlms_csv.py --csv ../data/mine/ppg_nhe_lan1_Hung.csv --ref 72     # --ref = nhip tim tham chieu (bpm)
Tuy chon: --channel ir|red  --taps 16  --mu 0.1  --eps 1.0  --skip 10 (bo n giay dau)

Cach doc ket qua (xem them o cuoi man hinh):
  - Do thi: PPG sau loc thong dai (truoc NLMS) va sau NLMS, kem do lon gia toc.
  - Neu co --ref: sai so HR truoc/sau NLMS so voi nhip tham chieu.
  - Neu khong co --ref: chi so duoc HR truoc/sau, va 'do on dinh' (do lech chuan cua HR theo thoi gian;
    nho hon = HR it nhay loan hon). KHONG co nghia la dung, chi nghia la on dinh hon.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nlms import clean_ppg, window_spectra
from ppg_utils import bandpass, fix_stale, track_hr

FS = 100.0


def fix_repeated_acc(a):
    """Mau gia toc lap y het mau truoc (do doc don) -> coi nhu thieu, noi suy tuyen tinh."""
    a = np.asarray(a, float).copy()
    rep = np.zeros(len(a), bool)
    rep[1:] = np.all(a[1:] == a[:-1], axis=1)
    if rep.any():
        idx = np.arange(len(a))
        for k in range(a.shape[1]):
            a[rep, k] = np.interp(idx[rep], idx[~rep], a[~rep, k])
    return a, int(rep.sum())


def hr_track(x, fs):
    axis, specs = window_spectra(x, fs)
    return track_hr(axis, specs)          # moi 2 s mot gia tri, cua so 8 s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--channel", default="ir", choices=["ir", "red"])
    ap.add_argument("--taps", type=int, default=16)
    ap.add_argument("--mu", type=float, default=0.1)
    ap.add_argument("--eps", type=float, default=1.0)
    ap.add_argument("--skip", type=float, default=10.0, help="bo n giay dau (cho NLMS kip hoc)")
    ap.add_argument("--ref", type=float, default=None, help="nhip tim tham chieu (bpm)")
    ap.add_argument("--out", default="nlms_csv.png")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    if not {"ax", "ay", "az"} <= set(df.columns):
        raise SystemExit("File khong co cot gia toc ax, ay, az; NLMS can gia toc.")
    red, ir, bad = fix_stale(df["red"].to_numpy(float), df["ir"].to_numpy(float))
    x = ir if args.channel == "ir" else red
    acc, n_rep = fix_repeated_acc(df[["ax", "ay", "az"]].to_numpy(float))
    acc = acc / 8192.0                                  # don vi g
    print(f"{len(df)} mau ({len(df) / FS:.1f} s); sua {len(bad)} mau PPG stale, {n_rep} mau gia toc lap")

    d, e = clean_ppg(x, acc, FS, args.taps, args.mu, args.eps)
    s = int(args.skip * FS)
    d_, e_ = d[s:], e[s:]
    hr_before, hr_after = hr_track(d_, FS), hr_track(e_, FS)
    t_hr = args.skip + 8 + 2 * np.arange(len(hr_before)) - 4      # tam moi cua so 8 s

    print("\nHR (bpm), cua so 8 s, moi 2 s:")
    print(f"  Truoc NLMS: trung binh {hr_before.mean():.1f}, do lech chuan {hr_before.std():.1f}")
    print(f"  Sau   NLMS: trung binh {hr_after.mean():.1f}, do lech chuan {hr_after.std():.1f}")
    if args.ref:
        mb = np.mean(np.abs(hr_before - args.ref))
        ma = np.mean(np.abs(hr_after - args.ref))
        print(f"  Sai so so voi tham chieu {args.ref:.0f} bpm: truoc {mb:.1f} -> sau {ma:.1f} bpm")
    am = np.linalg.norm(acc - acc.mean(axis=0), axis=1)
    print(f"  Gia toc |chuyen dong|: trung binh {am.mean():.3f} g, max {am.max():.3f} g")
    print(f"  Nang luong PPG sau NLMS / truoc NLMS: {np.sum(e_**2) / np.sum(d_**2):.2f}  "
          "(nho hon 1 = NLMS da tru bot thanh phan co lien quan gia toc)")

    t = np.arange(len(x)) / FS
    fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    ax[0].plot(t, d); ax[0].set_title("PPG sau loc thong dai 0.5-5 Hz (truoc NLMS)")
    ax[1].plot(t, e, color="tab:green"); ax[1].set_title("Sau NLMS")
    ax[2].plot(t, np.linalg.norm(acc - acc.mean(axis=0), axis=1), color="tab:red")
    ax[2].set_title("Do lon gia toc (g)")
    ax[3].plot(t_hr, hr_before, "o-", label="truoc NLMS")
    ax[3].plot(t_hr, hr_after, "s-", label="sau NLMS")
    if args.ref:
        ax[3].axhline(args.ref, color="k", ls="--", label="tham chieu")
    ax[3].set_title("HR theo doi (bpm)"); ax[3].legend(); ax[3].set_xlabel("Thoi gian (s)")
    fig.tight_layout(); fig.savefig(args.out, dpi=150)
    print(f"\nDa luu {args.out}")
    plt.show()


if __name__ == "__main__":
    main()
