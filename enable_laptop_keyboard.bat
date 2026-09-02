@echo off
title Enable Laptop Built-in Keyboard (Undo)
color 0A

echo.
echo   ================================================
echo     ENABLE LAPTOP BUILT-IN KEYBOARD (Undo)
echo   ================================================
echo.
echo   This will RE-ENABLE the built-in laptop keyboard.
echo   Requires a REBOOT to take effect.
echo   Run as ADMINISTRATOR.
echo.
echo   Press any key to continue, or close to cancel...
pause >nul

echo.
echo   Re-enabling PS/2 keyboard driver (i8042prt)...
sc config i8042prt start= demand

if %errorlevel%==0 (
    echo.
    echo   ================================================
    echo     DONE — Please REBOOT your computer
    echo   ================================================
    echo.
    echo   After reboot, the built-in keyboard will work again.
) else (
    echo.
    echo   [ERROR] Failed. Right-click this bat file and
    echo          select 'Run as administrator'.
)

echo.
pause
