__author__ = 'Rashid Bakirov, Esq.'

import wx
import wx.grid as gridlib
import collections
import os
import json
import numpy as np
import multiprocessing
from MatplotPanel import MatplotPanel, MatplotPanel3D
from Loader import Loader
from MayaviPanel import MayaviPanel
import platform
import math
from Tkinter import Tk
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw
import wx.lib.newevent
SelectionChangedEvent, EVT_SELECTION_CHANGED_EVENT = wx.lib.newevent.NewEvent()

import threading
import time

#from wx.lib.pubsub import pub

from mayavi import mlab
import numpy.matlib
import loadPrint
import re
import matplotlib.cm as cm
import copy
#import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects

#from wxAnyThread import anythread

from OpenOptionsDialog import OpenOptionsDialog
from GridOptionsDialog import GridOptionsDialog
import FlattenSurface


IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

LEFT_GAP=9
RIGHT_GAP=55

#TODO listener thread
class queue_listener(threading.Thread):
    """
        A thread class that will listen to the queue and signal the update of the progressbar
    """

    def __init__(self, q, parent):
        self.q = q
        threading.Thread.__init__(self)
        self.parent=parent

    def run(self):
        while True:
            time.sleep(0.5)
            update = self.q.get()
            #print(update)
            #if len(update)==1:
            print(update)
            #wx.CallAfter(pub.sendMessage, "update", msg=str(update))
            self.parent.updateProgress(str(update))
            #wx.GetApp().ProcessPendingEvents()
            #wx.WakeUpIdle()
            #wx.GetApp().ProcessIdle()

            # elif len(update)>1:
            #     for item in update:
            #         wx.CallAfter(pub.sendMessage, "update", msg=str(item))
            #         wx.GetApp().ProcessPendingEvents()


