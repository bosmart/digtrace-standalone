import wx
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar

IS_GTK = 'wxGTK' in wx.PlatformInfo
IS_WIN = 'wxMSW' in wx.PlatformInfo
IS_MAC = 'wxMac' in wx.PlatformInfo

class ContourPanel(wx.Panel):
    def __init__(self, parent, xyzi1, xyzi2, levels1, levels2, Tsav):
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(1, 1))

        self.ON_SAVE_PANEL = wx.NewId()
        # save contour file history
        self.csavefilehistory = wx.FileHistory(9)
        self.config_csavefile = wx.Config(localFilename = "pyTrans-Csavefile1", style=wx.CONFIG_USE_LOCAL_FILE)
        self.csavefilehistory.Load(self.config_csavefile)

        self.image_file_filter = "All supported files (*.jpg;*.png;*.pdf;*.svg;*.eps)|*.jpg;*.png;*.pdf;*.svg;*.eps|JPG files|*.jpg|PNG files|*.png|PDF files|*.pdf|SVG files|*.svg|EPS files|*.eps|All files (*.*)|*.*"


        self.xyzi1 = xyzi1
        self.xyzi2 = xyzi2
        self.Tsav = Tsav

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.fig = Figure()
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.ax = self.fig.add_subplot(111, aspect='equal')
        self.ax.set_axis_off()
        self.canvas = FigureCanvas(self, -1, self.fig)

        self.add_toolbar()  # add toolbar to zoom save etc.

        self.sizer.Add(self.canvas, 1)
        matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
        #sort contour levels in increasing order
        levels1.sort(axis=0)
        levels2.sort(axis=0)
        self.plt1 = self.ax.contour(xyzi1[0], xyzi1[1], xyzi1[2], levels1, origin='lower', colors='k')
        self.plt2 = self.ax.contour(xyzi2[0], xyzi2[1], xyzi2[2], levels2, origin='lower', colors='r')
        # self.plt1 = self.ax.contour(xyzi1[2], origin='lower', colors='k')
        # self.plt2 = self.ax.contour(xyzi2[2], origin='lower', colors='r')


    def add_toolbar(self):

        self.toolbar = NavigationToolbar(self.canvas)

        # delete subplots button from the toolbar
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 7
        self.toolbar.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)

        # delete the default save button from the NavigationToolbar
        POSITION_OF_SAVE_FIGURE_BTN = 7
        self.toolbar.DeleteToolByPos(POSITION_OF_SAVE_FIGURE_BTN)

        # customised save
        save_icon = wx.ImageFromBitmap(wx.Bitmap('icons\\save-comparison-contours.png'))
        save_icon = save_icon.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
        save_icon = wx.BitmapFromImage(save_icon)

        self.toolbar.AddSimpleTool(self.ON_SAVE_PANEL, save_icon, 'Save', 'Save the image to file')
        wx.EVT_TOOL(self, self.ON_SAVE_PANEL, self.new_save)

        # add to the plot
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        self.toolbar.Realize()

    def new_save(self, evt):
        # Fetch the required filename and file type.
        #filetypes = self.canvas._get_imagesave_wildcards()

        # insert your default dir here
        if self.csavefilehistory.GetCount() == 0:
            last_path = ""
        else:
            last_path = self.csavefilehistory.GetHistoryFile(0)

        dlg = wx.FileDialog(self, "Save to file", last_path, "", self.image_file_filter, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.fig.savefig(path)

            if IS_MAC:  # identify the path separator based on the used system
                index = path.rfind('/')
            elif IS_WIN:
                index = path.rfind('\\')
            path = path[:index]

            self.csavefilehistory.AddFileToHistory(path)
            self.csavefilehistory.Save(self.config_csavefile)

    def delete_figure(self):
        for coll in self.plt1.collections:
            coll.remove()
        for coll in self.plt2.collections:
            coll.remove()

