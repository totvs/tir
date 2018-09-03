@echo off
title TIR documentation publisher
echo -------------------------------------
echo Publishing TIR Documentation Website...
echo -------------------------------------

cd ..
cd doc_files
xcopy /E ".\build\html\*" "..\docs\"

echo -------------------------------------
echo Files copied to folder: %cd%
echo Publishing on git...
echo -------------------------------------

git

