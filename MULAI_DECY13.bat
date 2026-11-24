@echo off
title DECY-13 - Konfigurasi Awal & Pusat Kendali Siklotron
cd /d "%~dp0"
echo ============================================================================
echo   MEMUAT PROGRAM KONFIGURASI AWAL SIKLOTRON DECY-13 (MINI PC RUANG KONTROL)
echo ============================================================================
python tools\decy13_startup_wizard.py %*
if errorlevel 1 (
    echo.
    echo [!] Terjadi kendala saat menjalankan Python. Pastikan Python 3 terpasang di PATH.
    pause
)
