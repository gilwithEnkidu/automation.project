###############################################################################
# File Name : generate.raw.data.py
# Author    : gilgamesh with Claude
# Date      : 2026.03.11
# Version   : 0.0
# Description: raw data 생성 프로그램
#
###############################################################################

import numpy as np
import os

# 분석항목별 정규분포 파라미터 (min, max, mean, std)
params = {
    "Cl":  {"min": 1.0,  "max": 50.0, "mean": 25.0, "std": 8.0},
    "NO2": {"min": 0.1,  "max": 10.0, "mean": 3.0,  "std": 1.5},
    "NO3": {"min": 0.5,  "max": 30.0, "mean": 10.0, "std": 5.0},
    "SO4": {"min": 2.0,  "max": 60.0, "mean": 20.0, "std": 7.0},
}

os.makedirs("fake_data", exist_ok=True)

for i in range(1, 31):
    sample_name = f"SAMPLE_{i:02d}"
    injection_vol = 10.0       # 주입량
    dilution = 1               # 희석배수
    program = "IC_Program_A"   # 프로그램명
    run_time = 30              # run time (분)

    lines = []
    # 1번째 줄: 샘플명, 주입량
    lines.append(f"{sample_name}\t{injection_vol}")
    # 2번째 줄: 희석배수, 프로그램명, run time
    lines.append(f"{dilution}\t{program}\t{run_time}")
    # 분석항목 (번호, amount)
    for idx, (analyte, p) in enumerate(params.items(), start=1):
        val = np.random.normal(p["mean"], p["std"])
        val = np.clip(val, p["min"], p["max"])
        lines.append(f"{idx}\t{analyte}\t{val:.4f}")

    with open(f"fake_data/data_{i:02d}.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

print("30개 CSV 파일 생성 완료!")