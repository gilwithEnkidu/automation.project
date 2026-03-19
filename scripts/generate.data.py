###############################################################################
# File Name : generate.raw.data.py
# Author    : gil
# Date      : 2026.03.14
# Version   : 0.2
# Description: raw data 생성 프로그램
# params 및 고정 값 현실화
# output directory 수정 (v0.1)
# MAX_PER_DATE & count_date 수정 (v0.11)
# 정규분포로 생성되는 데이터의 이상치 발생 확률 추가 후 generate_value 함수 작성 (v0.2)
#
###############################################################################


import numpy as np
import os
import random
from datetime import date, timedelta

# ── 사용자 설정 ──────────────────────────────────────────
START_DATE  = date(2026, 3, 1)   # 시작 날짜
END_DATE    = date(2026, 3, 5)   # 종료 날짜
MAX_PER_DAY = 65                 # 하루 최대 생성 수

# 이상치 설정
# 6σ 이상치를 전체 데이터의 약 0.3~0.5% 비율로 주입
# 1800개 기준 → 약 5~9개 파일에서 이상치 발생
OUTLIER_PROB = 0.004             # 파일 1개당 이상치 발생 확률 (0.4%)
OUTLIER_SIGMA = 6.5              # 이상치 크기 (σ 배수, ±방향 랜덤)
# ────────────────────────────────────────────────────────

CAR_NUMBERS = ["8425", "5824", "8363", "8368", "5864", "5884"]

# 분석항목별 정규분포 파라미터 (min, max, mean, std)
params = {
    "Cl":  {"min": 0.03,  "max": 4.0, "mean": 0.214, "std": 0.243},
    "NO2": {"min": 0.08,  "max": 0.61, "mean": 0.193,  "std": 0.0865},
    "NO3": {"min": 0.07,  "max": 5.1, "mean": 0.584, "std": 0.121},
    "SO4": {"min": 0.17,  "max": 6.72, "mean": 0.628, "std": 0.123},
}

# 고정 값
INJECTION_VOL = "250.0"
UNIT          = "㎍/L"
DILUTION      = "0.8810"
INSTRUMENTS   = ["IC-5000-5 [p1]", "IC-5000-5 [p2]", "IC-5000-10 [p1]"]
RUN_TIME      = "35.00"

output_dir = os.path.expanduser("~/automation.proj/raw.data")    # 경로 수정, 260319
os.makedirs(output_dir, exist_ok=True)

def generate_value(p, is_outlier=False):
    """정규분포 값 생성. 이상치일 경우 6σ 이상의 값을 반환."""
    if is_outlier:
        direction = random.choice([-1, 1])          # 양방향 이상치
        sigma_mult = random.uniform(OUTLIER_SIGMA, OUTLIER_SIGMA + 1.0)
        val = p["mean"] + direction * sigma_mult * p["std"]
        # 물리적으로 불가능한 음수 방지
        val = max(val, 0.0)
    else:
        val = np.random.normal(p["mean"], p["std"])
        # 정상 범위는 ±4σ 내로 soft-clip (6σ 이상치 공간 확보)
        lo = p["mean"] - 4 * p["std"]
        hi = p["mean"] + 4 * p["std"]
        val = float(np.clip(val, max(p["min"], lo), min(p["max"], hi)))
    return round(float(val), 4)

file_count   = 0
outlier_count = 0
current_date = START_DATE

while current_date <= END_DATE:
    mm   = current_date.strftime("%m")
    dd   = current_date.strftime("%d")
    yy   = current_date.strftime("%y")
    date_str  = f"{mm}/{dd}"
    date_code = f"{yy}{mm}{dd}"


    # 하루 생성 데이터 60±5, batch number 생성 및 정렬
    count_today = random.randint(55, MAX_PER_DAY)
    seq_pool = random.sample(range(1, 76), min(count_today, 75))
    seq_pool.sort()

    for seq in seq_pool:
        car     = random.choice(CAR_NUMBERS)
        seq_str = f"{seq:03d}"

        sample_name = f"{car} {date_str} {date_code}{seq_str}"
        instrument  = random.choice(INSTRUMENTS)

        # 이 파일에서 이상치가 발생할지 결정
        has_outlier   = random.random() < OUTLIER_PROB
        outlier_analyte = random.choice(list(params.keys())) if has_outlier else None
        if has_outlier:
            outlier_count += 1

        lines = []
        lines.append(f"{sample_name}\t{INJECTION_VOL}\t{UNIT}")
        lines.append(f"{DILUTION}\t{instrument}\t{RUN_TIME}")

        for idx, (analyte, p) in enumerate(params.items(), start=1):
            is_outlier = (analyte == outlier_analyte)
            val = generate_value(p, is_outlier)
            lines.append(f"{idx}\t{analyte}\t{val:.4f}")

        filename = f"{output_dir}/{car} {mm}_{dd} {date_code}{seq_str}.csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        file_count += 1

    current_date += timedelta(days=1)

print(f"총 {file_count}개 CSV 파일 생성 완료! → ./{output_dir}/")
print(f"이상치 포함 파일 수: {outlier_count}개 ({outlier_count/file_count*100:.2f}%)")