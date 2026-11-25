"""Kiem tra moi truong Python cho do an PPG (viec 0.3 / 1.6)."""
import importlib
import sys

mods = ["numpy", "scipy", "matplotlib", "pandas", "sklearn", "serial"]
ok = True
print("Python", sys.version.split()[0])
for m in mods:
    try:
        mod = importlib.import_module(m)
        print(f"  OK   {m:12s} {getattr(mod, '__version__', '')}")
    except ImportError:
        ok = False
        print(f"  THIEU {m}")
print("San sang!" if ok else "Chay: pip install -r requirements.txt")