class Processor(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        self.sizer_vert = wx.BoxSizer(wx.VERTICAL)  # main Sizer
        self.toolbar = ProcessorToolbar(self)  # toolbar

        self.sizer_vert.Add(self.toolbar, 1, wx.EXPAND, wx.EXPAND, 5)
        self.toolbar.Realize()

        self.sizer_horiz = wx.BoxSizer(wx.HORIZONTAL)  # middle
        self.sizer_vert.Add(self.sizer_horiz, 10, wx.EXPAND,  5)
        #levels = np.hstack((levels1, levels2))

        self.sizer_views = wx.BoxSizer(wx.VERTICAL)  # top side front view sizer
        self.sizer_midright = wx.BoxSizer(wx.VERTICAL)  # mid right view sizer
        self.slider_sizer = wx.BoxSizer(wx.HORIZONTAL)  # sizer for the slider

        self.panel_front = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_front = wx.BoxSizer(wx.VERTICAL)
        self.panel_front.SetSizer(self.sizer_front)
        #self.sizer_front.Add(wx.Panel(self.panel_front, wx.ID_ANY, wx.DefaultPosition, self.panel_front.GetSize(), wx.TAB_TRAVERSAL| wx.SIMPLE_BORDER), 1, wx.EXPAND, wx.EXPAND, 10)
        #self.panel_front.Layout()

        self.panel_side = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_side = wx.BoxSizer(wx.VERTICAL)
        self.panel_side.SetSizer(self.sizer_side)
        self.panel_top = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_top = wx.BoxSizer(wx.VERTICAL)
        self.panel_top.SetSizer(self.sizer_top)



        self.sizer_views.Add(self.panel_front, 1, wx.EXPAND, wx.EXPAND, 10)
        self.sizer_views.Add(self.panel_side, 1, wx.EXPAND, wx.EXPAND, 10)
        self.sizer_views.Add(self.panel_top, 1, wx.EXPAND, wx.EXPAND, 10)

        self.sizer_horiz.Add(self.sizer_views, 1, wx.EXPAND, wx.ALL, 10)

        # a bit of complicated way to add the droptarget panel, borrowed from the Transformer
        self.panel_main = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_main = wx.BoxSizer(wx.VERTICAL)
        self.panel_main.SetSizer(self.sizer_main)
        self.panel_main.Layout()
        self.sizer_main.Fit(self.panel_main)
        self.drop_target = MyDropTarget(self.panel_main)
        self.panel_main.SetDropTarget(self.drop_target)

        self.sizer_midright.Add(self.panel_main, 19, wx.EXPAND,  5)
        self.sizer_midright.Add(self.slider_sizer, 0, wx.EXPAND,  5)
        self.sizer_horiz.Add(self.sizer_midright, 4, wx.EXPAND,  5)
        #self.sizer_main.Add(wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, self.panel_main.GetSize(), wx.TAB_TRAVERSAL), 2, flag=wx.CENTER)

        self.threshold_slider = None
        self.contour_slider = None
        self.crop_contour_slider = None

        self.prev_contour = wx.BitmapButton(self, -1, wx.Bitmap('icons\\back-arrow.png'))
        self.next_contour = wx.BitmapButton(self, -1, wx.Bitmap('icons\\forward-arrow.png'))

        self.panel_thumbs = parent.Parent.panel_thumbs
        self.sizer_thumbs = parent.Parent.sizer_thumbs
        self.prints = parent.Parent.prints

        self.refresh_flag = True

        self.SetSizer(self.sizer_vert)

        self.status_bar = parent.Parent.GetStatusBar()

        #TODO progressbar things
        #progress bar
        #self.ProgressBar = wx.Gauge(self.status_bar, -1, 100)
        #self.status_bar.AddWidget(self.ProgressBar, ESB.ESB_ALIGN_RIGHT, ESB.ESB_ALIGN_BOTTOM)
        #self.ProgressBar.Show(False)

        self.toolbar.Realize()

        self.Bind(wx.EVT_TOOL, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.on_switch_view, id=wx.ID_FIND)
        self.Bind(wx.EVT_TOOL, self.on_crop, id=wx.ID_CUT)
        self.Bind(wx.EVT_TOOL, self.on_save, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_TOOL, self.on_invert, id=wx.ID_REDO)
        self.Bind(wx.EVT_TOOL, self.on_autorotate, id=wx.ID_UP)
        self.Bind(wx.EVT_TOOL, self.on_rotate90, id=wx.ID_DOWN)
        self.Bind(wx.EVT_TOOL, self.on_landmark_distance, id=wx.ID_VIEW_LIST)
        self.Bind(wx.EVT_TOOL, self.on_toggle_threshold, id=wx.ID_FILE7)
        self.Bind(wx.EVT_TOOL, self.on_toggle_scalebar, id=wx.ID_FILE1)
        self.Bind(wx.EVT_TOOL, self.on_toggle_grid, id=wx.ID_FILE3)
        #self.Bind(wx.EVT_TOOL, self.on_zero_contours, id=wx.ID_ZOOM_100)
        self.Bind(wx.EVT_TOOL, self.on_toggle_rectangular_crop, id=wx.ID_FILE8)
        self.Bind(wx.EVT_TOOL, self.on_toggle_polygonal_crop, id=wx.ID_ICONIZE_FRAME)
        self.Bind(wx.EVT_TOOL, self.on_delete_landmarks, id=wx.ID_DELETE)
        self.Bind(wx.EVT_TOOL, self.on_toggle_contours, id=wx.ID_FORWARD)
        self.Bind(wx.EVT_TOOL, self.on_toggle_place_lmarks, id=wx.ID_ADD)
        self.Bind(wx.EVT_TOOL, self.on_toggle_quick_measure, id=wx.ID_FILE9)
        self.Bind(wx.EVT_TOOL, self.on_toggle_crop_contour, id=wx.ID_FILE2)
        self.Bind(wx.EVT_TOOL, self.on_toggle_flatten, id=wx.ID_CONVERT)
        self.Bind(wx.EVT_TOOL, self.on_flatten, id=wx.ID_BOTTOM)
        self.Bind(wx.EVT_TOOL, self.on_toggle_depth_landmarks, id=wx.ID_FILE6)
        self.Bind(wx.EVT_TOOL, self.on_depth_chart, id=wx.ID_FILE5)
        self.Bind(wx.EVT_TOOL, self.on_mirror, id=wx.ID_BACKWARD)


        self.prev_contour.Bind(wx.EVT_BUTTON, self.on_contour_shift_left)
        self.next_contour.Bind(wx.EVT_BUTTON, self.on_contour_shift_right)
        self.toolbar.choiceCm.Bind(wx.EVT_CHOICE, self.on_change_colormap)


        self.mayavi_panel = None
        self.matplot_panel = None
        self.mpl3d_front = None
        self.mpl3d_top = None
        self.mpl3d_side = None

        #  filter to open files
        self.all_file_filter = "All supported files (*.csv;*.asc;*.ply;*.txt)|*.csv;*.asc;*.ply;*.txt|CSV files|*.csv|ASC files|*.asc|PLY files|*.ply|TXT files|*.txt|All files (*.*)|*.*"

        # open file history
        self.openfilehistory = wx.FileHistory(9)
        self.config_openfile = wx.Config(localFilename = "pyTrans-openfile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.openfilehistory.Load(self.config_openfile)

        # file attributes
        self.current_xyz = None
        self.current_xyzi = None
        self.current_rgb = None
        self.original_xyz = None
        self.original_xyzi = None
        self.original_rgb = None
        self.current_fname = None

        self.rotate_mode = False

        # dragging and cropping stuff
        self.dragLine = None
        #self.flatLine = None
        self.startDragPos = [0, 0]
        self.hid = None  # for mousedrag event
        self.dragRectangle = None
        self.crop_h = list()  # crop points
        self.crop_xy = np.empty([0, 2])  # crop point coordinates
        self.crop_lines = list()  # crop lines
        self.flat_lines = list()  # flattening edges
        self.start_contour_crop_val = None
        self.end_contour_crop_val = None


        # camera angles
        self.yaw = 0
        self.pitch = 0
        self.roll = 0

        # for landmarks
        self.lmark_active = None  # index of active/selected landmark
        self.lmark_hlight = None  # index of highlighted landmark (mouse-over)
        self.texts= list()
        self.lmark_h = list()  #
        self.lmark_xy = np.empty([0, 2])  #
        self.landmarkDistances = np.empty([0, 2])
        self.landmarkRealCoords = np.empty([0, 2])
        self.marker_size = 9
        self.normal_width = 0.5
        self.normal_color = 'k'
        self.highlight_width = 2
        self.highlight_color = 'r'
        self.active_width = 2
        self.active_color = 'w'

        self.Bind(wx.EVT_SET_FOCUS, self.on_mainwindow_click)

        self.csv_edited = False

        self.ON_SAVE_DEPTH_CSV = wx.NewId()

        #TODO multiprocessing
        #for progress bar
        #implement a listeing thread
        #and subscribe to updates
        # manager = multiprocessing.Manager()
        # self.q = manager.Queue()
        # listener_trhead = queue_listener(self.q, self)
        # listener_trhead.start()
        #pub.subscribe(self.updateProgress, "update")

    #update the status bar from the thread
    #@anythread
    # def updateProgress(self, msg):
    #     print('hello')
    #     self.ProgressBar.SetValue(self.ProgressBar.GetValue()+int(msg)/self.num_processes)



    def on_mainwindow_click(self, event):
        #close grid window when clicked on the main frame, if it exists
        if hasattr(self, 'gridWindow'):
            self.on_gridwindow_close(event)


    #  Open new file
    def on_open(self, event, folder_history=None):
        # processbar = wx.ProgressDialog("Saving", "Please wait...", maximum=100, parent=self,
        #                                style=wx.PD_AUTO_HIDE )
        from time import sleep
        # sleep(30)
        # processbar.Destroy()
        # open_otions_dialog = OpenOptionsDialog(None)
        # open_otions_dialog.ShowModal()
        # sleep(1)
        # open_otions_dialog.Close()
        # open_otions_dialog.Destroy()

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

            # file opening options
            open_otions_dialog = OpenOptionsDialog(None)
            open_otions_dialog.ShowModal()

            if not open_otions_dialog.ok: #  if OK was not clicked abort the operation
                return

            precision = open_otions_dialog.precision
            scale = open_otions_dialog.scale

            self.status_bar.SetStatusText('Loading %d print(s) using %d CPU core(s). Please wait...' % (cnt, min(cnt, cores)))
            wx.Yield()

            #TODO progressbar
            #self.ProgressBar.Show(True)

            #get the number of processes to be used for progress bar
            self.num_processes = cnt

            print('Load and interpolate of %d files' % cnt)
            start_time = time.time()

            #TODO multiprocessing
            #result = run_job(paths_dict.keys(), Loader(precision, scale, self.q))
            result = run_job(paths_dict.keys(), Loader(precision, scale))

            not_loaded = ''
            loaded = 0
            sizes = ''
            #guessed_multiplier not used at the moment
            for xyzi, xyz, fname, guessed_multiplier in result:
                if xyzi is None:
                    not_loaded = not_loaded + os.path.basename(fname) + ', '

                else:
                    #alert the user if the selected multiplier is different from the guessed one
                    # if self.get_multiplier() != guessed_multiplier:
                    #     dlg = wx.MessageDialog(self.Parent,
                    #                            'Selected scale might be incorrect. Proceed?',
                    #                            'Alert!', wx.YES_NO | wx.ICON_INFORMATION)

                    loaded += 1

                    # set thumbs panel
                    ch = self.sizer_thumbs.GetChildren()
                    if len(ch) == 1 and type(ch[0].GetWindow()) is wx.StaticText:
                        self.sizer_thumbs.Clear(True)

                    # 'normalize' z axis: min(z)=0
                    xyz, xyzi = self.Parent.Parent.normalize_z_axis(xyz, xyzi, np.nanmin(xyzi[2]))

                    mpl = MatplotPanel(self.panel_thumbs, xyzi, xyz, scale, precision, title=os.path.basename(fname), fname=fname, lmark_xy=paths_dict[fname][0], A=paths_dict[fname][1])
                    mpl.data = wx.TextDataObject(str(mpl.fig.canvas.GetId()))
                    mpl.button_press_event = mpl.fig.canvas.mpl_connect('button_press_event', self.Parent.Parent.on_drag)
                    mpl.motion_notify_event = mpl.fig.canvas.mpl_connect('motion_notify_event', self.Parent.Parent.on_mouseover)
                    mpl.figure_leave_event = mpl.fig.canvas.mpl_connect('figure_leave_event', self.Parent.Parent.on_figureleave)
                    self.prints[mpl.fig.canvas.GetId()] = mpl
                    self.sizer_thumbs.Add(mpl, 0, wx.EXPAND | wx.ALL, 5)

                    self.panel_thumbs.SendSizeEvent() #needed
                    sizes = sizes + mpl.real_size_string() + '; '

                    wx.Yield()

            print('Elapsed time %f seconds' % (time.time() - start_time))

            #self.panel_thumbs.SendSizeEvent()
            msg = '%d print(s) loaded.' % loaded
            if len(not_loaded) > 0:
                msg = msg + ' ' + not_loaded[0:len(not_loaded) - 2] + ' not loaded!'
            self.status_bar.SetStatusText(msg + ' ' + sizes)
            wx.Yield()

            #TODO progressbar
            #time.sleep(1)
            #self.ProgressBar.SetValue(0)
            #self.ProgressBar.Show(False)

    def on_switch_view(self, event):
        #disable buttons on 3d view, enable on 2d view
        if self.toolbar.GetToolState(wx.ID_FIND):
            self.toolbar.EnableTool(wx.ID_FILE8, False)
            self.toolbar.EnableTool(wx.ID_REDO, False)
            self.toolbar.EnableTool(wx.ID_UP, False)
            self.toolbar.EnableTool(wx.ID_DOWN, False)
            self.toolbar.EnableTool(wx.ID_BACKWARD, False)
            self.toolbar.EnableTool(wx.ID_ICONIZE_FRAME, False)
            self.toolbar.EnableTool(wx.ID_CUT, False)
            self.toolbar.EnableTool(wx.ID_ADD, False)
            self.toolbar.EnableTool(wx.ID_DELETE, False)
            self.toolbar.EnableTool(wx.ID_VIEW_LIST, False)
            self.toolbar.EnableTool(wx.ID_FILE9, False)
            self.toolbar.EnableTool(wx.ID_FILE6, False)
            self.toolbar.EnableTool(wx.ID_FILE7, False)
            self.toolbar.EnableTool(wx.ID_FILE1, False)
            self.toolbar.EnableTool(wx.ID_FILE3, False)
            self.toolbar.EnableTool(wx.ID_ZOOM_100, False)
            self.toolbar.EnableTool(wx.ID_FORWARD, False)
            self.toolbar.EnableTool(wx.ID_CONVERT, False)
            self.toolbar.EnableTool(wx.ID_BOTTOM, False)
            self.toolbar.choiceCm.Enable(False)
        else:
            self.toolbar.EnableTool(wx.ID_FILE8, True)
            self.toolbar.EnableTool(wx.ID_REDO, True)
            self.toolbar.EnableTool(wx.ID_UP, True)
            self.toolbar.EnableTool(wx.ID_DOWN, True)
            self.toolbar.EnableTool(wx.ID_BACKWARD, True)
            self.toolbar.EnableTool(wx.ID_ICONIZE_FRAME, True)
            self.toolbar.EnableTool(wx.ID_CUT, True)
            self.toolbar.EnableTool(wx.ID_ADD, True)
            self.toolbar.EnableTool(wx.ID_DELETE, True)
            self.toolbar.EnableTool(wx.ID_VIEW_LIST, True)
            self.toolbar.EnableTool(wx.ID_FILE9, True)
            self.toolbar.EnableTool(wx.ID_FILE6, True)
            self.toolbar.EnableTool(wx.ID_FILE7, True)
            self.toolbar.EnableTool(wx.ID_FILE1, True)
            self.toolbar.EnableTool(wx.ID_FILE3, True)
            self.toolbar.EnableTool(wx.ID_FORWARD, True)
            self.toolbar.EnableTool(wx.ID_CONVERT, True)
            self.toolbar.EnableTool(wx.ID_BOTTOM, True)
            self.toolbar.choiceCm.Enable(True)
        self.drop_target.switch_view()
        self.GrandParent.fix_size() #make sure that the thumbs pannel is not getting small

    #  crop the image
    def on_crop(self, event):

        #disable crop tool
        self.toolbar.EnableTool(wx.ID_CUT, False)

        #if contour cropping


        x = self.matplot_panel.xyzi[0]
        y = self.matplot_panel.xyzi[1]
        z = self.matplot_panel.xyzi[2]

        if self.dragRectangle is not None:

            # correction of rectangle if not started dragging from top left
            if self.dragRectangle._width < 0:
                self.dragRectangle._width = self.dragRectangle._width*(-1)
                self.startDragPos[0] = self.startDragPos[0] - self.dragRectangle._width
            if self.dragRectangle._height > 0:
                self.startDragPos[1] = self.startDragPos[1] + self.dragRectangle._height
                self.dragRectangle._height = self.dragRectangle._height*(-1)

            # get the interpolated coordinates
            coords_interpolated = np.hstack((self.startDragPos[0], self.startDragPos[1]))
            coords_interpolated = coords_interpolated.astype(int)

            # need to convert height coordinates
            # height coordinate in the image starts from the bottom!
            coords_interpolated[1] = coords_interpolated[1] + int(round(self.dragRectangle._height))

            # slice matrices
            xsub=x[coords_interpolated[1]:coords_interpolated[1] - int(round(self.dragRectangle._height)),
                   coords_interpolated[0]:coords_interpolated[0] + int(round(self.dragRectangle._width))]
            ysub=y[coords_interpolated[1]:coords_interpolated[1] - int(round(self.dragRectangle._height)),
                    coords_interpolated[0]:coords_interpolated[0] + int(round(self.dragRectangle._width))]
            zsub=z[coords_interpolated[1]:coords_interpolated[1] - int(round(self.dragRectangle._height)),
                    coords_interpolated[0]:coords_interpolated[0] + int(round(self.dragRectangle._width))]

        #polygonal cropping
        elif self.crop_xy.shape[0]>=3:

            xsub = numpy.copy(x)
            ysub = numpy.copy(y)
            zsub = numpy.copy(z)

            img = Image.new('L', (self.current_xyzi[0].shape[1], self.current_xyzi[0].shape[0]), 0)
            ImageDraw.Draw(img).polygon(tuple(map(tuple, self.crop_xy)), outline=1, fill=1)
            maskLeave = numpy.array(img)
            maskLeave = (maskLeave == 0)
            maskLeaveIdxRows,maskLeaveIdxCols =np.where(maskLeave)

            #xsub[maskLeaveIdxRows, maskLeaveIdxCols] = None
            #ysub[maskLeaveIdxRows, maskLeaveIdxCols] = None
            zsub[maskLeaveIdxRows, maskLeaveIdxCols] = None

            #now remove rows and columns which are all nan
            mask = np.all(np.isnan(zsub), axis=0)
            xsub = xsub[:,~mask]
            ysub = ysub[:,~mask]
            zsub = zsub[:,~mask]

            mask = np.all(np.isnan(zsub), axis=1)
            xsub = xsub[~mask]
            ysub = ysub[~mask]
            zsub = zsub[~mask]

        # contour cropping
        elif self.start_contour_crop_val is not None and self.end_contour_crop_val is not None: #crop by contour
            xsub = numpy.copy(self.original_xyzi[0])
            ysub = numpy.copy(self.original_xyzi[1])
            zsub = numpy.copy(self.original_xyzi[2])
            #zsub = numpy.copy(z)

            # set the values outside of selection to None
            zsub[(zsub < self.start_contour_crop_val) | (zsub > self.end_contour_crop_val)] = None

        # create 1d arrays for the matplot
        xsub_1d = np.reshape(xsub, xsub.shape[0]*xsub.shape[1],1)
        ysub_1d = np.reshape(ysub, ysub.shape[0]*ysub.shape[1],1)
        zsub_1d = np.reshape(zsub, zsub.shape[0]*zsub.shape[1],1)

        # now create a new Matplot
        xyz_new = np.transpose(np.vstack((xsub_1d,ysub_1d,zsub_1d)))
        xyzi_new = (xsub, ysub, zsub, xsub[0,:], ysub[:,0])

        #normalize
        xyz_new, xyzi_new = self.Parent.Parent.normalize_z_axis(xyz_new, xyzi_new, np.nanmin(xyzi_new[2]))
        #self.reload_image(xyz_new, xyzi_new, multiplier)
        self.dragRectangle=None
        self.crop_h = list()  # crop points
        self.crop_xy = np.empty([0, 2])  # crop point coordinates
        self.crop_lines = list()  # crop lines


        self.start_contour_crop_val=None
        self.end_contour_crop_val = None

        #turn off the sliders
        self.slider_sizer.ShowItems(False)
        self.Unbind(wx.EVT_SLIDER)

        #disable contours and contour crop tool
        self.toolbar.ToggleTool(wx.ID_FORWARD, False)
        self.toolbar.ToggleTool(wx.ID_FILE2, False)
        self.toolbar.EnableTool(wx.ID_FILE2, False)

        # after the crop, delete matplotpanel "navigation history",
        # so that it is impossible to click "back" button
        # UNDOCUMENTED SOLUTION CONSIDER CHANGING
        self.matplot_panel.toolbar._views.clear()
        self.matplot_panel.toolbar._positions.clear()

        self.show_updated_image(xyz_new, xyzi_new)

        # set flag for project saving
        self.csv_edited = True

    print_file_filter = "All supported files (*.csv;*.asc)|*.csv;*.asc|CSV files|*.csv|ASC files|*.asc|All files (*.*)|*.*"
    def on_save(self, event):

        savefiledialog = wx.FileDialog(self, "Save file", "", "", self.print_file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if savefiledialog.ShowModal() != wx.ID_CANCEL:
            path = savefiledialog.GetPath()
            name, ext = os.path.splitext(path)

            self.current_fname=name+ext

            np.savetxt(self.current_fname, self.current_xyz, fmt='%.4f', delimiter=',', header='X,Y,Z', comments='')

            #  set new thumb
            ch = self.sizer_thumbs.GetChildren()
            if len(ch) == 1 and type(ch[0].GetWindow()) is wx.StaticText:
                self.sizer_thumbs.Clear(True)

            mpl = MatplotPanel(self.panel_thumbs, self.current_xyzi, self.current_xyz, multiplier=self.matplot_panel.multiplier, precision=self.matplot_panel.precision, title=os.path.basename(self.current_fname), fname=self.current_fname, lmark_xy=None, A=None)
            mpl.data = wx.TextDataObject(str(mpl.fig.canvas.GetId()))
            mpl.button_press_event = mpl.fig.canvas.mpl_connect('button_press_event', self.Parent.Parent.on_drag)
            mpl.motion_notify_event = mpl.fig.canvas.mpl_connect('motion_notify_event', self.Parent.Parent.on_mouseover)
            mpl.figure_leave_event = mpl.fig.canvas.mpl_connect('figure_leave_event', self.Parent.Parent.on_figureleave)
            self.prints[mpl.fig.canvas.GetId()] = mpl
            self.sizer_thumbs.Add(mpl, 0, wx.EXPAND | wx.ALL, 5)

            self.panel_thumbs.SendSizeEvent() #unchecked probably needed

            # set csv_edited flag for project saving
            self.csv_edited = False

    # def on_rotate(self, event):
    #     print(mlab.view())
    #     #R = euler2mat(-(mlab.view()[0]-90)*math.pi/180, (mlab.view()[1]-180)*math.pi/180, mlab.roll()*math.pi/180)
    #     #R = euler2mat(-(mlab.view()[0]-90)*math.pi/180, (mlab.view()[1]-180)*math.pi/180, 0*math.pi/180)
    #     R = euler2mat(-(80-90)*math.pi/180, (mlab.view()[1]-180)*math.pi/180, 0*math.pi/180)
    #     rotated_xyz = self.rotate(R, None)
    #     rotated_x, rotated_y, rotated_z, rotated_xm, rotated_ym = loadPrint.interpolate(rotated_xyz, self.matplot_panel.precision)
    #     rotated_xyzi=(rotated_x, rotated_y, rotated_z, rotated_xm, rotated_ym)
    #     multiplier=self.matplot_panel.multiplier
    #
    #     self.show_updated_image(rotated_xyz, rotated_xyzi, multiplier)

    def on_invert(self, event):
        # invert_options_dialog = InvertOptionsDialog(None)
        # invert_options_dialog.ShowModal()
        #
        # if not invert_options_dialog.ok:  # if OK was not clicked abort the operation
        #     return
        #
        # if not (invert_options_dialog.x or invert_options_dialog.y or invert_options_dialog.z):  # None of the axes were selected
        #     return

        inverted_xyz=np.copy(self.current_xyz)
        inverted_xyzi=copy.deepcopy(self.current_xyzi)
        # if invert_options_dialog.x:
        #     inverted_xyz[:, 0]=inverted_xyz[:,0]*(-1)
        #     inverted_xyzi = (inverted_xyzi[0]*(-1), inverted_xyzi[1], inverted_xyzi[2], inverted_xyzi[3], inverted_xyzi[4])
        # if invert_options_dialog.y:
        #     inverted_xyz[:, 1]=inverted_xyz[:,1]*(-1)
        #     inverted_xyzi = (inverted_xyzi[0], inverted_xyzi[1]*(-1), inverted_xyzi[2], inverted_xyzi[3], inverted_xyzi[4])
        # if invert_options_dialog.z:
        inverted_xyz[:, 2]=inverted_xyz[:,2]*(-1)
        inverted_xyzi = (inverted_xyzi[0], inverted_xyzi[1], inverted_xyzi[2]*(-1), inverted_xyzi[3], inverted_xyzi[4])

        #inverted_xyzi=(inverted_xyzi[0],inverted_xyzi[1],inverted_xyzi[2],inverted_xyzi[3],inverted_xyzi[4])
        inverted_xyz, inverted_xyzi = self.Parent.Parent.normalize_z_axis(inverted_xyz, inverted_xyzi,
                                                                                  np.nanmin(inverted_xyzi[2]))
        self.show_updated_image(inverted_xyz, inverted_xyzi)


    def on_autorotate(self, event):

        # eigenvectors cannot be calculated when there are NaN-s in the image.
        # We replace them with maximal value
        toRotate = self.current_xyz
        nanIndices = np.where(np.isnan(toRotate))
        toRotate[nanIndices] = np.nanmax(toRotate[:,2])

        c = np.nanmean(self.current_xyz,axis=0)
        c = np.matlib.repmat(c,self.current_xyz.shape[0],1)
        data = self.current_xyz-c

        nanIndices = np.where(np.isnan(data))
        data[nanIndices]=np.nanmax(data)

        eig = np.linalg.eig(np.dot(np.transpose(data),data))

        # numpy does not automatically order the eigenvectors.
        # We need to order them from the one corresponding to the max eigen value and descending
        order = np.argsort(eig[0])[::-1]

        PCs=np.vstack((eig[1][:,order[0]], eig[1][:,order[1]], eig[1][:,order[2]]))

        #see whether the matrix needs to be inverted

        #F=np.dot(np.linalg.eig(np.dot(data,np.transpose(data)))[1], np.linalg.eig(np.dot(np.transpose(data),data))[1])

        #  rotate in principal components directions

        rotated_xyz = self.rotate(PCs, toRotate)
        #  rotate -90 degrees
        #R = euler2mat(-90*math.pi/180,0,0)
        #rotated_xyz = self.rotate(R, rotated_xyz)

        rotated_x, rotated_y, rotated_z, rotated_xm, rotated_ym = loadPrint.interpolate(rotated_xyz, self.matplot_panel.precision)
        rotated_xyzi=(rotated_x, rotated_y, rotated_z, rotated_xm, rotated_ym)

        rotated_xyz, rotated_xyzi = self.Parent.Parent.normalize_z_axis(rotated_xyz, rotated_xyzi,
                                                                          np.nanmin(rotated_xyzi[2]))

        self.show_updated_image(rotated_xyz, rotated_xyzi)

    def on_rotate90(self, event):

        rotated_z = np.rot90(self.current_xyzi[2])

        # new coordinates for meshgrid
        xm = np.arange(self.current_xyzi[0][0,0], self.current_xyzi[0][0,0]+(self.current_xyzi[0].shape[0]-1)*self.matplot_panel.precision+self.matplot_panel.precision, self.matplot_panel.precision)
        ym = np.arange(self.current_xyzi[1][0,0], self.current_xyzi[1][0,0]+(self.current_xyzi[1].shape[1]-1)*self.matplot_panel.precision+self.matplot_panel.precision, self.matplot_panel.precision)

        rotated_x, rotated_y = np.meshgrid(xm, ym)

        # create 1d arrays for the matplot
        x_1d = np.reshape(rotated_x, rotated_x.shape[0]*rotated_x.shape[1],1)
        y_1d = np.reshape(rotated_y, rotated_y.shape[0]*rotated_y.shape[1],1)
        z_1d = np.reshape(rotated_z, rotated_z.shape[0]*rotated_z.shape[1],1)

        rotated_xyz = np.transpose(np.vstack((x_1d, y_1d, z_1d)))
        rotated_xyzi = (rotated_x, rotated_y, rotated_z, xm, ym)

        self.show_updated_image(rotated_xyz, rotated_xyzi)

    def on_mirror(self, event):
        mirrored_z = np.flip(self.current_xyzi[2],axis=1)

        # create 1d arrays for the matplot
        x_1d = np.reshape(self.current_xyzi[0], self.current_xyzi[0].shape[0]*self.current_xyzi[0].shape[1],1)
        y_1d = np.reshape(self.current_xyzi[1], self.current_xyzi[1].shape[0]*self.current_xyzi[1].shape[1],1)
        z_1d = np.reshape(mirrored_z, mirrored_z.shape[0]*mirrored_z.shape[1],1)

        mirrored_xyz = np.transpose(np.vstack((x_1d, y_1d, z_1d)))
        mirrored_xyzi = (self.current_xyzi[0], self.current_xyzi[1], mirrored_z, self.current_xyzi[3], self.current_xyzi[4])

        self.show_updated_image(mirrored_xyz, mirrored_xyzi)



    # pairwise distances matrix between landmarks
    def on_landmark_distance(self, event):

        self.landmarkDistances = np.zeros(shape=(len(self.lmark_xy), len(self.lmark_xy)))
        self.landmarkRealCoords = np.zeros(shape=(len(self.lmark_xy),3))

        i = 0
        for landmark in self.lmark_xy:
            j = 0
            for landmark2 in self.lmark_xy:
                distance, b = self.get_distance(landmark, landmark2)
                self.landmarkDistances[i, j]=round(distance,2)
                j = j+1
            i = i+1

        no_caption = wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.FRAME_NO_TASKBAR
        self.gridWindow = wx.Frame(self,  style=  wx.FRAME_FLOAT_ON_PARENT | no_caption)

        gridCoordinates = gridlib.Grid(self.gridWindow)
        gridCoordinates.CreateGrid(len(self.lmark_xy),3)
        gridCoordinates.SetColLabelValue(0, "X")
        gridCoordinates.SetColLabelValue(1, "Y")
        gridCoordinates.SetColLabelValue(2, "Z")
        gridCoordinates.EnableEditing(False)

        gridDistances = gridlib.Grid(self.gridWindow)
        gridDistances.CreateGrid(len(self.lmark_xy),len(self.lmark_xy))
        gridDistances.EnableEditing(False)

        for i in range(0, self.landmarkDistances.shape[0]):
            for j in range(0, self.landmarkDistances.shape[1]):
                gridDistances.SetCellValue(i, j, str(self.landmarkDistances[i, j]))
            gridDistances.SetColLabelValue(i, "L"+str(i+1))
            gridDistances.SetRowLabelValue(i, "L"+str(i+1))
            gridCoordinates.SetRowLabelValue(i, "L"+str(i+1))

        for i in range(0, len(self.lmark_xy)):
            image_xyz=self.get_image_xyz(self.lmark_xy[i][0], self.lmark_xy[i][1])
            gridCoordinates.SetCellValue(i,0, str(image_xyz[0]))
            gridCoordinates.SetCellValue(i,1, str(image_xyz[1]))
            gridCoordinates.SetCellValue(i,2, str(round(image_xyz[2],2)))
            self.landmarkRealCoords[i, 0] = round(image_xyz[0],2)
            self.landmarkRealCoords[i, 1] = round(image_xyz[1],2)
            self.landmarkRealCoords[i, 2] = round(image_xyz[2],2)

        i=1
        #add landmark number texsts to the picture
        for txt in self.texts:
            txt.set_text("L"+str(i))
            i=i+1

        self.matplot_panel.fig.canvas.draw()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self.gridWindow, label="Landmark Coordinates"))
        sizer.Add(gridCoordinates, 10, wx.EXPAND, wx.EXPAND)
        sizer.Add(wx.StaticText(self.gridWindow,label="Landmark Distances"))
        sizer.Add(gridDistances, 10, wx.EXPAND, wx.EXPAND)

        panel_main = wx.Panel(self.gridWindow, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        panel_main.SetSizer(sizer)
        panel_main.Layout()
        sizer.Fit(panel_main)

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(panel_main,0,wx.EXPAND, wx.EXPAND)
        self.gridWindow.SetSizer(sizer_main)

        sizer_main.Fit(self.gridWindow)
        panel_main.Fit()
        self.gridWindow.SetClientSize(panel_main.GetSize()+(10,10))

        tbar=self.gridWindow.CreateToolBar(wx.TB_HORIZONTAL, wx.ID_ANY)
        tbar.AddLabelTool(wx.ID_SAVE, 'Save', wx.Bitmap('icons\\save.png'), shortHelp="Save", longHelp="Save")
        tbar.Realize()
        self.gridWindow.Bind(wx.EVT_TOOL, self.on_landmark_save, id=wx.ID_SAVE)
        self.gridWindow.Bind(wx.EVT_CLOSE, self.on_gridwindow_close)
        #self.gridWindow.Bind(wx.EVT_KILL_FOCUS, self.on_gridwindow_close)
        self.gridWindow.SetTitle("Landmarks")
        self.gridWindow.Show()
        self.gridWindow.MakeModal(True)

    #delete all landmarks and cropping lines
    def on_delete_landmarks(self, event):

        #disable relevant icons
        self.toolbar.EnableTool(wx.ID_DELETE, False)
        self.toolbar.EnableTool(wx.ID_VIEW_LIST, False)

        #remove landmarks
        for landmark in self.lmark_h:
            self.matplot_panel.ax.lines.remove(landmark)
        for text in self.texts:
            self.matplot_panel.ax.texts.remove(text)

        self.lmark_h = list()  #
        self.lmark_xy = np.empty([0, 2])  #
        self.texts = list()

        self.matplot_panel.fig.canvas.draw()


    #save alndmark distances
    def on_landmark_save(self, event):

        i=0
        textlabels=np.empty(len(self.texts), dtype='|S20')[:, np.newaxis]
        textheader="UID"
        #rows = np.array(['row1', 'row2', 'row3'], dtype='|S20')[:, np.newaxis]
        # with open('test.csv', 'w') as f:
        #     np.savetxt(f, np.hstack((rows, data)), delimiter=', ', fmt='%s')
        #add landmark number texsts to the picture
        for txt in self.texts:
            textlabels[i]="L"+str(i+1)
            textheader=textheader+",L"+str(i+1)
            i = i + 1

        savefiledialog = wx.FileDialog(self, "Save file", "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if savefiledialog.ShowModal() != wx.ID_CANCEL:
            path = savefiledialog.GetPath()
            fname, ext = os.path.splitext(path)

        np.savetxt(fname+"Distances.csv", np.hstack((textlabels,self.landmarkDistances)), delimiter=",",fmt='%s',header=textheader, comments='')
        np.savetxt(fname + "Coordinates.csv", np.hstack((textlabels, self.landmarkRealCoords)), fmt='%s', delimiter=',',
                   header='POINT_ID,X,Y,Z', comments='')
        self.matplot_panel.fig.savefig(fname+".jpeg")

    # closing of the window with distances, remove texts
    def on_gridwindow_close(self, event):
        #remove texsts
        for txt in self.texts:
            txt.set_text(" ")

        self.matplot_panel.fig.canvas.draw()
        self.gridWindow.MakeModal(False)
        self.gridWindow.Destroy()

    # toggle rect crop on and off
    def on_toggle_rectangular_crop(self, event):
        self.on_delete_landmarks(event)

        for line in self.crop_lines:
            if self.matplot_panel.ax.lines.__contains__(line):
                self.matplot_panel.ax.lines.remove(line)

        for cropmark in self.crop_h:
            if self.matplot_panel.ax.lines.__contains__(cropmark):
                self.matplot_panel.ax.lines.remove(cropmark)

        # remove dragline
        if self.matplot_panel.ax.lines.__contains__(self.dragLine):
            self.matplot_panel.ax.lines.remove(self.dragLine)
        self.matplot_panel.fig.canvas.draw()

        self.toolbar.ToggleTool(wx.ID_ADD, False)
        self.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)
        self.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.toolbar.ToggleTool(wx.ID_FILE6, False)
        self.toolbar.ToggleTool(wx.ID_CONVERT, False)


    #toggle polyg crop on and off
    def on_toggle_polygonal_crop(self, event):
        self.on_delete_landmarks(event)

        for line in self.crop_lines:
            if self.matplot_panel.ax.lines.__contains__(line):
                self.matplot_panel.ax.lines.remove(line)

        for cropmark in self.crop_h:
            if self.matplot_panel.ax.lines.__contains__(cropmark):
                self.matplot_panel.ax.lines.remove(cropmark)

        # remove dragline
        if self.matplot_panel.ax.lines.__contains__(self.dragLine):
            self.matplot_panel.ax.lines.remove(self.dragLine)
        self.matplot_panel.fig.canvas.draw()

        self.crop_lines = list()
        self.crop_h = list()
        self.crop_xy = np.empty([0, 2])

        self.toolbar.ToggleTool(wx.ID_ADD, False)
        self.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.toolbar.ToggleTool(wx.ID_FILE6, False)
        self.toolbar.ToggleTool(wx.ID_CONVERT, False)

    # toggle quick measure - untoggles place landmarks if it was toggled
    def on_toggle_quick_measure(self, event):
        self.toolbar.ToggleTool(wx.ID_ADD, False)
        self.toolbar.ToggleTool(wx.ID_FILE6, False)
        self.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)
        self.toolbar.ToggleTool(wx.ID_CONVERT, False)

    # toggle place landmarks - untoggles quck measure if it was toggled
    def on_toggle_place_lmarks(self, event):
        self.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.toolbar.ToggleTool(wx.ID_FILE6, False)
        self.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)
        self.toolbar.ToggleTool(wx.ID_CONVERT, False)

    def on_toggle_scalebar(self, event):
        if self.toolbar.GetToolState(wx.ID_FILE1):
            self.matplot_panel.toggle_scalebar(True)
        else:
            self.matplot_panel.toggle_scalebar(False)

    def on_toggle_grid(self, event):
        if self.toolbar.GetToolState(wx.ID_FILE3):
            grid_otions_dialog = GridOptionsDialog(None)
            grid_otions_dialog.ShowModal()

            if not grid_otions_dialog.ok:  # if OK was not clicked abort the operation
                self.toolbar.ToggleTool(wx.ID_FILE3, False)
                return

            grid_distance = grid_otions_dialog.grid_distance

            self.matplot_panel.toggle_grid(True, grid_distance)
        else:
            self.matplot_panel.toggle_grid(False)

    def on_toggle_flatten(self, event):
        # if self.matplot_panel.ax.lines.__contains__(self.flatLine):
        #     self.matplot_panel.ax.lines.remove(self.flatLine)
        #     self.matplot_panel.ax.figure.canvas.draw()
        # self.flatLine = None

        self.on_delete_landmarks(event)
        self.toolbar.ToggleTool(wx.ID_ADD, False)
        self.toolbar.ToggleTool(wx.ID_FILE6, False)
        self.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)

        for i in range(0, self.flat_lines.__len__()):
            self.matplot_panel.ax.lines.remove(self.flat_lines.pop())
        self.matplot_panel.ax.figure.canvas.draw()



    def on_flatten(self, event):
        self.toolbar.ToggleTool(wx.ID_CONVERT, False)
        if self.flat_lines.__len__()==2:
            coords=np.empty(2)
            direction=0
            for i in range(0, self.flat_lines.__len__()):
                flatline = self.flat_lines.pop()
                direction = flatline._x[0] == flatline._x[1]
                if direction==1:
                    coords[i]=flatline._x[0]
                else:
                    coords[i] = flatline._y[0]
                self.matplot_panel.ax.lines.remove(flatline)

            xyz_new, xyzi_new = FlattenSurface.flatten(self.current_xyz,self.current_xyzi,
                                                       coords, direction) #direction if 1 along x axis if 0 y axis
            self.show_updated_image(xyz_new, xyzi_new)
            self.matplot_panel.ax.figure.canvas.draw()


    def  on_toggle_depth_landmarks(self, event):

        # disable relevant icons
        self.toolbar.ToggleTool(wx.ID_ADD, False)
        self.toolbar.ToggleTool(wx.ID_CONVERT, False)
        self.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)

        if self.toolbar.GetToolState(wx.ID_FILE6):
            self.toolbar.EnableTool(wx.ID_FILE5, True)
        else:
            self.toolbar.EnableTool(wx.ID_FILE5, False)

        self.on_delete_landmarks(event)
        for text in self.texts:
            self.matplot_panel.ax.texts.remove(text)

        for cropmark in self.crop_h:
            if self.matplot_panel.ax.lines.__contains__(cropmark):
                self.matplot_panel.ax.lines.remove(cropmark)

        for line in self.crop_lines:
            if self.matplot_panel.ax.lines.__contains__(line):
                self.matplot_panel.ax.lines.remove(line)

        self.crop_xy = np.empty([0, 2])  #
        self.texts = list()

        self.matplot_panel.fig.canvas.draw()

    #distance/depth chart between the specified landmarks
    def on_depth_chart(self, event):

        #if no lines, return
        if self.crop_xy.shape[0]<2:
            return

        depth_values=np.empty(0)
        depth_coords=np.empty((0,2))
        x = self.current_xyzi[0]
        y = self.current_xyzi[1]
        z = self.current_xyzi[2]

        for i in range(0, self.crop_xy.shape[0]-1):
            img = Image.new('L', (self.current_xyzi[0].shape[1], self.current_xyzi[0].shape[0]), 0)
            ImageDraw.Draw(img).line(tuple(map(tuple, self.crop_xy[i:i+2,:])), width=1, fill=1)
            maskLine = numpy.array(img)
            maskLine = (maskLine == 1)
            iIdxRows, iIdxCols = np.where(maskLine)
            iX = x[iIdxRows.astype(int), iIdxCols.astype(int)]
            iY = y[iIdxRows.astype(int), iIdxCols.astype(int)]
            iValues = z[iIdxRows.astype(int), iIdxCols.astype(int)]

            # check which point was the start of the line, and if needed swap the line coordinates
            if iIdxRows[-1]==self.crop_xy[i,1] and iIdxCols[-1]==self.crop_xy[i,0]:
                iValues=np.flipud(iValues)
                iX = np.flipud(iX)
                iY = np.flipud(iY)

            #set 0 coordinate to the second landmark
            if i==0:
                origin = iValues[-1]

            depth_values = np.hstack((depth_values, iValues))
            depth_coords = np.vstack((depth_coords, np.vstack((iX, iY)).transpose()))


        self.graph_depth_coords_values=np.hstack((depth_coords,np.expand_dims(depth_values.transpose(),axis=1)))


        from matplotlib.figure import Figure
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
        from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar

        no_caption = wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.FRAME_NO_TASKBAR

        self.graphWindow = wx.Frame(self, style=wx.FRAME_FLOAT_ON_PARENT | no_caption)
        self.graphWindow.Bind(wx.EVT_CLOSE, self.on_graphwindow_close)

        panel_main = wx.Panel(self.graphWindow, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)

        sizer = wx.BoxSizer(wx.VERTICAL)
        panel_main.SetSizer(sizer)


        fig = Figure()
        ax = fig.add_subplot(111)

        canvas = FigureCanvas(panel_main, -1, fig)

        toolbar = NavigationToolbar(canvas)

        # delete subplots button from the toolbar
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 6
        toolbar.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)
        # delete the default save button from the NavigationToolbar
        #POSITION_OF_SAVE_FIGURE_BTN = 7
        #toolbar.DeleteToolByPos(POSITION_OF_SAVE_FIGURE_BTN)

        save_icon = wx.ImageFromBitmap(wx.Bitmap('icons\\save.png'))
        save_icon = save_icon.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
        save_icon = wx.BitmapFromImage(save_icon)
        toolbar.AddSimpleTool(self.ON_SAVE_DEPTH_CSV , save_icon, 'Save', 'Save depth information')
        wx.EVT_TOOL(self, self.ON_SAVE_DEPTH_CSV, self.save_depth_csv)
        toolbar.Realize()


        sizer.Add(toolbar, 0, wx.LEFT | wx.EXPAND)
        toolbar.update()
        sizer.Add(canvas, 1, wx.EXPAND)
        ax.plot(range(0, len(depth_values)), depth_values)
        ax.set_axis_on()
        panel_main.SendSizeEvent()
        panel_main.Layout()
        sizer.Fit(panel_main)

        panel_main.Fit()



        self.graphWindow.SetSize(fig.get_size_inches() * fig.dpi)
        self.graphWindow.SetTitle("Depth chart")
        self.graphWindow.Show()
        self.graphWindow.MakeModal(True)


    # closing of the window with distances, remove texts
    def on_graphwindow_close(self, event):
        #remove texsts
        #for txt in self.texts:
        #    txt.set_text(" ")

        self.matplot_panel.fig.canvas.draw()
        self.graphWindow.MakeModal(False)
        self.graphWindow.Destroy()
        self.matplot_panel.SendSizeEvent()

    # event to close the depth_chart window
    def save_depth_csv(self, evt):
        dlg = wx.FileDialog(self, "Save depth information", "", "", "*.csv",
                            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            numpy.savetxt(path, self.graph_depth_coords_values,fmt='%.4f', delimiter=',', header='X,Y,Z',)


    # event to close the depth_chart window
    def handle_close(self, evt):
        self.Enable()

    #toggle thresholding on and off
    def on_toggle_threshold(self, event, pivot=None, start=None, end=None):
        if self.matplot_panel is None:
            return

        #delete landmarks
        self.on_delete_landmarks(event)


        #if contours are toggled, untoggle
        if self.toolbar.GetToolState(wx.ID_FORWARD):
            self.toolbar.ToggleTool(wx.ID_FORWARD, False)
            #self.on_toggle_contours(event)
            self.slider_sizer.ShowItems(False)
            self.sizer_midright.Layout()
            self.current_xyz = self.original_xyz
            self.current_xyzi = self.original_xyzi
            self.show_updated_image(self.current_xyz, self.current_xyzi, flag_update_sideviews=False)

        if self.toolbar.GetToolState(wx.ID_FILE7):
            if not self.threshold_slider:
                self.threshold_slider = wx.Slider(parent=self, value=(np.nanmin(self.current_xyzi[2]) + np.nanmax(self.current_xyzi[2])) / 2,
                                                    minValue=np.nanmin(self.current_xyzi[2]),
                                                    maxValue=np.ceil(np.nanmax(self.current_xyzi[2])),
                                                    pos=wx.DefaultPosition, size=(250, -1),
                                                    style = wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS )
                self.slider_sizer.Add(self.threshold_slider, 1, wx.EXPAND, wx.ALL, 5)
                self.SendSizeEvent() #needed

            else:
                self.slider_sizer.Show(self.threshold_slider)
                self.sizer_midright.Layout()


            self.Unbind(wx.EVT_SLIDER)


            self.threshold_slider.Bind(wx.EVT_LEFT_UP, self.on_thresholdSliderUpdate)

            # if not start is None and not end is None and not pivot is None:
            #     self.threshold_slider.SetValue(pivot)
            #     self.threshold_slider.SetSelection(start, end)
            # else:
            #     self.threshold_slider.SetSelection(self.threshold_slider.Value-1, self.threshold_slider.Value+1)

            self.matplot_panel.set_cmap('gray')

            self.original_xyz = self.current_xyz
            self.original_xyzi = self.current_xyzi

            self.do_threshold(self.threshold_slider.Value)

            self.Refresh()


        elif self.threshold_slider is not None:
            if self.threshold_slider.IsShown:
                self.slider_sizer.ShowItems(False)
                self.sizer_midright.Layout()

                self.matplot_panel.set_cmap(self.toolbar.choiceCm.GetString(self.toolbar.choiceCm.GetSelection()))

                self.current_xyz = self.original_xyz
                self.current_xyzi = self.original_xyzi

                self.show_updated_image(self.current_xyz, self.current_xyzi, flag_update_sideviews=False)

        self.GrandParent.fix_size() #fix the size

    #slide the range together with the slider
    def on_thresholdSliderUpdate(self, event):
        self.do_threshold(self.threshold_slider.Value)

        event.Skip()

    #do the actual thresholding
    def do_threshold(self, threshold_value):
        z = self.original_xyzi[2]

        bwz = np.ones(z.shape)

        # Where we set the RGB for each pixel
        #bwz[(z>=start_range) & (z<=end_range)] = 0
        bwz[z<threshold_value] = 0

        bwx_1d = np.reshape(self.original_xyzi[0], bwz.shape[0]*bwz.shape[1],1)
        bwy_1d = np.reshape(self.original_xyzi[1], bwz.shape[0]*bwz.shape[1],1)
        bwz_1d = np.reshape(bwz, bwz.shape[0]*bwz.shape[1],1)

        xyzi_bw=(self.original_xyzi[0],self.original_xyzi[1],bwz,self.original_xyzi[3],self.original_xyzi[4])
        xyz_bw = np.transpose(np.vstack((bwx_1d,bwy_1d,bwz_1d)))

        self.show_updated_image(xyz_bw, xyzi_bw, flag_update_sideviews=False)

    def on_toggle_contours(self, event, interval=None):
        if self.matplot_panel is None:
            return

        # delete landmarks
        self.on_delete_landmarks(event)

        #if threshold is toggled, untoggle
        if self.toolbar.GetToolState(wx.ID_FILE7):
            self.toolbar.ToggleTool(wx.ID_FILE7, False)
            #self.on_toggle_threshold(event)
            self.slider_sizer.ShowItems(False)
            self.sizer_midright.Layout()
            self.current_xyz = self.original_xyz
            self.current_xyzi = self.original_xyzi
            self.show_updated_image(self.current_xyz, self.current_xyzi, flag_update_sideviews=False)

        if self.toolbar.GetToolState(wx.ID_FORWARD):

            if not bool(self.contour_slider): #the slider doesnt exist meaning that it is the first time contours are switched on for current image
                # self.contour_slider = wx.Slider(parent=self, value=1,
                #                                 minValue=1, maxValue=np.abs(np.round(np.nanmin((self.current_xyzi[2])-np.nanmax(self.current_xyzi[2]))/2)*4),
                #                                 pos=wx.DefaultPosition, size=(250, -1),
                #                                 style =  wx.SL_HORIZONTAL | wx.SL_SELRANGE,)

                self.contour_slider = FloatSlider(self, wx.NewId(), 0.25, np.abs(np.round(np.nanmin((self.current_xyzi[2])-np.nanmax(self.current_xyzi[2]))/2)),
                                                                                 1, 4)

                #self.contour_slider.slider.SetTickFreq(1)

                self.prev_contour = wx.BitmapButton(self, -1, wx.Bitmap('icons\\back-arrow.png'))
                self.next_contour = wx.BitmapButton(self, -1, wx.Bitmap('icons\\forward-arrow.png'))
                self.prev_contour.Bind(wx.EVT_BUTTON, self.on_contour_shift_left)
                self.next_contour.Bind(wx.EVT_BUTTON, self.on_contour_shift_right)

                self.slider_sizer.Add(self.prev_contour, 1, wx.EXPAND, wx.ALL, 5)
                self.slider_sizer.Add(self.contour_slider, 10, wx.EXPAND, wx.ALL, 5)
                self.slider_sizer.Add(self.next_contour, 1, wx.EXPAND, wx.ALL, 5)

                self.SendSizeEvent()

            else:
                self.slider_sizer.Show(self.prev_contour)
                self.slider_sizer.Show(self.contour_slider)
                self.slider_sizer.Show(self.next_contour)
                self.sizer_midright.Layout()

            self.matplot_panel.switch_save_icon(False)

            # enable zero contours button
            self.toolbar.EnableTool(wx.ID_ZOOM_100, True)
            #enable contour crop
            self.toolbar.EnableTool(wx.ID_FILE2, True)

            self.Unbind(wx.EVT_SLIDER)
            self.Bind(wx.EVT_SLIDER, self.on_contourSliderUpdate)

            if not interval is None:
                self.matplot_panel.set_contours(interval)
                self.contour_slider.slider.SetValue(interval*4)
            else:
                self.matplot_panel.set_contours(1)
                self.contour_slider.slider.SetValue(4)

            self.Refresh()

        #untoggle
        elif bool(self.contour_slider):
            if self.contour_slider.IsShown:
                self.slider_sizer.ShowItems(False)
                self.sizer_midright.Layout()

                self.current_xyz, self.current_xyzi = self.Parent.Parent.normalize_z_axis(self.current_xyz, self.current_xyzi, np.nanmin(self.current_xyzi[2]))

                self.matplot_panel.set_cmap(self.toolbar.choiceCm.GetString(self.toolbar.choiceCm.GetSelection()))
                self.matplot_panel.switch_save_icon(True)

                #disabe zero contours button
                self.toolbar.EnableTool(wx.ID_ZOOM_100, False)

                # disable contour crop
                self.toolbar.EnableTool(wx.ID_FILE2, False)

                self.show_updated_image(self.current_xyz, self.current_xyzi, flag_update_sideviews=False)

        self.GrandParent.fix_size()

    #slide the range together with the slider
    def on_contourSliderUpdate(self, event):
        self.matplot_panel.set_contours(self.contour_slider.UserValue)
        event.Skip()

    #shift contours left
    def on_contour_shift_left(self, event):
        if self.matplot_panel is None:
            return
        self.matplot_panel.contour_shift(-0.25, self.contour_slider.UserValue)

    #shift contours right
    def on_contour_shift_right(self, event):
        if self.matplot_panel is None:
            return
        self.matplot_panel.contour_shift(0.25, self.contour_slider.UserValue)

    def on_toggle_crop_contour(self, event, pivot=None, start=None, end=None, interval=None):
        if self.matplot_panel is None:
            return
        # untoggle contours

        self.slider_sizer.ShowItems(False)
        self.sizer_midright.Layout()
        # load conoturs if needed
        if not interval is None:
            self.matplot_panel.set_contours(interval)
        self.matplot_panel.set_cmap(self.toolbar.choiceCm.GetString(self.toolbar.choiceCm.GetSelection()))

        if self.toolbar.GetToolState(wx.ID_FILE2):
            self.crop_contour_slider = RangeSlider(parent=self, value=self.matplot_panel.contours.shape[0] / 2,
                                                   minValue=0,
                                                   maxValue=self.matplot_panel.contours.shape[0] - 1,
                                                   pos=wx.DefaultPosition, size=(250, -1),
                                                   style=wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_SELRANGE,
                                                   left_gap=LEFT_GAP, right_gap=RIGHT_GAP)
            self.slider_sizer.Add(self.crop_contour_slider, 1, wx.EXPAND, wx.ALL, 5)
            self.SendSizeEvent()  # needed

            self.Unbind(wx.EVT_SLIDER)

            # self.Bind(wx.EVT_SLIDER, self.on_cropContourSliderUpdate)
            self.crop_contour_slider.Bind(wx.EVT_RIGHT_UP, self.on_cropContourSliderUpdate)
            self.crop_contour_slider.Bind(wx.EVT_LEFT_UP, self.on_cropContourSliderUpdate)

            if not start is None and not end is None and not pivot is None:
                 self.crop_contour_slider.SetValue(pivot)
                 self.crop_contour_slider.SetSelection(start, end)
            else:
                 self.crop_contour_slider.SetSelection(self.crop_contour_slider.Value - 1,
                                                  self.crop_contour_slider.Value + 1)

            self.original_xyz = self.current_xyz
            self.original_xyzi = self.current_xyzi

            if self.crop_contour_slider.SelStart<self.crop_contour_slider.SelEnd:
                self.do_cropContour(self.crop_contour_slider.SelStart, self.crop_contour_slider.SelEnd)
            else:
                self.status_bar.SetStatusText('Make sure that the start value of crop selection is less than the end value')

            self.toolbar.EnableTool(wx.ID_CUT, True)
            self.toolbar.EnableTool(wx.ID_ZOOM_100, False)

            self.Refresh()


        else:
            # if self.threshold_slider.IsShown:
            self.slider_sizer.ShowItems(False)
            self.slider_sizer.Show(self.prev_contour)
            self.slider_sizer.Show(self.contour_slider)
            self.slider_sizer.Show(self.next_contour)
            self.sizer_midright.Layout()

            self.current_xyz = self.original_xyz
            self.current_xyzi = self.original_xyzi

            self.show_updated_image(self.current_xyz, self.current_xyzi, flag_update_sideviews=False)

            self.Unbind(wx.EVT_SLIDER)
            self.Bind(wx.EVT_SLIDER, self.on_contourSliderUpdate)

            self.toolbar.EnableTool(wx.ID_CUT, False)
            self.toolbar.EnableTool(wx.ID_ZOOM_100, True)

            self.matplot_panel.set_contours(1)
            self.contour_slider.slider.SetValue(4)

            self.start_contour_crop_val = None
            self.end_contour_crop_val = None

        self.GrandParent.fix_size()  # fix the size

    # slide the range together with the slider
    def on_cropContourSliderUpdate(self, event):
        self.do_cropContour(self.crop_contour_slider.SelStart, self.crop_contour_slider.SelEnd)
        event.Skip()

    # select contours for thresholding
    def do_cropContour(self, start_range, end_range):

        self.show_updated_image(self.current_xyz, self.current_xyzi, flag_update_sideviews=False)
        # find the contour values responding to threshold range values
        self.start_contour_crop_val = self.matplot_panel.contours[start_range]
        self.end_contour_crop_val = self.matplot_panel.contours[end_range]
        self.matplot_panel.set_contours_for_cropping(
            np.hstack((self.start_contour_crop_val, self.end_contour_crop_val)))

    def on_change_colormap(self, event):
        self.matplot_panel.set_cmap(event.String)
        self.mpl3d_front.set_cmap3D(event.String)
        self.mpl3d_side.set_cmap3D(event.String)
        self.mpl3d_top.set_cmap3D(event.String)

    def rotate(self, R, xyz):
        if xyz is None:
            xyz = self.current_xyz
        c = np.nanmean(xyz,axis=0)
        c = np.matlib.repmat(c,xyz.shape[0],1)
        rotated_xyz = c + np.dot((xyz-c),np.transpose(R))
        return rotated_xyz

    # show updated image after processing operations
    def show_updated_image(self, xyz, xyzi, cnt_step=None, flag_update_sideviews=True):
        self.drop_target.show_updated_image(xyz, xyzi, cnt_step, flag_update_sideviews)

    # fully reload the panels
    def reload_image(self, xyz, xyzi, multiplier):
        self.drop_target.reload_image(xyz, xyzi, multiplier)

    # def update_image(self):
    #     self.Refresh()
    #     self.SendSizeEvent()

    #  change from mpl coordinates to image coordinates
    def change_coord_scale(self, x_mpl, y_mpl):
        x_mpl_max = self.matplot_panel.ax.get_xlim()[1].astype(int)
        y_mpl_max = self.matplot_panel.ax.get_ylim()[1].astype(int)

        x_image_max = self.matplot_panel.xyzi[0].shape[1]
        y_image_max = self.matplot_panel.xyzi[0].shape[0]

        x_image = (x_mpl * x_image_max)/x_mpl_max
        y_image = ((y_mpl_max-y_mpl) * y_image_max)/y_mpl_max

        return x_image, y_image


    # Fires on mouse click on the panel
    def on_press(self, event):
        #event.inaxes.figure.canvas.ReleaseMouse()

        if not event.inaxes:
            return

        if not event.inaxes == self.matplot_panel.ax:
            return

        # quick_measure_mode = self.toolbar.GetToolState(wx.ID_FILE9)
        # polygonal_cropping_mode = self.toolbar.GetToolState(wx.ID_FILE8)
        polygonal_cropping_mode=self.toolbar.GetToolState(wx.ID_ICONIZE_FRAME)
        landmark_placing_mode=self.toolbar.GetToolState(wx.ID_ADD)
        flattening_mode=self.toolbar.GetToolState(wx.ID_CONVERT)
        depth_chart_mode = self.toolbar.GetToolState(wx.ID_FILE6)

        #crop tool is disabled
        self.toolbar.EnableTool(wx.ID_CUT, False)
        #flattenning also disabled
        self.toolbar.EnableTool(wx.ID_BOTTOM, False)

        #delete crop rectangle if exists
        if event.inaxes.patches.__contains__(self.dragRectangle):
            event.inaxes.patches.remove(self.dragRectangle)
            event.inaxes.figure.canvas.draw()
            self.dragRectangle = None

        # # remove flatline if exists
        # if self.matplot_panel.ax.lines.__contains__(self.flatLine):
        #     self.matplot_panel.ax.lines.remove(self.flatLine)
        # self.flatLine = None

        #delete dragline if exists
        if event.inaxes.patches.__contains__(self.dragRectangle):
            event.inaxes.patches.remove(self.dragRectangle)
            event.inaxes.figure.canvas.draw()
            self.dragRectangle = None

        if self.matplot_panel.ax.lines.__contains__(self.dragLine) and (polygonal_cropping_mode == False and depth_chart_mode == False):
            self.matplot_panel.ax.lines.remove(self.dragLine)
            self.matplot_panel.ax.figure.canvas.draw()

        if not (polygonal_cropping_mode or depth_chart_mode):
            #delete polygon if exists
            for line in self.crop_lines:
                if event.inaxes.lines.__contains__(line):
                    event.inaxes.lines.remove(line)

            for cropmark in self.crop_h:
                if event.inaxes.lines.__contains__(cropmark):
                    event.inaxes.lines.remove(cropmark)

            event.inaxes.figure.canvas.draw()
            self.crop_lines = list()
            self.crop_h = list()
            self.crop_xy = np.empty([0, 2])


        if not flattening_mode:
            #delete flat lines if exist
            for i in range(0, self.flat_lines.__len__()):
                self.matplot_panel.ax.lines.remove(self.flat_lines.pop())
            self.flat_lines = list()

        self.status_bar.SetStatusText('')

        # if zoom activated show a message
        if self.matplot_panel.toolbar._active is not None:
            self.status_bar.SetStatusText('Deactivate zoom tools first')
            return

        pos = np.round(np.array([event.xdata, event.ydata]))
        idx = self.hit_test(pos)



        print(self.startDragPos)

        # this needs to go first for the axis not to resize on plotting
        axis = event.inaxes.axis()

        #doubleclick to zero in point Z axis, only if contours are toggled
        if event.dblclick or self.toolbar.GetToolState(wx.ID_ZOOM_100):
            if self.toolbar.GetToolState(wx.ID_FORWARD):
                image_xyz=self.get_image_xyz(event.xdata, event.ydata)
                # 'normalize' z axis: clicked Z=0
                self.current_xyz, self.current_xyzi = self.Parent.Parent.normalize_z_axis(self.current_xyz, self.current_xyzi, image_xyz[2])

                self.show_updated_image(self.current_xyz, self.current_xyzi, self.matplot_panel.cnt_step, flag_update_sideviews=False)
                self.toolbar.ToggleTool(wx.ID_ZOOM_100, False)

        # left-click
        elif event.button == 1:

            self.startDragPos = pos  # save position of the last click for drag operation
            self.matplot_panel.canvas.mpl_disconnect(self.hid)
            self.hid = self.matplot_panel.canvas.mpl_connect('motion_notify_event', self.on_motion_drag)

            # if bool(event.key == 'shift') | self.toolbar.GetToolState(
            #         wx.ID_FILE9):  # if shift is held, or quick measure toggled stop here this is distance measurement so no lanmdmark placement
            #     return
            #
            # if self.toolbar.GetToolState(wx.ID_ADD) is False:  # landmrk placement not toggled
            #     return


            if landmark_placing_mode:

                #enable relevant icons
                self.toolbar.EnableTool(wx.ID_DELETE, True)
                self.toolbar.EnableTool(wx.ID_VIEW_LIST, True)

                if idx is None:
                    idx = self.lmark_xy.shape[0]
                    h, = event.inaxes.plot(pos[0], pos[1], 'o', markersize=self.marker_size)

                    self.lmark_h.append(h)
                    self.lmark_xy = np.vstack((self.lmark_xy, pos))

                    # get the contract color of the background and set it to the landmarker
                    color_value = (self.current_xyzi[2][int(self.lmark_xy[-1][1])][int(self.lmark_xy[-1][0])] - self.matplot_panel.vmin) / (self.matplot_panel.vmax - self.matplot_panel.vmin)

                    if color_value <= 0.5:
                        color_value = color_value + 0.5
                    else:
                        color_value = color_value - 0.5
                    color = cm.jet(color_value)
                    self.lmark_h[idx].set_markerfacecolor(color)

                    txt=event.inaxes.text(pos[0], pos[1], " ", color='white', weight ='bold')
                    self.texts.append(txt)
            elif polygonal_cropping_mode: #if cropping
                if (idx != 0) | (len(self.crop_xy)<3):  #if not finishing the polygon
                    h, = event.inaxes.plot(pos[0], pos[1], 's', markersize=self.marker_size)
                    h.set_markerfacecolor('white')
                    self.crop_h.append(h)
                    self.crop_xy = np.vstack((self.crop_xy, pos))
                    if self.dragLine is not None:
                        self.crop_lines.append(self.dragLine)
                    self.dragLine=None
                else: #if finihsing the polygon
                    self.crop_xy = np.vstack((self.crop_xy, self.crop_xy[0,:]))
                    self.crop_lines.append(self.dragLine)
                    self.dragLine=None
                    self.matplot_panel.canvas.mpl_disconnect(self.hid)
                    self.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)
                    self.toolbar.EnableTool(wx.ID_CUT, True)
            elif depth_chart_mode:  # if depth chart
                if (idx != len(self.crop_xy)-1) or (len(self.crop_xy) <= 1):  # if not finishing
                        if self.crop_xy.shape[0]>0: #if at least one point
                            dcLine, = event.inaxes.plot([self.crop_xy[-1,0], pos[0]],
                                                               [self.crop_xy[-1,1], pos[1]], color='white')
                            self.crop_lines.append(dcLine)
                        self.crop_xy = np.vstack((self.crop_xy, pos))

                        txt = event.inaxes.text(pos[0], pos[1], str(len(self.crop_xy)), color='white', weight='bold')
                        txt.set_path_effects([PathEffects.withStroke(linewidth=1, foreground='k')])
                        self.texts.append(txt)
                else:
                        self.crop_lines.append(self.dragLine)
                        self.dragLine = None
                        self.matplot_panel.canvas.mpl_disconnect(self.hid)
                        self.toolbar.ToggleTool(wx.ID_FILE6, False)
                        self.toolbar.EnableTool(wx.ID_FILE5, True)
            elif flattening_mode:
                #add new line
                if self.flat_lines.__len__()<2:
                    if self.flat_lines.__len__()==1:
                        old_flatLine=self.flat_lines.pop()
                        if old_flatLine._x[0]==old_flatLine._x[1]:
                            self.flat_lines.append(old_flatLine)
                            self.toolbar.EnableTool(wx.ID_BOTTOM, True)
                        else:
                            event.inaxes.lines.remove(old_flatLine)

                    flatLine, = event.inaxes.plot([pos[0], pos[0]],
                                                           [0, self.matplot_panel.Size[1]], color='white')
                    #event.inaxes.figure.canvas.draw()
                    self.flat_lines.append(flatLine)
                else:
                    event.inaxes.lines.remove(self.flat_lines.pop())
                    event.inaxes.lines.remove(self.flat_lines.pop())

            # right-click
        elif event.button == 3:
            if landmark_placing_mode:
                if idx is not None:
                    event.inaxes.lines.remove(self.lmark_h[idx])
                    event.inaxes.texts.remove(self.texts[idx])
                    if self.lmark_h[idx] is not None:
                        #event.inaxes.figure.lines.remove(self.lmark_h[idx])
                        event.inaxes.figure.canvas.draw()
                    else:
                        refresh_flag = False

                    self.lmark_h.pop(idx)
                    self.texts.pop(idx)
                    self.lmark_xy = np.delete(self.lmark_xy, idx, axis=0)

                    if self.lmark_hlight == idx:
                        self.lmark_hlight = None

                    if len(self.lmark_h)==0:
                        # disable relevant icons
                        self.toolbar.EnableTool(wx.ID_DELETE, False)
                        self.toolbar.EnableTool(wx.ID_VIEW_LIST, False)

            elif (polygonal_cropping_mode and len(self.crop_h)>0) or (depth_chart_mode and len(self.texts)>0):

                if polygonal_cropping_mode:
                    event.inaxes.lines.remove(self.crop_h.pop())
                elif depth_chart_mode:
                    event.inaxes.texts.remove(self.texts.pop())

                if len(self.crop_lines)>0:
                    try:
                        event.inaxes.lines.remove(self.crop_lines.pop())
                    except:
                        print("extra crop_line, fix this")

                self.crop_xy = np.delete(self.crop_xy, self.crop_xy.shape[0]-1, axis=0)
                if len(self.crop_xy)>0:
                    self.startDragPos = self.crop_xy[self.crop_xy.shape[0]-1,:]
                    self.matplot_panel.canvas.mpl_disconnect(self.hid)
                    self.hid = self.matplot_panel.canvas.mpl_connect('motion_notify_event', self.on_motion_drag)
                else:
                    self.startDragPos = None
                    self.matplot_panel.canvas.mpl_disconnect(self.hid)
                    if event.inaxes.lines.__contains__(self.dragLine):
                        event.inaxes.lines.remove(self.dragLine)

            elif flattening_mode:
                #add new line
                if self.flat_lines.__len__()<2:
                    if self.flat_lines.__len__() == 1:
                        old_flatLine = self.flat_lines.pop()
                        if old_flatLine._y[0] == old_flatLine._y[1]:
                            self.flat_lines.append(old_flatLine)
                            self.toolbar.EnableTool(wx.ID_BOTTOM, True)
                        else:
                            event.inaxes.lines.remove(old_flatLine)
                    flatLine, = event.inaxes.plot([0, self.matplot_panel.xyzi[0].shape[1]],
                                                           [pos[1], pos[1]], color='white')
                    #event.inaxes.figure.canvas.draw()
                    self.flat_lines.append(flatLine)
                else:
                    event.inaxes.lines.remove(self.flat_lines.pop())
                    event.inaxes.lines.remove(self.flat_lines.pop())

        # this needs to go here for the axis not to resize on plotting
        event.inaxes.axis(axis)

        event.inaxes.figure.canvas.draw()
        return

    # Fires on mouse motion when shift is held
    def on_motion_drag(self, event):
        if not event.inaxes:
            #self.show_updated_image(self.current_xyz, self.current_xyzi)
            #print('drag outside axes')
            return

        if self.matplot_panel.ax.lines.__contains__(self.dragLine):
            self.matplot_panel.ax.lines.remove(self.dragLine)
        if self.matplot_panel.ax.patches.__contains__(self.dragRectangle):
            self.matplot_panel.ax.patches.remove(self.dragRectangle)

        if not event.inaxes == self.matplot_panel.ax:
            return

        # if zoom activated show a message
        if self.matplot_panel.toolbar._active is not None:
            self.status_bar.SetStatusText('Deactivate zoom tools first')
            return

        rectangular_cropping_mode=self.toolbar.GetToolState(wx.ID_FILE8)
        quick_measure_mode = self.toolbar.GetToolState(wx.ID_FILE9)
        polygonal_cropping_mode = self.toolbar.GetToolState(wx.ID_ICONIZE_FRAME)

        shift_held = event.key == 'shift'
        if shift_held or polygonal_cropping_mode or quick_measure_mode:
            self.dragLine, = event.inaxes.plot([self.startDragPos[0], event.xdata], [self.startDragPos[1], event.ydata],color='white')
            event.inaxes.figure.canvas.draw()

            distance, unit = self.get_distance(np.hstack((self.startDragPos[0], self.startDragPos[1])), np.hstack((event.xdata, event.ydata)))
            self.distance = distance
            self.status_bar.SetStatusText(str(self.distance) + unit)
        # elif polygonal_cropping_mode:
        #     self.dragLine, = event.inaxes.plot([self.startDragPos[0], event.xdata], [self.startDragPos[1], event.ydata],color='white')
        #     event.inaxes.figure.canvas.draw()
        elif rectangular_cropping_mode:
            width = event.xdata-self.startDragPos[0]
            height = event.ydata-self.startDragPos[1]
            self.dragRectangle = event.inaxes.add_patch(Rectangle((self.startDragPos[0], self.startDragPos[1]), width, height, alpha = 1, fill=False))
            self.toolbar.EnableTool(wx.ID_CUT, True)
        event.inaxes.figure.canvas.draw()

    # Fires on mouse button release
    def on_release(self, event):

        if not (self.toolbar.GetToolState(wx.ID_ICONIZE_FRAME) or self.toolbar.GetToolState(wx.ID_FILE6)):
            self.matplot_panel.canvas.mpl_disconnect(self.hid)

            if not event.inaxes:
                return

            #  remove the dragged line if exists and show distance between two points in status bar and copy to clipboard
            if self.matplot_panel.ax.lines.__contains__(self.dragLine):
                # self.matplot_panel.ax.lines.remove(self.dragLine)
                # self.matplot_panel.ax.figure.canvas.draw()

                self.status_bar.SetStatusText(self.status_bar.GetStatusText() + ' Copied to clipboard.')
                wx.MessageBox(self.status_bar.GetStatusText(), 'Distance',
                              wx.OK | wx.ICON_INFORMATION)
                if IS_WIN:
                    r = Tk()
                    r.withdraw()
                    r.clipboard_clear()
                    r.clipboard_append(str(self.distance))
                    r.destroy()

    def hit_test(self, pos):

        polygonal_cropping_mode=self.toolbar.GetToolState(wx.ID_ICONIZE_FRAME)
        depth_chart_mode = self.toolbar.GetToolState(wx.ID_FILE6)

        # if no landmark or cropmarks exist
        if (len(self.lmark_xy) == 0) & (len(self.crop_xy) == 0):
            # print('hit_test(): empty landmark')
            idx = None

        # mouse over existing landmark?
        else:

            if polygonal_cropping_mode or depth_chart_mode:
                idx = np.where(
                    (np.abs(self.crop_xy[:, 0] - pos[0]) <= self.matplot_panel.xthrs) &
                    (np.abs(self.crop_xy[:, 1] - pos[1]) <= self.matplot_panel.ythrs)
                )
            else:
                idx = np.where(
                    (np.abs(self.lmark_xy[:, 0] - pos[0]) <= self.matplot_panel.xthrs) &
                    (np.abs(self.lmark_xy[:, 1] - pos[1]) <= self.matplot_panel.ythrs)
                )

            # idx keeps an index of the landmark
            if idx[0].size == 0:
                idx = None
            else:
                idx = idx[0][0]

        return idx

    # get real distance between 2 points
    def get_distance(self, start, end):
        coords_interpolated_start = start.astype(int)
        coords_interpolated_end = end.astype(int)


        # need to convert height coordinates
        # height coordinate in the image starts from the bottom!
        coords_interpolated_start[1] = self.matplot_panel.xyzi[0].shape[0]- coords_interpolated_start[1]
        coords_interpolated_end[1] = self.matplot_panel.xyzi[0].shape[0]- coords_interpolated_end[1]

        x = self.matplot_panel.xyzi[0]
        y = self.matplot_panel.xyzi[1]

        #try:
        ystart=x[0, coords_interpolated_start[0]]
        yend=x[0, coords_interpolated_end[0]]
        xstart=y[coords_interpolated_start[1], 0]
        xend=y[coords_interpolated_end[1], 0]
        #except:
        #    return -1, ' endpoint outside image'

        #print([xstart, xend, ystart, yend])

        distance = math.hypot(xstart - xend, ystart - yend)
        distance = round(distance, 2)
        if self.matplot_panel.multiplier == 1:
            unit = ' mm.'
        elif self.matplot_panel.multiplier == 10:
            unit = ' cm.'
        elif self.matplot_panel.multiplier == 100:
            unit = ' dm.'
        else:
            unit = ' mm.'

        return distance, unit

    # get real image xyz from the click coordinates
    def get_image_xyz(self, x_click, y_click):
        # converting height coordinates
        # height coordinate in the image starts from the bottom!
        # column = x_click
        # row = self.matplot_panel.xyzi[0].shape[0] - y_click
        #
        # x = self.matplot_panel.xyzi[0][row, column]
        # y = self.matplot_panel.xyzi[1][row, column]
        # z = self.matplot_panel.xyzi[2][row, column]

        x = self.matplot_panel.xyzi[0][y_click.astype(int), x_click.astype(int)]
        y = self.matplot_panel.xyzi[1][y_click.astype(int), x_click.astype(int)]
        z = self.matplot_panel.xyzi[2][y_click.astype(int), x_click.astype(int)]

        return x, y, z

    def reset(self):
        # clear main panel
        if hasattr(self.panel_main, 'mpl') and isinstance(self.panel_main.mpl, MatplotPanel):
            self.panel_main.mpl.delete_figure()
            del self.panel_main.mpl

        self.sizer_main.Clear(True)

        # clear side views
        if self.mpl3d_front is not None:
            self.mpl3d_front.delete_figure()
        if self.mpl3d_side is not None:
            self.mpl3d_side.delete_figure()
        if self.mpl3d_top is not None:
            self.mpl3d_top.delete_figure()
        self.sizer_top.Clear(True)
        self.sizer_front.Clear(True)
        self.sizer_side.Clear(True)

        self.threshold_slider = None
        self.contour_slider = None

        self.refresh_flag = True

        self.mayavi_panel = None
        self.matplot_panel = None
        self.mpl3d_front = None
        self.mpl3d_top = None
        self.mpl3d_side = None

        # file attributes
        self.current_xyz = None
        self.current_xyzi = None
        self.current_rgb = None
        self.original_xyz = None
        self.original_xyzi = None
        self.original_rgb = None
        self.current_fname = None

        self.rotate_mode = False

        # dragging and cropping stuff
        self.dragLine = None
        self.startDragPos = [0, 0]
        self.hid = None  # for mousedrag event
        self.dragRectangle = None
        self.crop_h = list()  # crop points
        self.crop_xy = np.empty([0, 2])  # crop point coordinates
        self.crop_lines = list()  # crop lines

        # camera angles
        self.yaw = 0
        self.pitch = 0
        self.roll = 0

        # for landmarks
        self.lmark_active = None  # index of active/selected landmark
        self.lmark_hlight = None  # index of highlighted landmark (mouse-over)
        self.texts= list()
        self.lmark_h = list()  #
        self.lmark_xy = np.empty([0, 2])  #
        self.landmarkDistances = np.empty([0, 2])
        self.landmarkRealCoords = np.empty([0, 2])

        self.toolbar.init_tool_states()
        self.csv_edited = False


