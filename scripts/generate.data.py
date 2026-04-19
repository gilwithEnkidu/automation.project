###############################################################################
# File Name : generate.raw.data.py
# Author    : gil
# Date      : 2026.03.14
# Version   : 0.2
# Description : raw data 생성 프로그램
# update :
# params 및 고정 값 현실화, output directory 수정 (v0.1)
# MAX_PER_DATE & count_date 수정 (v0.11)
# 정규분포로 생성되는 데이터의 이상치 발생 확률 추가 후 generate_value 함수 작성 (v0.2)
# 시그마 수정 및 질산염 표준편차 현실화 (v0.21)
# 결측치 발생 코드 적용 (v0.22)
#
###############################################################################

########### raw data example ###########
#1| 5824 03/01 260301021   250.0    ㎍/L
#2| 0.8810  IC-5000-5 [p1]  35.00
#3| 1	Cl	0.2242
#4| 2	NO2	0.2409
#5| 3	NO3	0.3445
#6| 4	SO4	0.7208
#########################################

import numpy as np
import os
import random
from datetime import date, timedelta

# ── 사용자 설정 ──────────────────────────────────────────
START_DATE  = date(2026, 3, 1)
END_DATE    = date(2026, 3, 31)
MAX_PER_DAY = 23    # 하루 동안 생성되는 raw data 의 최대치

# 이상치 설정, 발생확률 0.4%
OUTLIER_PROB  = 0.004
OUTLIER_SIGMA = 3.5

# 결측치 설정, 전체 analyte 중 발생확률 0.3%, 한 파일마다 analyte이 4개 -> 각각 독립적으로 적용
MISSING_PROB = 0.003 / 4
# ────────────────────────────────────────────────────────

# 탱크로리 차량 번호
CAR_NUMBERS = ["8425", "5824", "8363", "8368", "5864", "5884"]

# 각 analyte의 최대값,최소값,기대값,표준편차 - 정규분포를 고려하여 설정
params = {
    "Cl" : {"min": 0.03,  "max": 4.0,  "mean": 0.214, "std": 0.243},
    "NO2": {"min": 0.08,  "max": 0.61, "mean": 0.193, "std": 0.0865},
    "NO3": {"min": 0.07,  "max": 5.1,  "mean": 0.584, "std": 0.222},
    "SO4": {"min": 0.17,  "max": 6.72, "mean": 0.628, "std": 0.123},
}

# raw data template header
INJECTION_VOL = "250.0"
UNIT          = "㎍/L"
DILUTION      = "0.8810"
INSTRUMENTS   = ["IC-5000-5 [p1]", "IC-5000-5 [p2]", "IC-5000-10 [p1]"]
RUN_TIME      = "35.00"

output_dir = os.path.expanduser("~/automation.project/raw.data")
os.makedirs(output_dir, exist_ok=True)

# analyte 이 이상치일 경우
def generate_value(p, is_outlier=False):
    if is_outlier:
        direction  = random.choice([-1, 1])
        sigma_mult = random.uniform(OUTLIER_SIGMA, OUTLIER_SIGMA + 1.0)
        val = p["mean"] + direction * sigma_mult * p["std"]
        val = max(val, 0.0)
    else:
        val = np.random.normal(p["mean"], p["std"])
        lo  = p["mean"] - 4 * p["std"]
        hi  = p["mean"] + 4 * p["std"]
        val = float(np.clip(val, max(p["min"], lo), min(p["max"], hi)))
    return round(float(val), 4)

file_count    = 0
outlier_count = 0
missing_count = 0
current_date  = START_DATE

while current_date <= END_DATE:
    mm   = current_date.strftime("%m")
    dd   = current_date.strftime("%d")
    yy   = current_date.strftime("%y")
    date_str  = f"{mm}/{dd}"
    date_code = f"{yy}{mm}{dd}"

    # 하루 생성할 Lot. 갯수 시뮬
    # -> 하루 간 검사할 샘플 수가 일정하지 않기 때문에 보통 60±5 Lot. 측정한다고 가정함
    count_today = random.randint(19, MAX_PER_DAY)

    # Lot. number 시뮬
    # -> Lot.에 기록되는 세자릿수 batch number가 001~076 사이의 임의의 수가 되도록 설정
    seq_pool    = random.sample(range(1, 76), min(count_today, 75))
    seq_pool.sort()

    for seq in seq_pool:
        car     = random.choice(CAR_NUMBERS)
        seq_str = f"{seq:03d}"

        sample_name = f"{car} {date_str} {date_code}{seq_str}"
        instrument  = random.choice(INSTRUMENTS)
        # 현재 다루고 있는 파일이 이상치를 가질 것인지 결정
        has_outlier     = random.random() < OUTLIER_PROB

        # outlier_analyte은 사용자 정의 함수에서 인자로 사용함
        outlier_analyte = random.choice(list(params.keys())) if has_outlier else None
        if has_outlier:
            outlier_count += 1

        lines = []
        lines.append(f"{sample_name}\t{INJECTION_VOL}\t{UNIT}")
        lines.append(f"{DILUTION}\t{instrument}\t{RUN_TIME}")

        for idx, (analyte, p) in enumerate(params.items(), start=1):
            is_missing = random.random() < MISSING_PROB
            if is_missing:
                lines.append(f"{idx}\t{analyte}\tn.a.")
                missing_count += 1
            else:
                is_outlier = (analyte == outlier_analyte)
                val = generate_value(p, is_outlier)
                lines.append(f"{idx}\t{analyte}\t{val:.4f}")

        filename = f"{output_dir}/{car} {mm}_{dd} {date_code}{seq_str}.csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        file_count += 1

    current_date += timedelta(days=1)

total_values = file_count * len(params)
print(f"총 {file_count}개 CSV 파일 생성 완료! → ./{output_dir}/")
print(f"이상치 포함 파일 수 : {outlier_count}개 ({outlier_count/file_count*100:.2f}%)")
print(f"결측치 발생 항목 수 : {missing_count}개 ({missing_count/total_values*100:.3f}%)")
