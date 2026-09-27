"""Shared field definitions and paths for the extraction workflow."""

import os
import sys
from pathlib import Path


def resource_root() -> Path:
    """Locate read-only assets both in source and in a PyInstaller bundle."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def user_data_root() -> Path:
    """Keep mutable files outside a one-file executable's temporary bundle."""
    if getattr(sys, "frozen", False):
        return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "ASW-Project01"
    return resource_root()


PROJECT_ROOT = resource_root()
APP_DATA_ROOT = user_data_root()
RUNTIME_TEMP_ROOT = APP_DATA_ROOT / ".runtime_tmp"
TEMPLATE = PROJECT_ROOT / "assets" / "业务联系单模板.xlsx"
MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
FIELDS = ("bl_number", "vessel", "voyage", "sailing_date", "containers", "station", "destination", "origin")
CELLS = {"bl_number": "B8", "vessel": "B9", "voyage": "E9", "sailing_date": "B10", "containers": "B11", "station": "B12", "destination": "B13", "origin": "E13"}
MANUAL_CELLS = {"carrier": "B4", "customer_service": "E3", "contract": "E5", "sales": "B39"}
LABELS = {"bl_number": "提单号/订舱号", "vessel": "船名", "voyage": "航次", "sailing_date": "船期", "containers": "箱量及类型", "station": "场站", "destination": "目的港", "origin": "起运港"}
