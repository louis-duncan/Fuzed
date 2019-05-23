import database_io
import wx
from wx.richtext import RichTextCtrl


class Launcher(wx.Frame):
    def __init__(self, parent, frame_id, title, database):
        super().__init__(parent,
                         frame_id,
                         title,
                         style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.title = title

        self.stock_viewer = None
        self.events_viewer = None
        self.control_panel = None

        self.database = database

        panel = wx.Panel(self, -1)

        main_sizer = wx.GridBagSizer()

        self.upcoming_text_lbl = wx.StaticText(panel,
                                               label="Upcoming Events:")

        self.upcoming_text = RichTextCtrl(panel,
                                          -1,
                                          style=wx.TE_MULTILINE | wx.TE_READONLY,
                                          size=(300, 300))
        self.upcoming_text.Caret.Hide()

        buttons = []

        self.stock_button = wx.Button(panel,
                                      label="Stock",
                                      size=(150, 50))
        buttons.append(self.stock_button)

        self.events_button = wx.Button(panel,
                                       label="Events",
                                       size=(150, 50))
        buttons.append(self.events_button)

        self.control_panel_button = wx.Button(panel,
                                              label="Control Panel",
                                              size=(150, 50))
        buttons.append(self.control_panel_button)

        i = 0
        for i, b in enumerate(buttons):
            main_sizer.Add(b,
                           pos=(2 * i + 1, 3),
                           span=(1, 1))
            if i != len(buttons) - 1:
                main_sizer.Add(pos=(2 * i + 2, 3),
                               size=(5, 5))

        main_sizer.Add(self.upcoming_text_lbl,
                       pos=(0, 1),
                       span=(1, 1))

        main_sizer.Add(self.upcoming_text,
                       pos=(1, 1),
                       span=(len(buttons) + 2, 1))

        main_sizer.Add(pos=(3 + len(buttons), 4),
                       size=(10, 10))

        panel.SetSizerAndFit(main_sizer)

        self.Fit()
        self.update_upcoming()

        self.Bind(wx.EVT_TEXT_URL, self.event_clicked)
        self.Bind(wx.EVT_BUTTON, self.stock_button_clicked, self.stock_button)
        self.Bind(wx.EVT_BUTTON, self.events_button_clicked, self.events_button)
        self.Bind(wx.EVT_BUTTON, self.control_panel_button_clicked, self.control_panel_button)

        self.Show()

    def update_upcoming(self):
        with self.database.open_database_connection() as con:
            shows = self.database.get_shows(con)

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

    def stock_button_clicked(self, e):
        print("Stock Button Clicked")
        if self.stock_viewer is None or not self.stock_viewer.open:
            self.stock_viewer = StockViewer(self,
                                            wx.ID_ANY,
                                            self.title,
                                            self.database)
        else:
            self.stock_viewer.Raise()

    def events_button_clicked(self, e):
        print("Events Button Clicked")

    def control_panel_button_clicked(self, e):
        print("Control Panel Button Clicked")


class StockViewer(wx.Frame):
    def __init__(self, parent, frame_id, title, database: database_io.DatabaseHandler):
        super().__init__(parent,
                         frame_id,
                         title + " - Stock Viewer",
                         style=wx.DEFAULT_FRAME_STYLE)
        self.title = title
        self.database = database
        self.open = True

        # Setup ListCtrl
        self.stock_list = wx.ListCtrl(self,
                                      size=(-1, -1),
                                      style=wx.LC_REPORT | wx.LC_HRULES)
        self.table_headers = {"SKU": ("sku", lambda x: str(x).zfill(6)),
                              "Product ID": ("product_id", lambda x: x),
                              "Description": ("description", lambda x: x),
                              "Category": ("category", lambda x: x),
                              "Classification": ("classification", lambda x: x),
                              "Unit Cost": ("unit_cost", lambda x: "£{:.2f}".format(x)),
                              "Unit Weight": ("unit_weight", lambda x: "{:.2f}kg".format(x)),
                              "NEC Weight": ("nec_weight", lambda x: "{:.2f}kg".format(x)),
                              "Calibre": ("calibre", lambda x: "{}mm".format(x)),
                              "Duration": ("duration", lambda x: "{}s".format(x)),
                              "Low Noise": ("low_noise", lambda x: "Yes" if x else "No")}

        for i, h in enumerate(self.table_headers.keys()):
            self.stock_list.InsertColumn(i, h)

        # Create and populate the controls area.
        controls_sizer = wx.BoxSizer(wx.VERTICAL)

        controls_panel = wx.Panel(self, -1)

        padding = 5

        self.create_new_button = wx.Button(controls_panel,
                                           label="Create New Item",
                                           size=(200, 50))
        controls_sizer.Add(self.create_new_button, 0, wx.LEFT | wx.RIGHT, padding)

        controls_sizer.AddSpacer(padding)

        self.edit_button = wx.Button(controls_panel,
                                     label="Edit Selected Item",
                                     size=(200, 50))
        controls_sizer.Add(self.edit_button, 0, wx.LEFT | wx.RIGHT, padding)

        controls_sizer.AddSpacer(padding * 3)

        self.search_box = wx.SearchCtrl(controls_panel, size=(200, -1))
        self.search_box.SetDescriptiveText("Filter...")
        controls_sizer.Add(self.search_box, 0, wx.LEFT | wx.RIGHT, padding)

        # Add filter boxes.
        controls_sizer.AddSpacer(padding * 3)

        with self.database.open_database_connection() as con:
            self.categories_select = wx.CheckListBox(controls_panel,
                                                     wx.ID_ANY,
                                                     size=(200, 100),
                                                     choices=self.database.get_categories(con))

            self.classifications_select = wx.CheckListBox(controls_panel,
                                                          wx.ID_ANY,
                                                          size=(200, 75),
                                                          choices=self.database.get_classifications(con))

        self.select_all_categories(None)
        self.select_all_classifications(None)

        categories_label = wx.StaticText(controls_panel,
                                         wx.ID_ANY,
                                         label="Categories:")
        controls_sizer.Add(categories_label, 0, wx.LEFT | wx.RIGHT, padding)
        controls_sizer.Add(self.categories_select, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, padding)

        controls_sizer.AddSpacer(padding / 2)

        cat_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cat_select_all = wx.Button(controls_panel,
                                        wx.ID_ANY,
                                        label="Select All",
                                        size=(-1, 30))
        self.cat_clear_all = wx.Button(controls_panel,
                                       wx.ID_ANY,
                                       label="Clear All",
                                       size=(-1, 30))
        cat_buttons_sizer.Add(self.cat_select_all, 1, wx.EXPAND)
        cat_buttons_sizer.Add(self.cat_clear_all, 1, wx.EXPAND)
        controls_sizer.Add(cat_buttons_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, padding)

        controls_sizer.AddSpacer(padding * 2)
        classifications_label = wx.StaticText(controls_panel,
                                              wx.ID_ANY,
                                              label="Classifications:")
        controls_sizer.Add(classifications_label, 0, wx.LEFT | wx.RIGHT, padding)
        controls_sizer.Add(self.classifications_select, 0, wx.LEFT | wx.RIGHT, padding)

        controls_sizer.AddSpacer(padding / 2)

        class_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.class_select_all = wx.Button(controls_panel,
                                          wx.ID_ANY,
                                          label="Select All",
                                          size=(-1, 30))
        self.class_clear_all = wx.Button(controls_panel,
                                         wx.ID_ANY,
                                         label="Clear All",
                                         size=(-1, 30))
        class_buttons_sizer.Add(self.class_select_all, 1, wx.EXPAND)
        class_buttons_sizer.Add(self.class_clear_all, 1, wx.EXPAND)
        controls_sizer.Add(class_buttons_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, padding)

        controls_sizer.AddSpacer(padding * 2)
        self.show_hidden_box = wx.CheckBox(controls_panel,
                                           wx.ID_ANY,
                                           label="Show hidden items.")
        controls_sizer.Add(self.show_hidden_box, 0, wx.LEFT | wx.RIGHT, padding)

        controls_sizer.AddSpacer(padding)

        controls_panel.SetSizerAndFit(controls_sizer)

        # Add things to the main sizer, and assign it to a main panel.
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        main_sizer.Add(self.stock_list, 1, wx.EXPAND)

        main_sizer.Add(controls_panel, 0, wx.EXPAND)

        main_sizer.SetSizeHints(self)

        self.SetSizerAndFit(main_sizer)

        self.Show()

        # Bindings
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_BUTTON, self.select_all_categories, self.cat_select_all)
        self.Bind(wx.EVT_BUTTON, self.clear_categories, self.cat_clear_all)
        self.Bind(wx.EVT_BUTTON, self.select_all_classifications, self.class_select_all)
        self.Bind(wx.EVT_BUTTON, self.clear_classifications, self.class_clear_all)
        self.Bind(wx.EVT_LISTBOX, self.category_filter_changed, self.categories_select)
        self.Bind(wx.EVT_LISTBOX, self.classification_filter_changed, self.classifications_select)

        self.populate_table(None)

    def category_filter_changed(self, e):
        # Do stuff

        # Stop items being highlighted.
        self.categories_select.Deselect(self.categories_select.GetSelection())

    def classification_filter_changed(self, e):
        # Do stuff

        # Stop items being highlighted.
        self.classifications_select.Deselect(self.classifications_select.GetSelection())

    def select_all_categories(self, e):
        for i in range(len(self.categories_select.Items)):
            self.categories_select.Check(i, True)

    def clear_categories(self, e):
        for i in range(len(self.categories_select.Items)):
            self.categories_select.Check(i, False)

    def select_all_classifications(self, e):
        for i in range(len(self.classifications_select.Items)):
            self.classifications_select.Check(i, True)

    def clear_classifications(self, e):
        for i in range(len(self.classifications_select.Items)):
            self.classifications_select.Check(i, False)

    def populate_table(self, e):
        with self.database.open_database_connection() as con:
            stock_items = self.database.get_all_items(con)

        for i in stock_items:
            self.stock_list.Append(["" if getattr(i, self.table_headers[h][0]) is None else
                                    self.table_headers[h][1](getattr(i, self.table_headers[h][0]))
                                    for h in self.table_headers])


    def update_table(self, e):
        pass

    def on_close(self, e):
        self.open = False
        e.Skip()
