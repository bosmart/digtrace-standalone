__author__ = 'Rachid'
import sys
sys.path.append(".")

import wx

import numpy as np
import collections
import os
import time
import datetime

import xml.etree.ElementTree as ET

class MainNotebook(wx.Notebook):
    def __init__(self, parent):
        from Transformer import Transformer
        from Processor import Processor
        from Photogrammetry import Photogrammetry

        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=
                                wx.BK_DEFAULT)

        self.photogrammetry_panel = Photogrammetry(self)
        self.AddPage(self.photogrammetry_panel, "Create")

        self.processor_panel = Processor(self)
        self.AddPage(self.processor_panel, "Measure")

        self.transformer_panel = Transformer(self)
        self.AddPage(self.transformer_panel, "Compare")





class MainFrame(wx.Frame):
    def __init__(self, parent, pos, size, style, version, proj_path = None):

        #import EnhancedStatusBar as ESB

        self.app_name = u"DigTrace " + version

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=self.app_name, pos=pos,
                          size=size,
                          style=style)

        #set window bar icon
        ico = wx.Icon('icons\\64x64.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(ico)

        #get the available video memory
        self.video_memory = self.get_video_memory()

        #self.q=queue
        from ProjectManager import ProjectManager

        # logging to file
        log_path = os.path.join(os.path.join(os.path.expanduser('~'), "DigTrace"), "log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        # remove log files older than one week
        filelist = [ f for f in os.listdir(log_path) if datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(log_path, f))) > datetime.timedelta(weeks=1)]
        for f in filelist:
            os.remove(os.path.join(log_path, f))

        log_path = os.path.join(log_path, "Log_" + time.strftime('%Y%m%d%H%M%S') + ".txt")
        self.log = open(log_path, "w", 0)
        sys.stdout = self.log
        sys.stderr = self.log

        self.status_bar = self.CreateStatusBar(1, wx.ST_SIZEGRIP, wx.ID_ANY)
        #self.status_bar = ESB.EnhancedStatusBar(self, -1)
        self.SetStatusBar(self.status_bar)

        self.panel_thumbs = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL | wx.SIMPLE_BORDER)
        self.panel_thumbs.SetScrollRate(5, 5)

        self.sizer_thumbs = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_thumbs.SetSizer(self.sizer_thumbs)
        self.sizer_thumbs.Fit(self.panel_thumbs)
        self.panel_thumbs.Layout()
        self.prints = collections.OrderedDict() # collection of prints across all 3 tabs

        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)
        txt = wx.StaticText(self.panel_thumbs, wx.ID_ANY, u"Project Library", style=wx.ALIGN_CENTER)
        txt.SetFont(font)
        txt.SetForegroundColour((128, 128, 128))
        self.sizer_thumbs.Add(txt, 1, flag=wx.CENTER)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = mainToolbar(self)  # project toolbar
        sizer.Add(self.toolbar, 0, wx.EXPAND, 5)

        self.notebook = MainNotebook(self)
        sizer.Add(self.notebook, 5, wx.ALL|wx.EXPAND, 5)

        sizer.Add(self.panel_thumbs, 1, wx.ALL|wx.EXPAND|wx.FIXED_MINSIZE, 5)

        #self.notebook.Bind(wx.EVT_SIZE, self.OnSizeNotebook, self)
        #self.panel_thumbs.Bind(wx.EVT_SIZE, self.OnSizeThumbs, self)


        self.SetSizer(sizer)
        self.Layout()
        self.toolbar.Realize()

        # save the size of Notebook for later resizing
        self.notebook_size = self.notebook.GetSize()

        self.project_manager = ProjectManager(self)
        self.Bind(wx.EVT_TOOL, self.project_manager.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.project_manager.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_TOOL, self.project_manager.on_export, id=self.toolbar.ID_EXPORT)

        #if there is a project given from command line, open it
        if proj_path is not None:
            self.project_manager.open_project(proj_path)

        self.Show()


    # get available video memory
    def get_video_memory(self):
        command = 'wmic path win32_videocontroller get /format:rawxml'
        tree = ET.parse(os.popen(command))
        result = tree.find('./RESULTS/CIM/INSTANCE')
        memory = result.find("PROPERTY/[@NAME='AdapterRAM']/VALUE").text
        return long(memory)

    def fix_size(self):
        self.notebook.SetMaxSize(self.notebook_size)
        self.notebook.SetSize(self.notebook_size)
        self.GetSizer().Layout()
        self.SendSizeEvent()

    # show names of files in the status bar
    def on_mouseover(self, evt):
        id = evt.canvas.GetId()
        if id is None:
            self.status_bar.SetStatusText("")
        else:
            try:
                mpl = self.prints[id]
                self.status_bar.SetStatusText(mpl.fname)
            except:
                print("deleting")

    # empty statusbar when mouse leaves the mini-plot
    def on_figureleave(self, evt):
        self.status_bar.SetStatusText("")

    def on_drag(self, evt):

        id = evt.canvas.GetId()
        mpl = self.prints[id]

        # left-click, beginning of drag and drop operation
        if evt.button == 1:
            try:
                src = wx.DropSource(mpl)
                src.SetData(mpl.data)
                src.DoDragDrop(True)
            except:
                # Catch an error in wxPython on fast click on a drag source:
                # wx._core.PyAssertionError: C++ assertion "Assert failure" failed at ..\..\src\common\wincmn.cpp(3346)
                # in DoNotifyWindowAboutCaptureLost(): window that captured the mouse didn't process wxEVT_MOUSE_CAPTURE_LOST
                pass

        # right-click, delete print if not used
        elif evt.button == 3 and not mpl.used:  # and print not used (grayed out)

            #delete figure
            mpl.delete_figure()

            # disconnect event handler
            mpl.fig.canvas.mpl_disconnect(mpl.button_press_event)

            # remove item from the sizer
            idx = self.prints.keys().index(id)
            item = self.sizer_thumbs.GetItem(idx)
            self.sizer_thumbs.Hide(idx)
            self.sizer_thumbs.Remove(idx)
            # item.DeleteWindows()

            # remove panel from the dictionary
            del (self.prints[id])

            # force redraw everything
            self.sizer_thumbs.Layout()
            self.panel_thumbs.SendSizeEvent()
            self.Refresh()

    #normalizing z axix: selected value becomes 0
    def normalize_z_axis(self, xyz, xyzi, val):
        dif = np.hstack((np.zeros((xyz.shape[0],2)), np.zeros((xyz.shape[0],1))+val))
        xyzi = (xyzi[0], xyzi[1], xyzi[2]-val, xyzi[3], xyzi[4])
        xyz = xyz-dif
        return xyz, xyzi


class mainToolbar(wx.ToolBar):
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent=parent, id=wx.ID_ANY)

        self.AddLabelTool(wx.ID_SAVE, 'Save project', wx.Bitmap('icons\\save.png'), shortHelp="Save project", longHelp="Save project")
        self.AddLabelTool(wx.ID_OPEN, 'Import project', wx.Bitmap('icons\\import.png'), shortHelp="Import project", longHelp="Import project")
        self.ID_EXPORT = wx.NewId()
        self.AddLabelTool(self.ID_EXPORT, 'Export project', wx.Bitmap('icons\\export.png'), shortHelp="Export project", longHelp="Export zipped project for sharing")