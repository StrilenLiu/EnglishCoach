@echo off
REM ===========================================================================
REM  EnglishCoach - Windows build script (v1.9.1)
REM  Output: dist\EnglishCoach\EnglishCoach.exe  and  EnglishCoach-1.0.7-windows.zip
REM  Bundles Argos en<->zh offline models.
REM  ASCII-only for GBK consoles.
REM ===========================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

set APP_NAME=English Coach
set VERSION=2.5.1
set MAIN=english_coach.py
set CONDA_ENV=EnglishCoach
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
    echo     Retry: pip install "sentencepiece==0.2.0" "ctranslate2==4.3.1" --only-binary :all:
    goto :end
)
echo     offline deps OK

echo ==^> Kokoro offline TTS deps + model
REM Kokoro deps. transformers 4.40.2 keeps compatibility with torch 2.2.x.
REM On Windows torch wheels exist for all versions; pin transformers for safety.
call :pipinstall "transformers==4.40.2"
call :pipinstall kokoro soundfile
call :pipinstall lameenc
REM File import/export + history multi-format download deps
call :pipinstall python-docx pypdf pdfplumber reportlab num2words
REM Kokoro/misaki transitive deps that are sometimes missing (e.g. ordered_set)
call :pipinstall ordered_set addict regex pydantic loguru
REM Chinese G2P deps (Kokoro Chinese needs pypinyin/jieba/cn2an)
call :pipinstall pypinyin jieba cn2an "misaki[zh]"
if errorlevel 1 call :pipinstall pypinyin jieba cn2an
REM misaki English G2P needs spaCy English model; preinstall to avoid runtime download
python -m pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" || call :pipinstall en_core_web_sm || echo   [!] en_core_web_sm preinstall failed; first offline EN read will download it
python -c "import torch,transformers,kokoro;print('Kokoro deps OK, torch',torch.__version__,'transformers',transformers.__version__)" || echo   [!] Kokoro dependency check failed
echo     Pre-download Kokoro model (~330MB, first time slow)...
python -c "import os;from huggingface_hub import snapshot_download;t=os.path.expanduser('~/EnglishCoach Models/Kokoro');os.makedirs(t,exist_ok=True);snapshot_download(repo_id='hexgrad/Kokoro-82M',local_dir=t);print('Kokoro model ready:',t)" || echo   [!] Kokoro model predownload failed; offline EN voices unavailable without network

echo ==^> [3/7] Prepare Argos en/zh offline models (cache subdir: argos)
if not exist argos_models mkdir argos_models
call :getmodel en_zh.argosmodel "https://argos-net.com/v1/translate-en_zh-1_9.argosmodel"
call :getmodel zh_en.argosmodel "https://argos-net.com/v1/translate-zh_en-1_9.argosmodel"

echo ==^> [4/7] Generate icon
if exist make_icon.py python make_icon.py
set ICON_ARG=
set DATA_ARG=--add-data icon_1024.png;.
if exist icon_1024.png (
    python -c "from PIL import Image; src='icon_win_1024.png' if __import__('os').path.exists('icon_win_1024.png') else 'icon_1024.png'; Image.open(src).save('AppIcon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
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
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

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
set OUT=%APP_NAME%-%VERSION%-windows.zip
if exist "%OUT%" del /q "%OUT%"
REM Zip the whole app folder (so the zip contains "English Coach\English Coach.exe")
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%APP_NAME%' -DestinationPath '%OUT%' -Force"

echo.
echo ================================================================
echo   Done.
echo   EXE : dist\%APP_NAME%\%APP_NAME%.exe
echo   Zip : %OUT%
echo ================================================================
echo.
echo If it fails to start, run the exe from a console to see the error:
echo     dist\%APP_NAME%\%APP_NAME%.exe
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

:end
endlocal
pause
