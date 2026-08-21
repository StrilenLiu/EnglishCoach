@echo off
REM ===========================================================================
REM  EnglishCoach - Windows build script (v1.9.1)
REM  Output: dist\Windows-x64-GPU\English Coach\English Coach.exe
REM          and  dist\Windows-x64-GPU\EnglishCoach-<ver>-Windows-x64-GPU.zip
REM  Bundles Argos en<->zh offline models.
REM  ASCII-only for GBK consoles.
REM ===========================================================================

chcp 65001 >nul
setlocal enabledelayedexpansion

set APP_NAME=English Coach GPU

REM ==========================================================================
REM  产物完整性拦截 / Build integrity gate
REM  任何会让产物功能残缺的问题都必须阻断编译。
REM  设 STRICT=0 可强行忽略：  set STRICT=0 ^&^& "Build Windows GPU.bat"
REM ==========================================================================
if not defined STRICT set STRICT=1
set "BUILD_PROBLEMS="
set "PROBLEM_COUNT=0"
rem Auto-extract version from english_coach.py (single source of truth)
for /f tokens^=2^ delims^=^" %%A in ('findstr /b /c:"APP_VERSION" english_coach.py') do set "VERSION=%%A"
if not defined VERSION set VERSION=0.0.0
set MAIN=english_coach.py
set CONDA_ENV=EnglishCoach-GPU
set PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
set PIP_FALLBACK=https://pypi.org/simple

echo ==^> [1/7] Activate conda env: %CONDA_ENV%
where conda >nul 2>nul
if errorlevel 1 (
    echo [X] conda not found. Install Anaconda/Miniconda and add to PATH.
    goto :end
)
call conda activate %CONDA_ENV%
if errorlevel 1 (
    echo [X] Cannot activate env "%CONDA_ENV%". Create it first:
    echo     conda create -n %CONDA_ENV% python=3.12 -y
    goto :end
)
REM Confirm we are really in the target env (avoid installing into base)
echo     ----------------------------------------
echo     Current conda env: %CONDA_DEFAULT_ENV%
python --version
echo     ----------------------------------------
if not "%CONDA_DEFAULT_ENV%"=="%CONDA_ENV%" (
    echo [X] Not in %CONDA_ENV% env ^(actual: %CONDA_DEFAULT_ENV%^). Aborting to avoid wrong env.
    goto :end
)

echo ==^> [2/7] Install dependencies ^(Tsinghua mirror, fallback to PyPI^)
python -m pip install --upgrade pip -i %PIP_MIRROR%
call :pipinstall PyQt6 edge-tts requests pyinstaller pillow
REM --- Argos offline translation: pinned, torch-free combo ---
REM ctranslate2 4.3.1 needs pkg_resources (removed in setuptools 81+),
REM so pin setuptools<81 first to keep pkg_resources available.
call :pipinstall "setuptools<81"
call :pipinstall "numpy<2"
call :pipinstall "sentencepiece==0.2.0"
call :pipinstall "ctranslate2==4.3.1"
python -m pip install "argostranslate==1.9.6" --no-deps -i %PIP_MIRROR%
if errorlevel 1 python -m pip install "argostranslate==1.9.6" --no-deps -i %PIP_FALLBACK%
call :pipinstall sacremoses
echo     Verify ctranslate2 + sentencepiece ...
python -c "import ctranslate2, sentencepiece" 2>nul
if errorlevel 1 (
    echo [X] ctranslate2 / sentencepiece import failed.
    echo     Try: pip install "setuptools^<81" then re-run.
    goto :end
)
echo     offline deps OK

echo ==^> Kokoro offline TTS deps + model (GPU / CUDA build)
REM ============================================================
REM  GPU build dependency set (verified on RTX 4090 Laptop,
REM  driver 610.47 / CUDA 13.3):
REM    PyTorch 2.9.1 + cu128 (CUDA 12.8 wheel, backward compatible)
REM    transformers 4.44-4.48 (GPU uses new version, no downgrade)
REM  If GPU/driver is very old, change cu128 to cu126; very new try cu130.
REM ============================================================
echo     Installing CUDA PyTorch 2.9.1 (cu128) ...
python -m pip install torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 echo   [!] CUDA torch install failed; check nvidia-smi / driver
call :pipinstall "transformers>=4.44,<4.49"
call :pipinstall kokoro soundfile
call :pipinstall lameenc
REM File import/export + history multi-format download deps
call :pipinstall python-docx pypdf pdfplumber reportlab num2words
call :pipinstall ordered_set addict regex pydantic loguru
call :pipinstall pypinyin jieba cn2an "misaki[zh]"
if errorlevel 1 call :pipinstall pypinyin jieba cn2an
rem en_core_web_sm is NOT on PyPI (spaCy models ship via GitHub Releases); mirrors
rem return a 0-byte placeholder that triggers a "Wheel is invalid" error. Check first:
rem skip if already installed (no noisy error), else install from the official GitHub wheel.
python -c "import en_core_web_sm" >nul 2>&1
if errorlevel 1 (
  python -m pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" || call :pipinstall en_core_web_sm || echo   [!] en_core_web_sm preinstall failed
) else (
  echo   [OK] en_core_web_sm already installed, skipping
)
REM Verify CUDA available (False = driver/version mismatch, will fall back to CPU)
python -c "import torch;print('torch',torch.__version__,'| CUDA available:',torch.cuda.is_available(),'|',(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'))"
python -c "import torch,transformers,kokoro;print('Kokoro deps OK, transformers',transformers.__version__)" || call :problem "Kokoro dependency chain check failed" "Offline speech synthesis will not work"
echo     Pre-download Kokoro model (~330MB, first time slow)...
python -c "import os;from huggingface_hub import snapshot_download;t=os.path.expanduser('~/EnglishCoach Models/Kokoro');os.makedirs(t,exist_ok=True);snapshot_download(repo_id='hexgrad/Kokoro-82M',local_dir=t);print('Kokoro model ready:',t)" || echo   [!] Kokoro model predownload failed

