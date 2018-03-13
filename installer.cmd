@echo off
title CAWebHelper installer
echo -------------------------
echo Building project...
echo -------------------------
python setup.py build
echo -------------------------
echo Installing project...
echo -------------------------
python setup.py install
echo -------------------------
echo Module installed successfully!
echo -------------------------
pause >nul | set/p = Press any key to exit ...