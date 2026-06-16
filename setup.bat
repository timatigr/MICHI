@echo off
cd /d "%~dp0"
echo === MICHI: подготовка окружения ===
echo.

REM Ищем Python: сначала лаунчер py, затем python из PATH
set "PYEXE="
py -3 --version >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE (
  python --version >nul 2>nul && set "PYEXE=python"
)
if not defined PYEXE (
  echo [!] Python не найден.
  echo     Установите Python 3.10+ с https://www.python.org/downloads/
  echo     и при установке отметьте "Add Python to PATH", затем запустите setup.bat снова.
  pause
  exit /b 1
)

echo Создаю виртуальное окружение .venv ...
%PYEXE% -m venv .venv
if errorlevel 1 ( echo [!] Не удалось создать .venv & pause & exit /b 1 )

echo Устанавливаю зависимости (это займёт пару минут) ...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 ( echo [!] Установка зависимостей не удалась & pause & exit /b 1 )

echo.
echo === Готово! Теперь запускайте run.bat ===
pause
