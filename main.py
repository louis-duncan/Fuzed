import wx
from wx import richtext
import database_io

TITLE = "Fuzed"


class Launcher(wx.Frame):
    def __init__(self, parent, frame_id, title):
        super().__init__(parent,
                         frame_id,
                         title,
                         style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX), )

        panel = wx.Panel(self, -1)

        main_sizer = wx.GridBagSizer()

        self.upcoming_text_lbl = wx.StaticText(panel,
                                               label="Upcoming Shows:")

        self.upcoming_text = richtext.RichTextCtrl(panel,
                                                   -1,
                                                   style=wx.TE_MULTILINE | wx.TE_READONLY,
                                                   size=(300, 300))
        self.upcoming_text.Caret.Hide()

        buttons = []

        self.search_stock = wx.Button(panel,
                                      label="Search Stock",
                                      size=(150, 50))
        buttons.append(self.search_stock)

        self.view_shows = wx.Button(panel,
                                    label="View Shows",
                                    size=(150, 50))
        buttons.append(self.view_shows)

        self.create_show = wx.Button(panel,
                                     label="Create Show",
                                     size=(150, 50))
        buttons.append(self.create_show)

        i = 0
        for i, b in enumerate(buttons):
            main_sizer.Add(b,
                           pos=(i + 1, 3),
                           span=(1, 1))

        main_sizer.Add(self.upcoming_text_lbl,
                       pos=(0, 1),
                       span=(1, 1))

        main_sizer.Add(self.upcoming_text,
                       pos=(1, 1),
                       span=(i + 1, 1))

        main_sizer.Add(pos=(1 + len(buttons), 4),
                       size=(10, 10))

        panel.SetSizerAndFit(main_sizer)

        self.Fit()
        self.update_upcoming()

        self.Bind(wx.EVT_TEXT_URL, self.event_clicked)

    def update_upcoming(self):
        with db.open_database_connection() as con:
            shows = db.get_shows(con)

        text = ""
        underlines = []
        headers = []
        bodies = []
        for s in shows:
            underline = [len(text), 0]
            text += s.date_time.ctime() + "\n"
            underline[1] = len(text) - 1

            header = [len(text), 0]
            text += s.show_title + "\n"
            header[1] = len(text) - 1

            body = [len(text), 0]
            text += s.show_description
            body[1] = len(text) - 1

            text += "\n\n"

            underlines.append(underline)
            headers.append(header)
            bodies.append(body)

        self.upcoming_text.SetValue(text)

        for i, u in enumerate(underlines):
            new_style = wx.TextAttr()
            new_style.SetFontUnderlined(True)
            new_style.SetURL(str(shows[i].show_id))
            self.upcoming_text.SetStyle(u[0],
                                        u[1],
                                        new_style)

        head_style = wx.TextAttr()
        head_style.SetFontWeight(wx.FONTWEIGHT_BOLD)

        for h in headers:
            self.upcoming_text.SetStyle(h[0],
                                        h[1],
                                        head_style)

        body_style = wx.TextAttr()
        body_style.SetFontStyle(wx.FONTSTYLE_ITALIC)

        for b in bodies:
            self.upcoming_text.SetStyle(b[0],
                                        b[1],
                                        body_style)



    def event_clicked(self, e):
        print("Clicked:", e.String)


db = database_io.init()
app = wx.App(False)
frame = Launcher(None,
                 wx.ID_ANY,
                 TITLE)
frame.Show()
app.MainLoop()
