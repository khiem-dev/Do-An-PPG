"""
Trich rieng du lieu CO TAY (BVP + gia toc + nhan HR + hoat dong) tu PPG-DaLiA ra file .npz nho.
Dataset goc ~2.7 GB (vi con co ECG nguc 700 Hz); phan can cho NLMS chi vai MB moi nguoi,
nen co the dua len GitHub.

  python extract_dalia_wrist.py ..\\data\\public\\PPG_FieldStudy ..\\data\\public_small
  python extract_dalia_wrist.py ..\\data\\public\\PPG_FieldStudy ..\\data\\public_small --subjects S1 S2 S3

Sau do chay NLMS:  python nlms.py --dalia ..\\data\\public_small\\S1.npz
Giay phep PPG-DaLiA: CC BY 4.0, phai ghi nguon (xem data/public_small/README.txt do script tao ra).
"""
import argparse
import os
import pickle

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="thu muc PPG_FieldStudy (chua S1, S2, ...)")
    ap.add_argument("dst", help="thu muc dich de luu .npz")
    ap.add_argument("--subjects", nargs="*", help="vd S1 S2 S3 (mac dinh: tat ca S1..S15 tim thay)")
    args = ap.parse_args()

    subjects = args.subjects or [f"S{i}" for i in range(1, 16)]
    os.makedirs(args.dst, exist_ok=True)
    done = []
    for s in subjects:
        pkl = os.path.join(args.src, s, f"{s}.pkl")
        if not os.path.exists(pkl):
            print(f"Bo qua {s}: khong thay {pkl}")
            continue
        with open(pkl, "rb") as f:                       # chi mo file tai tu nguon chinh thuc
            d = pickle.load(f, encoding="latin1")
        w = d["signal"]["wrist"]
        out = os.path.join(args.dst, f"{s}.npz")
        np.savez_compressed(
            out,
            bvp=np.asarray(w["BVP"], np.float32).ravel(),          # 64 Hz
            acc=np.asarray(w["ACC"], np.float32),                  # 32 Hz, (N, 3)
            label=np.asarray(d["label"], np.float32).ravel(),      # HR chuan moi 2 s
            activity=np.asarray(d["activity"]).ravel().astype(np.int8),
        )
        print(f"{s}: {os.path.getsize(out) / 1e6:.1f} MB -> {out}")
        done.append(s)

    with open(os.path.join(args.dst, "README.txt"), "w", encoding="utf-8") as f:
        f.write("Du lieu trich tu PPG-DaLiA (chi phan co tay: BVP 64 Hz, ACC 32 Hz, nhan HR, hoat dong).\n"
                "Nguon: Reiss, Indlekofer, Schmidt (2019). PPG-DaLiA. UCI Machine Learning Repository.\n"
                "DOI: 10.24432/C53890. Giay phep CC BY 4.0.\n"
                "https://archive.ics.uci.edu/dataset/495/ppg+dalia\n"
                f"Nguoi co trong thu muc nay: {', '.join(done)}\n")
    print("Xong. Da tao README.txt (ghi nguon) trong", args.dst)


if __name__ == "__main__":
    main()
