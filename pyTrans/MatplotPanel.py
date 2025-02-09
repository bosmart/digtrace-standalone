# import matplotlib
# matplotlib.use('PS')

import wx
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
import matplotlib.colorbar as colorbar
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D #this is needed for 3d projections, despite being grayed out
import scipy.interpolate
from matplotlib_scalebar.scalebar import ScaleBar

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

class MatplotPanel(wx.Panel):
    def __init__(self, parent, xyzi, xyz, multiplier, precision, size=None, mpl_src=None,  title='', fname='', lmark_xy=None, A=None, pid=-1, current_vmin=None, current_vmax=None, colormap='jet'):
        if size is None:
            size_p = parent.GetSize()
            size = (max(120, size_p[1]), size_p[1] - 30)

        wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)

        # save limage file history
        self.lsavefilehistory = wx.FileHistory(9)
        self.config_lsavefile = wx.Config(localFilename = "pyTrans-Lsavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.lsavefilehistory.Load(self.config_lsavefile)
        self.ON_SAVE_PANEL_LEFT = wx.NewId()

        # save rimage file history
        self.rsavefilehistory = wx.FileHistory(9)
        self.config_rsavefile = wx.Config(localFilename = "pyTrans-Rsavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.rsavefilehistory.Load(self.config_rsavefile)
        self.ON_SAVE_PANEL_RIGHT = wx.NewId()

        self.image_file_filter = "All supported files (*.jpg;*.png;*.pdf;*.svg;*.eps)|*.jpg;*.png;*.pdf;*.svg;*.eps|JPG files|*.jpg|PNG files|*.png|PDF files|*.pdf|SVG files|*.svg|EPS files|*.eps|All files (*.*)|*.*"


        self.xyzi = xyzi
        self.xyz = xyz
        self.mpl_src = mpl_src
        self.title = title
        self.lmark_xy = lmark_xy
        self.fname = fname
        self.master_fname = None
        self.master_lmark_xy = None
        self.cbar = None
        self.used = False
        self.A = A
        self.multiplier=multiplier
        self.precision=precision
        self.xthrs = self.xyzi[2].shape[0] / 100
        self.ythrs = self.xyzi[2].shape[1] / 100
        self.pid = pid

        self.cnt_step = 0 #contours none
        self.contour_level_start=0
        self.contours = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.fig = Figure()
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_off()
        self.canvas = FigureCanvas(self, -1, self.fig)

        self.colormap = colormap

        if isinstance(parent, wx._windows.ScrolledWindow):
            self.Selected = wx.CheckBox(self)  # check box
            self.sizer.Add(self.Selected)

        self.vmin, self.vmax = np.nanmin(self.xyzi[2]), np.nanmax(self.xyzi[2])
        if current_vmin is None or current_vmax is None:
            self.current_vmin, self.current_vmax = self.vmin, self.vmax
        else:
            self.current_vmin, self.current_vmax = current_vmin, current_vmax

        #  if not bottom panel
        #  this line checks whether matplotpanesl is in the bottom or center
        if not isinstance(parent, wx._windows.ScrolledWindow):
            self.add_toolbar()
            # add horizontal colorbar
            cbaxes = self.fig.add_axes([0.1, 0.05, 0.8, 0.03])
            self.cbar = colorbar.ColorbarBase(cbaxes, ticks=[0, 1], orientation='horizontal')
            self.cbar.ax.set_xticklabels([str(round(self.current_vmin, 1)), str(round(self.current_vmax, 1))])

        self.sizer.Add(self.canvas, 1, wx.EXPAND)


        # draw a plot on local scale
        self.plt = self.ax.imshow(self.xyzi[2], origin='lower', interpolation='none', vmin=self.current_vmin, vmax=self.current_vmax)


        #if the depth matrix is binary, automatically set greyscale
        if np.unique(xyzi[2]).__len__()==2:
            self.plt.set_cmap('gray')
            self.cbar.set_cmap('gray')
        else:
            self.plt.set_cmap(self.colormap)


        self.mouse_entry_flag = False
        self.redraw()
        # self.update()

    def set_cmap(self, cmap='jet'):
        self.colormap=cmap
        self.plt.set_cmap(cmap)
        if self.cbar is not None:
            self.cbar.set_cmap(cmap)
            self.cbar.draw_all()
            self.cbar.ax.set_xticklabels([str(round(self.current_vmin, 1)), str(round(self.current_vmax, 1))])
        self.SendSizeEvent()

    def redraw(self):
        if np.array_equal(self.A, np.vstack((np.eye(2), np.zeros((1, 2))))):
            self.ax.text(0.1, 0.1, 'M', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
        elif self.A is not None:
            self.ax.text(0.1, 0.1, 'R', horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
        self.SendSizeEvent()

    #set contours with a given width always starting from the mean
    def set_contours(self, step):
        self.set_cmap('gray')
        # levels1 = np.arange(np.nanmean(self.xyzi[2])-step, np.nanmin(self.xyzi[2]), -step )
        # levels2 = np.arange(np.nanmean(self.xyzi[2]), np.nanmax(self.xyzi[2]), step )
        #levels = np.hstack((levels1, levels2))
        levels = np.arange(self.contour_level_start, np.nanmax(self.xyzi[2]), step)
        self.update_image(self.xyzi, self.xyz)
        cnt = self.ax.contour(self.xyzi[2], levels)
        #self.ax.clabel(cnt, inline=1,inline_spacing=-2,fontsize=10,fmt='%1.0f')
        self.cnt_step=step
        #save contours for contour crop. add 0 and max Z
        self.contours = np.hstack((0, levels, np.nanmax(self.xyzi[2])))
        self.contours = np.unique(self.contours)

        self.SendSizeEvent()

    def set_contours_for_cropping(self, contours):
        self.ax.contour(self.xyzi[2], contours, linewidths=np.hstack((3, 3)),
                        colors=('white', 'black'))
        self.SendSizeEvent()

    #shift contours to the right or left, keep the same step
    def contour_shift(self, shift, step):
        self.contour_level_start=self.contour_level_start+shift
        if self.contour_level_start>=step:
            self.contour_level_start=0
        if self.contour_level_start<0:
            self.contour_level_start=self.contour_level_start+step
        self.set_contours(step)

    def toggle_scalebar(self, on):
        if on:
            self.scalebar = ScaleBar(self.precision/1000*self.multiplier)
            self.ax.add_artist(self.scalebar)
        else:
            self.scalebar.remove()
        self.redraw()

    def toggle_grid(self, on, grid_distance=10):
        if on:
            x_ticks = np.arange(0, self.xyzi[2].shape[1], grid_distance/self.precision)
            y_ticks = np.arange(0, self.xyzi[2].shape[0], grid_distance / self.precision)
            self.ax.set_xticks(x_ticks)
            self.ax.set_yticks(y_ticks)
            self.ax.grid(color='w', linestyle='-', linewidth=1)

            self.ax.set_axis_on()
            self.ax.get_xaxis().set_ticklabels([])
            self.ax.get_yaxis().set_ticklabels([])
        else:
            self.ax.set_axis_off()
        self.redraw()

    # #add one contour. not used at the moment
    # def add_contour(self):
    #     self.n_contours=self.n_contours+1
    #     self.update_image(self.xyzi, self.xyz)
    #     cnt = self.ax.contour(self.xyzi[2], self.n_contours)
    #     self.ax.clabel(cnt, inline=1, fontsize=10)
    #     self.SendSizeEvent()
    #
    # #remove one contour. not used at the moment
    # def remove_contour(self):
    #     self.update_image(self.xyzi, self.xyz)
    #     if self.n_contours>0:
    #         self.n_contours=self.n_contours-1
    #         if self.n_contours>0:
    #             cnt = self.ax.contour(self.xyzi[2], self.n_contours)
    #             self.ax.clabel(cnt, inline=1, fontsize=10)
    #     self.SendSizeEvent()

    #updating the image fast
    def update_image(self, xyzi, xyz, step=0, current_vmin=None, current_vmax=None):
        self.xyzi=xyzi
        self.xyz=xyz
        self.vmin, self.vmax = np.nanmin(self.xyzi[2]), np.nanmax(self.xyzi[2])
        if current_vmin is None or current_vmax is None:
            self.current_vmin, self.current_vmax = self.vmin, self.vmax
        else:
            self.current_vmin, self.current_vmax = current_vmin, current_vmax

        self.ax.clear()
        self.ax.set_axis_off()

        self.plt = self.ax.imshow(self.xyzi[2], origin='lower', interpolation='none', vmin=self.current_vmin, vmax=self.current_vmax)

        # if the depth matrix is binary, automatically set greyscale
        # if np.unique(xyzi[2]).__len__()==2:
        #     self.plt.set_cmap('gray')
        #     current_cmap = 'gray'
        #else:
        self.plt.set_cmap(self.colormap)
        current_cmap = self.colormap

        if self.cbar is not None:
            self.cbar.set_cmap(current_cmap)
            self.cbar.draw_all()
            self.cbar.ax.set_xticklabels([str(round(self.current_vmin, 1)), str(round(self.current_vmax, 1))])

        self.cnt_step = step
        if step > 0:
            #change start of contour levels to the vmin rounded
            self.contour_level_start = np.floor(self.current_vmin)
            self.set_contours(self.cnt_step)

        self.mouse_entry_flag = False
        self.redraw()

    def add_toolbar(self):

        self.toolbar = NavigationToolbar(self.canvas)

        if IS_MAC:
            # force refresh whenever a mouse enter the toolbar area
            self.toolbar.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_entry)
            self.toolbar.Bind(wx.EVT_LEAVE_WINDOW, self.on_mouse_leave)
            # HOME_BTN_ID = self.toolbar.GetToolByPos(1).GetId()
            # qtool = self.toolbar.FindById(HOME_BTN_ID)#.Bind(wx.EVT_LEFT_UP, self.on_mouse_release)
            # self.Bind(wx.EVT_LEFT_UP, self.on_mouse_release, qtool)

        # delete subplots button from the toolbar
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 6
        self.toolbar.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)

        # delete the default save button from the NavigationToolbar
        POSITION_OF_SAVE_FIGURE_BTN = 7
        self.toolbar.DeleteToolByPos(POSITION_OF_SAVE_FIGURE_BTN)

        # customised save
        save_icon = wx.ImageFromBitmap(wx.Bitmap('icons\\save.png'))
        save_icon = save_icon.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
        save_icon = wx.BitmapFromImage(save_icon)


        if self.pid == 0:
            self.toolbar.AddSimpleTool(self.ON_SAVE_PANEL_LEFT, save_icon, 'Save', 'Save the image to file')
            wx.EVT_TOOL(self, self.ON_SAVE_PANEL_LEFT, self.new_save)
        else:
            self.toolbar.AddSimpleTool(self.ON_SAVE_PANEL_RIGHT, save_icon, 'Save', 'Save the image to file')
            wx.EVT_TOOL(self, self.ON_SAVE_PANEL_RIGHT, self.new_save)

        # add to the plot
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        self.toolbar.Realize()
        # self.toolbar.update()

    def new_save(self, evt):
        # Fetch the required filename and file type.
        #filetypes = self.canvas._get_imagesave_wildcards()

        # insert your default dir here
        if self.pid == 0:
            count = self.lsavefilehistory.GetCount()
        else:
            count = self.rsavefilehistory.GetCount()
        if count == 0:
            last_path = ""
        else:
            if self.pid == 0:
                last_path = self.lsavefilehistory.GetHistoryFile(0)
                self.lsavefilehistory.GetHistoryFile(0)
            else:
                last_path = self.rsavefilehistory.GetHistoryFile(0)
                self.rsavefilehistory.GetHistoryFile(0)

        dlg = wx.FileDialog(self, "Save to file", last_path, "", self.image_file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:

            path = dlg.GetPath()
            self.fig.savefig(path)

            if IS_MAC:  # identify the path separator based on the used system
                index = path.rfind('/')
            elif IS_WIN:
                index = path.rfind('\\')
            path = path[:index]

            if self.pid == 0:
                self.lsavefilehistory.AddFileToHistory(path)
                self.lsavefilehistory.Save(self.config_lsavefile)
            else:
                self.rsavefilehistory.AddFileToHistory(path)
                self.rsavefilehistory.Save(self.config_rsavefile)

    def switch_save_icon(self, flag_save):

        POSITION_OF_SAVE_FIGURE_BTN = 7
        self.toolbar.DeleteToolByPos(POSITION_OF_SAVE_FIGURE_BTN)

        # if save contours icons is shown, replace it with save icon
        if flag_save:
            save_icon = wx.ImageFromBitmap(wx.Bitmap('icons\\save.png'))
            save_icon = save_icon.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
            save_icon = wx.BitmapFromImage(save_icon)

            self.toolbar.AddSimpleTool(self.ON_SAVE_PANEL_RIGHT, save_icon, 'Save', 'Save the image to file')

        else:
            save_icon = wx.ImageFromBitmap(wx.Bitmap('icons\\export-contours.png'))
            save_icon = save_icon.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
            save_icon = wx.BitmapFromImage(save_icon)

            self.toolbar.AddSimpleTool(self.ON_SAVE_PANEL_RIGHT, save_icon, 'Export contours',
                                       'Export contours to file')


        wx.EVT_TOOL(self, self.ON_SAVE_PANEL_RIGHT, self.new_save)

        self.toolbar.update()
        self.toolbar.Realize()


    # transform color scale with given max and min values
    def transform_color_scale(self, min_depth, max_depth):
        if not self.current_vmin == min_depth or not self.current_vmax == max_depth:  # transform only if needed to save time
            self.current_vmin, self.current_vmax = min_depth, max_depth
            self.plt = self.ax.imshow(self.xyzi[2], origin='lower', interpolation='none', vmin=self.current_vmin, vmax=self.current_vmax)
            if not self.cbar is None:  # if colorbar exists
                self.cbar.ax.set_xticklabels([str(round(self.current_vmin, 1)), str(round(self.current_vmax, 1))])
            self.redraw()

    # back to original color scale
    def revert_color_scale(self):
        if not self.current_vmin == self.vmin or not self.current_vmax == self.vmax:  # transform only if needed to save time
            self.current_vmin, self.current_vmax = self.vmin, self.vmax
            self.plt = self.ax.imshow(self.xyzi[2], origin='lower', interpolation='none', vmin=self.current_vmin, vmax=self.current_vmax)
            if not self.cbar is None:  # if colorbar exists
                self.cbar.ax.set_xticklabels([str(round(self.current_vmin, 1)), str(round(self.current_vmax, 1))])
            self.redraw()

    def on_mouse_entry(self, event):
        print("mouse entry!")
        self.mouse_entry_flag = True
        # self.canvas.draw()
        self.update()
        # mpl.mouse_release_event = mpl.fig.canvas.mpl_connect('button_release_event', self.Parent.Parent.on_mouse_release)
        # event.Skip()

    def on_mouse_leave(self, event):
        print("mouse out!!")
        self.mouse_entry_flag = False

    # when mouse entry mini toolbar area update plot every 1s
    def update(self):
        print("update!")
        self.canvas.draw()
        # mpl.mouse_release_event = mpl.fig.canvas.mpl_connect('button_release_event', self.Parent.Parent.on_mouse_release)
        # event.Skip()
        if self.mouse_entry_flag:
            wx.CallLater(int(1 * 1000), self.update)

    #return the real size of the print in selected multiplier in string
    def real_size_string(self):
        size = str(np.nanmax(self.xyzi[0]) - np.nanmin(self.xyzi[0])) + 'x'\
               + str(np.nanmax(self.xyzi[1]) - np.nanmin(self.xyzi[1]))

        if self.multiplier==1:
            size = size + ' mm.'
        elif self.multiplier==10:
            size = size + ' cm.'
        else:
            size = size + ' m.'

        return size

    def delete_figure(self):
        plt.close(self.fig)

class MatplotPanel3D(wx.Panel):
    def __init__(self, parent, xyzi, xyz, multiplier, elevation, azimuth, size=None, mpl_src=None,  title='', fname='', lmark_xy=None, A=None, pid=-1, current_vmin=None, current_vmax=None):
        if size is None:
            size_p = parent.GetSize()
            size = (max(120, size_p[1]), size_p[1] - 30)

        wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)

        # save limage file history
        # self.lsavefilehistory = wx.FileHistory(9)
        # self.config_lsavefile = wx.Config(localFilename = "pyTrans-Lsavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        # self.lsavefilehistory.Load(self.config_lsavefile)
        # self.ON_SAVE_PANEL_LEFT = wx.NewId()

        # save rimage file history
        # self.rsavefilehistory = wx.FileHistory(9)
        # self.config_rsavefile = wx.Config(localFilename = "pyTrans-Rsavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        # self.rsavefilehistory.Load(self.config_rsavefile)
        # self.ON_SAVE_PANEL_RIGHT = wx.NewId()

        #self.image_file_filter = "All supported files (*.jpg;*.png;*.pdf;*.svg;*.eps)|*.jpg;*.png;*.pdf;*.svg;*.eps|JPG files|*.jpg|PNG files|*.png|PDF files|*.pdf|SVG files|*.svg|EPS files|*.eps|All files (*.*)|*.*"


        self.xyzi = xyzi
        self.xyz = xyz
        self.mpl_src = mpl_src
        self.title = title
        self.lmark_xy = lmark_xy
        self.fname = fname
        self.master_fname = None
        self.master_lmark_xy = None
        self.cbar = None
        self.used = False
        self.A = A
        self.multiplier=multiplier
        self.xthrs = self.xyzi[2].shape[0] / 100
        self.ythrs = self.xyzi[2].shape[1] / 100
        self.pid = pid
        self.colormap='jet'


        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.canvas = FigureCanvas(self, -1, self.fig)

        if isinstance(parent, wx._windows.ScrolledWindow):
            self.Selected = wx.CheckBox(self)  # check box
            self.sizer.Add(self.Selected)

        self.vmin, self.vmax = np.nanmin(self.xyzi[2]), np.nanmax(self.xyzi[2])
        if current_vmin is None or current_vmax is None:
            self.current_vmin, self.current_vmax = self.vmin, self.vmax
        else:
            self.current_vmin, self.current_vmax = current_vmin, current_vmax

        #  if not bottom panel
        #  this line checks whether matplotpanesl is in the bottom or center
        if not isinstance(parent, wx._windows.ScrolledWindow):
            #self.add_toolbar()
            # add horizontal colorbar
            cbaxes = self.fig.add_axes([0.1, 0.05, 0.8, 0.03])
            self.cbar = colorbar.ColorbarBase(cbaxes, ticks=[0, 1], orientation='horizontal')
            self.cbar.ax.set_xticklabels([str(round(self.current_vmin, 1)), str(round(self.current_vmax, 1))])

        self.sizer.Add(self.canvas, 1)

        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_axis_off()

        # create meshgrid for 3d plot
        mn = self.xyz.min(axis=0)  # min and max values per column
        mx = self.xyz.max(axis=0)

        gridsize = 300

        xm, ym = np.meshgrid(np.linspace(mn[0], mx[0], gridsize), np.linspace(mn[1], mx[1], gridsize))
        grid_locations = np.vstack((xm.ravel(), ym.ravel())).T  # flatten to pass to griddata method
        Z = scipy.interpolate.griddata(self.xyz[:, [0,1]], self.xyz[:, 2], grid_locations, method='nearest')  # interpolate to the smaller grid
        Z = Z.reshape(xm.shape)

        # draw a plot on local scale
        self.plt = self.ax.plot_surface(xm, ym, Z, linewidth=0, cmap=cm.jet, vmin=np.min(Z), vmax=np.max(Z))
        self.ax.view_init(elev=elevation, azim=azimuth)
        self.ax.mouse_init(rotate_btn=None, zoom_btn=None)
        # mes_fig = self.fig.gca(projection='3d')
        # mes_fig.axis('equal')

        # self.ax.set_xlim3d(0.5*np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z))))-100,
        #                    0.5 *np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z))))-100)
        # self.ax.set_ylim3d(0.5*np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z))))-50,
        #                    0.5 *np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z))))-50)
        # self.ax.set_zlim3d(0.5*np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z)))),
        #                    0.5 *np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z)))))

        set_axes_equal(self.ax, xm, ym, Z, 0.35)


    # updating the image fast
    def update_image3D(self, xyzi, xyz, current_vmin=None, current_vmax=None):

        self.xyzi = xyzi
        self.xyz = xyz
        self.vmin, self.vmax = np.nanmin(self.xyzi[2]), np.nanmax(self.xyzi[2])
        if current_vmin is None or current_vmax is None:
            self.current_vmin, self.current_vmax = self.vmin, self.vmax
        else:
            self.current_vmin, self.current_vmax = current_vmin, current_vmax

        # self.ax.clear()
        # self.ax.set_axis_off() #not working atm
        self.plt.remove()

        # create meshgrid for 3d plot
        mn = np.nanmin(self.xyz, axis=0)  # min and max values per column
        mx = np.nanmax(self.xyz, axis=0)

        gridsize = 300

        xm, ym = np.meshgrid(np.linspace(mn[0], mx[0], gridsize), np.linspace(mn[1], mx[1], gridsize))
        grid_locations = np.vstack((xm.ravel(), ym.ravel())).T  # flatten to pass to griddata method
        Z = scipy.interpolate.griddata(self.xyz[:, [0, 1]], self.xyz[:, 2], grid_locations,
                                       method='nearest')  # interpolate to the smaller grid
        Z = Z.reshape(xm.shape)

        # draw a plot on local scale
        self.plt = self.ax.plot_surface(xm, ym, Z, linewidth=0, cmap=cm.jet, vmin=np.nanmin(Z), vmax=np.nanmax(Z))

        self.ax.set_xlim3d(np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z)))),
                      np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z)))))

        #self.plt
        #self.ax.view_init(elev=elevation, azim=azimuth)
        #self.ax.mouse_init(rotate_btn=None, zoom_btn=None)
        # mes_fig = self.fig.gca(projection='3d')
        # mes_fig.axis('equal')

        set_axes_equal(self.ax, xm, ym, Z, 0.35)

        #colormap
        self.plt.set_cmap(self.colormap)

        self.SendSizeEvent()

    def rotate_3d(self, elevation, azimuth):
        self.ax.view_init(elev=elevation, azim=azimuth)

    def delete_figure(self):
        plt.close(self.fig)

    def set_cmap3D(self, cmap='jet'):
        self.colormap = cmap
        self.plt.set_cmap(cmap)
        self.SendSizeEvent()



