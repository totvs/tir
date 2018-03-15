@echo off
title CAWebHelper documentation generator
echo -------------------------
echo Installing Sphinx Module...
echo -------------------------
pip install sphinx
echo -------------------------
echo Installing Sphinx HTML Theme...
echo -------------------------
pip install sphinx-rtd-theme
echo -------------------------
echo Cleaning Documentation...
echo -------------------------
docs/make.bat clean
echo -------------------------
echo Creating Documentation...
echo -------------------------
docs/make.bat html
echo ------------------------------------------------------------------------------------
echo Documentation created successfully! Website located at ./docs/build/html/index.html
echo ------------------------------------------------------------------------------------
pause >nul | set/p = Press any key to exit ...