@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
REM ============================================================================
REM   English Coach — Windows 卸载脚本 / Windows uninstaller
REM
REM   双击本文件即可运行。
REM   Double-click this file to run it.
REM
REM   默认只删除程序与快捷方式，保留个人数据（翻译历史、设置与 API Key）。
REM   运行时会询问是否一并删除。
REM   By default only the program and its shortcuts are removed; your history,
REM   settings and API keys are kept. You will be asked about those separately.
REM ============================================================================

set "APP_NAME=English Coach"
set "TARGET=%LOCALAPPDATA%\Programs\%APP_NAME%"
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

echo ==^> English Coach 卸载 / uninstaller
echo.

if not exist "%TARGET%" (
    echo   未找到已安装的 English Coach：
    echo     %TARGET%
    echo   Nothing to remove at the location above.
    echo.
    pause
    exit /b 0
)

echo   程序目录 / program: %TARGET%
echo.
set /p CONFIRM="确认卸载？Confirm uninstall? (y/N) "
if /i not "!CONFIRM!"=="y" (
    echo 已取消。
    pause
    exit /b 0
)

REM ---- 若程序在运行则先提示 ----
tasklist /fi "imagename eq %APP_NAME%.exe" 2>nul | find /i "%APP_NAME%.exe" >nul
if not errorlevel 1 (
    echo.
    echo   [!] English Coach 正在运行，请先关闭它再继续。
    echo       English Coach is running. Please close it first.
    pause
    exit /b 1
)

REM ---- 删除快捷方式 ----
echo ==^> 移除快捷方式
if exist "%STARTMENU%\%APP_NAME%.lnk" del /f /q "%STARTMENU%\%APP_NAME%.lnk"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d = (New-Object -ComObject WScript.Shell).SpecialFolders('Desktop');" ^
  "$p = Join-Path $d '%APP_NAME%.lnk';" ^
  "if (Test-Path $p) { Remove-Item $p -Force }" 2>nul
echo     已移除

REM ---- 删除程序目录 ----
REM 卸载脚本自身就在该目录内，先复制到临时目录再由它删除父目录
echo ==^> 移除程序文件
set "TMPBAT=%TEMP%\ec_uninstall_%RANDOM%.bat"
> "%TMPBAT%" echo @echo off
>> "%TMPBAT%" echo timeout /t 1 /nobreak ^>nul
>> "%TMPBAT%" echo rmdir /s /q "%TARGET%"
>> "%TMPBAT%" echo if exist "%TARGET%" (
>> "%TMPBAT%" echo     echo [X] 部分文件未能删除，请手动移除： %TARGET%
>> "%TMPBAT%" echo ^) else (
>> "%TMPBAT%" echo     echo [OK] 程序文件已移除
>> "%TMPBAT%" echo ^)
>> "%TMPBAT%" echo echo.

REM ---- 个人数据 ----
set "DATA=%APPDATA%\EnglishCoach"
set "HASDATA=0"
if exist "%DATA%" set "HASDATA=1"

if "!HASDATA!"=="1" (
    echo.
    echo   以下为个人数据 / Personal data:
    echo     %DATA%   （翻译历史、运行日志）
    echo     注册表 HKCU\Software\Strilen\EnglishCoach   （设置与 API Key）
    echo.
    set /p PURGE="是否一并删除？删除后无法恢复 (y/N) "
    if /i "!PURGE!"=="y" (
        >> "%TMPBAT%" echo rmdir /s /q "%DATA%" 2^>nul
        >> "%TMPBAT%" echo reg delete "HKCU\Software\Strilen\EnglishCoach" /f ^>nul 2^>^&1
        >> "%TMPBAT%" echo echo [OK] 个人数据已删除
    ) else (
        >> "%TMPBAT%" echo echo     个人数据已保留： %DATA%
    )
) else (
    >> "%TMPBAT%" echo reg delete "HKCU\Software\Strilen\EnglishCoach" /f ^>nul 2^>^&1
)

>> "%TMPBAT%" echo echo.
>> "%TMPBAT%" echo echo [OK] 卸载完成 / Uninstalled
>> "%TMPBAT%" echo echo.
>> "%TMPBAT%" echo pause
>> "%TMPBAT%" echo del /f /q "%%~f0"

echo.
echo   即将完成卸载，本窗口会关闭并弹出新窗口显示结果。
echo   A new window will open to finish the removal.
echo.
timeout /t 2 /nobreak >nul
start "" cmd /c "%TMPBAT%"
endlocal
exit /b 0
