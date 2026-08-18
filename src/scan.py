"""
GitHub Actions 入口 - 单次扫描，用于前端展示

使用方式:
    python3 src/scan.py

特点:
    - 单次执行，不常驻
    - 不执行自动交易
    - 输出 JSON 到 data/ 目录
    - 由 GitHub Actions cron 定时触发
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
from scanner import (
    main as scanner_main,
    load_config,
    _build_session,
    _maybe_clean_logs,
    _fm_session,
    _http_session,
    _bsc_session,
    FM_HEADERS,
    DS_HEADERS,
    scan_once,
    save_queue,
    load_queue,
    DATA_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    global _fm_session, _http_session, _bsc_session
    log.info("🚀 BSC Token Scanner - GitHub Actions 模式 (单次扫描)")

    try:
        cfg = load_config()
        _fm_session = _build_session(cfg.get("proxy"), FM_HEADERS)
        _http_session = _build_session(cfg.get("proxy"))
        _bsc_session = _build_session(cfg.get("proxy"), DS_HEADERS)
        _maybe_clean_logs()

        scan_once(cfg)

        log.info("✅ 扫描完成，JSON 已输出到 data/ 目录")
    except Exception as e:
        log.error("扫描失败: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
