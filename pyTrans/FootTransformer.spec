# -*- mode: python -*-
a = Analysis(['run.py'],
             pathex=['z:\\Dropbox\\Consultancy\\Applied Sciences\\pyTrans'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'scipy.sparse.csgraph._validation', 'matplotlib.backends.backend_tkagg'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='FootTransformer.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='FootTransformer')
