@echo off
echo.
echo  FinanceAI - Starting...
echo.

echo [1/2] Starting Backend...
start cmd /k "cd /d C:\Users\joels\Desktop\Joel\Projects\Finance_AI && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo Waiting for backend to start...
timeout /t 4 /nobreak >nul

echo [2/2] Starting Frontend...
start cmd /k "cd /d C:\Users\joels\Desktop\Joel\Projects\Finance_AI\frontend && npm run dev"

echo Waiting for frontend to start...
timeout /t 4 /nobreak >nul

echo.
echo  Both servers are starting!
echo.
echo  Frontend : http://localhost:5173
echo  Backend  : http://127.0.0.1:8000
echo  API Docs : http://127.0.0.1:8000/docs
echo.
start http://localhost:5173
pause