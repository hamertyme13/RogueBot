"""
Startup self-check for RogueBot.

Verifies critical subsystems before the main loop starts and returns
a spoken summary of what is online / offline.
"""

import urllib.error
import urllib.request

from config import OLLAMA_URL, OPENAI_API_KEY
from logger import log

import socket


def _check_ollama() -> bool:
    """Return True if the Ollama API is reachable."""
    try:
        # Hit the Ollama health/version endpoint (no auth needed)
        health_url = OLLAMA_URL.replace("/api/chat", "/api/version")
        urllib.request.urlopen(health_url, timeout=3)
        return True
    except Exception as exc:
        log.warning("Ollama check failed: %s", exc)
        return False


def _check_openai() -> bool:
    """Return True if an OpenAI key is configured (not verified live)."""
    return bool(OPENAI_API_KEY)


def _check_internet() -> bool:
    """Return True if we can reach a well-known host."""
    try:
       connection = socket.create_connection(("1.1.1.1", 443), timeout=3)
       connection.close()
       return True
    except OSError as error:
        log.warning("Internet check failed: %s", error)
        return False


def run_startup_checks() -> str:
    """
    Run all checks and return a brief spoken status string.
    Called once at boot before the wake-word loop starts.
    """

    log.info("Running startup self-check…")

    ollama_ok = _check_ollama()
    openai_ok = _check_openai()
    internet_ok = _check_internet()

    parts = []

    if ollama_ok:
        parts.append("local AI is online")
        log.info("Startup check: Ollama OK")
    else:
        parts.append("local AI is offline")
        log.warning("Startup check: Ollama unreachable")

    if openai_ok:
        parts.append("cloud AI is configured")
        log.info("Startup check: OpenAI key present")
    else:
        parts.append("cloud AI is not configured")
        log.info("Startup check: no OpenAI key")

    if not internet_ok:
        parts.append("internet appears unavailable")
        log.warning("Startup check: no internet connectivity")

    summary = "; ".join(parts).capitalize() + "."
    log.info("Startup check complete: %s", summary)
    return summary
