###############################################################################
# File Name : watcher.py
# Author    : gil
# Date      : 2026.04.01
# Version   : 0.1
# Description : 신규 raw data 생성 감시 파일
# update :
#
#
###############################################################################

import logging
import os
import re
import shutil
import time
from datetime import datetime
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

# ── 경로 설정 ────────────────────────────────────────────────
SOURCE_DIR  = "/mnt/ic_share"                       # 네트워크 마운트 경로
BASE_DIR    = os.path.expanduser("~/automation.proj")
RAW_DIR     = os.path.join(BASE_DIR, "raw.data")
LOG_DIR     = os.path.join(BASE_DIR, "logs")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ── 네트워크 환경 설정 ───────────────────────────────────────
POLL_INTERVAL   = 5     # watchdog 폴링 주기 (초)
MOUNT_CHECK_SEC = 30    # 마운트 상태 확인 주기 (초)
RETRY_COUNT     = 5     # 복사 실패 시 최대 재시도 횟수
RETRY_DELAY     = 3     # 재시도 간격 (초)
STABLE_WAIT     = 1.0   # 파일 안정성 확인 대기 (초)
STABLE_CHECKS   = 3     # 파일 안정성 확인 횟수

# ── 로깅 설정 ────────────────────────────────────────────────
log_file = os.path.join(LOG_DIR, f"watcher_{datetime.now().strftime('%y%m%d')}.log")
logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── 파일 유효성 검사 ─────────────────────────────────────────
VALID_PATTERN = re.compile(r'^\d{4} \d{2}_\d{2} \d{9}\.csv$')

def is_valid_file(filename):
    return filename.endswith(".csv") and VALID_PATTERN.match(filename)

# ── 마운트 상태 확인 ─────────────────────────────────────────
def is_mounted(path):
    """
    /proc/mounts를 읽어 해당 경로가 마운트되어 있는지 확인.
    os.path.exists()는 마운트가 끊겨도 True를 반환할 수 있어
    신뢰도가 낮으므로 /proc/mounts 직접 참조.
    """
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.read()
        return path in mounts
    except Exception as e:
        log.error(f"마운트 확인 실패: {e}")
        return False

def wait_for_mount(path, check_interval=MOUNT_CHECK_SEC):
    """마운트가 복구될 때까지 대기."""
    log.warning(f"마운트 끊김 감지: {path}")
    while not is_mounted(path):
        log.warning(f"{check_interval}초 후 마운트 재확인...")
        time.sleep(check_interval)
    log.info(f"마운트 복구 확인: {path}")

# ── 파일 안정성 확인 ─────────────────────────────────────────
def is_file_stable(filepath):
    """
    파일 크기가 STABLE_CHECKS 횟수 동안 변하지 않으면 안정적으로 판단.
    IC 소프트웨어가 파일을 쓰는 도중 복사하는 사고 방지.
    """
    prev_size = -1
    for _ in range(STABLE_CHECKS):
        try:
            curr_size = os.path.getsize(filepath)
        except OSError:
            return False
        if curr_size == prev_size and curr_size > 0:
            return True
        prev_size = curr_size
        time.sleep(STABLE_WAIT)
    return False

# ── 복사 처리 (재시도 포함) ──────────────────────────────────
def copy_file(src_path):
    filename  = os.path.basename(src_path)
    dest_path = os.path.join(RAW_DIR, filename)

    if not is_valid_file(filename):
        return
    if os.path.exists(dest_path):
        log.debug(f"이미 존재, 스킵: {filename}")
        return
    if not is_file_stable(src_path):
        log.warning(f"파일 불안정 (쓰기 중?), 스킵: {filename}")
        return

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            shutil.copy2(src_path, dest_path)
            log.info(f"복사 완료: {filename}")
            return
        except OSError as e:
            log.warning(f"복사 실패 ({attempt}/{RETRY_COUNT}): {filename} → {e}")
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
            else:
                log.error(f"복사 최종 실패, 포기: {filename}")

# ── watchdog 이벤트 핸들러 ───────────────────────────────────
class IcFileHandler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return
        log.info(f"새 파일 감지 (created): {event.src_path}")
        copy_file(event.src_path)

    def on_moved(self, event):
        """temp 파일로 쓴 뒤 rename하는 IC 소프트웨어 대응."""
        if event.is_directory:
            return
        log.info(f"새 파일 감지 (renamed): {event.dest_path}")
        copy_file(event.dest_path)

# ── 시작 시 누락 파일 동기화 ────────────────────────────────
def sync_existing():
    """watchdog 미가동 중 생성된 파일 일괄 동기화."""
    log.info("기존 파일 동기화 시작...")
    count = 0
    try:
        for filename in os.listdir(SOURCE_DIR):
            src  = os.path.join(SOURCE_DIR, filename)
            dest = os.path.join(RAW_DIR, filename)
            if os.path.isfile(src) and is_valid_file(filename) and not os.path.exists(dest):
                try:
                    shutil.copy2(src, dest)
                    log.info(f"동기화 복사: {filename}")
                    count += 1
                except Exception as e:
                    log.error(f"동기화 실패: {filename} → {e}")
    except Exception as e:
        log.error(f"동기화 중 오류: {e}")
    log.info(f"동기화 완료: {count}개 파일 복사됨")

# ── observer 생성 헬퍼 ───────────────────────────────────────
def create_observer(handler):
    observer = PollingObserver(timeout=POLL_INTERVAL)
    observer.schedule(handler, SOURCE_DIR, recursive=True)
    return observer

# ── 메인 ────────────────────────────────────────────────────
def main():
    log.info(f"감시 시작: {SOURCE_DIR}")
    log.info(f"저장 경로: {RAW_DIR}")

    # 마운트 확인 후 시작
    if not is_mounted(SOURCE_DIR):
        wait_for_mount(SOURCE_DIR)

    sync_existing()

    handler  = IcFileHandler()
    observer = create_observer(handler)
    observer.start()
    log.info("watchdog 실행 중... (종료: Ctrl+C)")

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            # 마운트 끊김 감지
            if not is_mounted(SOURCE_DIR):
                observer.stop()
                observer.join()
                wait_for_mount(SOURCE_DIR)      # 복구될 때까지 대기
                sync_existing()                 # 끊긴 동안 누락 파일 동기화
                observer = create_observer(handler)
                observer.start()
                log.info("watchdog 재시작 완료")
                continue

            # observer 비정상 종료 감지
            if not observer.is_alive():
                log.warning("observer 비정상 종료 감지, 재시작...")
                observer.stop()
                observer = create_observer(handler)
                observer.start()
                log.info("observer 재시작 완료")

    except KeyboardInterrupt:
        log.info("종료 신호 수신 (Ctrl+C)")
    finally:
        observer.stop()
        observer.join()
        log.info("watchdog 종료 완료")

if __name__ == "__main__":
    main()