@echo off
cd /d "%~dp0"
REM Режим разработки: автоперезагрузка при правках кода, без авто-открытия браузера.
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