def euler2mat(z, y, x):
    # from transform3d
    # ''' Return matrix for rotations around z, y and x axes
    #
    # Uses the z, then y, then x convention above
    #
    # Parameters
    # ----------
    # z : scalar
    #    Rotation angle in radians around z-axis (performed first)
    # y : scalar
    #    Rotation angle in radians around y-axis
    # x : scalar
    #    Rotation angle in radians around x-axis (performed last)
    #
    # Returns
    # -------
    # M : array shape (3,3)
    #    Rotation matrix giving same rotation as for given angles
    #
    # Examples
    # --------
    # >>> zrot = 1.3 # radians
    # >>> yrot = -0.1
    # >>> xrot = 0.2
    # >>> M = euler2mat(zrot, yrot, xrot)
    # >>> M.shape == (3, 3)
    # True
    #
    # The output rotation matrix is equal to the composition of the
    # individual rotations
    #
    # >>> M1 = euler2mat(zrot, 0, 0)
    # >>> M2 = euler2mat(0, yrot, 0)
    # >>> M3 = euler2mat(0, 0, xrot)
    # >>> composed_M = np.dot(M3, np.dot(M2, M1))
    # >>> np.allclose(M, composed_M)
    # True
    #
    # When applying M to a vector, the vector should column vector to the
    # right of M.  If the right hand side is a 2D array rather than a
    # vector, then each column of the 2D array represents a vector.
    #
    # >>> vec = np.array([1, 0, 0]).reshape((3,1))
    # >>> v2 = np.dot(M, vec)
    # >>> vecs = np.array([[1, 0, 0],[0, 1, 0]]).T # giving 3x2 array
    # >>> vecs2 = np.dot(M, vecs)
    #
    # Rotations are counter-clockwise.
    #
    # >>> zred = np.dot(euler2mat(np.pi/2, 0, 0), np.eye(3))
    # >>> np.allclose(zred, [[0, -1, 0],[1, 0, 0], [0, 0, 1]])
    # True
    # >>> yred = np.dot(euler2mat(0, np.pi/2, 0), np.eye(3))
    # >>> np.allclose(yred, [[0, 0, 1],[0, 1, 0], [-1, 0, 0]])
    # True
    # >>> xred = np.dot(euler2mat(0, 0, np.pi/2), np.eye(3))
    # >>> np.allclose(xred, [[1, 0, 0],[0, 0, -1], [0, 1, 0]])
    # True
    #
    # Notes
    # -----
    # The direction of rotation is given by the right-hand rule (orient
    # the thumb of the right hand along the axis around which the rotation
    # occurs, with the end of the thumb at the positive end of the axis;
    # curl your fingers; the direction your fingers curl is the direction
    # of rotation).  Therefore, the rotations are counterclockwise if
    # looking along the axis of rotation from positive to negative.
    # '''
    Ms = []
    if z:
        cosz = math.cos(z)
        sinz = math.sin(z)
        Ms.append(np.array(
                [[cosz, -sinz, 0],
                 [sinz, cosz, 0],
                 [0, 0, 1]]))
    if y:
        cosy = math.cos(y)
        siny = math.sin(y)
        Ms.append(np.array(
                [[cosy, 0, siny],
                 [0, 1, 0],
                 [-siny, 0, cosy]]))
    if x:
        cosx = math.cos(x)
        sinx = math.sin(x)
        Ms.append(np.array(
                [[1, 0, 0],
                 [0, cosx, -sinx],
                 [0, sinx, cosx]]))
    if Ms:
        return reduce(np.dot, Ms[::-1])
    return np.eye(3)


