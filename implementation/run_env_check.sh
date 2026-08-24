#!/usr/bin/env bash
# AMOG-Net Root Linux/macOS Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/00_prepare"
echo "Running AMOG-Net Automated Environment Setup and Verification..."
python3 auto_setup_and_verify.py
