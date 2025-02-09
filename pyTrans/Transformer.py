# TODO:
# (WONT FIX) 4. Drag from master/source back to bar
# 7. Drag and drop within thumbnail bar - change order of prints
# fixes
# import matplotlib
# matplotlib.use('PS')

import os
import sys
import Tkinter

sys.modules['tkinter'] = Tkinter
import FileDialog
a = FileDialog

import multiprocessing
import collections
import math

import wx
import numpy as np
import itertools

import re

import matplotlib.cm as cm

import json
import platform

import loadPrint as lp
from MatplotPanel import MatplotPanel
from ContourPanel import ContourPanel
from UploadDialog import UploadDialog
from OpenOptionsDialog import OpenOptionsDialog
from Loader import Loader

from Tkinter import Tk

from time import sleep
from scipy import stats

import pandas as pd


IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

class MyDropTarget(wx.TextDropTarget):
    # landmark colors and sizes
    marker_size = 9
    normal_width = 0.5
    normal_color = 'k'
    highlight_width = 2
    highlight_color = 'r'
    active_width = 2
    active_color = 'w'
    # distance measurement while dragging
    distance = 0

    def __init__(self, window):
        wx.TextDropTarget.__init__(self)
        self.window = window
        self.frame = window.GetParent()
        self.hid = None  # motion_notify_event handler
        self.Shift_is_held = False  # whether shift is held


    # Fires when something is dropped on the panel
    def OnDropText(self, x, y, data):
        panel = self.window
        if panel == self.frame.panel_master:
            pid = 0
        else:
            pid = 1

        # only drop to source if master is already there
        if pid == 1 and not hasattr(self.frame.panel_master, 'mpl'):
            self.frame.status_bar.SetStatusText('Select the master print first.')
            wx.Yield()
            return

        # if pid == 0 and not hasattr(self.frame.panel_source, 'mpl'):
        # self.frame.txt.Show()

        sizer = panel.GetSizer()


        try:
            data = int(data)
        except:
            #data = int(data[:-1])
            temp = re.findall('(-?\d+)',data)
            data = int(temp[0])
            # on OS X an extra or more character is added at the end

        mpl_src = self.frame.mpls[int(data)]


        # if there are landmarks with coordinates larger than the new image, delete those
        for idx, xy in reversed(list(enumerate(self.frame.lmark_xy[pid]))):
            if xy[0]>mpl_src.xyzi[2].shape[1] or xy[1]>mpl_src.xyzi[2].shape[0]:

                if pid==0:
                    if self.frame.lmark_h[1][idx] is not None:
                        self.frame.panel_source.mpl.ax.lines.remove(self.frame.lmark_h[1][idx])
                else:
                    if self.frame.lmark_h[0][idx] is not None:
                        self.frame.panel_master.mpl.ax.lines.remove(self.frame.lmark_h[0][idx])

                self.frame.lmark_h[0].pop(idx)
                self.frame.lmark_h[1].pop(idx)
                self.frame.lmark_xy[0] = np.delete(self.frame.lmark_xy[0], idx, axis=0)
                self.frame.lmark_xy[1] = np.delete(self.frame.lmark_xy[1], idx, axis=0)

                if self.frame.lmark_active == idx:
                    self.frame.lmark_active = None
                elif self.frame.lmark_active > idx:
                    self.frame.lmark_active -= 1

                if self.frame.lmark_hlight == idx:
                    self.frame.lmark_hlight = None

                self.frame.panel_source.mpl.ax.figure.canvas.draw()
                self.frame.panel_master.mpl.ax.figure.canvas.draw()

        # there must be landmarks defined for master before loading a source with landmarks
        if pid == 1 and mpl_src.lmark_xy is not None and \
                (self.frame.lmark_xy[0] is None or mpl_src.lmark_xy[0].shape[0] > self.frame.lmark_xy[0].shape[0]):
            self.frame.status_bar.SetStatusText('Define at least %d landmarks for the master print first.' % mpl_src.lmark_xy.shape[0])
            wx.Yield()
            return


        # If the drop source is already being used in either master or source, do nothing
        if mpl_src.used:
            return

        # Cleanup if this is not the first Drop operation in the panel
        # self.frame.lmark_active = None

        # Revert colormap of the print not being used any more
        if hasattr(panel, 'mpl') and panel.mpl:
            panel.mpl.delete_figure()
            panel.mpl.mpl_src.used = False
            panel.mpl.mpl_src.set_cmap()
            panel.mpl.mpl_src.pid = -1

        # Change colormap of the print being used
        mpl_src.used = True
        mpl_src.set_cmap('gray')
        mpl_src.pid = pid

        # Create a new plot, add it to a cleared sizer (clearing e.g. the static text) and subscribe to the event
        panel.mpl = MatplotPanel(self.window, mpl_src.xyzi, mpl_src.xyz, mpl_src.multiplier, mpl_src.precision, (1, 1),  mpl_src,  mpl_src.title, mpl_src.fname, pid=pid, current_vmin=mpl_src.current_vmin, current_vmax=mpl_src.current_vmax)
        sizer.Clear(True)
        panel.mpl.set_cmap(self.frame.toolbar.choiceCm.GetString(self.frame.toolbar.choiceCm.GetSelection()))

        # restore landmarks if exist
        if mpl_src.lmark_xy is not None:
            self.frame.lmark_xy[pid] = mpl_src.lmark_xy.copy()
            [h.remove() for h in self.frame.lmark_h[pid] if h is not None]
            cnt1 = self.frame.lmark_xy[pid].shape[0]
            cnt2 = len(self.frame.lmark_h[pid])
            if cnt2 == 0:
                self.frame.lmark_h[pid] = [None] * cnt1
                cnt2 = cnt1
                if len(self.frame.lmark_h[1 - pid]) == 0:
                    self.frame.lmark_h[1 - pid] = [None] * cnt1
            nan_arr = np.zeros((cnt2 - cnt1, 2))
            nan_arr[:] = np.NAN
            self.frame.lmark_xy[pid] = np.vstack((self.frame.lmark_xy[pid], nan_arr))
            self.frame.lmark_h[pid][cnt1:cnt2] = [None] * (cnt2 - cnt1)

        # add plot title to the sizer
        txt = wx.StaticText(panel, wx.ID_ANY, mpl_src.title, style=wx.ALIGN_CENTER)
        txt.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt.SetForegroundColour((128, 128, 128))
        sizer.Add(txt, flag=wx.CENTER)

        # add plot panel
        sizer.Add(panel.mpl, 1, wx.EXPAND | wx.ALL, 5)
        panel.mpl.canvas.mpl_connect('button_press_event', self.on_press)
        self.hid = panel.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion)
        panel.mpl.canvas.mpl_connect('button_release_event', self.on_release)
        panel.mpl.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        panel.mpl.fig.canvas.mpl_connect('key_release_event', self.on_key_release)
        #panel.mpl.fig.canvas.mpl_connect('button_press_event', self.on_drag_line)

        # Plot exiting landmarks and save/update their handles
        if self.frame.lmark_xy[pid].size:
            axis = panel.mpl.ax.axis()

            for i, h in enumerate(self.frame.lmark_h[pid]):
                c = self.frame.lmark_h[0][i]
                col = ''
                if c is not None:
                    col = c.get_markerfacecolor()

                self.frame.lmark_h[pid][i], = panel.mpl.ax.plot(self.frame.lmark_xy[pid][i, 0],
                                                                self.frame.lmark_xy[pid][i, 1],
                                                                marker='o',
                                                                markerfacecolor = col,
                                                                markersize=self.marker_size)

            if self.frame.lmark_active and self.frame.lmark_h[pid][self.frame.lmark_active]:
                self.frame.lmark_h[pid][self.frame.lmark_active].set_markeredgewidth(self.active_width)
                self.frame.lmark_h[pid][self.frame.lmark_active].set_markeredgecolor(self.active_color)

            panel.mpl.ax.axis(axis)

        #disable some icons
        self.frame.toolbar.EnableTool(wx.ID_SAVEAS, False)
        self.frame.toolbar.EnableTool(wx.ID_REMOVE, False)
        self.frame.toolbar.EnableTool(wx.ID_BACKWARD, False)
        self.frame.toolbar.EnableTool(wx.ID_FORWARD, False)
        self.frame.toolbar.EnableTool(wx.ID_APPLY, False)

        # enable icons
        self.frame.toolbar.EnableTool(wx.ID_ADD, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE9, True)

        # testing the correlation error measure
        # need to interpolate one of the images so they have the same dimensions
        # if hasattr(self.frame.panel_master, 'mpl') and self.frame.panel_master.mpl and hasattr(self.frame.panel_source, 'mpl') and self.frame.panel_source.mpl:
        #     mn, mx = self.frame.panel_master.mpl.xyz.min(axis=0), self.frame.panel_master.mpl.xyz.max(axis=0)
        #
        #     res = lp.interpolate(self.frame.panel_source.mpl.xyz, mn=mn, mx=mx, precision=self.frame.panel_source.mpl.precision)
        #
        #     uuu = np.transpose(np.vstack((self.frame.panel_master.mpl.xyzi[2].flatten(), res[2].flatten())))
        #     pduuu = pd.DataFrame(uuu, columns=list('AB'))
        #     corr = pduuu.corr()
        #
        #     self.frame.status_bar.SetStatusText("Correlation between images: " + str(corr.ix[0,1]))

        self.frame.contour_refresh()

        # Force redraw: windows.Refresh() doesn't seem to work
        self.window.SendSizeEvent()


    def hit_test(self, pos, pid):

        # is it an empty landmark
        if len(self.frame.lmark_xy[pid]) == 0:
            # print('hit_test(): empty landmark')
            idx = None

        # mouse over existing landmark?
        else:
            idx = np.where(
                (np.abs(self.frame.lmark_xy[pid][:, 0] - pos[0]) < self.window.mpl.xthrs) &
                (np.abs(self.frame.lmark_xy[pid][:, 1] - pos[1]) < self.window.mpl.ythrs)
            )

            # idx keeps an index of the landmark
            if idx[0].size == 0:
                idx = None
            else:
                idx = idx[0][0]

        return idx

    # Fires on mouse button release
    def on_release(self, event):
        self.window.mpl.canvas.mpl_disconnect(self.hid)
        self.hid = self.window.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion)

        if not event.inaxes:
            return

        #  remove the dragged line if exists and show distance between two points in status bar and copy to clipboard
        if event.inaxes.lines.__contains__(self.frame.dragLine):
            event.inaxes.lines.remove(self.frame.dragLine)
            event.inaxes.figure.canvas.draw()
            self.frame.status_bar.SetStatusText(self.frame.status_bar.GetStatusText() + ' Copied to clipboard.')
            wx.MessageBox(self.frame.status_bar.GetStatusText(), 'Distance',
                          wx.OK | wx.ICON_INFORMATION)
            if IS_WIN:
                r = Tk()
                r.withdraw()
                r.clipboard_clear()
                r.clipboard_append(str(self.distance))
                r.destroy()


        if not self.frame.refresh_flag:
            return
        self.frame.contour_refresh()

    # Fires on mouse motion
    def on_motion_drag(self, event):
        if not event.inaxes:
            return

        # this is to check if used clicked on the image or on the colorbar
        # if colorbar axes have axison=True and image axis False
        # temporary solution, fix later
        if event.inaxes.axison:
            return

        axis = event.inaxes.axis() #to avoid resize

        panel = self.window
        if panel == self.frame.panel_master:
            pid = 0
        else:
            pid = 1

        if bool(event.key == 'shift') or self.frame.toolbar.GetToolState(wx.ID_FILE9):
            if event.inaxes.lines.__contains__(self.frame.dragLine):
                event.inaxes.lines.remove(self.frame.dragLine)
            self.frame.dragLine, = event.inaxes.plot([self.frame.startDragPos[0], event.xdata], [self.frame.startDragPos[1], event.ydata],color='white')
            event.inaxes.figure.canvas.draw()

            # get the interpolated coordinates

            x = self.window.mpl.xyzi[0]
            y = self.window.mpl.xyzi[1]
            coords_interpolated_start = np.hstack((self.frame.startDragPos[0], self.frame.startDragPos[1]))
            coords_interpolated_start = coords_interpolated_start.astype(int)
            coords_interpolated_end = np.hstack((event.xdata, event.ydata))
            coords_interpolated_end = coords_interpolated_end.astype(int)
            # try:
            #     coords_interpolated = np.hstack((x[coords_interpolated[0], coords_interpolated[1]], y[coords_interpolated[0], coords_interpolated[1]]))
            # except:
            #     print('drag operation out of area')
            #     self.distance = 0

            # need to convert height coordinates
            # height coordinate in the image starts from the bottom!
            coords_interpolated_start[1] = self.window.mpl.xyzi[0].shape[0]- coords_interpolated_start[1]
            coords_interpolated_end[1] = self.window.mpl.xyzi[0].shape[0]- coords_interpolated_end[1]

            ystart=x[0, coords_interpolated_start[0]]
            yend=x[0, coords_interpolated_end[0]]
            xstart=y[coords_interpolated_start[1], 0]
            xend=y[coords_interpolated_end[1], 0]

            print([xstart, xend, ystart, yend])
            #print(coords_interpolated)
            # try:
            #     coords_interpolated = np.hstack((xm[coords_interpolated[:, 0], None].astype(int), ym[coords_interpolated[:, 1], None].astype(int)))
            # except:
            #     print('drag operation out of area')
            #     self.distance = 0
            # print(coords_interpolated)
            self.distance = math.hypot(xstart - xend, ystart - yend)
            self.distance = round(self.distance, 2)
            if self.window.mpl.multiplier == 1:
                unit = ' mm.'
            if self.window.mpl.multiplier == 10:
                unit = ' cm.'
            if self.window.mpl.multiplier == 100:
                unit = ' dm.'
            if self.window.mpl.multiplier == 1000:
                unit = ' m.'
            else:
                unit = ' mm.'
            self.frame.status_bar.SetStatusText(str(self.distance) + unit)

        if bool(self.frame.lmark_hlight is not None) & self.frame.toolbar.GetToolState(wx.ID_ADD): #dragging landmarks if landmark placement mode activated
            self.frame.lmark_h[pid][self.frame.lmark_hlight].set_xdata(round(event.xdata))
            self.frame.lmark_h[pid][self.frame.lmark_hlight].set_ydata(round(event.ydata))
            self.frame.lmark_xy[pid][self.frame.lmark_hlight, :] = [round(event.xdata), round(event.ydata)]

        event.inaxes.axis(axis) #to avoid resize
        event.inaxes.figure.canvas.draw()

    # Fires on mouse motion - highlight landmark - only after the print has been loaded in the print area
    def on_motion(self, event):
        if not event.inaxes: return

        panel = self.window
        if panel == self.frame.panel_master:
            pid = 0
        else:
            pid = 1

        pos = np.round(np.array([event.xdata, event.ydata]))
        idx = self.hit_test(pos, pid)

        # un-highlight the landmark in both panels
        if idx is None and self.frame.lmark_hlight is not None and self.frame.lmark_h[pid][
            self.frame.lmark_hlight] is not None:
            self.frame.lmark_h[0][self.frame.lmark_hlight].set_markeredgewidth(self.normal_width)
            self.frame.lmark_h[0][self.frame.lmark_hlight].set_markeredgecolor(self.normal_color)
            if self.frame.lmark_h[1][self.frame.lmark_hlight] is not None:
                self.frame.lmark_h[1][self.frame.lmark_hlight].set_markeredgewidth(self.normal_width)
                self.frame.lmark_h[1][self.frame.lmark_hlight].set_markeredgecolor(self.normal_color)

            # if it's active, change the marker
            if self.frame.lmark_hlight == self.frame.lmark_active:
                self.frame.lmark_h[0][self.frame.lmark_active].set_markeredgewidth(self.active_width)
                self.frame.lmark_h[0][self.frame.lmark_active].set_markeredgecolor(self.active_color)

            self.frame.lmark_hlight = None

        # highlight the landmark in both panels
        elif idx is not None:
            self.frame.lmark_hlight = idx

            if self.frame.lmark_h[0][self.frame.lmark_hlight] is not None:
                self.frame.lmark_h[0][self.frame.lmark_hlight].set_markeredgewidth(self.highlight_width)
                self.frame.lmark_h[0][self.frame.lmark_hlight].set_markeredgecolor(self.highlight_color)

            if self.frame.lmark_h[1][self.frame.lmark_hlight] is not None:
                self.frame.lmark_h[1][self.frame.lmark_hlight].set_markeredgewidth(self.highlight_width)
                self.frame.lmark_h[1][self.frame.lmark_hlight].set_markeredgecolor(self.highlight_color)

        # event.inaxes.figure.canvas.draw()
        if hasattr(self.frame.panel_master, 'mpl'):
            self.frame.panel_master.mpl.ax.figure.canvas.draw()
        if hasattr(self.frame.panel_source, 'mpl'):
            self.frame.panel_source.mpl.ax.figure.canvas.draw()

    # if "shift" is held
    def on_key_press(self, event):
        if event.key == 'shift':
            self.Shift_is_held = True

    # if "shift" is released
    def on_key_release(self, event):
        if event.key == 'shift':
            self.Shift_is_held = False


    # Fires on mouse click on the panel
    def on_press(self, event):

        #self.canvas.setFocusPolicy( wx )
        self.window.mpl.canvas.SetFocusFromKbd()

        if not event.inaxes:
            return

        # this is to check if used clicked on the image or on the colorbar
        # if colorbar axes have axison=True and image axis False
        # temporary solution, fix later
        if event.inaxes.axison:
            return

        self.frame.status_bar.SetStatusText('')
        panel = self.window

        # if zoom activated show a message
        if panel.mpl.toolbar._active is not None:
            self.frame.status_bar.SetStatusText('Deactivate zoom tools to set a landmark')
            return


        if panel == self.frame.panel_master:
            pid = 0
        else:
            pid = 1

        # click on existing landmark?
        pos = np.round(np.array([event.xdata, event.ydata]))
        idx = self.hit_test(pos, pid)

        # refresh the contour plot flag
        refresh_flag = True

        # left-click
        if event.button == 1:

            # in case this is a start of a drag operation
            print("on_click(): hook motion_notify_event, (x, y) = " + str(pos[0]) + ", " + str(pos[1]))
            self.frame.startDragPos = pos  # save position of the last click for drag operation
            self.window.mpl.canvas.mpl_disconnect(self.hid)
            self.hid = self.window.mpl.canvas.mpl_connect('motion_notify_event', self.on_motion_drag)
            print(self.frame.startDragPos)
            if bool(event.key == 'shift') | self.frame.toolbar.GetToolState(wx.ID_FILE9):  # if shift is held, or quick measure toggled stop here this is distance measurement so no lanmdmark placement
                return

            if self.frame.toolbar.GetToolState(wx.ID_ADD) is False: #landmrk placement not toggled
                return

            # enable remove icon
            self.frame.toolbar.EnableTool(wx.ID_REMOVE, True)

            # this needs to go first for the axis not to resize on plotting
            axis = event.inaxes.axis()

            # add new landmark to master panel
            if pid == 0:

                if idx is None:
                    idx = self.frame.lmark_xy[pid].shape[0]
                    h, = event.inaxes.plot(pos[0], pos[1], 'o', markersize=self.marker_size)
                    self.frame.lmark_h[pid].append(h)
                    self.frame.lmark_h[pid + 1].append(None)
                    self.frame.lmark_xy[pid] = np.vstack((self.frame.lmark_xy[pid], pos))
                    self.frame.lmark_xy[pid + 1] = np.vstack((self.frame.lmark_xy[pid + 1], [np.nan, np.nan]))

                    # get the contract color of the background and set it to the landmarker
                    color_value = (self.frame.panel_master.mpl.xyzi[2][int(self.frame.lmark_xy[pid][-1][1])][int(self.frame.lmark_xy[pid][-1][0])] - self.frame.panel_master.mpl.vmin) / (self.frame.panel_master.mpl.vmax - self.frame.panel_master.mpl.vmin)
                    if color_value <= 0.5:
                        color_value = color_value + 0.5
                    else:
                        color_value = color_value - 0.5
                    color = cm.jet(color_value)
                    self.frame.lmark_h[pid][idx].set_markerfacecolor(color)

                    refresh_flag = False

                # make the landmark active
                if self.frame.lmark_active is not None:
                    self.frame.lmark_h[pid][self.frame.lmark_active].set_markeredgewidth(self.normal_width)
                    self.frame.lmark_h[pid][self.frame.lmark_active].set_markeredgecolor(self.normal_color)

                self.frame.lmark_h[pid][idx].set_markeredgewidth(self.active_width)
                self.frame.lmark_h[pid][idx].set_markeredgecolor(self.active_color)
                self.frame.lmark_active = idx

            # add new landmark to source panel
            elif pid == 1 and self.frame.lmark_active is not None:

                idxa = self.frame.lmark_active
                if self.frame.lmark_h[pid][idxa] is None:
                    h, = event.inaxes.plot(pos[0], pos[1], 'o', markersize=self.marker_size)
                    h.set_markerfacecolor(self.frame.lmark_h[0][idxa].get_markerfacecolor())
                    self.frame.lmark_h[pid][idxa] = h
                    if self.frame.lmark_xy[pid].shape[0] <= idxa:
                        cnt = idxa - self.frame.lmark_xy[pid].shape[0]
                        nan_arr = np.reshape(np.repeat([np.nan, np.nan], cnt), (cnt, 2))
                        self.frame.lmark_xy[pid] = np.vstack((self.frame.lmark_xy[pid], nan_arr, pos))
                    else:
                        self.frame.lmark_xy[pid][idxa, :] = pos

                if idx is not None:

                    if idxa is not None and idxa != idx:
                        self.frame.lmark_h[0][idxa].set_markeredgewidth(self.normal_width)
                        self.frame.lmark_h[0][idxa].set_markeredgecolor(self.normal_color)

                    # make the landmark active
                    self.frame.lmark_h[0][idx].set_markeredgewidth(self.active_width)
                    self.frame.lmark_h[0][idx].set_markeredgecolor(self.active_color)
                    self.frame.lmark_active = idx

                    self.frame.panel_master.mpl.ax.figure.canvas.draw()

            elif pid == 1 and idx is None and self.frame.lmark_active is None:
                self.frame.status_bar.SetStatusText('Select a master landmark first.')
                wx.Yield()

            # this needs to go here for the axis not to resize on plotting
            event.inaxes.axis(axis)

        # right-click
        elif event.button == 3 and pid == 0:

            if self.frame.toolbar.GetToolState(wx.ID_ADD) is False:  # landmrk placement not toggled
                return

            # deactivate active landmark
            if idx is None and self.frame.lmark_active is not None:
                self.frame.lmark_h[pid][self.frame.lmark_active].set_markeredgewidth(self.normal_width)
                self.frame.lmark_h[pid][self.frame.lmark_active].set_markeredgecolor(self.normal_color)
                self.frame.lmark_active = None

            # remove selected landmark and correct self.frame.lmark_active
            elif idx is not None:
                event.inaxes.lines.remove(self.frame.lmark_h[pid][idx])
                if self.frame.lmark_h[1][idx] is not None:
                    self.frame.panel_source.mpl.ax.lines.remove(self.frame.lmark_h[1][idx])
                    self.frame.panel_source.mpl.ax.figure.canvas.draw()
                else:
                    refresh_flag = False

                self.frame.lmark_h[pid].pop(idx)
                self.frame.lmark_h[pid + 1].pop(idx)
                self.frame.lmark_xy[pid] = np.delete(self.frame.lmark_xy[pid], idx, axis=0)
                self.frame.lmark_xy[pid + 1] = np.delete(self.frame.lmark_xy[pid + 1], idx, axis=0)

                if self.frame.lmark_active == idx:
                    self.frame.lmark_active = None
                elif self.frame.lmark_active > idx:
                    self.frame.lmark_active -= 1

                if self.frame.lmark_hlight == idx:
                    self.frame.lmark_hlight = None

        if len(self.frame.lmark_h[0])==0:
            self.frame.toolbar.EnableTool(wx.ID_REMOVE, False)

        # force redraw - old way: self.window.SendSizeEvent()
        self.frame.refresh_flag = refresh_flag
        event.inaxes.figure.canvas.draw()


