@echo off
title Environment Setup
if defined ChocolateyInstall (goto install-packages) ELSE (goto install-choco)

:install-choco
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
goto install-packages

:install-packages
set /P py="Install/Update Python[Y/N]? "
set /P ff="Install/Update Firefox[Y/N]? "
set /P vsc="Install/Update Visual Studio Code[Y/N]? "
set /P gi="Install/Update Git[Y/N]? "

if /I "%py%" EQU "Y" choco upgrade python --version 3.6.5 -y
if /I "%ff%" EQU "Y" choco upgrade firefox -y
if /I "%vsc%" EQU "Y" choco upgrade vscode -y
if /I "%gi%" EQU "Y" choco upgrade git -y
