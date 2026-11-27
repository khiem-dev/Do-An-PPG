"""
Train mo hinh Random Forest cuoi cung tren toan bo tap sqi_features.csv
va xuat truc tiep sang code C thuan (khong can thu vien ngoai) cho STM32F407.

Chay:
  python3 export_sqi_c.py
"""
import argparse
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

FEATURE_COLS = [
    "pi_pct",
    "ppg_std",
    "ibi_std",
    "valid_ibi_ratio",
    "spec_purity",
    "acc_mean_g",
    "acc_max_g",
]


def emit_tree_c(tree, tree_idx):
    """Sinh ham C tinh xac suat lop Tot (1) cho 1 cay quyet dinh."""
    t = tree.tree_
    lines = [f"static float sqi_tree_{tree_idx}(const float f[7]) {{"]

    def walk(node, depth):
        indent = "    " * depth
        if t.feature[node] < 0:
            vals = t.value[node][0]
            total = vals[0] + vals[1]
            p1 = float(vals[1] / total) if total > 0 else 0.5
            lines.append(f"{indent}return {p1:.6f}f;")
        else:
            feat = t.feature[node]
            thresh = float(t.threshold[node])
            lines.append(f"{indent}if (f[{feat}] <= {thresh:.6f}f) {{")
            walk(t.children_left[node], depth + 1)
            lines.append(f"{indent}}} else {{")
            walk(t.children_right[node], depth + 1)
            lines.append(f"{indent}}}")

    walk(0, 1)
    lines.append("}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-csv", default="../report/sqi_features.csv")
    ap.add_argument(
        "--out-h",
        default="../firmware/ppg_f407/Core/Inc/sqi_trees.h",
    )
    args = ap.parse_args()

    df = pd.read_csv(args.features_csv)
    X = df[FEATURE_COLS].to_numpy(dtype=np.float32)
    y = df["label"].to_numpy(dtype=int)

    clf = RandomForestClassifier(n_estimators=15, max_depth=4, random_state=42)
    clf.fit(X, y)
    train_acc = accuracy_score(y, clf.predict(X))
    print(f"Train samples: {len(df)} | Train accuracy: {train_acc * 100:.2f}%")

    os.makedirs(os.path.dirname(args.out_h), exist_ok=True)
    with open(args.out_h, "w", encoding="utf-8") as fp:
        fp.write("/* Tu dong sinh boi python/export_sqi_c.py - KHONG SUA TAY */\n")
        fp.write("#ifndef SQI_TREES_H\n#define SQI_TREES_H\n\n")
        fp.write("/* Thu tu dac trung f[0..6]:\n")
        for i, col in enumerate(FEATURE_COLS):
            fp.write(f" * f[{i}] = {col}\n")
        fp.write(" */\n\n")

        for i, est in enumerate(clf.estimators_):
            fp.write(emit_tree_c(est, i))
            fp.write("\n\n")

        n_trees = len(clf.estimators_)
        fp.write("static inline int sqi_rf_predict(const float f[7], float *prob_good_out)\n{\n")
        fp.write("    float sum = 0.0f;\n")
        for i in range(n_trees):
            fp.write(f"    sum += sqi_tree_{i}(f);\n")
        fp.write(f"    float p = sum * {1.0 / n_trees:.8f}f;\n")
        fp.write("    if (prob_good_out) *prob_good_out = p;\n")
        fp.write("    return (p >= 0.5f) ? 1 : 0;\n")
        fp.write("}\n\n#endif /* SQI_TREES_H */\n")

    print(f"Da xuat C header: {args.out_h} ({n_trees} cay, max_depth=4)")


if __name__ == "__main__":
    main()
