"""Shared structured logger for the controls package.

Uses stdlib ``logging`` with a namespaced hierarchy so callers can configure
handlers per-subpackage (e.g. ``aigov.controls.pii``).
"""
from __future__ import annotations

import logging
import os

_ROOT = "aigov"
_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under ``aigov.<name>``.

    Configures a single stderr handler with a compact JSON-ish line format on
    first call so tests and CI emit deterministic output.
    """
    global _CONFIGURED
    if not _CONFIGURED:
        level = os.environ.get("AIGOV_LOG_LEVEL", "INFO").upper()
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt='{"ts":"%(asctime)s","level":"%(levelname)s",'
                '"logger":"%(name)s","msg":%(message)s}',
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
        root = logging.getLogger(_ROOT)
        root.addHandler(handler)
        root.setLevel(level)
        root.propagate = False
        _CONFIGURED = True

    return logging.getLogger(f"{_ROOT}.{name}")
