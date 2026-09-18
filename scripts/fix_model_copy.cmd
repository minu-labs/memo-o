@echo off
setlocal
set STAGE=%TEMP%\memoo-modelfix
if not exist "%STAGE%" mkdir "%STAGE%"
echo [1/2] source -> local temp
robocopy "\\wsl.localhost\Ubuntu\home\hg623\momo-o\models\small" "%STAGE%" model.bin /J /R:3 /W:2
echo [2/2] local temp -> dist
robocopy "%STAGE%" "\\wsl.localhost\Ubuntu\home\hg623\momo-o\dist\memo-o\models\small" model.bin /J /R:3 /W:2
