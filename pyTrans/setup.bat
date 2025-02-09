if "%1" == "-a" (
"C:\Python27\python.exe" setup_pro.py build -b "pro_build"
"C:\Program Files\WinRAR\rar.exe" a -r %cd%\pro_build\Digtrace-Pro%2.zip %cd%\pro_build\exe.win-amd64-2.7\*
"C:\Python27\python.exe" setup_pro.py bdist_msi -d "pro_installer"
)

if "%1" == "-b" (
"C:\Python27\python.exe" setup_pro.py build -b "pro_build"
"C:\Program Files\WinRAR\rar.exe" a -r %cd%\pro_build\Digtrace-Pro%2.zip %cd%\pro_build\exe.win-amd64-2.7\*
)

if "%1" == "-i" (
"C:\Python27\python.exe" setup_pro.py bdist_msi -d "pro_installer"
)