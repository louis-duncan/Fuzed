from gui import *
from custom_globals import *

db = database_io.init()
app = wx.App(False)
frame = Launcher(None,
                 wx.ID_ANY,
                 TITLE,
                 db)
frame.Show()
app.MainLoop()
