"""Ham dung chung: loc thong dai, tim dinh, tinh IBI/HR."""
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, find_peaks


def bandpass(x, fs, lo=0.5, hi=5.0, order=2, causal=False):
    """Loc thong dai Butterworth (SOS = dang biquad, giong CMSIS-DSP tren F407).
    causal=False: pha 0, dung de phan tich offline.
    causal=True : loc mot chieu, giong cach chay thoi gian thuc tren chip."""
    sos = butter(order, [lo, hi], btype="bandpass", fs=fs, output="sos")
    x = np.asarray(x, dtype=float)
    x = x - np.mean(x)
    return sosfilt(sos, x) if causal else sosfiltfilt(sos, x)


def detect_peaks(x, fs, max_bpm=180, prom_ratio=0.3):
    """Tim dinh xung tim: cach nhau toi thieu 60/max_bpm giay,
    do cao (prominence) toi thieu prom_ratio * do lech chuan."""
    dist = max(int(fs * 60.0 / max_bpm), 1)
    peaks, _ = find_peaks(x, distance=dist, prominence=prom_ratio * np.std(x))
    return peaks


def ibi_hr(peaks, fs, min_bpm=40, max_bpm=180):
    """Tra ve (thoi diem IBI, IBI [s], HR tuc thoi [bpm]); bo IBI ngoai 40-180 bpm."""
    t = np.asarray(peaks) / fs
    ibi = np.diff(t)
    ok = (ibi >= 60.0 / max_bpm) & (ibi <= 60.0 / min_bpm)
    t_ibi, ibi = t[1:][ok], ibi[ok]
    hr = 60.0 / ibi if len(ibi) else ibi
    return t_ibi, ibi, hr


def hr_fft(x, fs, lo=0.7, hi=3.5, nfft=8192):
    """Uoc luong HR (bpm) cua mot cua so bang dinh pho (0.7-3.5 Hz = 42-210 bpm)."""
    x = np.asarray(x, dtype=float)
    x = (x - np.mean(x)) * np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / fs)
    m = (f >= lo) & (f <= hi)
    return 60.0 * f[m][np.argmax(spec[m])]


def hr_spectrum(x, fs, lo=0.7, hi=3.5, nfft=8192):
    """Tra ve (bpm, bien do pho) trong dai lo-hi Hz cua 1 cua so."""
    x = np.asarray(x, dtype=float)
    x = (x - np.mean(x)) * np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / fs)
    m = (f >= lo) & (f <= hi)
    return 60.0 * f[m], spec[m]


def track_hr(bpm_axis, specs, max_jump=12.0, relock_after=3, min_ratio=0.4):
    """Theo doi HR. Moi cua so: lay dinh cao nhat NAM TRONG +-max_jump bpm so voi HR truoc,
    nhung chi nhan neu dinh do >= min_ratio * dinh cao nhat toan dai. Neu khong nhan duoc
    relock_after cua so lien tiep thi nhay sang dinh cao nhat toan dai.
    specs: (so_cua_so, so_bin)."""
    out = np.zeros(len(specs))
    prev, miss = None, 0
    for i, s in enumerate(specs):
        pk, _ = find_peaks(s)
        if len(pk) == 0:
            pk = np.array([np.argmax(s)])
        gbest = pk[np.argmax(s[pk])]
        if prev is None:
            prev = bpm_axis[gbest]
        else:
            near = pk[np.abs(bpm_axis[pk] - prev) <= max_jump]
            best = near[np.argmax(s[near])] if len(near) else None
            if best is not None and s[best] >= min_ratio * s[gbest]:
                prev, miss = bpm_axis[best], 0
            else:
                miss += 1
                if miss >= relock_after:
                    prev, miss = bpm_axis[gbest], 0
        out[i] = prev
    return out


def fix_stale(red, ir, lag=32):
    """Phat hien mau PPG bi doc nham tu o FIFO cu: (red, ir) trung y het mau cach `lag`=32 vi tri
    (FIFO cua MAX30102 sau 32 mau). Thay bang noi suy tuyen tinh. Tra ve (red, ir, chi_so_loi)."""
    red = np.asarray(red, dtype=float).copy()
    ir = np.asarray(ir, dtype=float).copy()
    bad = [i for i in range(lag, len(ir)) if red[i] == red[i - lag] and ir[i] == ir[i - lag]]
    if bad:
        idx = np.arange(len(ir))
        ok = np.ones(len(ir), dtype=bool)
        ok[bad] = False
        red[~ok] = np.interp(idx[~ok], idx[ok], red[ok])
        ir[~ok] = np.interp(idx[~ok], idx[ok], ir[ok])
    return red, ir, bad
