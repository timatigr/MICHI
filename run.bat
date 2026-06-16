@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [!] Окружение не найдено. Сначала запустите setup.bat
  pause
  exit /b 1
)

REM Откроем браузер, когда сервер успеет подняться (uvicorn ниже занимает это окно)
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 3; Start-Process 'http://127.0.0.1:8000'"

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
