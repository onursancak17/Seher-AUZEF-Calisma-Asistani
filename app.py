"""GitHub/Streamlit Cloud entry point for Seher's AUZEF study assistant.

The private bundle contains the seven study PDFs, quiz banks, and full source.
Extracting it at startup keeps deployment to a single archive upload.
"""
from __future__ import annotations

import os
import runpy
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "uygulama_paketi.zip"
RUNTIME = ROOT / ".runtime"
STAMP = RUNTIME / ".archive_stamp"

if not ARCHIVE.is_file():
    raise RuntimeError("uygulama_paketi.zip bulunamadı. GitHub deposuna yüklenmesi gerekiyor.")

current_stamp = str(ARCHIVE.stat().st_size) + ":" + str(ARCHIVE.stat().st_mtime_ns)
if not (RUNTIME / "app.py").is_file() or not STAMP.is_file() or STAMP.read_text() != current_stamp:
    RUNTIME.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "r") as bundle:
        root = RUNTIME.resolve()
        for item in bundle.infolist():
            path = (RUNTIME / item.filename).resolve()
            if not path.is_relative_to(root):
                raise RuntimeError("Paket içinde geçersiz dosya yolu bulundu.")
        bundle.extractall(RUNTIME)
    STAMP.write_text(current_stamp, encoding="utf-8")

sys.path.insert(0, str(RUNTIME))
os.chdir(RUNTIME)
runpy.run_path(str(RUNTIME / "app.py"), run_name="__main__")