def linethrupts(p1, p2):
    C = 1
    t = (p1[1]-p2[1])/(p1[0]-p2[0])
    B = -C/(p2[1]-p2[0]*t)
    A = -B*t
    return A, B, C


class ProcessorToolbar(wx.ToolBar):
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent=parent, id=wx.ID_ANY)


        self.AddLabelTool(wx.ID_OPEN, 'Import files...', wx.Bitmap('icons\\import.png'), shortHelp="Import files...", longHelp="Import files...")
        #self.AddLabelTool(wx.ID_SAVE, 'Save', wx.Bitmap('icons\\save.png'), shortHelp="Save", longHelp="Save")
        self.AddLabelTool(wx.ID_SAVEAS, 'Save as...', wx.Bitmap('icons\\save-as-copy.png'), shortHelp="Save as...", longHelp="Save as...")

        if platform.system().lower() == 'windows': self.AddSeparator()
        sep_size = (2, self.Size[1])
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        if platform.system().lower() == 'windows': self.AddSeparator()

        self.AddCheckLabelTool(wx.ID_FIND, 'Toggle 3D view on/off', wx.Bitmap('icons\\isometric-view.png'), shortHelp="Toggle 3D view on/off", longHelp="Toggle 3D view on/off")
        if platform.system().lower() == 'windows': self.AddSeparator()
        self.AddLabelTool(wx.ID_REDO, 'Invert', wx.Bitmap('icons\\invert.png'), shortHelp="Invert", longHelp="Invert")
        self.AddLabelTool(wx.ID_UP, 'Auto rotate', wx.Bitmap('icons\\auto-rotate.png'), shortHelp="Auto rotate", longHelp="Auto rotate")
        self.AddLabelTool(wx.ID_DOWN, 'Rotate 90 degrees', wx.Bitmap('icons\\apply-rotation.png'), shortHelp="Rotate 90 degrees", longHelp="Rotate 90 degrees")

        u = self.scale_bitmap(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD), 36, 36)
        self.AddLabelTool(wx.ID_BACKWARD, 'Mirror image', u, shortHelp="Mirror image", longHelp="Mirror image")


        if platform.system().lower() == 'windows': self.AddSeparator()
        sep_size = (2, self.Size[1])
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        if platform.system().lower() == 'windows': self.AddSeparator()

        self.AddCheckLabelTool(wx.ID_FILE8, 'Rectangular crop', wx.Bitmap('icons\\crop-by-rectangle.png'),
                               shortHelp="Rectangular crop", longHelp="Rectangular crop")
        self.AddCheckLabelTool(wx.ID_ICONIZE_FRAME, 'Polygonal crop', wx.Bitmap('icons\\crop-by-polygon.png'),
                               shortHelp="Polygonal crop", longHelp="Polygonal crop")
        self.AddLabelTool(wx.ID_CUT, 'Crop selection', wx.Bitmap('icons\\cut.png'),
                          shortHelp="Crop selection", longHelp="Crop selection")

        if platform.system().lower() == 'windows': self.AddSeparator()
        sep_size = (2, self.Size[1])
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        if platform.system().lower() == 'windows': self.AddSeparator()

        self.AddCheckLabelTool(wx.ID_ADD, 'Place landmarks', wx.Bitmap('icons\\place-landmark.png'),
                               shortHelp="Toggle landmark placing mode", longHelp="Toggle landmark placing mode")
        self.AddLabelTool(wx.ID_DELETE, 'Delete all landmarks', wx.Bitmap('icons\\delete-all-landmarks.png'), shortHelp="Delete all landmarks", longHelp="Delete all landmarks")
        self.AddLabelTool(wx.ID_VIEW_LIST, 'Landmark distances', wx.Bitmap('icons\\export-landmark-distances.png'), shortHelp="Landmark distances", longHelp="Landmark distances")

        if platform.system().lower() == 'windows': self.AddSeparator()
        sep_size = (2, self.Size[1])
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL, size=sep_size))
        if platform.system().lower() == 'windows': self.AddSeparator()

        u=wx.ImageFromBitmap(wx.Bitmap('icons\\landmarks-graph.png'))
        u = u.Scale(36, 36, wx.IMAGE_QUALITY_HIGH)
        u = wx.BitmapFromImage(u)
        self.AddCheckLabelTool(wx.ID_FILE6, 'Depth chart landmarks', u, shortHelp="Depth chart landmarks", longHelp="Depth chart landmarks")


        u = wx.ImageFromBitmap(wx.Bitmap('icons\\graph.png'))
        u = u.Scale(36, 36, wx.IMAGE_QUALITY_HIGH)
        u = wx.BitmapFromImage(u)
        self.AddLabelTool(wx.ID_FILE5, 'Depth chart', u, shortHelp="Depth chart", longHelp="Depth chart")
        self.AddCheckLabelTool(wx.ID_FILE9, 'Quick measure', wx.Bitmap('icons\\quick-measure.png'), shortHelp="Quick measure", longHelp="Quick measure")
        self.AddCheckLabelTool(wx.ID_FILE7, 'Black-and-white conversion', wx.Bitmap('icons\\3d-to-2d.png'), shortHelp="Black-and-white conversion", longHelp="Black-and-white conversion")

        u=self.scale_bitmap(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE), 36, 36)
        self.AddCheckLabelTool(wx.ID_CONVERT, 'Flatten image', u, shortHelp="Flatten image", longHelp="Flatten image")
        u = self.scale_bitmap(wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE), 36, 36)
        self.AddLabelTool(wx.ID_BOTTOM, 'Execute flattening', u, shortHelp="Execute flattening", longHelp="Execute flattening")

        self.AddCheckLabelTool(wx.ID_FORWARD, 'Toggle contours', wx.Bitmap('icons\\display-contours.png'),
                       shortHelp="Toggle contours",
                       longHelp="Toggle contours")
        self.AddCheckLabelTool(wx.ID_FILE2, 'Contour crop', wx.Bitmap('icons\\crop-by-contour.png'),
                               shortHelp="Contour crop",
                               longHelp="Contour crop")
        self.AddCheckLabelTool(wx.ID_ZOOM_100, 'Zero contours', wx.Bitmap('icons\\set-zero-contour.png'),
                               shortHelp="Zero contours",
                               longHelp="Set contours level to zero")
        self.AddCheckLabelTool(wx.ID_FILE1, 'Toggle scalebar', wx.Bitmap('icons\\add-scale-bar.png'), shortHelp="Toggle scalebar", longHelp="Toggle scalebar")
        u = self.scale_bitmap(wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW), 36, 36)
        self.AddCheckLabelTool(wx.ID_FILE3, 'Toggle 1 cm grid', u, shortHelp="Toggle 1 cm grid", longHelp="Toggle 1 cm grid")



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

        #all the buttons except Open are disabled at the start
        self.init_tool_states()

    def init_tool_states(self):
        self.EnableTool(wx.ID_SAVEAS, False)
        self.EnableTool(wx.ID_FILE8, False)
        self.EnableTool(wx.ID_FIND, False)
        self.EnableTool(wx.ID_REDO, False)
        self.EnableTool(wx.ID_UP, False)
        self.EnableTool(wx.ID_DOWN, False)
        self.EnableTool(wx.ID_BACKWARD, False)
        self.EnableTool(wx.ID_ICONIZE_FRAME, False)
        self.EnableTool(wx.ID_CUT, False)
        self.EnableTool(wx.ID_ADD, False)
        self.EnableTool(wx.ID_DELETE, False)
        self.EnableTool(wx.ID_VIEW_LIST, False)
        self.EnableTool(wx.ID_FILE9, False)
        self.EnableTool(wx.ID_FILE7, False)
        self.EnableTool(wx.ID_ZOOM_100, False)
        self.EnableTool(wx.ID_FILE1, False)
        self.EnableTool(wx.ID_FILE2, False)
        self.EnableTool(wx.ID_FILE3, False)
        self.EnableTool(wx.ID_FORWARD, False)
        self.EnableTool(wx.ID_BOTTOM, False)
        self.EnableTool(wx.ID_CONVERT, False)
        self.EnableTool(wx.ID_FILE5, False)
        self.EnableTool(wx.ID_FILE6, False)
        self.choiceCm.Enable(False)

        self.choiceCm.SetSelection(0)

    # scale image, potentially needed for menu item (not used here)
    def scale_bitmap(self, bitmap, width, height):
        image = wx.ImageFromBitmap(bitmap)
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        result = wx.BitmapFromImage(image)
        return result