class Transformer(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        #self.q = parent.Parent.q

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        self.sizer_vert = wx.BoxSizer(wx.VERTICAL)  # main Sizer
        self.toolbar = TransformerToolbar(self)  # toolbar
        self.sizer_vert.Add(self.toolbar, 0, wx.EXPAND, wx.EXPAND, 5)

        self.sizer_horiz = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_vert.Add(self.sizer_horiz, 4, wx.EXPAND, 5)

        self.panel_thumbs = parent.Parent.panel_thumbs
        self.sizer_thumbs = parent.Parent.sizer_thumbs
        #self.panel_thumbs = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL | wx.SIMPLE_BORDER)
        #self.panel_thumbs.SetScrollRate(5, 5)

        #self.sizer_thumbs = wx.BoxSizer(wx.HORIZONTAL)
        #self.panel_thumbs.SetSizer(self.sizer_thumbs)
        #self.sizer_thumbs.Fit(self.panel_thumbs)

        #self.panel_thumbs.Layout()
        #self.sizer_vert.Add(self.panel_thumbs, 1, wx.EXPAND | wx.ALL, 5)

        self.refresh_flag = True

        self.SetSizer(self.sizer_vert)

        self.status_bar = parent.Parent.GetStatusBar()

        self.toolbar.Realize()

        # self.Bind(wx.EVT_TOOL, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.show_folder_history_menu, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.on_statistics, id=wx.ID_SAVEAS)
        #self.Bind(wx.EVT_TOOL, self.on_ttest, id=self.toolbar.ID_TTEST)
        self.Bind(wx.EVT_TOOL, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_TOOL, self.on_save_contour, id=wx.ID_FLOPPY)
        self.Bind(wx.EVT_TOOL, self.on_toggle_place_lmarks, id=wx.ID_ADD)
        self.Bind(wx.EVT_TOOL, self.on_clear_lmarks, id=wx.ID_REMOVE)
        self.Bind(wx.EVT_TOOL, self.on_toggle_quick_measure, id=wx.ID_FILE9)
        self.Bind(wx.EVT_TOOL, self.on_backward, id=wx.ID_BACKWARD)
        self.Bind(wx.EVT_TOOL, self.on_forward, id=wx.ID_FORWARD)
        self.Bind(wx.EVT_CHOICE, self.on_choice)
        self.Bind(wx.EVT_TOOL, self.on_apply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_CHECKBOX, self.on_choice)
        self.Bind(wx.EVT_TOOL, self.on_colorscale, id=wx.ID_CONVERT)
        self.Bind(wx.EVT_TOOL, self.on_selectall, id=wx.ID_SELECTALL)
        self.toolbar.choiceCm.Bind(wx.EVT_CHOICE, self.on_change_colormap)



        # right click menu for open folder history
        #self.Bind(wx.EVT_TOOL_RCLICKED, self.show_folder_history, id=wx.ID_OPEN)


        self.panel_master = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_horiz.Add(self.panel_master, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer_master = wx.BoxSizer(wx.VERTICAL)
        self.panel_master.SetSizer(self.sizer_master)
        self.panel_master.Layout()
        self.sizer_master.Fit(self.panel_master)
        self.drop_target_master = MyDropTarget(self.panel_master)
        self.panel_master.SetDropTarget(self.drop_target_master)

        self.panel_overlay = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_horiz.Add(self.panel_overlay, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer_overlay = wx.BoxSizer(wx.VERTICAL)
        #self.sizer_overlay.Add(self.panel_overlay)
        self.panel_overlay.SetSizer(self.sizer_overlay)
        self.panel_overlay.Layout()
        self.sizer_overlay.Fit(self.panel_overlay)
        # self.panel_overlay.SetDropTarget(MyDropTarget(self.panel_overlay))

        self.panel_source = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_horiz.Add(self.panel_source, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer_source = wx.BoxSizer(wx.VERTICAL)
        self.panel_source.SetSizer(self.sizer_source)
        self.panel_source.Layout()
        self.sizer_source.Fit(self.panel_source)
        self.drop_target_source = MyDropTarget(self.panel_source)
        self.panel_source.SetDropTarget(self.drop_target_source)

        txt_drag = u"Drag a print here"
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)

        txt = wx.StaticText(self.panel_master, wx.ID_ANY, txt_drag, style=wx.ALIGN_CENTER)
        txt.SetFont(font)
        txt.SetForegroundColour((128, 128, 128))
        self.sizer_master.Add(txt, 1, flag=wx.CENTER)

        txt = wx.StaticText(self.panel_source, wx.ID_ANY, txt_drag, style=wx.ALIGN_CENTER)
        txt.SetFont(font)
        txt.SetForegroundColour((128, 128, 128))
        self.sizer_source.Add(txt, 1, flag=wx.CENTER)

        # txt1 = wx.StaticText(self.panel_overlay, wx.ID_ANY, u"Error: ?.????", style=wx.ALIGN_CENTER)
        # txt1.SetFont(font)
        # txt1.SetForegroundColour((128, 128, 128))
        # self.sizer_overlay.Add(txt1, 1, flag=wx.CENTER)

        # trick: add empty panels for the layout to work correctly on resizing in some situation
        self.sizer_master.Add(wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, self.panel_master.GetSize(), wx.TAB_TRAVERSAL), 2, flag=wx.CENTER)
        self.sizer_source.Add(wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, self.panel_source.GetSize(), wx.TAB_TRAVERSAL), 2, flag=wx.CENTER)
        # following line adds a white line to the interface, hence commented, looks like it works ok without this too
        #self.sizer_overlay.Add(wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, self.panel_overlay.GetSize(), wx.TAB_TRAVERSAL), 1, flag=wx.CENTER)

        self.Centre(wx.BOTH)
        self.Layout()


        # landmark coordinates etc.
        self.lmark_active = None  # index of active/selected landmark
        self.lmark_hlight = None  # index of highlighted landmark (mouse-over)
        self.lmark_h = [list(), list()]  # two element (master and source panels) list of lists for landmark handles
        self.lmark_xy = [np.empty([0, 2]), np.empty([0, 2])]  # two element (master and source panels) list of arrays for landmark coordintaes
        self.contour_lines = 0
        self.A = None
        #self.mpls = collections.OrderedDict()

        self.mpls = parent.Parent.prints
        self.dragLine = None
        self.startDragPos = [0, 0]

        # open file history
        self.openfilehistory = wx.FileHistory(9)
        self.config_openfile = wx.Config(localFilename = "pyTrans-openfile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.openfilehistory.Load(self.config_openfile)

        # save contour file history
        self.csavefilehistory = wx.FileHistory(9)
        self.config_csavefile = wx.Config(localFilename = "pyTrans-Csavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.csavefilehistory.Load(self.config_csavefile)

        # save project file history
        self.psavefilehistory = wx.FileHistory(9)
        self.config_psavefile = wx.Config(localFilename = "pyTrans-psavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.psavefilehistory.Load(self.config_psavefile)

        # save statistics file history
        self.ssavefilehistory = wx.FileHistory(9)
        self.config_ssavefile = wx.Config(localFilename = "pyTrans-Ssavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.ssavefilehistory.Load(self.config_ssavefile)

    def show_folder_history_menu(self, event):
        popupMenu = wx.Menu()
        openfile = popupMenu.Append(wx.ID_ANY, "Open...")
        popupMenu.AppendSeparator()
        i = 0
        while i < self.openfilehistory.GetCount():
            path = self.openfilehistory.GetHistoryFile(i)
            item = popupMenu.Append(wx.ID_ANY, path)
            self.Bind(wx.EVT_MENU, lambda event, folder_history=i: self.on_open(event, folder_history), item)
            i += 1
        self.Bind(wx.EVT_MENU, self.on_open, openfile)

        self.PopupMenu(popupMenu, (event.EventObject.Position.x + 15, event.EventObject.Position.y + 40))

    def __del__(self):
        pass

    all_file_filter = "All supported files (*.ftproj;*.csv;*.asc;*.ply;*.txt)|*.ftproj;*.csv;*.asc;*.ply;*.txt|Project (*.ftproj)|*.ftproj|CSV files|*.csv|ASC files|*.asc|PLY files|*.ply|TXT files|*.txt|All files (*.*)|*.*"
    print_file_filter = "All supported files (*.csv;*.asc)|*.csv;*.asc|CSV files|*.csv|ASC files|*.asc|All files (*.*)|*.*"
    project_file_filter = "Project (*.ftproj)|*.ftproj"
    image_file_filter = "All supported files (*.jpg;*.png;*.pdf;*.svg;*.eps)|*.jpg;*.png;*.pdf;*.svg;*.eps|JPG files|*.jpg|PNG files|*.png|PDF files|*.pdf|SVG files|*.svg|EPS files|*.eps|All files (*.*)|*.*"

    # apply transformation to a print
    def transform(self, xyzi, A):
        x = np.reshape(xyzi[0], (xyzi[0].size, 1))
        y = np.reshape(xyzi[1], (xyzi[1].size, 1))
        S1 = np.hstack((x, y, np.ones((x.size, 1))))
        T = np.dot(S1, A)
        xyzi_out = np.reshape(T[:, 0], xyzi[0].shape), np.reshape(T[:, 1], xyzi[1].shape), xyzi[2]
        Tsav = np.hstack((T, np.reshape(xyzi[2], (T.shape[0], 1))))
        Tsav = Tsav[~np.isnan(Tsav).any(axis=1)]
        return (xyzi_out, Tsav)

    def on_selectall(self, event):
        all_selected = True
        for key, mpl in self.mpls.iteritems():
            if not mpl.Selected.GetValue():
                all_selected = False
        if all_selected:
            for key, mpl in self.mpls.iteritems():
                mpl.Selected.SetValue(False)
        else:
            for key, mpl in self.mpls.iteritems():
                mpl.Selected.SetValue(True)


    # Switch between independent/joint colorscales. Checked footprints will be brought to the joint scale, unchecked will remain independent.
    def on_colorscale(self, event):

        min_list = []
        max_list = []

        # get mins and maxs of selected mpls
        for key, mpl in self.mpls.iteritems():
            if mpl.Selected.GetValue():
                min_list.append(mpl.vmin)
                max_list.append(mpl.vmax)

        # if at least two selected
        if min_list.__len__() >= 1:
            min_all = np.nanmin(min_list)
            max_all = np.nanmax(max_list)

        for key, mpl in self.mpls.iteritems():
            if mpl.Selected.GetValue():
                mpl.transform_color_scale(min_all, max_all)
                if mpl.pid == 0:  # if used change colormap of appropriate panel
                    self.panel_master.mpl.transform_color_scale(min_all, max_all)
                    mpl.set_cmap('gray')  # if used, set thumbnail color to gray
                if mpl.pid == 1:
                    self.panel_source.mpl.transform_color_scale(min_all, max_all)
                    mpl.set_cmap('gray')  # if used, set thumbnail color to gray
            else:
                mpl.revert_color_scale()
                if mpl.pid == 0:  # if used change colormap of appropriate panel
                    self.panel_master.mpl.revert_color_scale()
                    mpl.set_cmap('gray')  # if used, set thumbnail color to gray
                if mpl.pid == 1:
                    self.panel_source.mpl.revert_color_scale()
                    mpl.set_cmap('gray')  # if used, set thumbnail color to gray

    # calculate and export statistics
    def on_statistics(self, event):

        #check whether there are any loaded images
        if len(self.mpls) == 0:
            self.status_bar.SetStatusText('Nothing to save.')
            wx.Yield()
            return

        checkbox_selected =False
        #check whether the images are selected
        for key, mpl in self.mpls.iteritems():
            if mpl.Selected.GetValue():
                checkbox_selected = True
                break

        if  not checkbox_selected:
            self.status_bar.SetStatusText("No image selected.")
            return


        if self.ssavefilehistory.GetCount() == 0:
            last_path = ""
        else:
            last_path = self.ssavefilehistory.GetHistoryFile(0)

        savefiledialog = wx.FileDialog(self, "Save file", last_path, "", self.print_file_filter, wx.FD_SAVE)

        if savefiledialog.ShowModal() != wx.ID_CANCEL:

            processbar = wx.ProgressDialog("Saving", "Please wait...", maximum=100, parent=self.GrandParent, style=wx.PD_APP_MODAL)

            # go through all registered prints and calculate statistics
            T_all = []
            mn, mx = np.empty((0, 2)), np.empty((0, 2))

            for key, mpl in self.mpls.iteritems():
                if mpl.A is not None and mpl.Selected.GetValue():
                    (xyzi, T) = self.transform(mpl.xyzi, mpl.A)
                    T_all.append(T)
                    mn = np.vstack((mn, np.min(T[:, 0:2], axis=0)))
                    mx = np.vstack((mx, np.max(T[:, 0:2], axis=0)))

                    precision = mpl.precision
                    scale = mpl.multiplier

            mn, mx = np.max(mn, axis=0), np.min(mx, axis=0)

            self.status_bar.SetStatusText('Processing %d print(s) using %d CPU core(s). Please wait...' % (len(T_all), min(len(T_all), multiprocessing.cpu_count())))
            wx.Yield()

            processbar.Update(30, "Interpolating...")

            # TODO: fix precision, at the moment the last mpl's value used!
            result = run_job(T_all, Worker(mn, mx, precision))
            print("WARNING, fix precision, at the moment the last mpl's value used!")

            processbar.Update(99, "Saving...")
            sleep(0.5)
            processbar.Destroy()

            X, Y = np.hstack(result[0][0]), np.hstack(result[0][1])
            Z = np.empty((0, result[0][2].size))
            for r in result:
                Z = np.vstack((Z, np.hstack(r[2])))

            mask = ~np.any(np.isnan(Z), axis=0)

            path = savefiledialog.GetPath()
            fname, ext = os.path.splitext(path)

            self.status_bar.SetStatusText('Saving files...')
            wx.Yield()

            stat_names = ['mean', 'median', 'std', 'min', 'max', 'ptp', 'var_outlier_2sd','var_outlier_3sd']
            for name in stat_names:

                if name == 'var_outlier_2sd':
                    stat_vals = self.variance_outliers(2, Z[:, mask])
                elif name == 'var_outlier_3sd':
                    stat_vals = self.variance_outliers(3, Z[:, mask])
                else:
                    cmd = 'stat_vals = np.' + name + '(Z[:, mask], axis=0)'
                    exec (cmd)
                data = np.transpose(np.vstack((X[mask], Y[mask], stat_vals)))
                np.savetxt(fname + '_' + name + ext, data, delimiter=",", fmt=['%0.2f', '%0.2f', '%0.3f'], header='X,Y,Z', comments='')

                #save mean information
                if name == 'mean':
                    cmd = 'mean_Z = np.' + name + '(Z, axis=0)'
                    exec (cmd)
                    xyz=np.vstack((X, Y, mean_Z))
                    xyz=xyz.transpose()
                    xyzi_xx = result[0][0]
                    xyzi_yy = result[0][1]
                    xyzi_zz = np.reshape(mean_Z, (result[0][0].shape[0], result[0][0].shape[1]))
                    xyzi_x = X
                    xyzi_y = Y

                    xyzi = (xyzi_xx, xyzi_yy, xyzi_zz, xyzi_x, xyzi_y)

                    xyz, xyzi = self.Parent.Parent.normalize_z_axis(xyz, xyzi, np.nanmin(xyzi[2]))

                    mpl = MatplotPanel(self.panel_thumbs, xyzi, xyz, scale, precision, title=os.path.basename(fname),
                                       fname=fname)
                    mpl.data = wx.TextDataObject(str(mpl.fig.canvas.GetId()))
                    mpl.button_press_event = mpl.fig.canvas.mpl_connect('button_press_event',
                                                                        self.Parent.Parent.on_drag)
                    mpl.motion_notify_event = mpl.fig.canvas.mpl_connect('motion_notify_event',
                                                                         self.Parent.Parent.on_mouseover)
                    mpl.figure_leave_event = mpl.fig.canvas.mpl_connect('figure_leave_event',
                                                                        self.Parent.Parent.on_figureleave)
                    self.mpls[mpl.fig.canvas.GetId()] = mpl
                    self.sizer_thumbs.Add(mpl, 0, wx.EXPAND | wx.ALL, 5)

                    self.status_bar.SetStatusText("Mean loaded. Size:" + ' ' + mpl.real_size_string())
                    self.panel_thumbs.SendSizeEvent()


                # save number of images used for stats calculation
                #np.savetxt(fname + '_num.txt', result[0][2].size)

                # <------keep file history -----------
                if IS_MAC:  # identify the path separator based on the used system
                    index = path.rfind('/')
                elif IS_WIN:
                    index = path.rfind('\\')
                path = path[:index]
                self.ssavefilehistory.AddFileToHistory(path)
                self.ssavefilehistory.Save(self.config_ssavefile)
                # ----------------------------------->
                self.status_bar.SetStatusText('Files saved.')
                wx.Yield()

    # variance outliers identification
    def variance_outliers(self, mult, data):
        var = np.var(data, axis=0)
        mean = np.mean(var)
        sd = np.std(var)

        u = np.where( var > mean + mult * sd )
        u = np.hstack((u, np.where( var < mean - mult * sd )))

        out=var
        out[u]=0
        mask = np.ones(len(out), np.bool)
        mask[u] = 0
        out[mask]=1

        return out

    # ttest of two mean prints - they must be dragged to the master and source panels
    def on_ttest(self, event):
        if not (hasattr(self.frame.panel_master, 'mpl') and hasattr(self.frame.panel_master, 'mpl')):
            self.status_bar.SetStatusText('Please load two mean prints generated by DigTrace to be compared in master and source panels.')
            return

        fname_master, ext_master = os.path.splitext(self.frame.panel_master.mpl.fname)
        fname_source, ext_source = os.path.splitext(self.frame.panel_source.mpl.fname)

        filetype_master = fname_master['_':]
        filetype_source = fname_source['_':]

        std_master_path = os.path.join(fname_master[:'_'], '_std', ext_master)
        std_source_path = os.path.join(fname_source[:'_'], '_std', ext_source)

        if not (filetype_master=='mean' and filetype_source=='mean'):
            self.status_bar.SetStatusText('Please load two mean prints generated by DigTrace to be compared in master and source panels.')
            return

        if not (os.path.isfile(std_master_path) and os.path.isfile(std_source_path)):
            self.status_bar.SetStatusText('Please make sure that the standard deviation files are in the same folder with respective means')
            return

        num_master_path = os.path.join(fname_master[:'_'], '_num.txt', ext_master)
        num_source_path = os.path.join(fname_source[:'_'], '_num.txt', ext_source)

        if not (os.path.isfile(num_master_path) and os.path.isfile(num_source_path)):
            self.status_bar.SetStatusText('Please make sure that the num files are in the same folder with respective means')
            return

        savefiledialog = wx.FileDialog(self, "Save file", "", "", self.print_file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if savefiledialog.ShowModal() != wx.ID_CANCEL:
            path = savefiledialog.GetPath()
            fname, ext = os.path.splitext(path)

            std_master = np.loadtxt(std_master_path)
            std_master = std_master[:,2]
            std_source = np.loadtxt(std_source_path)
            std_source = std_source[:, 2]

            n_master = np.loadtxt(num_master_path)
            n_source = np.loadtxt(num_source_path)

            mean_master = self.frame.panel_master.mpl.xyz[:,2]
            mean_source = self.frame.panel_source.mpl.xyz[:, 2]

            delta_std = np.sqrt(np.square(std_master)/n_master + np.square(std_source)/n_source)
            t = (mean_master-mean_source)/delta_std  # t-statistic
            df = n_master + n_source - 2  # degrees of freedom
            p = 1 - stats.t.cdf(t, df=df)   # p-value
            p = p * 2  # 2-sided p-value

            # 5% significance
            u = np.where(p > 1.96)
            out5 = p
            out5[u] = 0
            mask = np.ones(len(out5), np.bool)
            mask[u] = 0
            out5[mask] = 1

            data = np.transpose(np.vstack((self.frame.panel_source.mpl.xyz[:, 0], self.frame.panel_source.mpl.xyz[:, 1], out5)))
            np.savetxt(fname + '_5' + ext, data, delimiter=",", fmt=['%0.2f', '%0.2f', '%0.3f'], header='X,Y,0.05 not significant',
                       comments='')

            # 1% significance
            u = np.where(p > 2.33)
            out1 = p
            out1[u] = 0
            mask = np.ones(len(out1), np.bool)
            mask[u] = 0
            out1[mask] = 1

            data = np.transpose(
            np.vstack((self.frame.panel_source.mpl.xyz[:, 0], self.frame.panel_source.mpl.xyz[:, 1], out1)))
            np.savetxt(fname + '_1' + ext, data, delimiter=",", fmt=['%0.2f', '%0.2f', '%0.3f'],
                   header='X,Y,0.05 not significant',
                   comments='')


    # save contours
    def on_save_contour(self, event):

            if hasattr(self, 'cntrpanel') and hasattr(self.cntrpanel, 'Tsav'):
                file_filter = self.image_file_filter

                if self.csavefilehistory.GetCount() == 0:
                    last_path = ""
                else:
                    last_path = self.csavefilehistory.GetHistoryFile(0)

                savefiledialog = wx.FileDialog(self, "Save file", last_path, "", file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

                if savefiledialog.ShowModal() != wx.ID_CANCEL:
                    fname = savefiledialog.GetPath()

                    # save contour
                    self.status_bar.SetStatusText('Saving contour...')
                    wx.Yield()
                    self.cntrpanel.fig.savefig(fname)
                    # <------keep file history -----------
                    if IS_MAC:  # identify the path separator based on the used system
                        index = fname.rfind('/')
                    elif IS_WIN:
                        index = fname.rfind('\\')
                    path = fname[:index]
                    self.csavefilehistory.AddFileToHistory(path)
                    self.csavefilehistory.Save(self.config_csavefile)
                    # ----------------------------------->
                    self.status_bar.SetStatusText('File saved.')
                    wx.Yield()

            else:
                self.status_bar.SetStatusText('Nothing to save.')
                wx.Yield()

            #savefiledialog = wx.FileDialog(self, "Save file", "", "", file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            #if savefiledialog.ShowModal() != wx.ID_CANCEL:


    # save project
    def on_save(self, event):

        if len(self.mpls) > 0:

            if hasattr(self, 'cntrpanel') and hasattr(self.cntrpanel, 'Tsav'):
                file_filter = self.all_file_filter
            else:
                file_filter = self.project_file_filter

            if self.psavefilehistory.GetCount() == 0:
                last_path = ""
            else:
                last_path = self.psavefilehistory.GetHistoryFile(0)

            savefiledialog = wx.FileDialog(self, "Save file", last_path, "", file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if savefiledialog.ShowModal() != wx.ID_CANCEL:

                path = savefiledialog.GetPath()
                fname, ext = os.path.splitext(path)

                # save project
                if ext.lower() == '.ftproj':
                    self.status_bar.SetStatusText('Saving project...')
                    wx.Yield()

                    project = list()
                    for mpl in self.mpls:
                        fname = self.mpls[mpl].fname

                        A = self.mpls[mpl].A
                        if A is not None:
                            A = A.tolist()

                        lmark_xy = self.mpls[mpl].lmark_xy
                        if lmark_xy is not None:
                            # self.q.put((fname, lmark_xy))
                            lmark_xy = lmark_xy.tolist()

                        entry = {'fname': os.path.basename(fname), 'lmark_xy': lmark_xy, 'A': A}
                        project.append(entry)

                    with open(savefiledialog.GetPath(), 'wb') as fp:
                        json.dump(project, fp)

                    # <------keep file history -----------

                    if IS_MAC:  # identify the path separator based on the used system
                        index = path.rfind('/')
                    elif IS_WIN:
                        index = path.rfind('\\')
                    path = path[:index]
                    self.psavefilehistory.AddFileToHistory(path)
                    self.psavefilehistory.Save(self.config_psavefile)

                    # ----------------------------------->
                    self.status_bar.SetStatusText('Project saved.')
                    wx.Yield()

                # export current print
                else:
                    self.status_bar.SetStatusText('Saving print...')
                    wx.Yield()

                    lm_master = self.lmark_xy[0]
                    lm_source = self.lmark_xy[1]
                    hdr = {
                        'master': {'name': self.panel_master.mpl.title, 'landmarks': lm_master.tolist()},
                        'source': {'name': self.panel_source.mpl.title, 'landmarks': lm_source.tolist()},
                        'transformation': self.toolbar.choice.GetSelection(),
                        'version': app_name
                    }

                    np.savetxt(savefiledialog.GetPath(), self.cntrpanel.Tsav, delimiter=",", header=json.dumps(hdr), fmt='%0.2f')
                    self.status_bar.SetStatusText('File saved.')
                    wx.Yield()

                    if UploadDialog(self).ShowDialog() == 1:
                        print("commented out")
                        #self.q.put((self.panel_master.mpl.fname, self.panel_source.mpl.fname, lm_master.copy(), lm_source.copy()))

        else:
            self.status_bar.SetStatusText('Nothing to save.')
            wx.Yield()

    # register the print (store landmarks)
    def on_apply(self, event):
        if hasattr(self, 'cntrpanel') and hasattr(self.cntrpanel, 'Tsav'):

            # if UploadDialog(self).ShowDialog() == 1:
            #     self.q.put((self.panel_master.mpl.fname, self.panel_source.mpl.fname, self.lmark_xy[0].copy(), self.lmark_xy[1].copy()))

            self.panel_master.mpl.mpl_src.lmark_xy = self.lmark_xy[0].copy()
            self.panel_master.mpl.mpl_src.A = np.vstack((np.eye(2), np.zeros((1, 2))))

            self.panel_source.mpl.mpl_src.lmark_xy = self.lmark_xy[1].copy()
            self.panel_source.mpl.mpl_src.A = self.A

            # self.panel_source.mpl.mpl_src.master_lmark_xy = self.lmark_xy[0].copy()
            # self.panel_source.mpl.mpl_src.master_fname = self.panel_master.mpl.mpl_src.fname
            # self.panel_source.mpl.mpl_src.geom_lmarks = [self.cbgeom2.IsChecked(), self.cbgeom3.IsChecked(), self.cbgeom4.IsChecked()]
            # self.panel_source.mpl.mpl_src.transformation = self.choice.GetSelection()

            self.panel_master.mpl.mpl_src.redraw()
            self.panel_source.mpl.mpl_src.redraw()

            #enable icon
            self.toolbar.EnableTool(wx.ID_SAVEAS, True)

    # toggle quick measure - untoggles place landmarks if it was toggled
    def on_toggle_quick_measure(self, event):
        self.toolbar.ToggleTool(wx.ID_ADD, False)

    #toggle place landmarks - untoggles quck measure if it was toggled
    def on_toggle_place_lmarks(self, event):
        self.toolbar.ToggleTool(wx.ID_FILE9, False)

    # delete all landmark in the source plot
    def on_clear_lmarks(self, event):
        # self.lmark_xy[0] = np.empty([self.lmark_xy[0].shape[0], 2])
        # self.lmark_xy[1] = np.empty([self.lmark_xy[1].shape[0], 2])

        self.toolbar.EnableTool(wx.ID_REMOVE, False)

        if hasattr(self.panel_master, 'mpl'):
            for h in self.lmark_h[0]:
                if h is not None:
                    h.remove()
            #self.lmark_h[0] = [h.remove() for h in self.lmark_h[0]]
            self.panel_master.mpl.ax.figure.canvas.draw()
        if hasattr(self.panel_source, 'mpl'):
            #self.lmark_h[1] = [h.remove() for h in self.lmark_h[1]]
            for h in self.lmark_h[1]:
                if h is not None:
                    h.remove()
            self.panel_source.mpl.ax.figure.canvas.draw()

        self.lmark_active = None
        self.lmark_h = [list(), list()]  # two element (master and source panels) list of lists for landmark handles
        self.lmark_xy = [np.empty([0, 2]), np.empty([0, 2])]  # two element (master and source panels) list of arrays for landmark coordintaes


    def get_precision(self):
            choice = self.toolbar.choicePrec.GetSelection()
            if choice == 0:
                return 0.25
            elif choice == 1:
                return 0.50
            elif choice == 2:
                return 1.00

    def get_multiplier(self):
        choice = self.toolbar.choiceMult.GetSelection()
        return pow(10, choice)

    def on_choice(self, event):
        if event.GetId() == self.toolbar.choice.GetId():
            self.contour_refresh()

    def on_forward(self, event):
        self.contour_lines = min(3, self.contour_lines + 1)
        self.contour_refresh()

    def on_backward(self, event):
        self.contour_lines = max(0, self.contour_lines - 1)
        self.contour_refresh()

    def on_change_colormap(self, event):
        if hasattr(self.panel_master, 'mpl'):
            self.panel_master.mpl.set_cmap(event.String)
        if hasattr(self.panel_source, 'mpl'):
            self.panel_source.mpl.set_cmap(event.String)

    def on_open(self, event, folder_history=None):
        if self.openfilehistory.GetCount() == 0:
            last_path = ""
        else:
            if folder_history == None:
                last_path = self.openfilehistory.GetHistoryFile(0)
            else:
                last_path = self.openfilehistory.GetHistoryFile(folder_history)

        openfiledialog = wx.FileDialog(self, "Open files", last_path, "", self.all_file_filter, wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST)

        if openfiledialog.ShowModal() != wx.ID_CANCEL:

            # replace all .ftproj files with .csv/.asc files (remove duplicates!)
            paths = openfiledialog.GetPaths()

            paths_dict = collections.OrderedDict()
            for path in paths:
                fname, ext = os.path.splitext(path)

                if ext.lower() != '.ftproj':
                    if not paths_dict.has_key(path):
                        paths_dict[path] = (None, None)

                # parse the project structure
                else:
                    with open(path, 'r') as fp:
                        project = json.load(fp)

                    dirname = os.path.dirname(path)
                    for item in project:
                        A = None
                        if item['A'] is not None:
                            A = np.array(item['A'])

                        lmark_xy = None
                        if item['lmark_xy'] is not None:
                            lmark_xy = np.array(item['lmark_xy'])

                        key = dirname + os.sep + item['fname']
                        paths_dict[key] = (lmark_xy, A)

            cnt = len(paths_dict)
            cores = multiprocessing.cpu_count()

            # <------keep file history -----------
            path = openfiledialog.GetPath()
            if IS_MAC:  # identify the path separator based on the used system
                index = path.rfind('/')
            elif IS_WIN:
                index = path.rfind('\\')
            path = path[:index]
            self.openfilehistory.AddFileToHistory(path)
            self.openfilehistory.Save(self.config_openfile)
            # ----------------------------------->

            #file opening options
            open_otions_dialog = OpenOptionsDialog(None)
            open_otions_dialog.ShowModal()

            if not open_otions_dialog.ok: #  if OK was not clicked abort the operation
                return

            precision = open_otions_dialog.precision
            scale = open_otions_dialog.scale

            self.status_bar.SetStatusText('Loading %d print(s) using %d CPU core(s). Please wait...' % (cnt, min(cnt, cores)))
            wx.Yield()

            import time

            print('Load and interpolate of %d files' % cnt)
            start_time = time.time()
            result = run_job(paths_dict.keys(), Loader(precision, scale))

            ch = self.sizer_thumbs.GetChildren()
            if len(ch) == 1 and type(ch[0].GetWindow()) is wx.StaticText:
                self.sizer_thumbs.Clear(True)

            not_loaded = ''
            loaded = 0
            sizes = ''
            for xyzi, xyz, fname, guessed_multiplier in result:
                if xyzi is None:
                    not_loaded = not_loaded + os.path.basename(fname) + ', '

                else:
                    loaded += 1

                    # 'normalize' z axis: min(z)=0
                    xyz, xyzi = self.Parent.Parent.normalize_z_axis(xyz, xyzi, np.nanmin(xyzi[2]))

                    mpl = MatplotPanel(self.panel_thumbs, xyzi, xyz, scale, precision, title=os.path.basename(fname), fname=fname, lmark_xy=paths_dict[fname][0], A=paths_dict[fname][1])
                    mpl.data = wx.TextDataObject(str(mpl.fig.canvas.GetId()))
                    mpl.button_press_event = mpl.fig.canvas.mpl_connect('button_press_event', self.Parent.Parent.on_drag)
                    mpl.motion_notify_event = mpl.fig.canvas.mpl_connect('motion_notify_event', self.Parent.Parent.on_mouseover)
                    mpl.figure_leave_event = mpl.fig.canvas.mpl_connect('figure_leave_event', self.Parent.Parent.on_figureleave)
                    self.mpls[mpl.fig.canvas.GetId()] = mpl
                    self.sizer_thumbs.Add(mpl, 0, wx.EXPAND | wx.ALL, 5)

                    sizes = sizes + mpl.real_size_string() + '; '

            print('Elapsed time %f seconds' % (time.time() - start_time))

            self.panel_thumbs.SendSizeEvent()
            msg = '%d print(s) loaded.' % loaded
            if len(not_loaded) > 0:
                msg = msg + ' ' + not_loaded[0:len(not_loaded) - 2] + ' not loaded!'
            self.status_bar.SetStatusText(msg + ' ' + sizes)
            wx.Yield()

    def interp(self, l_in):
        l_in = l_in.astype(float)
        l_out = np.zeros(shape=(2 * len(l_in) + 1, 1), dtype=float)
        l_out[0] = l_in[0] - (l_in[1] - l_in[0]) / 2

        for i in range(len(l_in) - 1):
            l_out[1 + 2 * i] = l_in[i]
            l_out[2 + 2 * i] = (l_in[i] + l_in[i + 1]) / 2

        l_out[-2] = l_in[-1]
        l_out[-1] = l_in[-1] + (l_in[-1] - l_in[-2]) / 2

        l_out = np.squeeze(np.asarray(l_out))

        return l_out

    def contour_refresh(self):

        if hasattr(self.panel_master, 'mpl') and hasattr(self.panel_source, 'mpl'):
            lm_master = self.lmark_xy[0]
            lm_source = self.lmark_xy[1]

            nan_mask = ~np.isnan(lm_source[:, 0])

            if np.sum(nan_mask) > 2 and lm_source.shape[0] == lm_master.shape[0]:

                # geometric landmarks
                lm_master_g = np.empty([0, 2])
                lm_source_g = np.empty([0, 2])

                if self.toolbar.cbgeom2.IsChecked():
                    for val in itertools.combinations(np.arange(0, lm_master.shape[0], 1), 2):
                        lm_master_g = np.vstack((lm_master_g, lm_master[val, :].mean(axis=0, keepdims=True)))
                        lm_source_g = np.vstack((lm_source_g, lm_source[val, :].mean(axis=0, keepdims=True)))

                if self.toolbar.cbgeom3.IsChecked():
                    for val in itertools.combinations(np.arange(0, lm_master.shape[0], 1), 3):
                        lm_master_g = np.vstack((lm_master_g, lm_master[val, :].mean(axis=0, keepdims=True)))
                        lm_source_g = np.vstack((lm_source_g, lm_source[val, :].mean(axis=0, keepdims=True)))

                if self.toolbar.cbgeom4.IsChecked():
                    for val in itertools.combinations(np.arange(0, lm_master.shape[0], 1), 4):
                        lm_master_g = np.vstack((lm_master_g, lm_master[val, :].mean(axis=0, keepdims=True)))
                        lm_source_g = np.vstack((lm_source_g, lm_source[val, :].mean(axis=0, keepdims=True)))

                # transform landmark coordinates (0..X, 0..Y) to interpolated coordinates
                xm = self.panel_master.mpl.xyzi[3]
                ym = self.panel_master.mpl.xyzi[4]
                z = self.panel_master.mpl.xyzi[2]
                Y = lm_master[nan_mask, :].astype(int)
                levels1 = z[Y[:, 1], Y[:, 0]]
                Y = np.vstack((Y, lm_master_g.astype(int)))
                Y = np.hstack((xm[Y[:, 0], None], ym[Y[:, 1], None]))

                xm = self.panel_source.mpl.xyzi[3]
                ym = self.panel_source.mpl.xyzi[4]
                z = self.panel_source.mpl.xyzi[2]
                X = lm_source[nan_mask, :].astype(int)
                levels2 = z[X[:, 1], X[:, 0]]
                X = np.vstack((X, lm_source_g.astype(int)))
                X = np.hstack((xm[X[:, 0], None], ym[X[:, 1], None], np.ones((X.shape[0], 1))))

                for i in range(self.contour_lines):
                    levels1 = self.interp(levels1)
                    levels2 = self.interp(levels2)

                # build a regression model to find optimal (in the MSE sense) linear transformation S->T
                if self.toolbar.choice.GetSelection() == 0:

                    centrX, centrY = np.zeros((1, 3)), np.zeros((1, 3))
                    A = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(X), X)), np.transpose(X)), Y)

                # rigid transformation https://github.com/charnley/rmsd
                else:

                    # theta = np.arctan((np.dot(X[:, 0], Y[:, 1]) - np.dot(X[:, 1], Y[:, 0])) / (np.dot(X[:, 0], Y[:, 0]) + np.dot(X[:, 1], Y[:, 1])))
                    # A = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])

                    # optimal translation - move center of gravity to the origin
                    centrX = X[:, 0:2].mean(axis=0, keepdims=True)
                    centrY = Y.mean(axis=0, keepdims=True)

                    C = np.dot(np.transpose(X[:, 0:2] - centrX), Y - centrY)
                    V, S, W = np.linalg.svd(C)
                    VW = np.dot(V, W)
                    A = np.vstack((VW, centrY - np.dot(centrX, VW)))

                self.A = A

                (xyzi, Tsav) = self.transform(self.panel_source.mpl.xyzi, A)
                err = np.sqrt((((Y[0:np.sum(nan_mask), :] - np.dot(X[0:np.sum(nan_mask), :], A)) ** 2).sum(axis=1).mean()))

                # testing the correlation error measure
                # need to interpolate one of the images so they have the same dimensions
                #TODO: commented this out now until better options is found

                # mn, mx = self.panel_master.mpl.xyz.min(axis=0), self.panel_master.mpl.xyz.max(axis=0)
                #
                # res = lp.interpolate(Tsav, mn=mn, mx=mx,
                #                      precision=self.panel_source.mpl.precision)
                #
                # uuu = np.transpose(np.vstack((self.panel_master.mpl.xyzi[2].flatten(), res[2].flatten())))
                # pduuu = pd.DataFrame(uuu, columns=list('AB'))
                # corr = pduuu.corr()

                # self.status_bar.SetStatusText("Correlation between images: " + str(corr.ix[0, 1]))


                self.cntrpanel = ContourPanel(self.panel_overlay, self.panel_master.mpl.xyzi, xyzi, levels1, levels2,
                                              Tsav)

                sizer = self.panel_overlay.GetSizer()
                # sizer = self.sizer_overlay
                sizer.Clear(True)

                # add plot title to the sizer
                #txt = wx.StaticText(self.panel_overlay, wx.ID_ANY,
                #                    "Error: %0.4f; Correlation: %0.4f " % (err, corr.ix[0, 1]), style=wx.ALIGN_CENTER)
                txt = wx.StaticText(self.panel_overlay, wx.ID_ANY,
                                    "Error: %0.4f" %err, style = wx.ALIGN_CENTER)
                txt.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
                txt.SetForegroundColour((128, 128, 128))
                self.sizer_overlay.Add(txt, flag=wx.CENTER)

                sizer.Add(self.cntrpanel, 1, wx.EXPAND | wx.ALL, 5)
                self.panel_overlay.SendSizeEvent()

                #enable icons
                self.toolbar.EnableTool(wx.ID_BACKWARD, True)
                self.toolbar.EnableTool(wx.ID_FORWARD, True)
                self.toolbar.EnableTool(wx.ID_APPLY, True)

    def reset(self):
        # clear all panels
        if hasattr(self.panel_master, 'mpl') and isinstance(self.panel_master.mpl, MatplotPanel):
            self.panel_master.mpl.delete_figure()
            del self.panel_master.mpl
        self.sizer_master.Clear(True)

        if hasattr(self.panel_source, 'mpl') and isinstance(self.panel_source.mpl, MatplotPanel):
            self.panel_source.mpl.delete_figure()
            del self.panel_source.mpl
        self.sizer_source.Clear(True)

        if hasattr(self, 'cntrpanel') and isinstance(self.cntrpanel, ContourPanel):
            self.panel_overlay.Children[0].delete_figure()
        self.sizer_overlay.Clear(True)

        # clear bottom thumbs/ project library
        # for idx, mpl in reversed(list(enumerate(self.GrandParent.prints))):
        #     # refer to MainFrame on_drag right-click
        #     if isinstance(self.GrandParent.prints[mpl], MatplotPanel):
        #         self.GrandParent.prints[mpl].delete_figure()
        #         # mpl.fig.canvas.mpl_disconnect(mpl.button_press_event)
        #         # mpl.fig.canvas.mpl_disconnect(mpl.button_release_event)
        #
        #         # remove item from the sizer
        #         id = self.GrandParent.prints.keys()[idx]
        #         # item = self.sizer_thumbs.GetItem(idx)
        #         self.sizer_thumbs.Hide(idx)
        #         self.sizer_thumbs.Remove(idx)
        #         # item.DeleteWindows()
        #
        #         # remove panel from the dictionary
        #         del (self.GrandParent.prints[id])
        #         self.GrandParent.prints.popitem(id)
        while len(self.GrandParent.prints) > 0:
            self.GrandParent.prints.popitem()

        # force redraw everything
        self.sizer_thumbs.Layout()
        self.panel_thumbs.SendSizeEvent()
        self.Refresh()
        self.sizer_thumbs.Clear(True)


        self.refresh_flag = True


        txt_drag = u"Drag a print here"
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)

        txt = wx.StaticText(self.panel_master, wx.ID_ANY, txt_drag, style=wx.ALIGN_CENTER)
        txt.SetFont(font)
        txt.SetForegroundColour((128, 128, 128))
        self.sizer_master.Add(txt, 1, flag=wx.CENTER)

        txt = wx.StaticText(self.panel_source, wx.ID_ANY, txt_drag, style=wx.ALIGN_CENTER)
        txt.SetFont(font)
        txt.SetForegroundColour((128, 128, 128))
        self.sizer_source.Add(txt, 1, flag=wx.CENTER)

        # landmark coordinates etc.
        self.lmark_active = None  # index of active/selected landmark
        self.lmark_hlight = None  # index of highlighted landmark (mouse-over)
        self.lmark_h = [list(), list()]  # two element (master and source panels) list of lists for landmark handles
        self.lmark_xy = [np.empty([0, 2]), np.empty([0, 2])]  # two element (master and source panels) list of arrays for landmark coordintaes
        self.contour_lines = 0
        self.A = None
        #self.mpls = collections.OrderedDict()

        self.dragLine = None
        self.startDragPos = [0, 0]

        self.toolbar.init_tool_states()


class Worker(object):
    def __init__(self, mn, mx, precision):
        self.mn, self.mx = mn, mx
        self.precision = precision

    def __call__(self, data):

        res = lp.interpolate(data, mn=self.mn, mx=self.mx, precision=self.precision)
        return res

# run parallel job
def run_job(items, obj):
    cnt = len(items)
    cores = multiprocessing.cpu_count()

    if cnt > 1 and cores > 1:
        print('Using multiprocess')
        pool = multiprocessing.Pool(processes=min(cnt, cores))
        result = pool.map(obj, items)
        pool.close()
    else:
        print('Using single process')
        result = list()
        for item in items:
            result.append(obj.__call__(item))
    return result

class TransformerToolbar(wx.ToolBar):
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent=parent, id=wx.ID_ANY)
        self.AddLabelTool(wx.ID_OPEN, 'Import files...', wx.Bitmap('icons\\import.png'), shortHelp="Import files...", longHelp="Import files...")
        #self.AddLabelTool(wx.ID_SAVE, 'Save', wx.Bitmap('icons\\save.png'), shortHelp="Save", longHelp="Save")
        self.AddLabelTool(wx.ID_SAVEAS, 'Export statistics', wx.Bitmap('icons\\report.png'), shortHelp="Export statistics", longHelp="Export statistics")
        self.ID_TTEST = wx.NewId()
        #self.AddLabelTool(self.ID_TTEST, 'Export statistics', wx.Bitmap('icons\\report.png'), shortHelp="Export statistics", longHelp="Export statistics")


        if platform.system().lower() == 'windows': self.AddSeparator()
        sep_size = (2, self.Size[1])
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        #if platform.system().lower() == 'windows': self.AddSeparator()
        self.AddCheckLabelTool(wx.ID_ADD, 'Place landmarks', wx.Bitmap('icons\\place-landmark.png'), shortHelp="Toggle landmark placing mode", longHelp="Toggle landmark placing mode")
        self.AddLabelTool(wx.ID_REMOVE, 'Clear landmarks', wx.Bitmap('icons\\delete-all-landmarks.png'), shortHelp="Clear landmarks", longHelp="Clear landmarks")

        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        self.AddCheckLabelTool(wx.ID_FILE9, 'Quick measure', wx.Bitmap('icons\\quick-measure.png'), shortHelp="Quick measure", longHelp="Quick measure")
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))

        self.AddLabelTool(wx.ID_BACKWARD, 'Remove contour line', wx.Bitmap('icons\\reduce-contours.png'), shortHelp="Remove contour line", longHelp="Remove contour line")
        self.AddLabelTool(wx.ID_FORWARD, 'Add contour line', wx.Bitmap('icons\\increase-contours.png'), shortHelp="Add contour line", longHelp="Add contour line")

        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        self.AddLabelTool(wx.ID_CONVERT, 'Color scale transformation', wx.Bitmap('icons\\joint-contour-scales.png'), shortHelp="Switch between independent/joint colorscales. Checked footprints will be brought to the joint scale, unchecked will remain independent", longHelp="Switch between independent/joint colorscales. Checked footprints will be brought to the joint scale, unchecked will remain independent")
        self.AddLabelTool(wx.ID_SELECTALL, 'Select/deselect all', wx.Bitmap('icons\\select-all.png'), shortHelp="Select/deselect all", longHelp="Select/deselect all")

        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        if platform.system().lower() == 'windows': self.AddSeparator()
        self.choice = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["Affine transformation", "Rigid transformation"])
        self.choice.SetSelection(1)
        self.AddControl(self.choice)
        self.AddLabelTool(wx.ID_APPLY, 'Register print', wx.Bitmap('icons\\register-aligned-track.png'), shortHelp="Register print", longHelp="Register print")

        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        if platform.system().lower() == 'windows': self.AddSeparator()
        #self.AddControl(wx.StaticText(self, wx.ID_ANY, 'Geometric\nlandmarks: '))
        u = self.AddLabelTool(wx.ID_ANY, 'Geometrical landmarks', wx.Bitmap('icons\\geometrical-landmarks.png'), shortHelp="Geometrical landmarks", longHelp="Geometrical landmarks")
        u.SetDisabledBitmap(wx.Bitmap('icons\\geometrical-landmarks.png'))
        u.Enable(False)
        self.cbgeom2 = wx.CheckBox(self, wx.ID_ANY, 'Line')
        self.AddControl(self.cbgeom2)
        self.cbgeom3 = wx.CheckBox(self, wx.ID_ANY, 'Triangle')
        self.AddControl(self.cbgeom3)
        self.cbgeom4 = wx.CheckBox(self, wx.ID_ANY, 'Square')
        self.AddControl(self.cbgeom4)

        if platform.system().lower() == 'windows': self.AddSeparator()
        if platform.system().lower() == 'windows': self.AddSeparator()
        if platform.system().lower() == 'windows': self.AddSeparator()

        u = self.AddLabelTool(wx.ID_ANY, 'Color map', wx.Bitmap('icons\\colour-ramp.png'), shortHelp="Color map", longHelp="Color map")
        u.SetDisabledBitmap(wx.Bitmap('icons\\colour-ramp.png'))
        u.Enable(False)

        self.choiceCm = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["jet", "terrain",
                                                                          "bone", "copper",
                                                                          "gray", "hot", "Greys"])
        self.choiceCm.SetSelection(0)
        self.AddControl(self.choiceCm, label="Colormap")

        self.init_tool_states()

    def init_tool_states(self):
        #all the buttons except Open are disabled at the start
        self.EnableTool(wx.ID_SAVEAS, False)
        self.EnableTool(wx.ID_ADD, False)
        self.EnableTool(wx.ID_REMOVE, False)

        self.EnableTool(wx.ID_FILE9, False)
        self.EnableTool(wx.ID_BACKWARD, False)
        self.EnableTool(wx.ID_FORWARD, False)
        self.EnableTool(wx.ID_APPLY, False)


    # scale image, needed for menu item
    def scale_bitmap(self, bitmap, width, height):
        image = wx.ImageFromBitmap(bitmap)
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.BitmapFromImage(image)
        return result





