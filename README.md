# PPG Motion Noise Cancellation + Signal Quality Index (SQI) on STM32F407

> **Embedded biomedical system** that reads a photoplethysmography (PPG) signal in real time, removes motion artifact using an adaptive NLMS filter, estimates heart rate (HR), and classifies signal quality (Good / Bad) using a lightweight TinyML model — all running on a bare-metal STM32F407 microcontroller.

---

## What This Project Actually Does

| Capability | Status |
|---|---|
| Read PPG (IR/Red) + 3-axis accelerometer at **100 Hz** via I2C | ✅ Done |
| Adaptive **NLMS motion cancellation** using accelerometer as noise reference | ✅ Done |
| Real-time **HR estimation** displayed on OLED | ✅ Done |
| Validate algorithm on **PPG-DaLiA public dataset** (15 subjects, ECG ground truth) | ✅ Done |
| Collect **self-recorded dataset** from 8 people, 4 motion conditions | ✅ Done |
| **SQI classification** (Good/Bad) with LOSO cross-validation — 71.5% accuracy | ✅ Done |
| Port bandpass filter + NLMS to **C (bare-metal, FPU)** on STM32F407 | ✅ Done |
| Export SQI model to C and display `SQI: GOOD/BAD` on OLED | 🔄 In Progress |

---

## Hardware

```
STM32F407VGT6 (Discovery board)
├── MAX30102   — PPG sensor (IR + Red), I2C @ 0x57 → PB6/PB7
├── MPU6050    — 3-axis accelerometer, I2C @ 0x68 → PB6/PB7
├── SSD1306    — 128×64 OLED display, I2C @ 0x3C → PB6/PB7
└── USART2     — PA2/PA3 → USB-UART (data streaming to PC at 115200 baud)
```

All three sensors share the same **I2C1 bus** with different addresses — no extra wiring needed.  
When collecting CSV data, `USE_OLED 0` disables OLED to avoid I2C timing jitter.

---

## Results That Matter

### Motion Artifact Removal — NLMS (PPG-DaLiA, 15 subjects, ECG reference)

| Condition | MAE before NLMS | MAE after NLMS | Reduction |
|---|:---:|:---:|:---:|
| Climbing stairs (S1) | 49.6 bpm | 27.2 bpm | **−45%** |
| Climbing stairs (S5) | 64.4 bpm | **2.0 bpm** | **−97%** |
| Walking (S3) | 24.0 bpm | **4.9 bpm** | **−80%** |
| Cycling (S5) | 80.9 bpm | 34.1 bpm | **−58%** |
| **Overall (15 subjects)** | 11.83 bpm | **11.06 bpm** | −6.5% |

Chosen configuration: `taps=32, mu=0.02, eps_rel=1.0`

### NLMS on Real Hardware (MAX30102 + MPU6050 at 100 Hz)

| File | Motion (mean / peak g) | HR before NLMS | HR after NLMS |
|---|:---:|:---:|:---:|
| `ppg_manh_Hung` | 0.530 / 2.263 g | 111.3 ± 24.8 bpm | **60.7 ± 2.6 bpm** |
| `ppg_manh_Khiem` | 0.255 / 1.870 g | 101.7 ± 9.9 bpm | **68.8 ± 13.9 bpm** |

NLMS reduced residual energy to **39–44%** of pre-filter energy in heavy motion cases.

### SQI Classifier — Leave-One-Subject-Out Evaluation (8 subjects, 1,034 windows)

| Model | Accuracy | Precision | Recall | F1 |
|---|:---:|:---:|:---:|:---:|
| Decision Tree (depth=4) | 67.3% | 0.678 | 0.671 | 0.669 |
| **Random Forest (15×4)** | **71.5%** | **0.715** | **0.715** | **0.715** |
| MLP (16, 8) | 63.1% | 0.636 | 0.632 | 0.629 |

**7 lightweight features** per 10-second window (all writable in C on-chip):  
`PI%`, `PPG std`, `IBI std`, `Valid IBI ratio`, `Spectral purity`, `Acc mean g`, `Acc max g`

---

## Repository Structure