def set_axes_equal(ax, xm, ym, Z, coefficient):
    '''Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc..  This is one possible solution to Matplotlib's
    ax.set_aspect('equal') and ax.axis('equal') not working for 3D.

    Input
      ax: a matplotlib axis, e.g., as output from plt.gca().
    '''

    # x_limits = ax.get_xlim3d()
    # y_limits = ax.get_ylim3d()
    # z_limits = ax.get_zlim3d()

    # self.ax.set_xlim3d(0.5 * np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z)))) - 100,
    #                    0.5 * np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z)))) - 100)
    #
    # self.ax.set_ylim3d(0.5 * np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z)))) - 50,
    #                    0.5 * np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z)))) - 50)
    # self.ax.set_zlim3d(0.5 * np.nanmin(np.hstack((np.nanmin(xm), np.nanmin(ym), np.nanmin(Z)))),
    #                    0.5 * np.nanmax(np.hstack((np.nanmax(xm), np.nanmax(ym), np.nanmax(Z)))))

    x_range = np.nanmax(xm) - np.nanmin(xm); x_mean = (np.nanmax(xm) + np.nanmin(xm))/2
    y_range = np.nanmax(ym) - np.nanmin(ym); y_mean = (np.nanmax(ym) + np.nanmin(ym))/2
    z_range = np.nanmax(Z) - np.nanmin(Z); z_mean = (np.nanmax(Z) + np.nanmin(Z))/2

    # The plot bounding box is a sphere in the sense of the infinity
    # norm, hence I call half the max range the plot radius.
    #plot_radius = 0.25*max([x_range, y_range, z_range])
    plot_radius = coefficient*max([x_range, y_range, z_range])

    ax.set_xlim3d([x_mean - plot_radius, x_mean + plot_radius])
    ax.set_ylim3d([y_mean - plot_radius, y_mean + plot_radius])
    ax.set_zlim3d([z_mean - plot_radius, z_mean + plot_radius])