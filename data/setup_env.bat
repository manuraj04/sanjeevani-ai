@echo off
REM Sanjeevani Dataset Engineering -- Environment Setup
REM Run this once before starting the pipeline.
REM
REM NOTE: numpy 2.x DLLs are blocked by this machine's Application Control
REM policy. The venv is created on D:\ and numpy is pinned to 1.26.4.

set VENV=D:\sanjeevani_env

echo ============================================================
echo  Sanjeevani Scan AI - Environment Setup
echo ============================================================
echo.

REM Create virtual environment on D:\ (outside AppData restriction)
if not exist "%VENV%\Scripts\python.exe" (
    echo Creating virtual environment at %VENV% ...
    python -m venv "%VENV%"
) else (
    echo Virtual environment already exists at %VENV%
)

echo.
echo Installing Python packages (numpy pinned to 1.26.4) ...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%VENV%\Scripts\pip.exe" install -r requirements.txt

echo.
echo Verifying imports ...
"%VENV%\Scripts\python.exe" -c "import numpy, pandas, PIL, imagehash, matplotlib, sklearn; print('  All packages OK')"
if errorlevel 1 (
    echo.
    echo ERROR: Some packages failed to import. Check the output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup complete!
echo.
echo  IMPORTANT: Always use this Python to run scripts:
echo    %VENV%\Scripts\python.exe scripts\run_pipeline.py
echo.
echo  Or activate the venv first:
echo    %VENV%\Scripts\activate
echo    python scripts/run_pipeline.py
echo.
echo  Next steps:
echo    1. Put your kaggle.json in %%USERPROFILE%%\.kaggle\
echo       (get it from https://www.kaggle.com/account)
echo    2. Download IMPPAT_plants.csv from https://cb.imsc.res.in/imppat/
echo       and place it in metadata/
echo    3. Run the pipeline from sanjeevani_dataset\ folder
echo ============================================================
pause
