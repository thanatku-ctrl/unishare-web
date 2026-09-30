@echo off
title UniShare - ระบบเช่า-ยืม-ซื้อ (Flask + SQLite)
echo ================================================================
echo   UniShare - Student Sharing Platform
echo   Starting Flask Web Server with SQLite Database (unishare.db)...
echo ================================================================
echo.
echo   Server is running on: http://localhost:5000
echo   Database file: unishare.db
echo.
start http://localhost:5000
python app.py
pause
