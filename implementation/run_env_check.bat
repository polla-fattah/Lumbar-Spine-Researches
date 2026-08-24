@echo off
REM AMOG-Net Root Windows Launcher
cd /d "%~dp000_prepare"
echo Running AMOG-Net Automated Environment Setup and Verification...
python auto_setup_and_verify.py
pause