echo ==^> [3/7] Prepare Argos en/zh offline models (cache subdir: argos)
if not exist argos_models mkdir argos_models
call :getmodel en_zh.argosmodel "https://argos-net.com/v1/translate-en_zh-1_9.argosmodel"
call :getmodel zh_en.argosmodel "https://argos-net.com/v1/translate-zh_en-1_9.argosmodel"

echo ==^> [4/7] Generate icon
if exist make_icon.py python make_icon.py
set ICON_ARG=
set DATA_ARG=--add-data icon_1024.png;.
if exist icon_1024.png (
    python -c "from PIL import Image; import os; src=('icon_gpu_win_1024.png' if os.path.exists('icon_gpu_win_1024.png') else ('icon_win_1024.png' if os.path.exists('icon_win_1024.png') else 'icon_1024.png')); Image.open(src).save('AppIcon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
    if exist AppIcon.ico set ICON_ARG=--icon AppIcon.ico
)
set MODEL_ARG=
if exist argos_models set MODEL_ARG=--add-data argos_models;argos_models
set KOKORO_DATA=
if exist "%USERPROFILE%\EnglishCoach Models\Kokoro" (
    REM Path has a space; stage to a no-space dir so --add-data parses correctly
    if exist _kokoro_stage rmdir /s /q _kokoro_stage
    mkdir _kokoro_stage
    xcopy "%USERPROFILE%\EnglishCoach Models\Kokoro" _kokoro_stage\ /E /I /Q >nul
    set KOKORO_DATA=--add-data _kokoro_stage;kokoro_model
)

echo ==^> [5/7] Clean old build
set DESTDIR=dist\Windows-x64-GPU
if exist build rmdir /s /q build
rem Clean only this platform's own output folder, keep other platforms' artifacts
if exist "%DESTDIR%" rmdir /s /q "%DESTDIR%"
if not exist dist mkdir dist
mkdir "%DESTDIR%"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

REM 编译前结算：功能性缺失在此拦截
call :gate
if errorlevel 1 goto :end

echo ==^> [6/7] PyInstaller build
python -m PyInstaller ^
    --name "%APP_NAME%" ^
    --windowed ^
    --noconfirm ^
    --clean ^
    %ICON_ARG% ^
    %DATA_ARG% ^
    %MODEL_ARG% ^
    %KOKORO_DATA% ^
    --collect-all argostranslate ^
    --collect-all ctranslate2 ^
    --collect-all sentencepiece ^
    --collect-all kokoro ^
    --collect-all misaki ^
    --collect-all language_tags ^
    --collect-all espeakng_loader ^
    --collect-all num2words ^
    --collect-all en_core_web_sm ^
    --collect-all transformers ^
    --collect-submodules lameenc ^
    --hidden-import ordered_set ^
    --hidden-import addict ^
    --hidden-import pypinyin ^
    --collect-all jieba ^
    --hidden-import cn2an ^
    --collect-all docx ^
    --collect-all pdfplumber ^
    --collect-all reportlab ^
    --hidden-import num2words ^
    --hidden-import pypdf ^
    --copy-metadata kokoro ^
    --copy-metadata misaki ^
    %MAIN%
if errorlevel 1 (
    echo [X] PyInstaller build failed.
    goto :end
)

