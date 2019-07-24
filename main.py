from gui import *
from custom_globals import *


app = wx.App(False)
frame = Launcher(None,
                 wx.ID_ANY,
                 TITLE)
frame.Show()
app.MainLoop()
