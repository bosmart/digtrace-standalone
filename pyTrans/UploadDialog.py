import wx
import wx.xrc
from ConfigParser import SafeConfigParser


class UploadDialog(wx.Dialog):
    def __init__(self, parent):

        self.config = SafeConfigParser()
        self.config.read('config.ini')

        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(self, wx.ID_ANY, u"Please help make this application better!", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText1.Wrap(-1)
        self.m_staticText1.SetFont(wx.Font(12, 74, 90, 92, False, "Arial"))

        bSizer1.Add(self.m_staticText1, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.m_staticText2 = wx.StaticText(self, wx.ID_ANY,
                                           u"We are currently working on improvements to this application, which will allow automatic landmark placement on prints.\n"
                                           u"To facilitate this, we need a large collection of annotated prints.\n\n"
                                           u"Would you like to donate the prints you are processing using this application?",
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        bSizer1.Add(self.m_staticText2, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.m_panel1 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.btnYes = wx.Button(self.m_panel1, wx.ID_YES, u"Yes", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer3.Add(self.btnYes, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.on_yes, id=wx.ID_YES)

        self.btnNotNow = wx.Button(self.m_panel1, wx.ID_NO, u"Maybe later", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer3.Add(self.btnNotNow, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.on_no, id=wx.ID_NO)

        self.m_panel1.SetSizer(bSizer3)
        self.m_panel1.Layout()
        bSizer3.Fit(self.m_panel1)
        bSizer2.Add(self.m_panel1, 1, wx.EXPAND | wx.ALL, 5)

        bSizer1.Add(bSizer2, 1, wx.ALIGN_CENTER, 5)

        self.SetSizer(bSizer1)
        self.Layout()
        bSizer1.Fit(self)

        self.Centre(wx.BOTH)

    def __del__(self):
        pass

    def ShowDialog(self):
        if self.config.has_option('main', 'upload') and self.config.get('main', 'upload') == '1':
            return 1
        else:
            return self.ShowModal()

    def on_yes(self, event):
        self.config.set('main', 'upload', '1')
        self.save_config()
        self.EndModal(1)

    def on_no(self, event):
        self.EndModal(0)

    def save_config(self):
        with open('config.ini', 'w') as f:
            self.config.write(f)