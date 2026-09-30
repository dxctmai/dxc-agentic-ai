@echo off
REM ===== ONE-TIME SETUP (run once, in Session 1) =====
setlocal
set UPSTREAM=https://github.com/askanilkumar/dxc-agentic-ai.git
cd /d C:\AskIT\dxc-agentic-ai || (echo [!!] Repo must be at C:\AskIT\dxc-agentic-ai - see setup\SETUP_GUIDE.md & pause & exit /b 1)
echo [1/6] Linking trainer repo (upstream)...
git remote get-url upstream >nul 2>&1 || git remote add upstream %UPSTREAM%
echo [2/6] Creating Python environment (.venv)...
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
echo [3/6] Installing packages...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
echo [4/6] Your identity...
if not exist me.json python tools\setup_me.py
echo [5/6] First push (a GitHub sign-in window may open - sign in)...
git add me.json
git commit -q -m "join: me.json" 2>nul
git push -q origin HEAD
if errorlevel 1 (echo [!!] Push failed - call the trainer) else (echo [OK] Push works)
echo [6/6] Keys: paste the values the trainer shares, SAVE, close Notepad...
if not exist .env copy .env.example .env >nul
notepad .env
python tools\verify_env.py
pause