# run parallel job
def run_job(items, obj):
    cnt = len(items)
    cores = multiprocessing.cpu_count()

    if cnt > 1 and cores > 1:
        print('Using multiprocess')
        # TODO proper multiprocessing
        # for item in items:
        #     p = multiprocessing.Process(target=obj.__call__, args=item)
        #     a = p.start()
        #     print("process done")
        pool = multiprocessing.Pool(processes=min(cnt, cores))
        #result = pool.apply_async(obj, items)
        result = pool.map(obj, items)
        pool.close()
        #pool.join()
    else:
        print('Using single process')
        result = list()
        for item in items:
            result.append(obj.__call__(item))
    return result


class MyDropTarget(wx.TextDropTarget):


    def __init__(self, window):
        wx.TextDropTarget.__init__(self)
        self.window = window

        self.frame = window.GetParent()
        self.hid = None  # motion_notify_event handler
        self.Shift_is_held = False  # whether shift is held
        self.rotate_mode = False




    # Fires when something is dropped on the panel
    def OnDropText(self, x, y, data):

        # renew main panel when opening new files

        panel = self.window
        sizer = panel.GetSizer()

        try:
            data = int(data)
        except:
            #data = int(data[:-1])
            temp = re.findall('(-?\d+)',data)
            data = int(temp[0])
            # on OS X an extra or more character is added at the end

        mpl_src = self.frame.prints[int(data)]

        # If the drop source is already being used in either master or source, do nothing
        if mpl_src.used:
            return


        if self.frame.matplot_panel is not None:
            self.frame.matplot_panel.delete_figure()  # delete old figure to free memory

        if len(self.window.Children)>0:
            self.window.DestroyChildren()

        # Create a new plot, add it to a cleared sizer (clearing e.g. the static text) and subscribe to the event
        panel.mpl = MatplotPanel(self.window, mpl_src.xyzi, mpl_src.xyz, mpl_src.multiplier, mpl_src.precision, (1, 1),  mpl_src,  mpl_src.title, mpl_src.fname, pid=None, current_vmin=mpl_src.current_vmin, current_vmax=mpl_src.current_vmax)
        #panel.myv = MayaviPanel(self.window, mpl_src.xyzi, multiplier=mpl_src.multiplier, title=mpl_src.title, fname=mpl_src.fname, lmark_xy=None)


        self.frame.matplot_panel = panel.mpl
        self.frame.mayavi_panel = None

        # self.window.Children[0].Show()
        # self.window.Children[1].Hide()

        sizer.Clear(True)
        self.frame.slider_sizer.Clear(True)



        self.frame.current_xyz = mpl_src.xyz
        self.frame.current_xyzi = mpl_src.xyzi
        self.frame.current_fname = mpl_src.fname
        self.frame.original_xyz = mpl_src.xyz
        self.frame.original_xyzi = mpl_src.xyzi

        self.rotate_mode = False

        self.frame.toolbar.ToggleTool(wx.ID_FILE7, False)
        self.frame.toolbar.ToggleTool(wx.ID_FILE1, False)
        self.frame.toolbar.ToggleTool(wx.ID_FILE3, False)
        self.frame.toolbar.ToggleTool(wx.ID_ZOOM_100, False)
        self.frame.toolbar.ToggleTool(wx.ID_FILE8, False)
        self.frame.toolbar.ToggleTool(wx.ID_FILE9, False)
        self.frame.toolbar.ToggleTool(wx.ID_FIND, False)
        self.frame.toolbar.ToggleTool(wx.ID_ADD, False)
        self.frame.toolbar.ToggleTool(wx.ID_FORWARD, False)
        self.frame.toolbar.ToggleTool(wx.ID_CONVERT, False)
        self.frame.toolbar.ToggleTool(wx.ID_FILE2, False)
        self.frame.toolbar.ToggleTool(wx.ID_ICONIZE_FRAME, False)
        self.frame.toolbar.ToggleTool(wx.ID_FILE6, False)


        # add plot panel
        sizer.Add(panel.mpl, 1, wx.EXPAND | wx.ALL, 5)
        panel.mpl.canvas.mpl_connect('button_press_event', self.frame.on_press)
        panel.mpl.canvas.mpl_connect('button_release_event', self.frame.on_release)

        # add plot title to the sizer
        txt = wx.StaticText(panel, wx.ID_ANY, mpl_src.title, style=wx.ALIGN_CENTER)
        txt.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt.SetForegroundColour((128, 128, 128))
        sizer.Add(txt, flag=wx.CENTER)

        self.create_side_panels(mpl_src)

        #set colormap selection jet active
        self.frame.toolbar.choiceCm.SetSelection(0)

        # remove landmarks
        self.frame.lmark_h = list()  #
        self.frame.lmark_xy = np.empty([0, 2])  #
        self.frame.texts = list()

        #disable some icons
        self.frame.toolbar.EnableTool(wx.ID_CUT, False)
        self.frame.toolbar.EnableTool(wx.ID_DELETE, False)
        self.frame.toolbar.EnableTool(wx.ID_VIEW_LIST, False)
        self.frame.toolbar.EnableTool(wx.ID_ZOOM_100, False)
        self.frame.toolbar.EnableTool(wx.ID_FILE2, False)
        self.frame.toolbar.EnableTool(wx.ID_BOTTOM, False)

        #enable icons
        self.frame.toolbar.EnableTool(wx.ID_SAVEAS, True)
        self.frame.toolbar.EnableTool(wx.ID_FIND, True)
        self.frame.toolbar.EnableTool(wx.ID_REDO, True)
        self.frame.toolbar.EnableTool(wx.ID_UP, True)
        self.frame.toolbar.EnableTool(wx.ID_DOWN, True)
        self.frame.toolbar.EnableTool(wx.ID_BACKWARD, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE8, True)
        self.frame.toolbar.EnableTool(wx.ID_ICONIZE_FRAME, True)
        self.frame.toolbar.EnableTool(wx.ID_ADD, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE6, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE9, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE7, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE1, True)
        self.frame.toolbar.EnableTool(wx.ID_FILE3, True)
        self.frame.toolbar.EnableTool(wx.ID_FORWARD, True)

        self.frame.toolbar.EnableTool(wx.ID_CONVERT, True)
        self.frame.toolbar.choiceCm.Enable(True)

        self.frame.Refresh()

        # Force redraw: windows.Refresh() doesn't seem to work
        self.window.SendSizeEvent() #needed
        self.frame.GrandParent.fix_size() # fix resizing to be sure

    #fast routine to show the updated image without reloading all the panels
    def show_updated_image(self, xyz, xyzi, cnt_step, flag_update_sideviews):

        self.frame.matplot_panel.update_image(xyzi,xyz,step=cnt_step)

        if flag_update_sideviews:
            self.frame.mpl3d_front.update_image3D(xyzi, xyz)
            self.frame.mpl3d_side.update_image3D(xyzi, xyz)
            self.frame.mpl3d_top.update_image3D(xyzi, xyz)

        self.frame.current_xyz = xyz
        self.frame.current_xyzi = xyzi
        self.rotate_mode = False

        #self.update_side_panels1(self.frame.matplot_panel)
        self.frame.matplot_panel.Refresh()
        self.frame.Refresh()



    # Switch view between mayavi (for rotation) and matplotlib all other operations
    def switch_view(self):
        panel = self.window
        sizer = panel.GetSizer()
        if self.rotate_mode:  # if in rotate mode switch back to
            self.rotate_mode = False
            self.window.Children[0].Show()
            self.window.Children[2].Hide()
        else:
            if self.frame.mayavi_panel is None:
                panel.myv = MayaviPanel(self.window, self.frame.current_xyzi, panel.mpl.multiplier, title=os.path.basename(self.frame.current_fname), fname=self.frame.current_fname, lmark_xy=None, memory=self.frame.Parent.Parent.video_memory)
                self.frame.mayavi_panel = panel.myv
                panel.myv.mayavi_view.scene.scene_editor.actions[2].remove(
                    panel.myv.mayavi_view.scene.scene_editor.actions[2]._get_items()[1])
                #add mayavi panel to the sizer for auto resizing
                sizer.Insert(0, panel.myv, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
                mlab.view(azimuth=90, elevation=180)
            self.rotate_mode = True
            self.window.Children[2].Show()
            self.window.Children[0].Hide()
        self.frame.Refresh()
        #self.frame.GrandParent.Layout()
        #self.frame.GrandParent.Fit()
        #self.frame.SendSizeEvent()

    #fully reload all the panels
    def reload_image(self, xyz, xyzi, multiplier, precision):
        panel = self.window
        sizer = panel.GetSizer()

        if len(self.window.Children)>0:
            self.window.DestroyChildren()


        # Create a new plot, add it to a cleared sizer (clearing e.g. the static text) and subscribe to the event
        panel.mpl = MatplotPanel(self.window, xyzi, xyz, multiplier, precision, (1, 1),  title=os.path.basename(self.frame.current_fname), fname=self.frame.current_fname, pid=None)
       #panel.myv = MayaviPanel(self.window, xyzi, multiplier=multiplier, title=os.path.basename(self.frame.current_fname), fname=self.frame.current_fname, lmark_xy=None)
       # mlab.view(azimuth=90, elevation=180)

        self.frame.matplot_panel = panel.mpl
        self.frame.mayavi_panel = None

        self.frame.matplot_panel.set_cmap(self.frame.toolbar.choiceCm.GetString(self.frame.toolbar.choiceCm.GetSelection()))
        # self.window.Children[0].Show()
        # self.window.Children[1].Hide()

        sizer.Clear(True)

        # add plot title to the sizer
        txt = wx.StaticText(panel, wx.ID_ANY, panel.mpl.title, style=wx.ALIGN_CENTER)
        txt.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt.SetForegroundColour((128, 128, 128))
        sizer.Add(txt, flag=wx.CENTER)

        self.frame.current_xyz = xyz
        self.frame.current_xyzi = xyzi

        self.rotate_mode = False

        # add plot panel
        sizer.Add(panel.mpl, 9, wx.EXPAND | wx.ALL , 5)


        panel.mpl.canvas.mpl_connect('button_press_event', self.frame.on_press)
        panel.mpl.canvas.mpl_connect('button_release_event', self.frame.on_release)

        self.create_side_panels(self.frame.matplot_panel)

        self.frame.Refresh()

        # Force redraw: windows.Refresh() doesn't seem to work
        self.window.SendSizeEvent()

    # update side panels
    def create_side_panels(self, mpl_src):
        if self.frame.mpl3d_front is not None:
            self.frame.mpl3d_front.delete_figure()
        if self.frame.mpl3d_side is not None:
            self.frame.mpl3d_side.delete_figure()
        if self.frame.mpl3d_top is not None:
            self.frame.mpl3d_top.delete_figure()

        self.frame.sizer_front.Clear(True)
        self.frame.sizer_side.Clear(True)
        self.frame.sizer_top.Clear(True)

        # creation of the side panels separately - slowish, could be improved
        self.frame.mpl3d_front = MatplotPanel3D(self.frame.panel_front, mpl_src.xyzi, mpl_src.xyz, mpl_src.multiplier, 0, 90)
        self.frame.mpl3d_side = MatplotPanel3D(self.frame.panel_side, mpl_src.xyzi, mpl_src.xyz, mpl_src.multiplier, 0, 0)
        self.frame.mpl3d_top = MatplotPanel3D(self.frame.panel_top, mpl_src.xyzi, mpl_src.xyz, mpl_src.multiplier, 45, 45)

        txt1 = wx.StaticText(self.frame.panel_front, wx.ID_ANY, 'Front View', style=wx.ALIGN_CENTER)
        txt1.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt1.SetForegroundColour((128, 128, 128))

        self.frame.sizer_front.Add(txt1, flag=wx.CENTER)
        self.frame.sizer_front.Add(self.frame.mpl3d_front, 1, wx.EXPAND, wx.ALL, 5)
        self.frame.panel_front.Layout()


        txt2 = wx.StaticText(self.frame.panel_side, wx.ID_ANY, 'Side View', style=wx.ALIGN_CENTER)
        txt2.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
        txt2.SetForegroundColour((128, 128, 128))
        self.frame.sizer_side.Add(txt2, flag=wx.CENTER)
        self.frame.sizer_side.Add(self.frame.mpl3d_side, 1, wx.EXPAND, wx.ALL, 5)
        self.frame.panel_side.Layout()


        txt3 = wx.StaticText(self.frame.panel_top, wx.ID_ANY, 'Isometric View', style=wx.ALIGN_CENTER)
        txt3.SetForegroundColour((128, 128, 128))
        txt3.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.frame.sizer_top.Add(txt3, flag=wx.CENTER)
        self.frame.sizer_top.Add(self.frame.mpl3d_top, 1, wx.EXPAND, wx.ALL, 5)
        self.frame.panel_top.Layout()

class RangeSlider(wx.Slider):

    def __init__(self, left_gap, right_gap, *args, **kwargs):
        wx.Slider.__init__(self, *args, **kwargs)
        self.left_gap = left_gap
        self.right_gap = right_gap
        self.Bind(wx.EVT_LEFT_UP, self.on_left_click)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        self.Bind(wx.EVT_SCROLL_PAGEUP, self.on_pageup)
        self.Bind(wx.EVT_SCROLL_PAGEDOWN, self.on_pagedown)
        self.Bind(wx.EVT_SCROLL_THUMBTRACK, self.on_slide)

        self.slider_value=self.Value
        self.is_dragging=False

    def linapp(self, x1, x2, y1, y2, x):
        proportion=float(x - x1) / (x2 - x1)
        length = y2 - y1
        return round(proportion*length + y1)

    # if left click set the start of selection
    def on_left_click(self, e):

        if not self.is_dragging: #if this wasn't a dragging operation
            position = self.get_position(e)
            if position <= self.SelEnd:
                self.SetSelection(position, self.SelEnd)
            else:
                self.SetSelection(self.SelEnd, position)
        else:

            self.is_dragging = False

        evt = SelectionChangedEvent()
        wx.PostEvent(self, evt)
        e.Skip()

    # if right click set the end of selection
    def on_right_click(self, e):
        position = self.get_position(e)
        if position >= self.SelStart:
            self.SetSelection(self.SelStart, position)
        else:
            self.SetSelection(position, self.SelStart)
        e.Skip()

    # drag the selection along when sliding
    def on_slide(self, e):
        self.is_dragging=True
        delta_distance=self.Value-self.slider_value
        self.SetSelection(self.SelStart+delta_distance, self.SelEnd+delta_distance)
        self.slider_value=self.Value

    # disable pageup and pagedown using following functions
    def on_pageup(self, e):
        self.SetValue(self.Value+self.PageSize)

    def on_pagedown(self, e):
        self.SetValue(self.Value-self.PageSize)

    # get click position on the slider scale
    def get_position(self, e):
        click_min = self.left_gap #standard size 9
        click_max = self.GetSize()[0] - self.right_gap #standard size 55
        click_position = e.GetX()
        result_min = self.GetMin()
        result_max = self.GetMax()
        if click_position > click_min and click_position < click_max:
            result = self.linapp(click_min, click_max,
                                 result_min, result_max,
                                 click_position)
        elif click_position <= click_min:
            result = result_min
        else:
            result = result_max

        return result

class FloatSlider(wx.Panel):

    def __init__(self, parent, id, UserMinValue, UserMaxValue, UserValue, increment_factor):
        wx.Panel.__init__(self, parent, id, wx.DefaultPosition, wx.DefaultSize)
        self.parent = parent
        self.increment_factor=increment_factor

        self.UserMinValue = UserMinValue
        self.UserMaxValue = UserMaxValue
        self.UserValue = UserValue

        self.SliderMinValue = UserMinValue*increment_factor
        self.SliderMaxValue = UserMaxValue*increment_factor
        self.SliderValue = UserValue*increment_factor

        self.statxt1 = wx.StaticText(self, wx.ID_ANY, 'left',
        style=wx.ST_NO_AUTORESIZE | wx.ALIGN_LEFT)
        self.statxt2 = wx.StaticText(self, wx.ID_ANY, 'middle',
        style=wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTRE)
        self.statxt3 = wx.StaticText(self, wx.ID_ANY, 'right',
        style=wx.ST_NO_AUTORESIZE | wx.ALIGN_RIGHT)

        self.statxt1.SetLabel(str(self.UserMinValue))
        self.statxt2.SetLabel(str(self.UserValue))
        self.statxt3.SetLabel(str(self.UserMaxValue))

        self.slider = wx.Slider(self, wx.ID_ANY, self.SliderValue, \
        self.SliderMinValue, self.SliderMaxValue, \
        style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS)
        self.slider.SetTickFreq(1)

        self.slider.Bind(wx.EVT_SCROLL, self.OnScroll)

        b = 20
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add(self.statxt1, 1, wx.RIGHT, b)
        hsizer1.Add(self.statxt2, 1, wx.LEFT | wx.RIGHT, b)
        hsizer1.Add(self.statxt3, 1, wx.LEFT, b)

        b = 4
        vsizer1 = wx.BoxSizer(wx.VERTICAL)
        vsizer1.Add(hsizer1, 0, wx.EXPAND | wx.ALL, b)
        vsizer1.Add(self.slider, 0, wx.EXPAND | wx.LEFT | wx.TOP | wx.BOTTOM, b)

        self.SetSizerAndFit(vsizer1)
        #self.parent.SetClientSize((500, vsizer1.GetSize()[1]))
        #self.parent.CentreOnScreen()

    def OnScroll(self, event):
        self.SliderValue = self.slider.GetValue()
        self.UserValue = float(self.SliderValue) / self.increment_factor
        self.statxt2.SetLabel(str(self.UserValue))


# class MyToolbar(NavigationToolbar2TkAgg):
#         def _init_toolbar(self):
#
#     # this was all copied verbatim from backend_tkagg.py
#             xmin, xmax = self.canvas.figure.bbox.intervalx().get_bounds()
#             height, width = 50, xmax - xmin
#             Tk.Frame.__init__(self, master=self.window,
#                               width=width, height=height,
#                               borderwidth=2)
#
#             self.update()  # Make axes menu
#
#             self.bHome = self._Button(text="Home", file="home.ppm",
#                                       command=self.home)
#
#             self.bBack = self._Button(text="Back", file="back.ppm",
#                                       command=self.back)
#
#             self.bForward = self._Button(text="Forward", file="forward.ppm",
#                                          command=self.forward)
#
#             self.bPan = self._Button(text="Pan", file="move.ppm",
#                                      command=self.pan)
#
#             self.bZoom = self._Button(text="Zoom",
#                                       file="zoom_to_rect.ppm",
#                                       command=self.zoom)
#
#             self.bsave = self._Button(text="Save", file="filesave.ppm",
#                                       command=self.save_figure)
#
#             ### now I'm going to add a custom button that calls myfunction
#             self.mybutton = self._Button(text="Save", file="myicon.ppm",
#                                          command=self.myfunction)
#             self.message = Tk.StringVar(master=self)
#             self._message_label = Tk.Label(master=self, textvariable=self.message)
#             self._message_label.pack(side=Tk.RIGHT)
#             self.pack(side=Tk.BOTTOM, fill=Tk.X)
#
#             def myfunction(self, *args):
#                 #this function is called when "mybutton" is clicked
#                 print "You clicked me!"


# class NavigationToolbar(NavigationToolbar2Wx):
#     def __init__(self, plotCanvas):
#         # create the default toolbar
#         NavigationToolbar2Wx.__init__(self, plotCanvas)
#         # remove the unwanted button
#         POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 6
#         self.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)


class NavigationToolbar(NavigationToolbar2TkAgg):
    # only display the buttons we need
    def __init__(self, canvas_, parent_):
        self.toolitems = [t for t in NavigationToolbar2TkAgg.toolitems if
                     t[0] in ('Home', 'Pan', 'Zoom', 'Save')]
        NavigationToolbar2TkAgg.__init__(self, canvas_, parent_)




