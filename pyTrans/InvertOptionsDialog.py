#file open options dialog

import wx

class InvertOptionsDialog(wx.Dialog):

    def __init__(self, *args, **kw):
        super(InvertOptionsDialog, self).__init__(*args, **kw)

        self.InitUI()
        #self.SetSize((250, 200))
        self.SetTitle("Invert axes")

        self.x = False
        self.y = False
        self.z = False


    def InitUI(self):

        self.ok = False  # OK clicked?

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.xCheck = wx.CheckBox(self, wx.ID_ANY, label="X axis")
        self.yCheck = wx.CheckBox(self, wx.ID_ANY, label="Y axis")
        self.zCheck = wx.CheckBox(self, wx.ID_ANY, label="Z axis")

        buttons = self.CreateButtonSizer(wx.CANCEL | wx.OK)

        vbox.Add(self.xCheck, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        vbox.Add(self.yCheck, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        vbox.Add(self.zCheck, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        vbox.Add(buttons, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)

        self.SetSizer(vbox)
        self.Fit()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_OK)

    def OnClose(self, e):

        self.x = float(self.xCheck.GetValue())
        self.y = float(self.yCheck.GetValue())
        self.z = float(self.zCheck.GetValue())

        self.ok = True #OK clicked is true

        self.Destroy()