#file open options dialog

import wx

class GridOptionsDialog(wx.Dialog):


    def __init__(self, *args, **kw):
        super(GridOptionsDialog, self).__init__(*args, **kw)

        self.InitUI()
        # self.SetSize((250, 200))
        self.SetTitle("Choose grid distance")

        self.grid_distance = 10

    def InitUI(self):

        self.ok = False #OK clicked?

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        #self.choicePrec = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["0.25mm", "0.50mm", "1.00mm"]) #0.25 precision crashes, too mcu memory
        self.inputValue = wx.TextCtrl(self, wx.ID_ANY, value="10")
        self.choiceMult = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["mm.", "cm.", "dm.", "m."]) # choice of multiplier
        self.choiceMult.SetSelection(0)

        hbox.Add(self.inputValue, flag=wx.LEFT | wx.RIGHT, border=25)
        hbox.Add(self.choiceMult, flag=wx.LEFT | wx.RIGHT, border=25)
        buttons = self.CreateButtonSizer(wx.CANCEL | wx.OK)

        self.warning_text = wx.StaticText(self, label="Please enter a valid distance")
        self.warning_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.warning_text.SetForegroundColour((255, 0, 0))  # set text color


        vbox.Add(hbox, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, border=10)
        vbox.Add(self.warning_text, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        vbox.Add(buttons, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, border=10)

        #okButton = wx.Button(self, label='Ok')
        #vbox.Add(okButton, flag=wx.ALL, border=2)

        self.SetSizer(vbox)
        self.Fit()
        #self.warning_text.Hide()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_OK)





    def OnClose(self, e):

        try:
            value = float(self.inputValue.GetValue())
        except:
            self.warning_text.Show()
            self.Layout()
            return

        self.ok = True #OK clicked is true

        choice = self.choiceMult.GetSelection()

        scale= pow(10, choice)

        self.grid_distance=value * scale

        self.Destroy()