@echo off
REM ===== START_DAY.bat 1   (or 2, 3 ...)  opens that day's page. Double-click = it asks. =====
cd /d C:\AskIT\dxc-agentic-ai || (echo [!!] Repo not found at C:\AskIT\dxc-agentic-ai & pause & exit /b 1)
if "%~1"=="" goto ask
set ASKIT_DAY=%~1
goto go
:ask
set /p ASKIT_DAY=Which day? Type 1 or 2 and press Enter: 
:go
echo Opening Day %ASKIT_DAY% ...
echo Getting new content from the trainer...
git fetch -q upstream
git merge -q upstream/main --no-edit
if errorlevel 1 (git merge --abort & echo [!!] Could not update - call the trainer & pause & exit /b 1)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
python tools\portal.py
pause
