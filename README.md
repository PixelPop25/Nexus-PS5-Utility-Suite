# Nexus-PS5-Utility-Suite
A simple desktop utility for PS5 metadata &amp; database patching, autoload editor, FTP, TCP sending, and FFPFSC packaging.

## Features

- **YouTube Patcher** — patch app databases and icons for a Title ID  
- **Autoload Editor** — edit and deploy `autoload.txt`  
- **Y2JB Updater** — manage sandbox cache files  
- **TCP Sender** — send `.bin` / `.elf` payloads with history  
- **FTP Manager** — dual-pane local / remote browser  
- **FFPFSC Creator** — compress dumps with `mkpfs` 
- **Console Browser** — bookmarks for common console services i.e Garlic Saves/Cheatrunner

## Requirements

- Python 3.10+  
- [PyQt6](https://pypi.org/project/PyQt6/)  
- [PyQt6-WebEngine](https://pypi.org/project/PyQt6-WebEngine/) (optional, Console Browser)  
- `mkpfs` (optional, FFPFSC Creator)  

```bash
pip install PyQt6 PyQt6-WebEngine
```

## Run from source

```bash
python nexus_ps6.py
```

Optional assets next to the script:

```text
nexus_ps5.py
nexus_icon.ico
sounds/ui_click.wav
```

## Configuration

Settings and history:

| Platform | Path |
|----------|------|
| Windows | `%APPDATA%\NexusPS5Utility\` |
| macOS / Linux | `~/NexusPS5Utility/` |

## Local packaging

See [BUILD.md](BUILD.md) for PyInstaller / Nuitka commands on your machine.

## Disclaimer

Use at your own risk. Intended for personal research on hardware you own.
