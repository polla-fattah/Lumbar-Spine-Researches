#!/usr/bin/env bash
# AMOG-Net Automated Environment Setup Launcher for Linux/macOS
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
echo "Running AMOG-Net Automated Environment Setup and Verification..."
python3 auto_setup_and_verify.py
