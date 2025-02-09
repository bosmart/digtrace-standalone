@echo off
set name=TrackTransformer
set out_path=C:\TEMP\x32
rd %out_path% /s /q
call C:\python27_32\scripts\pyinstaller run.py --distpath=%out_path% --workpath=C:\TEMP\pyinst1 --name=%name% --onedir --icon=icon.ico --hidden-import=scipy.special._ufuncs_cxx --hidden-import=scipy.sparse.csgraph._validation --hidden-import=matplotlib.backends.backend_tkagg --noconsole 
copy *.png %out_path%\%name%
rd %out_path%\%name%\mpl-data\sample_data /s /q
rd %out_path%\%name%\mpl-data\fonts /s /q
rd %out_path%\%name%\mpl-data\images /s /q
rd %out_path%\%name%\include /s /q
rd %out_path%\%name%\_MEI /s /q
rd %out_path%\%name%\pytz /s /q
call Z:\Dropbox\Tools\upx-par.bat %out_path%\*

rem --upx-dir C:\Utils --clean
rem --hidden-import=scipy.special._ufuncs.cxx
pause