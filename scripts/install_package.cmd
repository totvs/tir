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
pip install -U dist/tir_framework-1.17.7.tar.gz
=======
pip install -U dist/tir_framework-1.17.10.tar.gz
>>>>>>> 9c4c34fd99155e03ba4041427fe7474e729a7ced
pause >nul | set/p = Press any key to exit ...