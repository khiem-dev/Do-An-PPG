"""
Viec 1.6: NLMS dung gia toc lam tham chieu de giam nhieu chuyen dong tren PPG.

  python nlms.py --demo                       # tin hieu mo phong (kiem tra thuat toan)
  python nlms.py --dalia path/S1/S1.pkl       # PPG-DaLiA (can tai dataset)
"""
import argparse
import pickle

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import resample_poly

from ppg_utils import bandpass, hr_spectrum, track_hr


def nlms(d, X, taps=16, mu=0.02, eps_rel=1.0):
    """Loc thich nghi NLMS.
    d : tin hieu can lam sach (PPG da loc thong dai), shape (N,)
    X : tin hieu tham chieu (gia toc 3 truc da loc), shape (K, N)
    mu      : buoc hoc (nho hon = on dinh hon)
    eps_rel : he so 'chuan hoa mem': mau so = eps_rel * cong suat TRUNG BINH + cong suat tuc thoi.
              Khi gia toc dang yen (cong suat tuc thoi ~ 0) buoc cap nhat tu dong nho lai,
              tranh bung trong so roi phun ga khi gia toc tang dot ngot.
    Tra ve e = d - y (PPG sau khi tru phan nhieu du doan tu gia toc)."""
    d = np.asarray(d, float)
    X = np.atleast_2d(np.asarray(X, float))
    K, N = X.shape
    U = np.zeros((N, K * taps))
    for k in range(K):
        for m in range(taps):
            U[m:, k * taps + m] = X[k, : N - m]
    pw = np.einsum("ij,ij->i", U, U)                 # cong suat tuc thoi cua vector tham chieu
    eps = eps_rel * np.mean(pw) + 1e-12
    w = np.zeros(K * taps)
    e = np.zeros(N)
    for n in range(N):
        u = U[n]
        e[n] = d[n] - w @ u
        w += mu * e[n] * u / (eps + pw[n])
    return e


def clean_ppg(ppg, acc, fs, taps=16, mu=0.02, eps_rel=1.0):
    """Quy trinh giong tren chip: loc thong dai (mot chieu) -> NLMS."""
    d = bandpass(ppg, fs, 0.5, 5.0, causal=True)
    X = np.array([bandpass(acc[:, k], fs, 0.5, 5.0, causal=True) for k in range(acc.shape[1])])
    X = X / (np.std(X, axis=1, keepdims=True) + 1e-12)      # chuan hoa moi truc
    return d, nlms(d, X, taps, mu, eps_rel)


def window_spectra(x, fs, win_s=8, shift_s=2):
    w, s = int(win_s * fs), int(shift_s * fs)
    specs, axis = [], None
    for i in range(0, len(x) - w + 1, s):
        axis, sp = hr_spectrum(x[i:i + w], fs)
        specs.append(sp)
    return axis, np.array(specs)


ACTIVITY_NAMES = {0: "chuyen tiep", 1: "ngoi", 2: "len/xuong cau thang", 3: "da bi lac",
                  4: "dap xe", 5: "lai xe", 6: "nghi trua", 7: "di bo", 8: "lam viec"}


def synth_motion_ppg(fs=64, dur=120, bpm=72, seed=1):
    """PPG sach + nhieu chuyen dong (tron tu gia toc qua bo loc ngau nhien)."""
    rng = np.random.default_rng(seed)
    n = int(fs * dur)
    t = np.arange(n) / fs
    f = bpm / 60.0
    clean = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t + 0.8)
    acc = np.zeros((n, 3))
    for k in range(3):
        noise = rng.normal(0, 1, n)
        acc[:, k] = bandpass(noise, fs, 0.7, 4.0)                       # chuyen dong ngau nhien
        acc[:, k] += 1.5 * np.sin(2 * np.pi * (2.0 + 0.1 * k) * t)       # nhip buoc/vung tay ~2 Hz
    art = np.zeros(n)
    for k in range(3):
        h = rng.normal(0, 1, 8)
        art += np.convolve(acc[:, k], h, mode="full")[:n]
    ppg = 100.0 + 0.5 * clean + 0.8 * art + rng.normal(0, 0.05, n)
    return t, clean, ppg, acc


