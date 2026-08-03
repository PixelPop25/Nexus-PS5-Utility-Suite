# NEXUS — Native Build Guide

Build a standalone app for Windows, macOS, or Linux, so you do **not** need Python or pip.

## Prerequisites (developer machine only)

```bash
pip install pyinstaller PyQt6 PyQt6-WebEngine
# optional faster/smaller builds:
# pip install nuitka ordered-set zstandard
```

Place `nexus_icon.ico` (and optional `sounds/ui_click.wav`) next to `nexus_ps5.py`.

---

## Windows (one-file `.exe`)

```bash
pyinstaller --noconfirm --clean --windowed --onefile ^
  --name "NEXUS" ^
  --icon nexus_icon.ico ^
  --add-data "sounds;sounds" ^
  --hidden-import PyQt6.QtWebEngineWidgets ^
  nexus_ps5.py
```

Output: `dist/NEXUS.exe`

## macOS (`.app` bundle)

```bash
pyinstaller --noconfirm --clean --windowed --onedir \
  --name "NEXUS" \
  --icon nexus_icon.icns \
  --add-data "sounds:sounds" \
  --hidden-import PyQt6.QtWebEngineWidgets \
  nexus_ps5.py
```

Optional codesign (Apple Developer ID):

```bash
codesign --deep --force --sign "Developer ID Application: YOUR_NAME" dist/NEXUS.app
```

## Linux (AppImage-friendly onedir)

```bash
pyinstaller --noconfirm --clean --windowed --onedir \
  --name "NEXUS" \
  --add-data "sounds:sounds" \
  --hidden-import PyQt6.QtWebEngineWidgets \
  nexus_ps5.py
```

You can wrap `dist/NEXUS/` with [appimagetool](https://appimage.github.io/) for a single AppImage.

---

## Nuitka alternative (smaller / faster startup)

```bash
python -m nuitka --standalone --onefile --enable-plugin=pyqt6 \
  --windows-disable-console --windows-icon-from-ico=nexus_icon.ico \
  --include-data-dir=sounds=sounds \
  --output-filename=NEXUS \
  nexus_ps5.py
```

---

## Notes

- WebEngine embeds Chromium; first build is large (~150–250 MB). That is expected.
- Ship `sounds/ui_click.wav` inside the bundle so UI clicks work offline.
- Test FTP / TCP features against a real console after packaging; antivirus may flag one-file PyInstaller binaries the first time (submit for reputation if needed).
