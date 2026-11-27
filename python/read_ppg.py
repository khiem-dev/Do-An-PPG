"""
Doc du lieu PPG tu STM32 qua cong COM, luu CSV va ve do thi.
Dong du lieu tu board: index,red,ir  hoac  index,red,ir,ax,ay,az   (100 mau/giay)

Cai thu vien:  pip install pyserial matplotlib
Chay:          python read_ppg.py --port COM5 --seconds 30 --out ../data/ppg_dungyen_01.csv
"""
import argparse
import csv
import os
import sys
import time

import serial
import matplotlib.pyplot as plt

FS = 100.0  # tan so lay mau (Hz), khop voi cau hinh SPO2_CONFIG tren board


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="vd COM5 (xem Device Manager > Ports)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=float, default=30, help="thoi gian ghi")
    ap.add_argument("--out", default="ppg.csv", help="file CSV dau ra")
    ap.add_argument("--wait", type=int, default=5, help="dem nguoc truoc khi ghi (s), de kip dat tay")
    ap.add_argument("--force", action="store_true", help="cho phep ghi de file da ton tai")
    args = ap.parse_args()

    if os.path.exists(args.out) and not args.force:
        sys.exit(f"File {args.out} da ton tai, se KHONG ghi de. Doi so lan do (vd _02) hoac them --force.")

    rows = []          # (sample, red, ir, ax, ay, az)   ax,ay,az = None neu board khong gui
    first_idx = None
    last_idx = None
    dropped = 0

    ser = serial.Serial(args.port, args.baud, timeout=1)
    for k in range(args.wait, 0, -1):
        print(f"Bat dau sau {k} s... hay dat tay san sang", end="\r", flush=True)
        time.sleep(1)
    ser.reset_input_buffer()
    print(f"\nDang ghi {args.seconds:.0f} s tu {args.port}. Giu dung tu the do da dinh.      ")
    t0 = time.time()
    try:
        while time.time() - t0 < args.seconds:
            line = ser.readline().decode("ascii", errors="ignore").strip()
            parts = line.split(",")
            if len(parts) not in (3, 6):
                continue                      # bo qua dong chu (quet I2C, thong bao...)
            try:
                vals = [int(p) for p in parts]
            except ValueError:
                continue
            idx, red, ir = vals[:3]
            acc = vals[3:] if len(vals) == 6 else [None, None, None]
            if first_idx is None:
                first_idx = idx
            if last_idx is not None and idx != last_idx + 1:
                dropped += abs(idx - last_idx - 1)
            last_idx = idx
            rows.append((idx - first_idx, red, ir, *acc))
    finally:
        ser.close()

    if not rows:
        sys.exit("Khong nhan duoc dong du lieu nao. Kiem tra cong COM, baud, day TX/RX/GND.")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        has_acc = rows[0][3] is not None
        w.writerow(["sample", "t_s", "red", "ir"] + (["ax", "ay", "az"] if has_acc else []))
        for s, red, ir, ax, ay, az in rows:
            w.writerow([s, f"{s / FS:.2f}", red, ir] + ([ax, ay, az] if has_acc else []))

    print(f"Da luu {len(rows)} mau ({len(rows) / FS:.1f} s) vao {args.out}")
    if dropped:
        print(f"CANH BAO: mat {dropped} mau (loi truyen hoac tran bo dem).")

    t = [r[0] / FS for r in rows]
    n_plots = 3 if has_acc else 2
    fig, ax = plt.subplots(n_plots, 1, sharex=True, figsize=(10, 3 * n_plots))
    ax[0].plot(t, [r[2] for r in rows])
    ax[0].set_ylabel("IR")
    ax[1].plot(t, [r[1] for r in rows], color="tab:red")
    ax[1].set_ylabel("Red")
    if has_acc:
        for k, name in enumerate(["ax", "ay", "az"]):
            ax[2].plot(t, [r[3 + k] for r in rows], label=name)
        ax[2].set_ylabel("Gia toc (tho)")
        ax[2].legend(loc="upper right")
    ax[-1].set_xlabel("Thoi gian (s)")
    fig.suptitle(os.path.basename(args.out))
    png = os.path.splitext(args.out)[0] + ".png"
    fig.savefig(png, dpi=150)
    print(f"Da luu do thi {png}")
    plt.show()


if __name__ == "__main__":
    main()
