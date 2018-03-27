@echo off
title CAWebHelper installer
echo -------------------------
echo Building project...
echo -------------------------
python setup.py sdist
echo -------------------------
echo Terminating possible open driver instances
echo -------------------------
taskkill /f /im geckodriver.exe
taskkill /f /im chromedriver.exe
echo -------------------------
echo Installing project...
echo -------------------------
pip install -U dist/cawebhelper-0.1.tar.gz
pause >nul | set/p = Press any key to exit ...