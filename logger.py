"""
Centralised logging configuration for RogueBot.

Usage in any module:
    from logger import log
    log.info("Something happened")
    log.warning("Something odd")
    log.error("Something broke")

Console: WARNING and above.
File:    DEBUG and above, rotating at 1 MB, keeping 3 backups.
"""

import logging
import logging.handlers
from pathlib import Path

_LOG_DIR = Path("data")
_LOG_FILE = _LOG_DIR / "roguebot.log"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger("roguebot")
log.setLevel(logging.DEBUG)

# ---- File handler (DEBUG+, rotating) ----
_file_handler = logging.handlers.RotatingFileHandler(
    _LOG_FILE,
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)

# ---- Console handler (WARNING+) ----
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.WARNING)
_console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

log.addHandler(_file_handler)
log.addHandler(_console_handler)
