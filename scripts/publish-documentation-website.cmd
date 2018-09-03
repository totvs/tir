@echo off
title TIR documentation publisher
echo -------------------------------------
echo Publishing TIR Documentation Website...
echo -------------------------------------

git checkout .
git checkout master

cd ..
cd doc_files
call make.bat clean
call make.bat html
xcopy /E ".\build\html\*" "..\docs\" /Y

echo -------------------------------------
echo Files created and copied to folder: %cd%
echo Publishing on git...
echo -------------------------------------

cd ..
git add docs/
git commit -m "Publishing documentation %date% %time:~0,5%"
git push


echo -------------------------------------
echo Files published on git successfully.
echo -------------------------------------
pause >nul | set/p = Press any key to exit ...