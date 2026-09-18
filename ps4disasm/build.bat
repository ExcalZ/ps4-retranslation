@ECHO OFF

REM // make sure we can write to the file ps4built.bin
REM // also make a backup to ps4built.prev.bin
IF NOT EXIST ps4built.bin goto LABLNOCOPY
IF EXIST ps4built.prev.bin del ps4built.prev.bin
IF EXIST ps4built.prev.bin goto LABLNOCOPY
move /Y ps4built.bin ps4built.prev.bin
IF EXIST ps4built.bin goto LABLERROR3
:LABLNOCOPY

REM // delete some intermediate assembler output just in case
IF EXIST ps4.p del ps4.p
IF EXIST ps4.p goto LABLERROR2
IF EXIST ps4.h del ps4.h
IF EXIST ps4.h goto LABLERROR1

REM // clear the output window
REM cls

REM // run the assembler
REM // -xx shows the most detailed error output
REM // -E creates log file for errors/warnings
REM // -A gives us a small speedup
set AS_MSGPATH=AS/win32
set USEANSI=n

REM // allow the user to choose to output error messages to file by supplying the -logerrors parameter
IF "%1"=="-logerrors" ( "AS/win32/asw.exe" -xx -c -E -A -L ps4.asm ) ELSE "AS/win32/asw.exe" -xx -c -E -A -L ps4.asm

REM // if there were errors, a log file is produced
IF EXIST ps4.log goto LABLERROR4

REM // combine the assembler output into a rom
IF EXIST ps4.p "AS/win32/ps4p2bin" ps4.p ps4built.bin ps4.h

REM // done -- pause if we seem to have failed, then exit
IF NOT EXIST ps4.p goto LABLPAUSE
IF NOT EXIST ps4built.bin goto LABLPAUSE
"%~dp0fixheader.exe" ps4built.bin
exit /b
:LABLPAUSE

pause


exit /b

:LABLERROR1
echo Failed to build because write access to ps4.h was denied.
pause


exit /b

:LABLERROR2
echo Failed to build because write access to ps4.p was denied.
pause


exit /b

:LABLERROR3
echo Failed to build because write access to ps4built.bin was denied.
pause

exit /b

:LABLERROR4
REM // display a noticeable message
echo.
echo ***************************************************************************
echo *                                                                         *
echo *   There were build errors/warnings. See ps4.log for more details.  	   *
echo *                                                                         *
echo ***************************************************************************
echo.
pause

