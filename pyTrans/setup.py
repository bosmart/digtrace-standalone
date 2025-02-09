import sys
import os
from cx_Freeze import setup, Executable
import scipy

scipy_path = os.path.dirname(scipy.__file__) #use this if you are also using scipy in your application

build_exe_options = {"packages": ["pyface.ui.wx", "tvtk.vtk_module", "tvtk.pyface.ui.wx", "matplotlib.backends.backend_tkagg"],
                     "excludes": ['numarray', 'IPython', 'collections.abc'],
                     "include_files": [("C:\\Python27\\Lib\\site-packages\\tvtk\\pyface\\images\\", "tvtk\\pyface\\images"),
                                       ("C:\\Python27\\Lib\\site-packages\\pyface\\images\\", "pyface\\images"),
                                       ("C:\\Python27\\Lib\\site-packages\\tvtk\\plugins\\scene\\preferences.ini", "tvtk\\plugins\\scene\\preferences.ini"),
                                       ("C:\\Python27\\Lib\\site-packages\\tvtk\\tvtk_classes.zip", "tvtk\\tvtk_classes.zip"),
                                       ("C:\\Python27\\Lib\\site-packages\\mayavi\\core\\lut\\pylab_luts.pkl","mayavi\\core\\lut\\pylab_luts.pkl"),
                                       ("C:\\Python27\\Lib\\site-packages\\mayavi\\preferences\\preferences.ini","mayavi\\preferences\\preferences.ini"),
                                       ("C:\\Python27\\Lib\\site-packages\\numpy\\core\\libifcoremd.dll","numpy\\core\\libifcoremd.dll"),
                                       ("C:\\Python27\\Lib\\site-packages\\numpy\\core\\libmmd.dll","numpy\\core\\libmmd.dll"),
                                       (str(scipy_path), "scipy") #for scipy
                                       ]                       
                     ,"create_shared_zip": False #to avoid creating library.zip
                     }

executables = [
    Executable('test2.py', targetName="test2.exe", base=None)
]

setup(name='myfile',
      version='1.0',
      description='myfile',
      options = {"build_exe": build_exe_options},
      executables=executables
      ) 