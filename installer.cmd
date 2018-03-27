@echo off
title CAWebHelper installer
echo -------------------------
echo Building project...
echo -------------------------
python setup.py build
echo -------------------------
echo Terminating possible open driver instances
echo -------------------------
taskkill /f /im geckodriver.exe
taskkill /f /im chromedriver.exe
echo -------------------------
echo Installing project...
echo -------------------------
python setup.py install
pause >nul | set/p = Press any key to exit ...