```
Do-An-PPG/
├── firmware/ppg_f407/        # STM32CubeIDE project (bare-metal C)
│   └── Core/Src/
│       ├── main.c            # Sensor init, 100 Hz loop, OLED display
│       ├── dsp_nlms.c        # Bandpass filter (Biquad) + NLMS (C/FPU)
│       └── dsp_nlms.h
├── python/
│   ├── ppg_utils.py          # Bandpass, peak detection, HR/IBI, FFT tools
│   ├── nlms.py               # NLMS core + PPG-DaLiA loader
│   ├── nlms_csv.py           # Run NLMS on a self-recorded CSV file
│   ├── sweep_nlms.py         # Grid search over (taps, mu, eps) on DaLiA
│   ├── train_sqi.py          # Feature extraction + SQI model training (LOSO)
│   ├── check_data.py         # Quick data quality report for any CSV
│   └── read_ppg.py           # Stream CSV from UART in real time
├── data/
│   ├── mine/                 # Self-recorded dataset (8 people × 4 conditions)
│   │   ├── Du/   Hieu/   KhiemHungMinh/
│   │   └── conditions: dungyen | nhe | epchat | manh (~60 s each)
│   └── public/               # PPG-DaLiA (gitignored, ~2.7 GB)
├── report/
│   ├── nlms_S1–S3.png        # Algorithm validation plots (DaLiA)
│   ├── nlms_Hung_manh.png    # Real hardware validation
│   ├── nlms_Khiem_manh.png
│   ├── sqi_confusion.png     # Confusion matrix (8-subject LOSO)
│   ├── sqi_features.csv      # Feature table for all windows
│   └── dalia_all_results.txt # MAE table for S1–S15
└── picture/                  # Hardware photos and schematics
```

---

## Quick Start

### 1. Collect data with the STM32 board
```bash
# In main.c: set USE_OLED 0 before collecting CSV
# Open a serial monitor at 115200 baud, copy output to data/mine/<name>/
python3 python/read_ppg.py --port /dev/ttyUSB0 --out data/mine/Du/ppg_dungyen_lan1_Du.csv
```

### 2. Check data quality
```bash
cd python
python3 check_data.py ../data/mine/Du/ppg_dungyen_lan1_Du.csv
```

### 3. Run NLMS on a CSV file
```bash
python3 nlms_csv.py --csv ../data/mine/KhiemHungMinh/ppg_manh_lan2_Hung.csv \
                    --taps 32 --mu 0.02 --eps 1.0 --ref 60
```

### 4. Sweep parameters on PPG-DaLiA
```bash
python3 sweep_nlms.py ../data/public/PPG_FieldStudy/S1/S1.pkl
```

### 5. Train SQI model (auto-finds all CSVs in data/mine/)
```bash
python3 train_sqi.py
# → report/sqi_confusion.png, report/sqi_features.csv
```

### 6. Flash firmware to STM32F407
Open `firmware/ppg_f407` in **STM32CubeIDE** → Build → Run (ST-Link)

---

## Signal Processing Pipeline

```
MAX30102 (IR/Red 100 Hz) ──┐
                            ├─→ fix_stale (FIFO repeat fix) ─→ Biquad BP [0.5–5 Hz]
MPU6050 (ax,ay,az 100 Hz) ─┘                                              │
                                                              NLMS (taps=32, mu=0.02)
                                                                           │
                                                               Peak detect + HR/IBI
                                                                           │
                                                     Feature extraction (7 features, 10 s window)
                                                                           │
                                                             SQI classifier → GOOD / BAD
                                                                           │
                                                                    OLED display
```

---

## Dependencies

```txt
numpy  scipy  matplotlib  pandas  scikit-learn  pyserial
```
Install: `pip install -r python/requirements.txt`

Firmware: STM32CubeIDE 1.x, STM32F4 HAL (no external DSP library needed — FPU math only)

---

## Dataset

| Source | Used for | Sampling rate | Ground truth |
|---|---|:---:|---|
| **PPG-DaLiA** (self-collected from UCI) | NLMS validation | 64 Hz | ECG-derived HR |
| **Self-recorded** (8 people × 4 conditions) | SQI training & NLMS verification on real HW | 100 Hz | — |

> PPG-DaLiA is excluded from git (`.gitignore`). Download from [UCI ML Repository](https://archive.ics.uci.edu/dataset/495/ppg+dalia) (CC BY 4.0).

---

## About

Academic project — *Biomedical Electronics, 2026*  
Hardware: STM32F407 Discovery, MAX30102, MPU6050, SSD1306 OLED  
For academic and research purposes only. Not intended for medical diagnosis.
