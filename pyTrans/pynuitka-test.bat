call "c:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\bin\amd64\vcvars64.bat"
call c:\Python27\Scripts\nuitka --standalone --icon=icon.ico wxTest.py --output-dir=C:\temp\dist-nuitka --remove-output --improved --show-modules --show-scons --show-progress
rem --verbose

rem --show-progress

rem *** WORKING **
rem call c:\Python27\Scripts\nuitka --standalone --icon=icon.ico run.py --output-dir=C:\temp\dist-nuitka --remove-output --improved --nofreeze-stdlib /Od /wx-

rem *** NOT WORKING **

rem *** TO TEST ***

rem ** RUNNING MARCIN ***
rem call c:\Python27\Scripts\nuitka --standalone --icon=icon.ico run.py --output-dir=C:\temp\dist-nuitka --remove-output --improved --nofreeze-stdlib /Ox /wx-

rem call c:\Python27\Scripts\nuitka --standalone --icon=icon.ico run.py --output-dir=C:\temp\dist-nuitka --remove-output --improved
rem call c:\Python27\Scripts\nuitka --standalone --icon=icon.ico run.py --output-dir=C:\temp\dist-nuitka --remove-output --improved --nofreeze-stdlib /Od /wx+
rem call c:\Python27\Scripts\nuitka --output-dir=C:\temp\dist-nuitka --remove-output --improved --nofreeze-stdlib /Od /wx+

rem --recurse-none --recurse-stdlib --windows-disable-console --recurse-directory

pause