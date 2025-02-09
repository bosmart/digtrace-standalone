#file open options dialog

import wx

class OpenOptionsDialog(wx.Dialog):

    def __init__(self, *args, **kw):
        super(OpenOptionsDialog, self).__init__(*args, **kw)

        self.InitUI()
        #self.SetSize((250, 200))
        self.SetTitle("Open...")

        self.precision = 0.5
        self.scale = 1


    def InitUI(self):

        self.ok = False #OK clicked?

        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        #self.choicePrec = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["0.25mm", "0.50mm", "1.00mm"]) #0.25 precision crashes, too mcu memory
        self.choicePrec = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["0.50", "1.00"])
        self.choicePrec.SetSelection(0)
        self.choiceMult = wx.Choice(self, wx.ID_ANY, (-1, -1), (-1, -1), ["mm.", "cm.", "dm.", "m."]) # choice of multiplier
        self.choiceMult.SetSelection(0)

        text = wx.StaticText(self, label="Precision:")
        text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))

        vbox1.Add(text, flag=wx.ALL, border=2)
        vbox1.Add(self.choicePrec, flag=wx.ALL, border=2)

        text = wx.StaticText(self, label="Scale:")
        text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))

        vbox2.Add(text, flag=wx.ALL, border=2)
        vbox2.Add(self.choiceMult, flag=wx.ALL, border=2)

        hbox.Add(vbox1, flag=wx.LEFT | wx.RIGHT, border=25)
        hbox.Add(vbox2, flag=wx.LEFT | wx.RIGHT, border=25)
        buttons = self.CreateButtonSizer(wx.CANCEL | wx.OK)

        text = wx.StaticText(self, label="Select settings to open files:")
        text.SetFont(wx.Font(14, wx.DEFAULT, wx.ITALIC, wx.BOLD))

        vbox.Add(text, flag=wx.ALL|wx.ALIGN_CENTER, border=4)
        vbox.Add(hbox, flag=wx.BOTTOM|wx.ALIGN_CENTER, border=10)
        vbox.Add(buttons, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, border=10)

        #okButton = wx.Button(self, label='Ok')
        #vbox.Add(okButton, flag=wx.ALL, border=2)



        self.SetSizer(vbox)
        self.Fit()
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_OK)





    def OnClose(self, e):

        choice = self.choicePrec.GetSelection()

        self.ok = True #OK clicked is true

        if choice == 0:
            self.precision = 0.50
        elif choice == 1:
            self.precision = 1.00


        choice = self.choiceMult.GetSelection()

        self.scale= pow(10, choice)

        self.Destroy()