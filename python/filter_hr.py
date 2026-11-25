"""
Viec 1.5: loc thong dai 0.5-5 Hz, tim dinh, tinh HR/IBI.

  python filter_hr.py --demo                       # thu tren tin hieu mo phong
  python filter_hr.py --csv ../data/ppg_dungyen_01.csv --channel ir
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ppg_utils import bandpass, detect_peaks, fix_stale, hr_fft, ibi_hr


def synth_ppg(fs=100, dur=30, bpm=72, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(fs * dur)) / fs
    f = bpm / 60.0
    pulse = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t + 0.8)
    base = 50000 + 800 * np.sin(2 * np.pi * 0.2 * t)       # troi nen cham
    return t, base + 300 * pulse + rng.normal(0, 40, len(t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="file CSV tu read_ppg.py (cot sample,t_s,red,ir)")
    ap.add_argument("--channel", default="ir", choices=["ir", "red"])
    ap.add_argument("--fs", type=float, default=100.0)
    ap.add_argument("--invert", action="store_true", help="dao dau neu dinh bi nguoc")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--lo", type=float, default=0.5, help="tan so cat duoi (Hz)")
    ap.add_argument("--hi", type=float, default=5.0, help="tan so cat tren (Hz); thu 3.0 neu dem thua dinh")
    ap.add_argument("--prom", type=float, default=0.3, help="do cao dinh toi thieu (x do lech chuan); thu 0.5")
    ap.add_argument("--max-bpm", type=float, default=180, help="HR toi da cho phep khi tim dinh")
    ap.add_argument("--no-fix", action="store_true", help="khong sua mau FIFO bi doc nham")
    ap.add_argument("--skip", type=float, default=2.0, help="bo n giay dau (qua do bo loc)")
    args = ap.parse_args()

    if args.demo or not args.csv:
        t, raw = synth_ppg(args.fs)
        title = "Tin hieu mo phong (that su 72 bpm)"
    else:
        df = pd.read_csv(args.csv)
        t = df["t_s"].to_numpy()
        red, ir = df["red"].to_numpy(dtype=float), df["ir"].to_numpy(dtype=float)
        if not args.no_fix:
            red, ir, bad = fix_stale(red, ir)
            if bad:
                print(f"Da sua {len(bad)} mau FIFO bi doc nham tai chi so {bad}")
        raw = ir if args.channel == "ir" else red
        title = args.csv

    x = -raw if args.invert else raw
    filt = bandpass(x, args.fs, args.lo, args.hi)
    peaks = detect_peaks(filt, args.fs, args.max_bpm, args.prom)
    peaks = peaks[peaks / args.fs >= args.skip]
    t_ibi, ibi, hr = ibi_hr(peaks, args.fs)

    skip_n = int(args.skip * args.fs)
    print(f"So dinh: {len(peaks)} | IBI hop le: {len(ibi)}")
    print(f"Doi chieu bang pho tan so: {hr_fft(filt[skip_n:], args.fs):.1f} bpm (dinh pho manh nhat)")
    if len(ibi):
        print(f"HR trung binh: {60.0 / np.mean(ibi):.1f} bpm")
        print(f"IBI trung binh: {1000 * np.mean(ibi):.0f} ms, do lech chuan (SDNN): {1000 * np.std(ibi):.0f} ms")
    else:
        print("Khong du dinh de tinh HR. Thu --invert, doi kenh, hoac do lai tin hieu.")

    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    ax[0].plot(t, raw); ax[0].set_ylabel("Tho")
    ax[1].plot(t, filt); ax[1].plot(t[peaks], filt[peaks], "rv"); ax[1].set_ylabel("Sau loc 0.5-5 Hz")
    if len(hr):
        ax[2].plot(t_ibi, hr, "o-"); ax[2].set_ylabel("HR tuc thoi (bpm)")
    ax[2].set_xlabel("Thoi gian (s)")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig("filter_hr.png", dpi=150)
    print("Da luu filter_hr.png")
    plt.show()


if __name__ == "__main__":
    main()
