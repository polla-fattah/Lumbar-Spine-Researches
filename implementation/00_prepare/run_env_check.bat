@echo off
REM AMOG-Net Automated Environment Setup Launcher for Windows
cd /d "%~dp0"
echo Running AMOG-Net Automated Environment Setup & Verification...
python auto_setup_and_verify.py
pause
