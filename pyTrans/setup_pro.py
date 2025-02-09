# -*- coding: utf-8 -*-

# A simple setup script to create an executable running wxPython. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# wxapp.py is a very simple 'Hello, world' type wxPython application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

import sys
import os
from cx_Freeze import setup, Executable
import datetime
import scipy
from distutils.dir_util import copy_tree
from distutils.file_util import move_file

VERSION = '1.8.3'

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa371847(v=vs.85).aspx
shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "DigTrace Pro",           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]DigTrace.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}
# Change some default MSI options and specify the use of the above defined tables
bdist_msi_options = {'data': msi_data}

current_time = str(datetime.datetime.now().time())
current_time = current_time.replace(':', '.')

base = None
# if sys.platform == 'win32':
#     base = 'Win32GUI'

#print 'Argument List:', str(sys.argv)

#identify the icons based on the version supplied in argument
#ver=os.environ['DIGTRACE_VER']
#print(ver)

# if ver=='acd':
#     print("Academic version")
#     copy_tree("icons_pro", "icons")
# elif ver=='pro':
#     print("Pro version")
#     copy_tree("icons_pro", "icons")
# else:
#     sys.exit()

#first we need to copy custom matplot icons in its directory, if we haven't done so already earlier
if not os.path.exists("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original"):
    os.makedirs("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original")
    move_file("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\back.png",
             "C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original\\back.png")
    move_file("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\forward.png",
             "C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original\\forward.png")
    move_file("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\home.png",
             "C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original\\home.png")
    move_file("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\move.png",
             "C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original\\move.png")
    move_file("C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\zoom_to_rect.png",
             "C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images\\original\\zoom_to_rect.png")

copy_tree("icons_pro\\matplot", "C:\\Python27\\Lib\\site-packages\\matplotlib\\mpl-data\\images")

#and mayavi icons
if not os.path.exists("C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\16x16\\original"):
    os.makedirs("C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\16x16\\original")
    copy_tree("C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\16x16", "C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\16x16\\original")
copy_tree("icons_pro\\mayavi", "C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\16x16")



scipy_path = os.path.dirname(scipy.__file__)

build_exe_options = {"packages": ["pyface.ui.wx", "tvtk.vtk_module", "tvtk.pyface.ui.wx","matplotlib.backends.backend_tkagg", "matplotlib.backends.backend_ps", "traitsui.wx.range_editor", "tkFileDialog","tkMessageBox"],
                     "excludes": ['numarray', 'IPython', 'collections.abc'],
                     "include_files": [("C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\", "tvtk\\pyface\\images"),
                                       ("C:\\Python27\\Lib\\site-packages\\pyface\\images\\", "pyface\\images"),
                                       ("C:\\Python27\\Lib\\site-packages\\traitsui\\wx\\", "traitsui\\wx\\"),
                                       ("C:\\Python27\\Lib\\site-packages\\tvtk\\plugins\\scene\\preferences.ini", "tvtk\\plugins\\scene\\preferences.ini"),
                                       ("C:\\Python27\\Lib\\site-packages\\tvtk\\tvtk_classes.zip", "tvtk\\tvtk_classes.zip"),
                                       ("C:\\Python27\\Lib\\site-packages\\traitsui\\image\\library\\std.zip", "traitsui\\image\\library\\std.zip"),
                                       ("C:\\Python27\\Lib\\site-packages\\mayavi\\core\\lut\\pylab_luts.pkl","mayavi\\core\\lut\\pylab_luts.pkl"),
                                       ("C:\\Python27\\Lib\\site-packages\\mayavi\\preferences\\preferences.ini","mayavi\\preferences\\preferences.ini"),
                                       ("C:\\Python27\\Lib\\site-packages\\numpy\\core\\libifcoremd.dll","numpy\\core\\libifcoremd.dll"),
                                       ("C:\\Python27\\Lib\\site-packages\\numpy\\core\\libmmd.dll","numpy\\core\\libmmd.dll"),
                                       (str(scipy_path), "scipy"),
                                       ("icons_pro\\matplot", "tvtk\\pyface\\images\\16x16"),
                                       ("utilities", "utilities"),
                                       ("icons_pro", "icons"),
                                       ("msvcr\\", ".\\")
                                       ]
                     # following options are for not creating scipy
                     ,"create_shared_zip": False
                     #,"append_script_to_exe": True
                     #,"include_in_shared_zip": False
                     }

executables = [
    Executable('run.py', targetName="DigTrace.exe", base='Win32GUI', icon="icons_pro\\64x64.ico", appendScriptToExe=True)
    #Executable('run.py', targetName="DigTrace.exe", base=None, icon="icons_pro\\64x64.ico", appendScriptToExe=True)
]

setup(name='DigTrace Pro',
      #version=current_time,
      version=VERSION,
      description='Digital Track Capture and Examination',
      options = {"build_exe": build_exe_options
                ,"bdist_msi": bdist_msi_options},
      executables=executables
      )