def load_dalia(path):
    """Doc S?.pkl goc cua PPG-DaLiA, hoac S?.npz da trich bang extract_dalia_wrist.py."""
    if str(path).lower().endswith(".npz"):
        z = np.load(path)
        bvp = z["bvp"].astype(float)
        acc = z["acc"].astype(float)
        label = z["label"].astype(float)
        act = z["activity"].astype(int) if "activity" in z.files else None
    else:
        with open(path, "rb") as f:                   # chi mo file tai tu nguon chinh thuc
            data = pickle.load(f, encoding="latin1")
        bvp = np.asarray(data["signal"]["wrist"]["BVP"], float).ravel()       # 64 Hz
        acc = np.asarray(data["signal"]["wrist"]["ACC"], float)               # 32 Hz, (N,3)
        label = np.asarray(data["label"], float).ravel()                     # HR chuan moi 2 s
        act = data.get("activity")
        act = None if act is None else np.asarray(act).ravel().astype(int)
    acc = resample_poly(acc, 2, 1, axis=0)[: len(bvp)]                        # len len 64 Hz
    return bvp, acc, label, act


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--dalia")
    ap.add_argument("--taps", type=int, default=16)
    ap.add_argument("--mu", type=float, default=0.02)
    ap.add_argument("--eps", type=float, default=1.0, help="eps_rel: chuan hoa mem (0 = NLMS thuan)")
    ap.add_argument("--jump", type=float, default=12.0, help="HR duoc phep doi toi da moi cua so (bpm)")
    args = ap.parse_args()
    fs = 64.0

    act = None
    if args.dalia:
        ppg, acc, truth, act = load_dalia(args.dalia)
        clean = None
        title = args.dalia
    else:
        t, clean, ppg, acc = synth_motion_ppg(fs)
        truth = None
        title = "Mo phong (HR that = 72 bpm)"

    before, after = clean_ppg(ppg, acc, fs, args.taps, args.mu, args.eps)
    skip = int(10 * fs)

    axis, sp_b = window_spectra(before, fs)
    _, sp_a = window_spectra(after, fs)
    raw_b, raw_a = axis[np.argmax(sp_b, axis=1)], axis[np.argmax(sp_a, axis=1)]
    W0 = 5                                             # bo 5 cua so dau (10 s) cho bo loc/NLMS on dinh
    def tracked(sp):
        t = track_hr(axis, sp[W0:], args.jump)
        return np.concatenate([np.full(W0, t[0]), t])
    trk_b, trk_a = tracked(sp_b), tracked(sp_a)

    nwin = len(trk_b)
    if truth is None:
        truth_w = np.full(nwin, 72.0)
    else:
        nwin = min(nwin, len(truth))
        truth_w = truth[:nwin]
    raw_b, raw_a, trk_b, trk_a = raw_b[:nwin], raw_a[:nwin], trk_b[:nwin], trk_a[:nwin]

    valid = np.arange(nwin) >= 5                       # bo 10 s dau cho NLMS hoi tu
    act_w = None
    if act is not None:
        dur = len(ppg) / fs
        rate = len(act) / dur                          # tan so lay mau cua nhan hoat dong
        centers = (2 * np.arange(nwin) + 4.0) * rate   # giua moi cua so 8 s
        act_w = act[np.minimum(centers.astype(int), len(act) - 1)]
        valid &= act_w != 0                            # bo doan chuyen tiep

    def mae(est, m=valid):
        return np.mean(np.abs(est[m] - truth_w[m])) if m.any() else float("nan")

    print("Sai so HR tuyet doi trung binh (MAE, bpm)")
    print(f"  Dinh pho tho  : truoc NLMS {mae(raw_b):.1f} | sau NLMS {mae(raw_a):.1f}")
    print(f"  Co theo doi HR: truoc NLMS {mae(trk_b):.1f} | sau NLMS {mae(trk_a):.1f}")
    if act_w is not None:
        print("Theo tung hoat dong (co theo doi HR):  truoc -> sau NLMS  [so cua so]")
        for k in sorted(set(act_w[valid])):
            m = valid & (act_w == k)
            print(f"  {k} {ACTIVITY_NAMES.get(k, '?'):22s} {mae(trk_b, m):5.1f} -> {mae(trk_a, m):5.1f}   [{m.sum()}]")

    if clean is not None:
        ref = bandpass(clean, fs, 0.5, 5.0, causal=True)
        def snr(x):
            r, xs = ref[skip:], x[skip:]
            a = np.dot(xs, r) / np.dot(r, r)
            return 10 * np.log10(np.var(a * r) / np.var(xs - a * r))
        print(f"SNR: truoc {snr(before):.1f} dB | sau {snr(after):.1f} dB")

    fig, ax = plt.subplots(3, 1, figsize=(10, 9))
    tt = np.arange(len(before)) / fs
    c0 = min(int(600 * fs), max(0, len(before) - int(20 * fs)))
    lim = slice(c0, c0 + int(20 * fs))
    ax[0].plot(tt[lim], before[lim]); ax[0].set_title("PPG sau loc thong dai (truoc NLMS), doan 20 s")
    ax[1].plot(tt[lim], after[lim], color="tab:green"); ax[1].set_title("Sau NLMS, cung doan")
    w0 = min(300, max(0, nwin - 150)); wl = slice(w0, w0 + 150)       # 150 cua so = 5 phut
    x = np.arange(nwin)[wl] * 2.0
    ax[2].plot(x, trk_b[wl], label="truoc NLMS"); ax[2].plot(x, trk_a[wl], label="sau NLMS")
    ax[2].plot(x, truth_w[wl], "k--", label="HR chuan"); ax[2].legend()
    ax[2].set_ylabel("HR (bpm)"); ax[2].set_xlabel("Thoi gian (s), doan 5 phut")
    fig.suptitle(title); fig.tight_layout(); fig.savefig("nlms_result.png", dpi=150)
    print("Da luu nlms_result.png")
    plt.show()


if __name__ == "__main__":
    main()
