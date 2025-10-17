@echo off
echo Stopping all Python processes...
taskkill /f /im python.exe 2>nul

echo.
echo Waiting for processes to stop...
timeout /t 3 /nobreak >nul

echo.
echo Starting admin panel...
start "Admin Panel" /min python run_admin.py

echo.
echo Waiting for admin panel to start...
timeout /t 5 /nobreak >nul

echo.
echo Starting main bot...
start "Main Bot" /min python -m guide_ai_bot.main

echo.
echo Waiting for main bot to start...
timeout /t 5 /nobreak >nul

echo.
echo Starting web server (if needed)...
start "Web Server" /min python run_web.py

echo.
echo All components restarted successfully!
echo Admin Panel: http://127.0.0.1:5000/admin
echo Bot is running...

timeout /t 3 /nobreak >nul