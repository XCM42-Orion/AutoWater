@echo off
setlocal EnableDelayedExpansion
echo AutoWater启动中
if not exist napcat_dir.txt (
	fsutil file createNew napcat_dir.txt 0
)
set napcat_dir = <napcat_dir.txt
:check_dir
if exist "%napcat_dir%/napcat.bat" (
	set batpath = %~dp0
	cd %napcat_dir%
	start napcat.bat
	echo 等待napcat启动中
	timeout /t 10 >nul
	cd %batpath%
	python autowater.py
) else (
	set /p napcat_dir=请输入napcat.bat所在的目录，如C:\Users\NapCat.Shell.Windows.OneKey\NapCat.41785.Shell:
	echo %napcat_dir% > napcat_dir.txt
	goto check_dir
)
pause