import numpy as np
import scipy.interpolate as interp
import pandas as pd
from plyfile import PlyData
import wx
from time import sleep

def load(fname, multiplier, precision=0.25):
    try:
        processbar = wx.ProgressDialog("Loading " + fname, "Please wait...", maximum=100, parent=None, style=wx.PD_APP_MODAL)
        processbar.Update(5, "Reading file...")

        if fname[-3:]=='ply':  # if *.ply file
            plydata = PlyData.read(str(fname))  # need to convert to string otherwise not working
            # ply files sometimes have more than xyz attributes, so we need to parse the first three columns out first
            data = plydata.elements[0].data
            data = np.vstack([data['x'], data['y'], data['z']])
            data = np.transpose(data)
            data = data.view('<f4')

        else: # other file types
            data = read(fname)

        processbar.Update(30, "Interpolating...")

        #check the correctness of the selected multiplier

        ranges=np.nanmax(data,0)-np.nanmin(data,0)
        if np.mean(ranges) < 10:
            guessed_multiplier = 100
        elif np.mean(ranges) < 50:
            guessed_multiplier = 10
        else:
            guessed_multiplier = 1

        processbar.Update(40, "Interpolating...")

        #apply multiplier to both data and precision

        x, y, z, xm, ym = interpolate(data*multiplier, precision)


        # np.savetxt(fname + '_x.csv', x, delimiter=',')
        # np.savetxt(fname + '_y.csv', y, delimiter=',')
        # np.savetxt(fname + '_z.csv', z, delimiter=',')

        processbar.Update(99, "Interpolating...")
        sleep(0.5)
        processbar.Destroy()

        #guessed multiplier is not used at the moment
        return (x, y, z, xm, ym), data, fname, guessed_multiplier  # os.path.basename(fname)

    except:
        return (None, None, fname, None)



def read(fname):
    data=pd.read_csv(fname, sep='[,\s+]', skipinitialspace=True, comment='#', engine='python')
    data = data.values[:, 0:3]
    return data

def interpolate(data, precision=0.25, method='linear', mn=None, mx=None):
    if mn is None or mx is None:
        mn, mx = data.min(axis=0), data.max(axis=0)

    mn = precision * (10 * mn / (precision * 10)).astype(int) #why int ?
    mx = precision * (10 * mx / (precision * 10)).astype(int)

    xm = np.arange(mn[0], mx[0] + precision, precision)
    ym = np.arange(mn[1], mx[1] + precision, precision)

    x, y = np.meshgrid(xm, ym)
    z = interp.griddata(data[:, 0:2], data[:, 2], (x, y), method=method)

    return x, y, z, xm, ym

