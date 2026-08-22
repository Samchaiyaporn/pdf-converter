@echo off
echo Starting PDF Converter...
pip install -r requirements.txt >nul 2>&1
python app.py
