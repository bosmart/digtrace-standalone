# -*- coding: utf-8 -*-
__author__ = 'shujiedeng'

import wx
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'wx'

import sys
import os
import shutil
import numpy as np
import numpy.matlib
import multiprocessing
import multiprocessing.pool
import PIL.ExifTags

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

import wx.lib.agw.multidirdialog as MDD
import re
import vtk
from vtk.util.numpy_support import vtk_to_numpy
import glob
from plyfile import PlyData
from mayavi import mlab
from tvtk.api import tvtk
import difflib
from PhotogrammetryPanel import PhotogrammetryPanel
import PhotogrammetryGenerator as pg
import wx.lib.mixins.listctrl  as  listmix

import wx.lib.agw.thumbnailctrl as TC

from distutils.file_util import copy_file
from DecreaseSizeDialog import DecreaseSizeDialog
from InvertOptionsDialog import InvertOptionsDialog
#import EnhancedStatusBar as ESB
#from wx.lib.pubsub import pub

class Photogrammetry(wx.Panel):
    def __init__(self, parent):

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        self.sizer_vert = wx.BoxSizer(wx.VERTICAL)  # main Sizer
        self.toolbar = photogrammetryToolbar(self)  # toolbar
        self.sizer_vert.Add(self.toolbar, 0, wx.EXPAND, wx.EXPAND, 5)

        self.sizer_horiz = wx.BoxSizer(wx.HORIZONTAL)  # middle
        self.sizer_vert.Add(self.sizer_horiz, 4, wx.EXPAND | wx.ALL, 5)

        # The left panel for listing folders
        # self.panel_thumbs = TC.ThumbnailCtrl(self, imagehandler=TC.NativeImageHandler)
        # self.sizer_horiz.Add(self.panel_thumbs, 1, wx.EXPAND | wx.RIGHT, 10)
        # self.panel_thumbs.Bind(TC.EVT_THUMBNAILS_DCLICK, self.OnDoulbleClickThumb)
        self.panel_list = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.SIMPLE_BORDER)
        self.sizer_horiz.Add(self.panel_list, 1, wx.EXPAND | wx.RIGHT, 5)
        # self.list_ctrl = wx.ListCtrl(self.panel_list, size=(-1, 600), style=wx.LC_REPORT|wx.LC_EDIT_LABELS)
        self.list_ctrl = EditableListCtrl(self.panel_list, style=wx.LC_REPORT | wx.NO_BORDER)
        self.list_ctrl.InsertColumn(0, 'Folder')
        self.list_ctrl.InsertColumn(1, 'Path')
        self.list_ctrl.InsertColumn(2, 'sensor size(mm)', width=100)
        self.list_ctrl.InsertColumn(3, 'Downsize?')
        self.list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_sizer.Add(self.list_ctrl, 1, wx.EXPAND)
        self.panel_list.SetSizer(self.list_sizer)
        self.panel_list.Layout()
        self.list_sizer.Fit(self.panel_list)

        # self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.displayThumbs, self.list_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_folder_delete, self.list_ctrl)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_save_input_db, self.list_ctrl)

        # The second left panel for listing images
        self.panel_thumbs = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.SIMPLE_BORDER)
        self.sizer_horiz.Add(self.panel_thumbs, 1, wx.EXPAND | wx.RIGHT, 5)
        self.thumbs_ctrl = TC.ThumbnailCtrl(self.panel_thumbs, imagehandler=TC.NativeImageHandler)
        # self.sizer_horiz.Add(self.thumbs_ctrl, 1, wx.EXPAND | wx.RIGHT, 10)
        self.thumbs_sizer = wx.BoxSizer(wx.VERTICAL)
        self.thumbs_sizer.Add(self.thumbs_ctrl, 1, wx.EXPAND)
        self.panel_thumbs.SetSizer(self.thumbs_sizer)
        self.panel_thumbs.Layout()
        self.thumbs_sizer.Fit(self.panel_thumbs)

        self.thumbs_ctrl.Bind(TC.EVT_THUMBNAILS_DCLICK, self.OnDoulbleClickThumb)
        # self.Bind(wx.EVT_RIGHT_UP, self.show_thumbnail_menu)

        # The middle panel for displaying generated ply
        self.panel_display = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        self.sizer_horiz.Add(self.panel_display, 3, wx.EXPAND, 5)
        self.display = wx.BoxSizer(wx.VERTICAL)
        self.panel_display.SetSizer(self.display)
        self.panel_display.Layout()
        self.display.Fit(self.panel_display)

        # show console output
        #self.panel_console = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize)
        #self.sizer_horiz.Add(self.panel_console, 1, wx.EXPAND | wx.LEFT, 10)
        #style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL
        #log = wx.TextCtrl(self.panel_console, wx.ID_ANY, size=(150, 100), style=style)
        #self.console_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.console_sizer.Add(log, 1, wx.EXPAND)
        #self.panel_console.SetSizer(self.console_sizer)
        #self.panel_console.Layout()
        #self.console_sizer.Fit(self.panel_console)

        # redirect text here
        # sys.stdout = log
        # sys.stderr = log

        # reserved for showing generated csv
        # self.panel_bottom = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SIMPLE_BORDER)
        # self.sizer_vert.Add(self.panel_bottom, 1, wx.EXPAND | wx.ALL, 5)

        self.panel_thumbs_bottom = parent.Parent.panel_thumbs
        self.sizer_thumbs_bottom = parent.Parent.sizer_thumbs
        self.prints = parent.Parent.prints

        self.refresh_flag = True
        self.ply_loading_flag = False

        self.SetSizer(self.sizer_vert)

        self.status_bar = parent.Parent.GetStatusBar()

        self.toolbar.Realize()

        self.Bind(wx.EVT_TOOL, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.on_generate, id=wx.ID_APPLY)
        self.Bind(wx.EVT_TOOL, self.on_scale, id=wx.ID_CONVERT)
        self.Bind(wx.EVT_TOOL, self.on_autorotate, id=self.toolbar.ID_AUTOROTATE)
        self.Bind(wx.EVT_TOOL, self.on_invert, id=self.toolbar.ID_INVERT)
        self.Bind(wx.EVT_TOOL, self.on_crop, id=wx.ID_CUT)
        self.Bind(wx.EVT_TOOL, self.on_3dcrop, id=self.toolbar.ID_3DCROP)
        self.Bind(wx.EVT_TOOL, self.on_measure, id=self.toolbar.ID_MEASURE)
        self.Bind(wx.EVT_TOOL, self.on_saveas, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_TOOL, self.on_delete_outputs, id=wx.ID_DELETE)
        self.toolbar.selectModel.Bind(wx.EVT_CHOICE, self.on_change_model)

        # self.on_drag = parent.Parent.on_drag()

        self.loaded_folder_num = 0
        # photogrammetry panel open file history
        self.popenfilehistory = wx.FileHistory(9)
        self.config_popenfile = wx.Config(localFilename = "pyTrans-popenfile", style=wx.CONFIG_USE_LOCAL_FILE)
        self.popenfilehistory.Load(self.config_popenfile)

        self.generated_ply_path = ""

        # self.incremental_sfm = False
        self.focal_lengths = []

        self.paths = [] # saves the list of folders
        self.path_names = []
        self.new_added_paths = []
        #self.folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, )

        utils_path = os.path.join(os.path.join(os.path.expanduser('~'),"DigTrace"),"utilities")
        self.camera_file_params = os.path.join(os.path.join(os.path.join(os.path.expanduser('~'),"DigTrace"),"utilities"), "sensor_width_camera_database.txt")
        if not os.path.exists(self.camera_file_params):
            if not os.path.exists(utils_path):
                os.makedirs(utils_path)
            copy_file(os.path.join("utilities", "sensor_width_camera_database.txt"),
                      os.path.join(utils_path, "sensor_width_camera_database.txt"))

        self.sensor_size_db = {}
        self.get_sensor_size_db()
        self.fill_size_list = [] # to cache folders that has no sensor size, need to fill by the user
        self.loaded_ply_index = -1

        self.ply_edited = False  # if the displayed ply has been scaled and cropped

        # pub.subscribe(self.updateProgress, "update")
        #progress bar
        # self.progressbar = wx.Gauge(self.status_bar, -1, 100)
        # self.status_bar.AddWidget(self.progressbar, ESB.ESB_ALIGN_RIGHT, ESB.ESB_ALIGN_BOTTOM)
        # self.progressbar.Show(False)

    def reset(self):
        # clear display panels
        self.clean_display_panel()

        # clear image thumbs
        for i in range(self.thumbs_ctrl.GetItemCount()-1, -1, -1):
            self.thumbs_ctrl.RemoveItemAt(i)
        self.panel_thumbs.Refresh()  # force refresh otherwise the image thumbs still stays

        # clear list
        for row in range(self.list_ctrl.GetItemCount()-1, -1, -1):
            self.list_ctrl.DeleteItem(row)

        self.refresh_flag = True

        self.loaded_folder_num = 0

        self.generated_ply_path = ""

        # self.incremental_sfm = False
        self.focal_lengths = []

        self.paths = []
        self.path_names = []
        self.new_added_paths = []

        self.fill_size_list = [] # to cache folders that has no sensor size, need to fill by the user
        self.loaded_ply_index = -1

        self.ply_edited = False

        self.toolbar.init_tool_states()

    #  Open new file
    def on_open(self, event, folder_history=None):
        if self.popenfilehistory.GetCount() == 0:
            last_path = ""
        else:
            if folder_history == None:
                last_path = self.popenfilehistory.GetHistoryFile(0)
            else:
                last_path = self.popenfilehistory.GetHistoryFile(folder_history)

        try:
            dlg = MDD.MultiDirDialog(self, message="Choose folders:", defaultPath=last_path, agwStyle=MDD.DD_MULTIPLE|MDD.DD_DIR_MUST_EXIST)
            # dlg = wx.DirDialog(self, "Choose folders:", last_path, wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST)
        except IndexError:
            # clean folder history log
            foldercount = self.popenfilehistory.GetCount()
            print self.popenfilehistory.GetCount()
            i = foldercount
            while i > 0:
               self.popenfilehistory.RemoveFileFromHistory(i-1)
               i = i - 1
            print self.popenfilehistory.GetCount()
            # then open again
            dlg = MDD.MultiDirDialog(self, message="Choose folders:", defaultPath="", agwStyle=MDD.DD_MULTIPLE|MDD.DD_DIR_MUST_EXIST)

        sensor_size_flag = False
        if dlg.ShowModal() == wx.ID_OK:

            self.new_added_paths = dlg.GetPaths()
            for i, path in enumerate(self.new_added_paths):
                if IS_MAC:  # identify the path separator based on the used system
                    index = path.find('/')
                    path = path[index:] # remove macindosh hd
                elif IS_WIN: #windows return "BLAH (C:)\\blah\\blah" need format
                    sindex = path.find(':')
                    sindex = sindex - 1
                    path = path[sindex:] # remove 'BLAH ' in the beginning
                    path = re.sub(r'[()]', '', path, flags=re.UNICODE)  #remove()
                self.new_added_paths[i] = path

            # only unique folders can be added
            self.new_added_paths = [x for x in self.new_added_paths if x not in self.paths]
            self.paths.extend(self.new_added_paths)

            num_paths = self.new_added_paths.__len__()

            sensor_size_flag = self.list_folder()

            # self.add_list_items(dlg.GetPaths())

            # self.JPG2jpg(path)
            # self.displayThumbs(path)

            # <------ keep file history -----------
            self.popenfilehistory.AddFileToHistory(path)
            self.popenfilehistory.Save(self.config_popenfile)
            # ----------------------------------->

            wx.Yield()

            # open the last available PLY
            for i in range(self.list_ctrl.ItemCount-1, self.list_ctrl.ItemCount-num_paths-1, -1):
                if self.list_ctrl.GetItemText(i, 1) != "":
                    self.displayPLY(i)
                    break


        # dlg.Destroy()

        # if records not exist in the db, popup dialog to alert user input data
        # self.SetSensorSizePopup(sensor_size_flag)

        # ask the user to choose initial pair
        # self.choose_initial_pair_alert()

    def add_list_item(self, path):
        self.new_added_paths.append(path)
        # only unique folders can be added
        if not path in self.paths:
            self.paths.append(path)
            self.list_folder()
        else:
            del self.new_added_paths[0]

    def on_generate(self, event):
        if self.SetSensorSizePopup():
            self.status_bar.SetStatusText("This process is going to take a while...")
            paths_to_be_generated, indices_to_be_generated = self.to_be_generated_folders()
            if len(paths_to_be_generated) > 0:
                # get the chosen SfM method
                if self.toolbar.choiceSfM.GetSelection() == 0:
                    incremental_sfm = False  # global
                else:
                    incremental_sfm = True  # sequential/incremental

                # get the chosen whether mesh creation is on
                mesh_on=self.toolbar.checkMesh.GetValue()



                manager = multiprocessing.Manager()
                q = manager.Queue()

                # #progress bar
                # range = len(to_be_generated) * 100
                # self.progressbar = wx.Gauge(self.status_bar, -1, range)
                # self.status_bar.AddWidget(self.progressbar, ESB.ESB_ALIGN_RIGHT, ESB.ESB_ALIGN_BOTTOM)
                # self.progressbar.Show(True)

                # processbar = wx.ProgressDialog("Generation.", "Please wait...", maximum=100, parent=None, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT)
                # self.progress = wx.Gauge(self, range=20)
                #
                # sizer = wx.BoxSizer(wx.VERTICAL)
                # sizer.Add(self.progress, 0, wx.EXPAND)
                # self.SetSizer(sizer)

                # zip() passes different params (path, focal length etc.) for each item
                # if the sensor size is given by the user, then focal length is None
                generated_ply_paths = run_job(zip(paths_to_be_generated, self.get_focal_array(), self.get_downsize_array()), Worker(incremental_sfm, mesh_on, self.GrandParent.log, len(paths_to_be_generated), q)) #self.paths
                # if generated_ply_path is valid
                # if os.path.exists(self.generated_ply_path):
                #     self.status_bar.SetStatusText("Point cloud generate!")
                print generated_ply_paths
                # self.progressbar.Show(False)
                # if all folder has a generated ply file
                if not "" in generated_ply_paths:
                    for p in generated_ply_paths:
                        for target in paths_to_be_generated:
                            if os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(p))))) == target or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(p)))) == target:
                                row = paths_to_be_generated.index(target)
                                self.list_ctrl.SetStringItem(indices_to_be_generated[row], 1, str(p))
                                display_path=p
                                display_row=indices_to_be_generated[row]
                                break



                    # open the first available PLY
                    self.displayPLY(display_row)
                    self.status_bar.SetStatusText("Ply(s) generated! " + str(display_path) + " loaded.")

                else:# if some folder failed generating a ply file (see comments below)
                    failed_paths = []
                    for i, path in enumerate(paths_to_be_generated):
                        print path
                        # filter out the failed paths
                        if generated_ply_paths[i] == "":
                            failed_paths.append(os.path.basename(path))

                        # find old generated files
                        if incremental_sfm:
                            reconstruction_dir = "reconstruction_sequential"
                        else:
                            reconstruction_dir = "reconstruction_global"
                        # ply_path = os.path.join(path, "outputs", reconstruction_dir, "MVE", "mve_output_mesh_clean.ply")
                        # ply_path = os.path.join(path, "outputs", "result.0.ply")
                        ply_path = os.path.join(path, "outputs", reconstruction_dir, "PMVS", "models", os.path.basename(path) + ".ply")

                        for row in range(self.list_ctrl.GetItemCount()):
                            if self.paths[row] == path:
                                if os.path.isfile(ply_path):
                                    self.list_ctrl.SetStringItem(row, 1, str(ply_path))
                                else:
                                    self.list_ctrl.SetStringItem(row, 1, "")

                    if len(failed_paths) != 0:
                        self.kill_alert(failed_paths)
            else:
                #todo: diable generation button if no folder listed
                self.status_bar.SetStatusText("Please import image folder first!")

    #update the status bar from the thread
    # def updateProgress(self, msg):
    #     print('deng')
    #     self.progressbar.SetValue(msg)

    def to_be_generated_folders(self):
        # if no folder selected, only generate those have no ply listed
        # otherwise generate those were selected.
        paths = []
        indices = []
        if self.list_ctrl.GetSelectedItemCount() == 0:
            if self.list_ctrl.GetItemCount() == 1:  # can't mouse select when only one item
                paths.append(self.paths[0])
                indices.append(0)
            else:
                for row in range(self.list_ctrl.GetItemCount()):
                    if self.list_ctrl.GetItem(row, 1).GetText() == "" or self.list_ctrl.GetItem(row, 1).GetText() == None:
                        paths.append(self.paths[row])
                        indices.append(row)
        else:
            for row in range(self.list_ctrl.GetItemCount()):
                if self.list_ctrl.IsSelected(row):
                    paths.append(self.paths[row])
                    indices.append(row)
                    self.list_ctrl.SetStringItem(self.list_ctrl.GetItemCount()-1, 1, "")
        return paths, indices

    def on_scale(self, event):
        if not self.toolbar.GetToolState(wx.ID_CONVERT):
            print "scale toggle off"
            self.toolbar.enable_tools()
            self.clean_markers()
        else:
            print "scale toggle on"
            if hasattr(self, 'photogrammetry_panel'):
                if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                    self.toolbar.disable_tools(besides=[wx.ID_CONVERT])

    def on_autorotate(self, event):
        print "on auto rotate"
        if hasattr(self, 'photogrammetry_panel'):
            if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                # first toggle off other buttons
                # self.toolbar.disable_tools(besides=[self.toolbar.ID_AUTOROTATE, wx.ID_SAVEAS])

                # then do the actual rotate process
                c = np.nanmean(self.photogrammetry_panel.mayavi_view.point_array, axis=0)
                c = np.matlib.repmat(c, self.photogrammetry_panel.mayavi_view.point_array.shape[0], 1)
                data = self.photogrammetry_panel.mayavi_view.point_array - c
                eig = np.linalg.eig(np.dot(np.transpose(data),data))

                # numpy does not automatically order the eigenvectors.
                # We need to order them from the one corresponding to the max eigen value and descending
                order = np.argsort(eig[0])[::-1]

                PCs=np.vstack((eig[1][:,order[0]], eig[1][:,order[1]], eig[1][:,order[2]]))

                #  rotate in principal components directions
                rotated_xyz = self.rotate(PCs)
                self.photogrammetry_panel.mayavi_view.point_array = rotated_xyz
                self.photogrammetry_panel.mayavi_view.update()

                # set ply_edited flag
                self.ply_edited = True

    def on_invert(self,event):
        invert_options_dialog = InvertOptionsDialog(None)
        invert_options_dialog.ShowModal()

        if not invert_options_dialog.ok:  # if OK was not clicked abort the operation
            return

        if not (invert_options_dialog.x or invert_options_dialog.y or invert_options_dialog.z):  # None of the axes were selected
            return

        self.photogrammetry_panel.invert(invert_options_dialog.x,invert_options_dialog.y,invert_options_dialog.z)
        self.ply_edited = True

    def on_crop(self, event):
        if not self.toolbar.GetToolState(wx.ID_CUT):
            print "crop toggle off"
            self.toolbar.enable_tools()
            self.clean_markers()
        else:
            print "crop toggle on"
            if hasattr(self, 'photogrammetry_panel'):
                if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                    self.toolbar.disable_tools(besides=[wx.ID_CUT, wx.ID_SAVEAS])

    def on_3dcrop(self, event):
        if not self.toolbar.GetToolState(self.toolbar.ID_3DCROP):
            print "3d crop toggle off"
            self.toolbar.enable_tools()
            if hasattr(self, 'photogrammetry_panel'):
                if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                    # self.mayavi_view.mayavi_view.remove_markers()
                    self.photogrammetry_panel.mayavi_view.point_array = self.photogrammetry_panel.extent_dialog.point_array
                    self.photogrammetry_panel.mayavi_view.color_array = self.photogrammetry_panel.extent_dialog.color_array
                    self.photogrammetry_panel.mayavi_view.update()

        else:
            print "3d crop toggle on"
            if hasattr(self, 'photogrammetry_panel'):
                if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                    self.toolbar.disable_tools(besides=[self.toolbar.ID_3DCROP])
                    self.photogrammetry_panel.cube_crop()

    def on_measure(self, event):
        if not self.toolbar.GetToolState(self.toolbar.ID_MEASURE):
            print "measure toggle off"
            self.toolbar.enable_tools()
            self.clean_markers()
        else:
            print "measure toggle on"
            if hasattr(self, 'photogrammetry_panel'):
                if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                    self.toolbar.disable_tools(besides=[self.toolbar.ID_MEASURE])

    def on_saveas(self, event):
            # set saving path with a dialog window
            dlg = wx.FileDialog(self, "Save depth information", "", "", "CSV file|*.csv|PLY file|*.ply",
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()

                filename, extension = os.path.splitext(path)

                if extension==".csv":
                    if self.panel_display.Children[0].marker_scale < 0.1:
                        # because loading mpl need to set multiplier (default mm), data before scaling are unrealistic, such as 0.01mm
                        self.status_bar.SetStatusText("Please scale before saving as csv")
                    else:
                        percent, random = self.show_decrease_size_dialog()
                        self.photogrammetry_panel.PLY2CSV(self.photogrammetry_panel.mayavi_view.point_array, path, percent, random)
                        self.photogrammetry_panel.load_csv()
                        self.ply_edited = False
                elif extension==".ply":
                    self.photogrammetry_panel.save_ply(path)
                self.status_bar.SetStatusText("Model saved")

    def show_decrease_size_dialog(self):
        decrease_size_dialog = DecreaseSizeDialog(None)
        decrease_size_dialog.ShowModal()

        if not decrease_size_dialog.ok:  # if OK was not clicked abort the operation
            return

        percent = decrease_size_dialog.percent
        random = decrease_size_dialog.random

        return percent, random
    def on_delete_outputs(self, event):

        if self.list_ctrl.GetItemCount()>1:
            for row in range(self.list_ctrl.GetItemCount()):
                if self.list_ctrl.IsSelected(row): #if folder selected
                    shutil.rmtree(os.path.join (self.paths[row],"outputs"))
                    self.list_ctrl.SetStringItem(row, 1, "")
                    if row==self.loaded_ply_index:
                        self.clean_display_panel()

        else:
            shutil.rmtree(os.path.join(self.paths[0], "outputs"))
            self.list_ctrl.SetStringItem(0, 1, "")
            self.clean_display_panel()

        self.status_bar.SetStatusText("Outputs have been removed")

    def on_change_model(self, event):
        if self.list_ctrl.GetSelectedItemCount() == 0:
            selected_row = 0
        else:
            for row in range(self.list_ctrl.GetItemCount()):
                if self.list_ctrl.IsSelected(row):
                    selected_row = row
        self.displayPLY(selected_row)

    def rotate(self, R, xyz=None):
        if xyz is None:
            xyz = self.photogrammetry_panel.mayavi_view.point_array
        c = np.nanmean(xyz,axis=0)
        c = np.matlib.repmat(c,xyz.shape[0],1)
        rotated_xyz = c + np.dot((xyz-c),np.transpose(R))
        return rotated_xyz

    def clean_markers(self):
        if hasattr(self, 'photogrammetry_panel'):
            if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                self.photogrammetry_panel.mayavi_view.remove_markers()
                self.photogrammetry_panel.markers = []  # scale markers
                self.photogrammetry_panel.crop_markers = []
                self.photogrammetry_panel.measure_markers = []

    def displayThumbs(self, row):
        # self.panel_thumbs = TC.ThumbnailCtrl(self, imagehandler=TC.NativeImageHandler)
        # self.sizer_horiz.Add(self.panel_thumbs, 1, wx.EXPAND | wx.RIGHT, 10)
        # self.panel_thumbs.Bind(TC.EVT_THUMBNAILS_DCLICK, self.OnDoulbleClickThumb)

        # # change background color and text color back to normal for all items
        # for i in range(self.list_ctrl.GetItemCount()):
        #     self.list_ctrl.SetItemBackgroundColour(i, "white")
        #     self.list_ctrl.SetItemTextColour(i, "black")
        #
        # # highlight the selected item
        # self.list_ctrl.SetItemBackgroundColour(event.GetIndex(), "blue")
        # self.list_ctrl.SetItemTextColour(event.GetIndex(), "white")

        path = self.paths[row] #event.GetIndex()
        try:
            self.JPG2jpg(path)
        except:
            print("Error in converting extensions from caps to lowercase:", sys.exc_info()[0])
        self.thumbs_ctrl.ShowDir(path)
        self.loaded_folder_num = self.thumbs_ctrl.GetItemCount()
        # print self.panel_thumbs.GetShowDir()
        if self.loaded_ply_index != -1 and self.loaded_ply_index != row:
            self.clean_display_panel()
        self.status_bar.SetStatusText('Loaded %d image file(s)' % self.loaded_folder_num)
        # if this folder has generated ply file, show the ply file
        # if not self.list_ctrl.GetItemText(row, 1) == "":
        #     ply_path = self.list_ctrl.GetItemText(row, 1)
        #     # delete thumbnails
        #     if self.panel_thumbs.GetItemCount() != 0 and not self.panel_thumbs.GetShowDir() == self.paths[row]:
        #         for i in range(self.panel_thumbs.GetItemCount()-1, -1, -1):
        #             self.panel_thumbs.RemoveItemAt(i)
        #     # show ply on mayavi
        #     self.displayPLY(ply_path)

        # self.panel_thumbs.GetItem(0).Selected = wx.CheckBox(self, wx.ID_ANY)  # check box#
        # self.panel_thumbs.GetItem(1).Selected = wx.CheckBox(self, wx.ID_ANY)  # check box

    def populateSelectView(self, path):

        # find old generated files
        # order: global MVE, sequential MVE, global PMVS, sequential PMVS

        ply_found = False

        fname = os.path.basename(path)
        self.toolbar.selectModel.Clear()

        ply_path = os.path.join(path, "outputs", "reconstruction_global", "MVE", "mve_output_mesh_clean.ply")
        if os.path.isfile(ply_path):
            self.toolbar.selectModel.Append("Global, with mesh")
            ply_found = True

        ply_path = os.path.join(path, "outputs", "reconstruction_sequential", "MVE", "mve_output_mesh_clean.ply")
        if os.path.isfile(ply_path):
            self.toolbar.selectModel.Append("Sequential, with mesh")
            ply_found = True

        ply_path = os.path.join(path, "outputs", "reconstruction_global", "PMVS", "models", fname + ".ply")
        if os.path.isfile(ply_path):
            self.toolbar.selectModel.Append("Global, no mesh")
            ply_found = True

        ply_path = os.path.join(path, "outputs", "reconstruction_sequential", "PMVS", "models", fname + ".ply")
        if os.path.isfile(ply_path):
            self.toolbar.selectModel.Append("Sequential, no mesh")
            ply_found = True

        try:
            self.toolbar.selectModel.SetSelection(0)
        except:
            print("Folder does not contain any models")

        return ply_found


    def clean_display_panel(self):
        # clean mayavi panel
        if hasattr(self, 'photogrammetry_panel'):
            if hasattr(self.photogrammetry_panel, 'mayavi_view'):
                self.photogrammetry_panel.mayavi_view.remove_all()
        # disable toggle buttons
        self.toolbar.disable_tools()
        # cleanup the panel
        for child in self.panel_display.GetChildren():
            child.Destroy()
        self.loaded_ply_index = -1
        if hasattr(self, 'image_path'):
            del self.image_path

        self.ply_edited = False

    def getPLYPathfromSelection(self, fname, folder_path):


        selection = self.toolbar.selectModel.GetString(self.toolbar.selectModel.GetSelection())

        if selection == "Global, with mesh":
            ply_path = os.path.join(folder_path, "outputs", "reconstruction_global", "MVE", "mve_output_mesh_clean.ply")
        elif selection == "Sequential, with mesh":
            ply_path = os.path.join(folder_path, "outputs", "reconstruction_sequential", "MVE", "mve_output_mesh_clean.ply")
        if selection == "Global, no mesh":
            ply_path = os.path.join(folder_path, "outputs", "reconstruction_global", "PMVS", "models", fname + ".ply")
        elif selection == "Sequential, no mesh":
            ply_path = os.path.join(folder_path, "outputs", "reconstruction_sequential", "PMVS", "models", fname + ".ply")

        return ply_path


    def displayPLY(self, row):
        if not self.ply_loading_flag:  # if not loading
            print("Ready - strt loading")
            self.ply_loading_flag = True  # set flag loading

            self.Parent.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))  # set cursor to "busy"

            # cleanup the panel first
            self.clean_display_panel()
            if self.list_ctrl.GetItemText(row, 1) != "":
                # load new plot
                path = self.getPLYPathfromSelection(self.list_ctrl.GetItemText(row, 0),self.list_ctrl.GetItemText(row, 1))
                # path = generated_ply_path

                sizer = self.panel_display.GetSizer()
                try:
                    self.photogrammetry_panel = PhotogrammetryPanel(self.panel_display, fname=path)
                except:
                    print("Error in displaying of 3D model, possibly deleted:", sys.exc_info()[0])
                    self.Parent.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))  # set cursor to "normal"
                    return
                sizer.Add(self.photogrammetry_panel, 1, wx.EXPAND | wx.ALL, 5)

                self.GrandParent.fix_size() #make sure thumbs tab is not getting smaller
                msg = os.path.basename(path) + ' model loaded.'
                # if len(not_loaded) > 0:
                #     msg = 'ply model not loaded!'
                self.status_bar.SetStatusText(msg)
                self.loaded_ply_index = row
                self.toolbar.enable_tools()

            self.Parent.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))  # set cursor to "normal"
            self.ply_loading_flag = False  # unset flag loading
        else:
            print("Not ready")

    #not used
    def mayaviDisplay(self):
        plydata = PlyData.read(str(self.generated_ply_path))
        vertex = plydata['vertex']
        (x, y, z) = (vertex[t] for t in ('x', 'y', 'z'))
        (r, g, b) = (vertex[t] for t in ('red', 'green', 'blue'))
        r = r.astype(float)/255
        g = g.astype(float)/255
        b = b.astype(float)/255

        sc=tvtk.UnsignedCharArray()
        sc.from_array((r, g, b))

        pts=mlab.points3d(x, y, z, mode='point')
        pts.mlab_source.dataset.point_data.scalars=sc
        pts.mlab_source.dataset.modified()
        mlab.show()

    def OnDoulbleClickThumb(self, event):
        # cleanup the panel first
        self.clean_display_panel()

        selected_image =  self.thumbs_ctrl.GetPointedItem()
        self.image_path = os.path.join(selected_image._dir, selected_image._filename)
        print self.image_path

        self.display_image(self.image_path)

    def display_image(self, path):
        # self.image_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = self.panel_display.GetSizer()
        # self.SetSizer(self.image_sizer)
        img = wx.Image(path, wx.BITMAP_TYPE_ANY)

        # scale image to fit the sizer
        W = img.GetWidth()
        H = img.GetHeight()
        width, height = self.display.GetSize()
        NewW = width
        NewH = width * H / W
        img = img.Scale(NewW, NewH)
        self.imageCtrl = wx.StaticBitmap(self.panel_display, wx.ID_ANY, wx.BitmapFromImage(img))
        sizer.Add(self.imageCtrl, 0, wx.EXPAND | wx.ALL, 5)


    # not used
    def readPLYFile(self):
        reader = vtk.vtkPLYReader()
        if reader.CanReadFile(self.generated_ply_path) == 0:
            self.status_bar.SetStatusText('Error: Invalid PLY file.')
        elif reader.CanReadFile(self.generated_ply_path) == 1:
            self.status_bar.SetStatusText('Loading generated PLY file.')
            reader.SetFileName(os.path.join(self.generated_ply_path))
            reader.Update()
            output = reader.GetOutput()
            points = output.GetPoints()
            point_array = vtk_to_numpy(points.GetData()) # points xyz
            color_array = vtk_to_numpy(output.GetPointData().GetScalars()) # points color

            plydata = PlyData.read(str(self.generated_ply_path))
            vertex = plydata['vertex']
            (x, y, z) = (vertex[t] for t in ('x', 'y', 'z'))

            sc=tvtk.UnsignedCharArray()
            sc.from_array(color_array)

            pts=mlab.points3d(x,y,z, mode='point')
            pts.mlab_source.dataset.point_data.scalars=sc
            pts.mlab_source.dataset.modified()
            mlab.show()
            #DisplayPanel3D(self, point_array)

    # not used
    def PLY2CSV(self, path):
        plydata = PlyData.read(str(self.generated_ply_path))  # need to convert to string otherwise not working
        data = plydata.elements[0].data
        data = np.vstack([data['x'], data['y'], data['z']])
        data = np.transpose(data)
        with open(os.path.join(path, 'output.csv'), 'w') as f:
            f.write('X,Y,Z\n')
            for item in data:
                f.write("%.4f,%.4f,%.4f\n" % (item[0], item[1], item[2]))
                # print(item)

    # thumbnailctrl doesn't recognise .JPG, so convert all to .jpg
    def JPG2jpg(self, folder):
        list = glob.glob(os.path.join(folder, "*.JPG"))
        for filename in list:
            base = os.path.splitext(filename)[0]
            os.rename(filename, base + ".jpg")

    def list_folder(self):
        flag = False
        for path in self.new_added_paths:
            # if IS_MAC:  # identify the path separator based on the used system
            #     index = path.rfind('/')
            # elif IS_WIN:
            #     index = path.rfind('\\')
            size = self.list_sensor_size(path)
            if size == "":
                flag = True # any one entry has no size info, flag it
            # path = path[index+1:] # get folder name
            fname = os.path.basename(path)
            self.path_names.append(fname)
            # print path
            # self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount())
            print self.list_ctrl.GetItemCount()
            self.list_ctrl.InsertStringItem(self.list_ctrl.GetItemCount(), str(fname))
            self.list_ctrl.SetStringItem(self.list_ctrl.GetItemCount()-1, 2, str(size))

            #populate the list view
            if self.populateSelectView(path):
                self.list_ctrl.SetStringItem(self.list_ctrl.GetItemCount() - 1, 1, path)

        self.new_added_paths = []
        return flag

    # parse exif file to find a match in sensor size database
    def list_sensor_size(self, path):
        images = glob.glob(path + '\\*.jpg')
        if len(images) > 0:
            img = PIL.Image.open(images[0])
            # exif_data = img._getexif()
            exif_data = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            print exif_data['Model']
            keywords = exif_data['Model'].split(' ') # keywords in the model string
            # try to find a strict match first
            model_split = exif_data['Model'].split(' ')
            if not model_split[0] == exif_data['Make']: # if the first word in model name is not the brand name
                model_name = exif_data['Make'] + " " + exif_data['Model']
            else:
                model_name = exif_data['Model']
            found = difflib.get_close_matches(model_name, self.sensor_size_db.keys(), n=1, cutoff=1)
            if not found == []:
                print found, self.sensor_size_db[found[0]]
                return self.sensor_size_db[found[0]]
            else: # if no strict match is found, sometimes because different naming format of the model
                model_number = self.has_numbers(keywords) # parse the model number out
                for entry in self.sensor_size_db.keys():
                    if exif_data['Make'].lower() in entry.lower(): # try to find in same brand
                        if not model_number == None:
                            if model_number.lower() in entry.lower():
                                print entry, self.sensor_size_db[entry]
                                return self.sensor_size_db[entry]
                    elif keywords[0].lower() in entry.lower(): # some make is not a single word, but contains in model[0]
                        if not model_number == None:
                            if model_number.lower() in entry.lower():
                                print entry, self.sensor_size_db[entry]
                                return self.sensor_size_db[entry]
                # cache camera that has no sensor size in the db
                # self.fill_size_list.append([exif_data['Make'], exif_data['Model'], exif_data['FocalLength']])
                return ""

    def has_numbers(self, input_list):
        for word in input_list:
            if bool(re.search(r'\d', word)):
                return word
        return None

    def get_sensor_size_db(self): #parse the db txt into cache self.sensor_size_db
        # the db is loaded when init
        # camera_file_params = os.path.join("utilities", "sensor_width_camera_database.txt")
        lines = open(self.camera_file_params, "r")
        for line in lines:
            if not line == '':
                items = line.split(';')
                self.sensor_size_db[items[0]] = items[1]
        lines.close()

    def on_save_input_db(self, event):
        # TODO: only access exif once
        # camera_file_params = os.path.join("utilities", "sensor_width_camera_database.txt")
        if not event.IsEditCancelled():
            # parse the brand and model from exif
            # currently all images in the same folder are taken by the same camera by default
            images = glob.glob(self.paths[event.GetIndex()] + '\\*.jpg')
            if len(images) > 0:
                img = PIL.Image.open(images[0])
                exif_data = {
                    PIL.ExifTags.TAGS[k]: v
                    for k, v in img._getexif().items()
                    if k in PIL.ExifTags.TAGS
                }
            brand_name = exif_data['Model'].partition(' ')[0]
            if brand_name in exif_data['Make']:
                model_name = exif_data['Model']
            else:
                brand_name = exif_data['Make']
                model_name = brand_name + " " + exif_data['Model']

            temp_str = ';'.join([model_name, event.GetText()]) +'\n'
            # check if this entry already exists, its for unique entries in the db
            found = difflib.get_close_matches(model_name, self.sensor_size_db.keys(), n=1, cutoff=1)
            if not found == []:
                # if entry exists but value changed
                if not self.sensor_size_db[found[0]] == event.GetText():
                    # update the entry in txt
                    self.replace_line(model_name, temp_str)
                    # update self.sensor_size_db cache
                    self.sensor_size_db[model_name] = event.GetText()
            else: # if it doesn't exist
                f = open(self.camera_file_params, 'a')
                f.write(temp_str)
                f.close()
                # add new entry to the db cache
                self.sensor_size_db[model_name] = event.GetText()
            # update all list entries
            self.update_list()
            # clear cache fill_size_list
            # for i, cam in enumerate(self.fill_size_list):
            #     if cam[0] == exif_data['Make'] and cam[1] == exif_data['Model']:
            #         del self.fill_size_list[i]
            #         print "deleted ", exif_data['Make'], exif_data['Model']
            #         return
        else:
            print "edit was cancelled"

    # update listctrl third column
    def update_list(self):
        for row in range(self.list_ctrl.GetItemCount()):
            size = self.list_sensor_size(self.paths[row])
            self.list_ctrl.SetStringItem(row, 2, str(size))

    # update censor_size.txt
    def replace_line(self, model, text):
        lines = open(self.camera_file_params, 'r').readlines()
        for i, line in enumerate(lines):
            if model in line:
                lines[i] = text
        out = open(self.camera_file_params, 'w')
        out.writelines(lines)
        out.close()

        # for line in fileinput.input(self.camera_file_params, inplace=1):
        #     if model in line:
        #         line = line.replace(line, text)

    #popup which asks for confirmation if no sensor size is given
    def SetSensorSizePopup(self, sensor_size_flag=None):
        # if any entry has no sensor size info
        flag = False # True: there is at least one entry has no sensor size
        if sensor_size_flag == None: # called by on_generate
            for row in range(self.list_ctrl.GetItemCount()):
                if self.list_ctrl.GetItem(row, 2).GetText() == "" or self.list_ctrl.GetItem(row, 2).GetText() == None:
                    flag = True
                    break
        # if called by on_open, i.e. sensor_size_flag is passed as true or false, not None
        else:
            flag = sensor_size_flag

        # pop alert
        if flag:
            dlg = wx.MessageDialog(self.Parent, 'Some of the camera sensor size are not found in the database.\nPress \'Yes\' to enter in the table.\nPress \'No\' to proceed with default value.', 'Alert!', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                return False # don't run generation
            else:
                return True # run generation anyway
        return True

    #popup when some folders could not be generated
    def kill_alert(self, paths):
        paths_string = '; '.join([item for item in paths])
        dlg = wx.MessageDialog(self.Parent, 'Point cloud for folder(s) [' + str(paths_string) + '] not generated. Please refer to the troubleshooting section of the user manual.\nShowing old generation if exists.', 'Alert!', wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    # def choose_initial_pair_alert(self):
    #     msg = 'Please click the folder name then choose two images from\n' \
    #           'the displayed pictures as the initial pair by ctrl+click.\n' \
    #           'The selected two images need to be convergent with numerous\n' \
    #           'correspondences while keeping a wide enough baseline.\n\n' \
    #           'If no initial images are selected, the software will choose\n' \
    #           'automatically but the reconstruction may fail.'
    #     dlg = wx.MessageDialog(self.Parent, msg, 'Alert!', wx.OK|wx.ICON_INFORMATION)
    #     dlg.ShowModal()
    #     dlg.Destroy()

    #calculation of focal length from exif information or using default method, if given returns none (OpenMVG will take care of this automatically)
    def calculate_focal(self, path):
        # for entry in self.fill_size_list: #[exif_data['Make'], exif_data['Model'], exif_Data['FocalLength']]
        #     model_name = entry[0] + " " + entry[1]
        #     print entry[2]
        #     value = float(entry[2]) / 1.2
        #     temp_str = ';'.join([entry[0], model_name, value]) +'\n'
        #     f = open(self.camera_file_params, 'a')
        #     f.write(temp_str)
        #     f.close()#
        f = None
        images = glob.glob(path + '\\*.jpg')
        if len(images) > 0:
            img = PIL.Image.open(images[0])
            exif_data = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            width, height = img.size
            if exif_data.has_key('FocalPlaneXResolution'):
            # TODO: check if resize affects the value of FocalPlaneXResolution two tuples. if no, nothing to do otherwise add conditions here
                if width >= height:
                    f = exif_data['FocalLength'][0] * exif_data['FocalPlaneXResolution'][0] / (exif_data['FocalPlaneXResolution'][1] * 24.64)
                else:
                    f = exif_data['FocalLength'][0] * exif_data['FocalPlaneXResolution'][0] / (exif_data['FocalPlaneXResolution'][1] * 24.64)
            else:
                if max(width, height) > 3264:
                    f= 1.2 * 3264
                else:
                    f = 1.2 * max(width, height)
        return f

    # get the focal length array
    def get_focal_array(self):
        focal_lengths = []
        # for p in self.paths:
        for row in range(self.list_ctrl.GetItemCount()):
            if self.list_ctrl.GetItem(row, 1).GetText() == "" or self.list_ctrl.GetItem(row, 1).GetText() == None or self.list_ctrl.IsSelected(row) or self.list_ctrl.GetItemCount() == 1:
                if self.list_ctrl.GetItem(row, 2).GetText() == "" or self.list_ctrl.GetItem(row, 2).GetText() == None:
                    f = self.calculate_focal(self.paths[row])
                else:
                    f = None # ccd size found in db
                focal_lengths.append(f)
        return focal_lengths

    # right click the list item deletes it
    def on_folder_delete(self, event):
        # clear display first in case the to-be-delete folder is displayed
        self.clean_display_panel()

        # if a folder is expanded, need to delete the thumbnails as well
        # when the folders first loaded and no folder has been clicked to expand in panel_thumbs yet
        # GetShowDir is empty so call it will fail, thus we need to check if GetItemCount can return a number>0
        # if it's >0 then it's safe to call GetShowDir, otherwise it will return error
        if self.thumbs_ctrl.GetItemCount() != 0 and self.thumbs_ctrl.GetShowDir() == self.paths[event.GetIndex()]:
            for i in range(self.thumbs_ctrl.GetItemCount()-1, -1, -1):
                self.thumbs_ctrl.RemoveItemAt(i)
        self.panel_thumbs.Refresh()  # force refresh otherwise the image thumbs still stays

        del self.paths[event.GetIndex()]
        del self.path_names[event.GetIndex()]
        # delete the item in the folder list
        self.list_ctrl.DeleteItem(event.GetIndex())

    # array with downsizeing choice (yes/no(empty)) for each folder
    def get_downsize_array(self):
        # an array sent to on_generate multiprocess, if downsize or not
        downsize_array = []
        for row in range(self.list_ctrl.GetItemCount()):
            downsize_array.append(self.list_ctrl.GetItem(row, 3).GetText())
        return downsize_array


class photogrammetryToolbar(wx.ToolBar):
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent=parent, id=wx.ID_ANY)

        self.AddLabelTool(wx.ID_OPEN, 'Open', wx.Bitmap('icons\\connect-to-folder.png'), shortHelp="Open", longHelp="Open images folder")
        self.AddLabelTool(wx.ID_APPLY, 'Generate', wx.Bitmap('icons\\insert-3d-axes.png'), shortHelp="Generate", longHelp="Generate point cloud")
        if IS_WIN: self.AddSeparator()

        # dropdown for choosing SfM method
        self.choiceSfM = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["Global SfM", "Sequential SfM"])
        self.choiceSfM.SetSelection(0)
        self.AddControl(self.choiceSfM)
        if IS_WIN: self.AddSeparator()

        # checkbox for mesh creation MVE vs no mesh PMVS
        self.checkMesh = wx.CheckBox(self, wx.ID_ANY, label="Mesh on")
        self.AddControl(self.checkMesh)

        if IS_WIN: self.AddSeparator()

        # dropdown for choosing scaling method
        #self.choiceScale = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["2-point scaling", "4-point scaling-experimental"])
        #self.choiceScale.SetSelection(0)
        #self.AddControl(self.choiceScale)

        self.AddCheckLabelTool(wx.ID_CONVERT, 'Scale', wx.Bitmap('icons\\scale.png'), shortHelp="Scale", longHelp="Scale the generated point cloud")
        self.ID_AUTOROTATE = wx.NewId()
        self.AddLabelTool(self.ID_AUTOROTATE, 'Autorotate', wx.Bitmap('icons\\auto-rotate.png'), shortHelp="Auto Rotate", longHelp="Automatically rotate the model to be orthogonal")
        self.ID_INVERT = wx.NewId()
        self.AddLabelTool(self.ID_INVERT, 'Invert', wx.Bitmap('icons\\invert.png'), shortHelp="Invert", longHelp="Invert")
        self.AddCheckLabelTool(wx.ID_CUT, 'Crop', wx.Bitmap('icons\\crop-by-rectangle.png'), shortHelp="4-point Crop", longHelp="Place four points to crop the model")
        self.ID_3DCROP = wx.NewId()
        self.AddCheckLabelTool(self.ID_3DCROP, '3D Crop', wx.Bitmap('icons\\crop.png'), shortHelp="3D Crop", longHelp="Adjust the outline to crop")
        self.ID_MEASURE = wx.NewId()
        self.AddCheckLabelTool(self.ID_MEASURE, 'Measure', wx.Bitmap('icons\\quick-measure.png'), shortHelp="Measure", longHelp="Measure distance between two points")
        self.AddLabelTool(wx.ID_SAVEAS, 'Save as...', wx.Bitmap('icons\\save-as-copy.png'), shortHelp="Save", longHelp="Save current ply file")
        self.AddLabelTool(wx.ID_DELETE, 'Delete outputs', wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK ), shortHelp="Delete outputs",
                          longHelp="Delete generated 3D model outputs for the folder")

        self.selectModel = wx.Choice(self, wx.ID_ANY, (-1, -1), (150, -1), [])
        # self.selectModel = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.AddControl( wx.StaticText( self, label="3D model selection"))
        self.AddSeparator()
        self.AddControl(self.selectModel)

        # disable buttons
        self.disable_tools()

    def disable_tools(self, besides=None):
        if besides is None:
            besides = []
        tools = [wx.ID_CONVERT, self.ID_AUTOROTATE, self.ID_INVERT, wx.ID_CUT, self.ID_3DCROP, self.ID_MEASURE, wx.ID_SAVEAS]
        disable_tools = set(tools) - set(besides)
        for t in disable_tools:
            self.EnableTool(t, False)

    def enable_tools(self):
        tools = [wx.ID_CONVERT, self.ID_AUTOROTATE, self.ID_INVERT, wx.ID_CUT, self.ID_3DCROP, self.ID_MEASURE, wx.ID_SAVEAS]
        for t in tools:
            self.EnableTool(t, True)

        # if self.GetToolState(wx.ID_CONVERT):
        #     self.disable_tools(besides=[wx.ID_CONVERT, wx.ID_SAVEAS])
        # if self.GetToolState(self.ID_AUTOROTATE):
        #     self.disable_tools(besides=[self.ID_AUTOROTATE, wx.ID_SAVEAS])
        # if self.GetToolState(wx.ID_CUT):
        #     self.disable_tools(besides=[wx.ID_CUT, wx.ID_SAVEAS])
        # if self.GetToolState(self.ID_3DCROP):
        #     self.disable_tools(besides=[self.ID_3DCROP, wx.ID_SAVEAS])
        # if self.GetToolState(self.ID_MEASURE):
        #     self.disable_tools(besides=[self.ID_MEASURE, wx.ID_SAVEAS])

    def init_tool_states(self):
        if self.GetToolState(wx.ID_CONVERT):
            self.ToggleTool(wx.ID_CONVERT, False)
        if self.GetToolState(self.ID_AUTOROTATE):
            self.ToggleTool(self.ID_AUTOROTATE, False)
        if self.GetToolState(self.ID_INVERT):
            self.ToggleTool(self.ID_INVERT, False)
        if self.GetToolState(wx.ID_CUT):
            self.ToggleTool(wx.ID_CUT, False)
        if self.GetToolState(self.ID_3DCROP):
            self.ToggleTool(self.ID_3DCROP, False)
        if self.GetToolState(self.ID_MEASURE):
            self.ToggleTool(self.ID_MEASURE, False)
        # if self.GetToolState(wx.ID_DELETE):
        #     self.ToggleTool(wx.ID_DELETE, False)

        self.disable_tools()
        #self.choiceScale.SetSelection(0)
        #self.choiceSfM.SetSelection(0)

