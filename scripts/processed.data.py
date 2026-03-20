###############################################################################
# File Name : processing.data.py
# Author    : gil
# Date      : 2026.03.20
# Version   : 0.1
# Description : raw data 정제 프로그램
# raw.data 폴더에 들어있는 csv 파일들에서 주요 정보를 골라 리스트로 저장하되
# 그 가운데 analyte에 해당되는 데이터의 규격이 벗어났는지 여부를 판단한 결과도
# 함께 저장하는 프로그램
# update :
#
###############################################################################

import os
import csv
from datetime import datetime

# 경로설정
BASE_DIR  = os.path.expanduser("~/automation.proj")
RAW_DIR   = os.path.join(BASE_DIR, "raw.data")
OUT_DIR   = os.path.join(BASE_DIR, "processed")

date_str  = datetime.now().strftime("%y%m%d")
OUT_FILE  = os.path.join(OUT_DIR, f"processed_data_{date_str}.csv")

os.makedirs(OUT_DIR, exist_ok=True)

# spec 설정
LIMITS = {
    "Cl": (0.03, 0.943),
    "NO2": (0.08, 0.453),
    "NO3": (0.07, 1.25),
    "SO4": (0.17, 0.997),
}

# 결과 저장용 리스트
results = []

for filename in os.listdir(RAW_DIR):
    if not filename.endswith(".csv"):
        continue
    filepath = os.path.join(RAW_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in lines[2:6]:
        parts = line.split("\t")
        analyte = parts[1]
        value = float(parts[2])
        low, high = LIMITS[analyte]
        status = "ALERT" if value < low or value > high else "OK"
        results.append([filename, analyte, value, status])

with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["file_name", "analyte", "value", "status"])
    writer.writerows(results)

print(f"처리 완료! → {OUT_FILE}")
print(f"총 항목 수: {len(results)}")
print(f"ALERT 수: {sum(1 for r in results if r[3]=='ALERT')}")