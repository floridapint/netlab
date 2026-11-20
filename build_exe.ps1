# Build NetLab into a standalone Windows app: dist\NetLab\NetLab.exe
$ErrorActionPreference = "Stop"
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --windowed --name NetLab main.py
Write-Host "Done: dist\NetLab\NetLab.exe"
