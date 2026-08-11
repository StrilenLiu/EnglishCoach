@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
REM ============================================================================
REM   English Coach — Windows 安装脚本 / Windows installer
REM
REM   双击本文件即可运行。
REM   Double-click this file to run it.
REM
REM   它做三件事 / It does three things:
REM     1. 把程序复制到 %LOCALAPPDATA%\Programs\English Coach
REM        Copies the program into your local Programs folder
REM     2. 在「开始」菜单创建快捷方式
REM        Creates a Start Menu shortcut
REM     3. 询问是否在桌面也创建快捷方式
REM        Optionally creates a Desktop shortcut
REM
REM   全程无需管理员权限；卸载请运行同目录的 Uninstall.bat
REM   No administrator rights required. To remove, run Uninstall.bat.
REM ============================================================================

set "APP_NAME=English Coach"
set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

echo ==^> English Coach 安装 / installer
echo.

REM ---- 检查产物完整性 ----
if not exist "%HERE%\%APP_NAME%.exe" (
    echo [X] 在脚本所在目录找不到 "%APP_NAME%.exe"
    echo     请确认本脚本与程序放在同一目录（解压后的目录内）。
    echo.
    echo     Could not find "%APP_NAME%.exe" next to this script.
    pause
    exit /b 1
)
if not exist "%HERE%\_internal" (
    echo [X] 找不到 _internal 目录 —— 它包含全部依赖库，必须与 exe 同在。
    echo     请重新完整解压压缩包，不要只复制单个文件。
    echo.
    echo     The _internal folder is missing. Extract the full archive again.
    pause
    exit /b 1
)

set "TARGET=%LOCALAPPDATA%\Programs\%APP_NAME%"
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

echo     目标 / target: %TARGET%
echo.

REM ---- 若已安装则先移除 ----
if exist "%TARGET%" (
    echo ==^> [1/3] 移除旧版本
    rmdir /s /q "%TARGET%" 2>nul
    if exist "%TARGET%" (
        echo [X] 无法移除旧版本，请先关闭正在运行的 English Coach 再试。
        echo     Could not remove the previous version. Close English Coach and retry.
        pause
        exit /b 1
    )
) else (
    echo ==^> [1/3] 准备安装目录
)

mkdir "%TARGET%" 2>nul

REM ---- 复制文件（排除安装脚本自身）----
echo ==^> [2/3] 复制程序文件（文件较多，请稍候）
robocopy "%HERE%" "%TARGET%" /E /NFL /NDL /NJH /NJS /NP ^
    /XF "Install.bat" "Uninstall.bat" "Install.sh" "Uninstall.sh" ^
        "Install.command" "Uninstall.command" >nul
if %ERRORLEVEL% GEQ 8 (
    echo [X] 复制失败（robocopy 返回 %ERRORLEVEL%）
    pause
    exit /b 1
)

REM 把卸载脚本放进安装目录，方便日后卸载
if exist "%HERE%\Uninstall.bat" copy /y "%HERE%\Uninstall.bat" "%TARGET%\Uninstall.bat" >nul

REM ---- 创建快捷方式 ----
echo ==^> [3/3] 创建快捷方式

REM 图标：优先用目录内的 .ico，没有则用 exe 自带图标
set "ICON=%TARGET%\%APP_NAME%.exe,0"
if exist "%TARGET%\icon_win_1024.ico" set "ICON=%TARGET%\icon_win_1024.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$W = New-Object -ComObject WScript.Shell;" ^
  "$s = $W.CreateShortcut('%STARTMENU%\%APP_NAME%.lnk');" ^
  "$s.TargetPath = '%TARGET%\%APP_NAME%.exe';" ^
  "$s.WorkingDirectory = '%TARGET%';" ^
  "$s.IconLocation = '%ICON%';" ^
  "$s.Description = 'Chinese-English translation, speech and karaoke subtitles';" ^
  "$s.Save()" 2>nul

if exist "%STARTMENU%\%APP_NAME%.lnk" (
    echo     已创建「开始」菜单快捷方式
) else (
    echo     ! 「开始」菜单快捷方式创建失败，可手动创建
)

echo.
set /p MKDESK="是否在桌面创建快捷方式？Create a Desktop shortcut? (y/N) "
if /i "!MKDESK!"=="y" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$W = New-Object -ComObject WScript.Shell;" ^
      "$d = $W.SpecialFolders('Desktop');" ^
      "$s = $W.CreateShortcut((Join-Path $d '%APP_NAME%.lnk'));" ^
      "$s.TargetPath = '%TARGET%\%APP_NAME%.exe';" ^
      "$s.WorkingDirectory = '%TARGET%';" ^
      "$s.IconLocation = '%ICON%';" ^
      "$s.Save()" 2>nul
    echo     已创建桌面快捷方式
)

echo.
echo [OK] 安装完成 / Installation complete
echo.
echo   启动方式 / How to launch:
echo     · 在「开始」菜单搜索 English Coach
echo       Search for English Coach in the Start Menu
echo     · 或运行 / or run:
echo         "%TARGET%\%APP_NAME%.exe"
echo.
echo   卸载 / To uninstall:
echo     运行 "%TARGET%\Uninstall.bat"
echo.
echo   首次启动若被 SmartScreen 拦截，点「更多信息」→「仍要运行」。
echo   If SmartScreen blocks the first launch, click More info then Run anyway.
echo.
pause
endlocal