echo ==^> [7/7] Package zip
set OUT=%DESTDIR%\EnglishCoach-%VERSION%-Windows-x64-GPU.zip
if exist "%OUT%" del /q "%OUT%"
rem Move the PyInstaller output into this platform's folder, keep dist root clean
if exist "dist\%APP_NAME%" move /y "dist\%APP_NAME%" "%DESTDIR%" >nul
REM ---- 产物实物校验 ----
echo     Verifying build output ...
if not exist "%DESTDIR%\%APP_NAME%\%APP_NAME%.exe" (
    call :problem "Executable missing from the build" "The program cannot start at all"
)
if not exist "%DESTDIR%\%APP_NAME%\_internal" (
    call :problem "_internal folder missing from the build" "All bundled libraries are absent"
)
set "ARGOS_N=0"
for /r "%DESTDIR%\%APP_NAME%" %%F in (*.argosmodel) do (
    if %%~zF GTR 30000000 set /a ARGOS_N+=1
)
if %ARGOS_N% LSS 2 (
    call :problem "Argos offline translation models incomplete in the build" "Offline translation will not work for users"
) else (
    echo       OK - Argos models: %ARGOS_N%
)
set "KOK_N=0"
for /r "%DESTDIR%\%APP_NAME%" %%F in (*.pth *.safetensors *.onnx) do (
    if %%~zF GTR 10000000 set /a KOK_N+=1
)
if %KOK_N% LSS 1 (
    call :problem "No Kokoro model weights in the build" "Offline speech needs a network download on first use"
) else (
    echo       OK - Kokoro weights: %KOK_N%
)

call :gate
if errorlevel 1 goto :end

REM --- 随产物附带安装/卸载脚本（必须在打包成 zip 之前放进去）---
for %%S in (Install.bat Uninstall.bat) do (
    if exist "%%S" (
        copy /y "%%S" "%DESTDIR%\%APP_NAME%\%%S" >nul
        echo     already bundled %%S
    ) else (
        echo     [!] %%S not found - installer will be missing from the build
    )
)

powershell -NoProfile -Command "Compress-Archive -Path '%DESTDIR%\%APP_NAME%' -DestinationPath '%OUT%' -Force"

echo.
echo ================================================================
echo   Done.
echo   EXE : %DESTDIR%\%APP_NAME%\%APP_NAME%.exe
echo   Zip : %OUT%
echo ================================================================
echo.
echo If it fails to start, run the exe from a console to see the error:
echo     %DESTDIR%\%APP_NAME%\%APP_NAME%.exe
echo.
echo Translation/TTS need internet ^(Argos works offline after bundle^).
goto :end

:pipinstall
python -m pip install %* -i %PIP_MIRROR%
if errorlevel 1 python -m pip install %* -i %PIP_FALLBACK%
exit /b 0

:getmodel
REM %1 = filename, %2 = url. Reuse from shared repo before downloading.
REM Repo search order: %ENGLISHCOACH_MODELS%, ...\EnglishCoach Models\Argos, ...\EnglishCoach Models, ..\_models
set "FN=%~1"
set "URL=%~2"
set "DST=argos_models\%FN%"
set "ARGOS_CACHE=%USERPROFILE%\EnglishCoach Models\Argos"
REM already present and big enough?
call :isbig "%DST%" && ( echo   already present %DST% & exit /b 0 )
for %%R in ("%ENGLISHCOACH_MODELS%" "%ARGOS_CACHE%" "%USERPROFILE%\EnglishCoach Models" "..\_models") do (
    if not "%%~R"=="" if exist "%%~R\%FN%" (
        call :isbig "%%~R\%FN%" && (
            copy /Y "%%~R\%FN%" "%DST%" >nul
            echo   reused from %%~R\%FN%
            exit /b 0
        )
    )
)
echo   downloading %FN% ...
curl --http1.1 -L --retry 10 --retry-delay 5 -C - -o "%DST%" "%URL%"
REM cache a copy to the argos subdir for future reuse
call :isbig "%DST%" && (
    if not exist "%ARGOS_CACHE%" mkdir "%ARGOS_CACHE%"
    copy /Y "%DST%" "%ARGOS_CACHE%\%FN%" >nul
    echo   cached to %ARGOS_CACHE%\%FN%
)
exit /b 0

:isbig
REM succeed (errorlevel 0) if file exists and > 40MB
if not exist "%~1" exit /b 1
for %%A in ("%~1") do if %%~zA GTR 40000000 (exit /b 0)
exit /b 1

:problem
set /a PROBLEM_COUNT+=1
echo   [X] %~1
echo       Impact: %~2
set "BUILD_PROBLEMS=1"
exit /b 0

:gate
if not defined BUILD_PROBLEMS exit /b 0
echo.
echo ============================================================
echo   BUILD BLOCKED - the output would be functionally incomplete
echo   编译被拦截：产物将存在功能缺失（共 %PROBLEM_COUNT% 项，见上方 [X] 行）
echo ============================================================
echo.
if "%STRICT%"=="1" (
    echo   已中止，未产出安装包。修复上述问题后重新编译即可。
    echo   Aborted; no package was produced. Fix the issues above and rebuild.
    echo.
    echo       set STRICT=0 ^&^& "Build Windows GPU.bat"
    echo.
    exit /b 1
)
echo   STRICT=0: 已知问题被忽略，继续编译（产物功能不完整）。
echo.
set "BUILD_PROBLEMS="
exit /b 0

:end
endlocal
pause
