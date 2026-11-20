
import os
import runpy
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "online_banking_system"

os.chdir(APP_DIR)

runpy.run_path(
    str(APP_DIR / "app.py"),
    run_name="__main__"
)
