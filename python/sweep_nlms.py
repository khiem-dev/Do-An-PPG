"""
Quet vai bo tham so NLMS tren mot nguoi cua PPG-DaLiA va in bang so sanh.
  python sweep_nlms.py ..\\data\\public\\PPG_FieldStudy\\S1\\S1.pkl
Moi cau hinh mat khoang bang 1 lan chay nlms.py, nen cho vai phut.
"""
import sys

import numpy as np

from nlms import (ACTIVITY_NAMES, clean_ppg, load_dalia, window_spectra)
from ppg_utils import track_hr

CONFIGS = [  # (taps, mu, eps_rel)
    (16, 0.02, 1.0),
    (16, 0.01, 1.0),
    (16, 0.005, 1.0),
    (32, 0.02, 1.0),
    (16, 0.02, 3.0),
]
SHOW = [1, 7, 2, 4, 8]   # ngoi, di bo, cau thang, dap xe, lam viec
FS, W0 = 64.0, 5


def tracked_hr(x):
    axis, sp = window_spectra(x, FS)
    t = track_hr(axis, sp[W0:], 12.0)
    return np.concatenate([np.full(W0, t[0]), t])


def main():
    ppg, acc, truth, act = load_dalia(sys.argv[1])
    nwin_all = None
    base, _ = clean_ppg(ppg, acc, FS, 16, 0.02, 1.0)       # 'truoc NLMS' (khong phu thuoc tham so)
    hb = tracked_hr(base)
    n = min(len(hb), len(truth))
    valid = np.arange(n) >= W0
    act_w = None
    if act is not None:
        rate = len(act) / (len(ppg) / FS)
        c = ((2 * np.arange(n) + 4.0) * rate).astype(int)
        act_w = act[np.minimum(c, len(act) - 1)]
        valid &= act_w != 0

    def mae(est, m):
        return np.mean(np.abs(est[:n][m] - truth[:n][m])) if m.any() else float("nan")

    head = "cau hinh".ljust(22) + "TONG".rjust(6) + "".join(ACTIVITY_NAMES[k][:8].rjust(10) for k in SHOW)
    print(head)
    def row(lab, est):
        s = lab.ljust(22) + f"{mae(est, valid):6.1f}"
        for k in SHOW:
            s += f"{mae(est, valid & (act_w == k)):10.1f}" if act_w is not None else ""
        print(s, flush=True)
    row("truoc NLMS", hb)
    for taps, mu, eps in CONFIGS:
        _, after = clean_ppg(ppg, acc, FS, taps, mu, eps)
        row(f"taps={taps} mu={mu} eps={eps}", tracked_hr(after))


if __name__ == "__main__":
    main()
