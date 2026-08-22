@echo off
echo ========================================
echo  Building PDF Converter .exe
echo ========================================
echo.

pip install -r requirements.txt

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "PDF Converter" ^
  --collect-all customtkinter ^
  --collect-all pymupdf ^
  --hidden-import=PIL ^
  --hidden-import=filetype ^
  app.py

echo.
echo ========================================
echo  Done! ไฟล์ .exe อยู่ใน dist/
echo ========================================
pause
