@echo off
title Disable Laptop Built-in Keyboard
color 0C

echo.
echo   ================================================
echo     DISABLE LAPTOP BUILT-IN KEYBOARD
echo   ================================================
echo.
echo   This will DISABLE the built-in laptop keyboard.
echo   External USB keyboards will STILL WORK.
echo   Touchpad will NOT be affected (it uses HID, not PS/2).
echo.
echo   Requires a REBOOT to take effect.
echo   Run as ADMINISTRATOR.
echo.
echo   To undo: run enable_laptop_keyboard.bat
echo.
echo   Press any key to continue, or close to cancel...
pause >nul

echo.
echo   Disabling PS/2 keyboard driver (i8042prt)...
sc config i8042prt start= disabled

if %errorlevel%==0 (
    echo.
    echo   ================================================
    echo     DONE — Please REBOOT your computer
    echo   ================================================
    echo.
    echo   After reboot:
    echo   - Built-in laptop keyboard: DISABLED
    echo   - External USB keyboard: WORKS
    echo   - Touchpad: WORKS (not affected)
    echo.
    echo   To re-enable: run enable_laptop_keyboard.bat + reboot
) else (
    echo.
    echo   [ERROR] Failed. Right-click this bat file and
    echo          select 'Run as administrator'.
)

echo.
pause
