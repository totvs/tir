@echo off
title TIR installer
echo -------------------------
cd ..
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
<<<<<<< HEAD
pip install -U dist/tir-1.9.1.tar.gz
=======
pip install -U dist/tir-1.9.0.tar.gz
>>>>>>> master
pause >nul | set/p = Press any key to exit ...