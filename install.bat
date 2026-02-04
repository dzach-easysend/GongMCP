@echo off
REM Simple installation script for Windows

echo Installing Gong MCP Server...
echo.

REM Check if .whl file was provided as argument
if not "%~1"=="" (
    set WHEEL_FILE=%~1
    if not exist "%WHEEL_FILE%" (
        echo Error: File not found: %WHEEL_FILE%
        pause
        exit /b 1
    )
    goto :found
)

REM Try to find the wheel file in common locations
set WHEEL_FILE=

REM Current directory
for %%f in (*.whl) do set WHEEL_FILE=%%f
if not "%WHEEL_FILE%"=="" goto :found

REM Script's directory
cd /d "%~dp0"
for %%f in (*.whl) do set WHEEL_FILE=%%f
if not "%WHEEL_FILE%"=="" goto :found

REM Downloads folder
if exist "%USERPROFILE%\Downloads\*.whl" (
    for %%f in ("%USERPROFILE%\Downloads\*.whl") do set WHEEL_FILE=%%f
    if not "%WHEEL_FILE%"=="" goto :found
)

REM Desktop
if exist "%USERPROFILE%\Desktop\*.whl" (
    for %%f in ("%USERPROFILE%\Desktop\*.whl") do set WHEEL_FILE=%%f
    if not "%WHEEL_FILE%"=="" goto :found
)

echo Error: Could not find the .whl file.
echo.
echo Please either:
echo 1. Put the .whl file in the same folder as this script, or
echo 2. Drag and drop the .whl file onto this script, or
echo 3. Run: install.bat "C:\path\to\gong_mcp-0.1.0-py3-none-any.whl"
echo 4. Or use the manual installation method in INSTALL.md
pause
exit /b 1

:found
echo Found: %WHEEL_FILE%
echo.

REM Try different pip commands
python -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing with python -m pip...
    python -m pip install "%WHEEL_FILE%"
    goto :success
)

python3 -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing with python3 -m pip...
    python3 -m pip install "%WHEEL_FILE%"
    goto :success
)

pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing with pip...
    pip install "%WHEEL_FILE%"
    goto :success
)

pip3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing with pip3...
    pip3 install "%WHEEL_FILE%"
    goto :success
)

echo Error: Could not find Python or pip.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:success
if %errorlevel% equ 0 (
    echo.
    echo Installation complete!
    echo.
    echo Next steps:
    echo 1. Get your API keys from Gong and Anthropic
    echo 2. Add them to Claude Desktop config file
    echo 3. See INSTALL.md for detailed instructions
) else (
    echo.
    echo Installation failed. Please check the error messages above.
)
pause
