# Build on Windows: .\.venv\Scripts\python.exe -m PyInstaller --noconfirm desktop.spec
from pathlib import Path


project = Path(SPECPATH)
assets = [
    (str(project / "assets" / "业务联系单模板.xlsx"), "assets"),
    (str(project / "app" / "static" / "index.html"), "app/static"),
    (str(project / "prompts" / "booking_extraction.txt"), "prompts"),
    (str(project / "data" / "field_aliases.json"), "data"),
    (str(project / "app" / "tools" / "legacy_extract.ps1"), "app/tools"),
    (str(project / "app" / "tools" / "word_to_pdf.ps1"), "app/tools"),
]

a = Analysis(
    [str(project / "desktop.py")],
    pathex=[str(project)],
    binaries=[],
    datas=assets,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ASW-Contact-Sheet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
