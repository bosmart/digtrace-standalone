#file open options dialog

import wx

class DecreaseSizeDialog(wx.Dialog):

    def __init__(self, *args, **kw):
        super(DecreaseSizeDialog, self).__init__(*args, **kw)

        self.InitUI()
        #self.SetSize((250, 200))
        self.SetTitle("Decrease size...")

        self.percent = 0
        self.random = True


    def InitUI(self):

        self.ok = False #OK clicked?


        vbox = wx.BoxSizer(wx.VERTICAL)


        self.percentSlider = wx.Slider(parent=self, value=0,
                  minValue=40,
                  maxValue=100,
                  pos=wx.DefaultPosition, size=(250, -1),
                  style=wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.percentSlider.SetValue(100)

        self.randomCheck = wx.CheckBox(self, wx.ID_ANY, label="Random row deletion")


        text = wx.StaticText(self, label="Select image(csv) quality settings:")
        text.SetFont(wx.Font(14, wx.DEFAULT, wx.ITALIC, wx.BOLD))
        vbox.Add(text, flag=wx.ALL | wx.ALIGN_CENTER, border=4)

        text = wx.StaticText(self, label="Image(csv) quality:")
        text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        vbox.Add(text, flag=wx.ALL | wx.ALIGN_CENTER, border=2)

        vbox.Add(self.percentSlider, flag=wx.ALL | wx.ALIGN_CENTER, border=2)
        vbox.Add(self.randomCheck, flag=wx.ALL | wx.ALIGN_CENTER, border=2)

        buttons = self.CreateButtonSizer(wx.CANCEL | wx.OK)
        vbox.Add(buttons, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, border=10)

        #okButton = wx.Button(self, label='Ok')
        #vbox.Add(okButton, flag=wx.ALL, border=2)



        self.SetSizer(vbox)
        self.Fit()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_OK)





    def OnClose(self, e):

        self.percent = self.percentSlider.GetValue()
        self.random = self.randomCheck.GetValue()

        self.ok = True #OK clicked is true

        self.Destroy()