class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin):
    ''' TextEditMixin allows any column to be edited. '''

    #----------------------------------------------------------------------
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        """Constructor"""
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        # listmix.CheckListCtrlMixin.__init__(self)

    # defines what to do when user clicks on each column
    def OpenEditor(self, col, row):

        self.Parent.Parent.populateSelectView(self.GetItemText(row, 1))
        if col == 0:
            self.Parent.Parent.displayThumbs(row)
        elif col == 1:
            self.Parent.Parent.displayPLY(row)
        elif col == 2:
            listmix.TextEditMixin.OpenEditor(self, col, row)
        elif col == 3:
            self.toggle_downsize(row, col)

    # def OnCheckItem(self, index, flag):
    #     print(index, flag)

    def toggle_downsize(self, row, col):
        if self.GrandParent.list_ctrl.GetItem(row, col).GetText() == "":
            self.GrandParent.list_ctrl.SetStringItem(row, col, "Yes")
        elif self.GrandParent.list_ctrl.GetItem(row, col).GetText() == "Yes":
            self.GrandParent.list_ctrl.SetStringItem(row, col, "")


class Worker(object):
    def __init__(self, incremental_sfm, mesh_on, log, threads_count, queue):
        self.incremental_sfm = incremental_sfm
        self.mesh_on = mesh_on
        self.log = log
        # self.panel_display = panel_display
        self.threads_count = threads_count
        self.queue = queue

    def __call__(self, (fname, focal_length, downsize_flag)):
        #return pg.generation_gui((fname, focal_length, downsize_flag), incremental_sfm=self.incremental_sfm, log=self.log)
        return pg.generation_pipeline((fname, focal_length, downsize_flag), incremental_sfm=self.incremental_sfm, mesh_on=self.mesh_on, log=self.log, threads_count=self.threads_count, queue=self.queue)

# run parallel job
def run_job(items, obj):
    cnt = len(items)
    cores = multiprocessing.cpu_count()

    if cores > 1:
        print('Using multiprocess')
        pool = multiprocessing.Pool(processes=min(cnt, cores))
        #pool = NonDaemonPool(processes=min(cnt, cores)) #non-daemon process pool
        result = pool.map(obj, items)  # obj is worker
        pool.close()
    else:
        print('Using single process')
        result = list()
        for item in items:
            result.append(obj.__call__(item))
    return result


#we need non-daemonic process to start another process in the process
class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

class NonDaemonPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess
