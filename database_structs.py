import datetime


class StockItem:
    def __init__(self,
                 sku,
                 product_id="",
                 description="",
                 category=0,
                 classification=0,
                 calibre=0.0,
                 unit_cost=0.0,
                 unit_weight=0.0,
                 nec_weight=0.0,
                 case_size=0,
                 hse_no="",
                 ce_no="",
                 serial_no="",
                 duration=0.0,
                 low_noise=False,
                 notes="",
                 preview_link="",
                 hidden=False,
                 stock_on_hand=0,
                 shots=0
                 ):
        if type(sku) in (str, int):
            self.sku = sku
            self.product_id = product_id
            self.description = description
            self.category = category
            self.classification = classification
            self.calibre = calibre
            self.unit_cost = unit_cost
            self.unit_weight = unit_weight
            self.nec_weight = nec_weight
            self.case_size = case_size
            self.hse_no = hse_no
            self.ce_no = ce_no
            self.serial_no = serial_no
            self.duration = duration
            self.low_noise = low_noise
            self.notes = notes
            self.preview_link = preview_link
            self.hidden = hidden
            self.product_id = product_id
            self.stock_on_hand = stock_on_hand
            self.shots = shots
        else:
            pass


class Show:
    def __init__(self,
                 show_id,
                 show_title="",
                 show_description="",
                 supervisor=0,
                 date_time=datetime.datetime.now(),
                 complete=False,
                 changes=(),
                 items=()
                 ):
        self.show_id = show_id
        self.show_title = show_title
        self.show_description = show_description
        self.supervisor = supervisor
        self.date_time = date_time
        self.items = list(items)  # list of (stock item, qty).
        self.changes = list(changes)  # list of Record objects.
        self.complete = complete

    def add_change_log(self, date_time, user_id, action_text):
        self.changes.append({'date_time': date_time,
                             'user_id': user_id,
                             'action_text': action_text})


class ShowChange:
    def __init__(self,
                 date_time,
                 text):
        self.date_time = date_time
        self.text = text


class User:
    def __init__(self,
                 user_id,
                 name=None,
                 auth_level=None):
        if name is None or auth_level is None:
            record = user_id
            self.user_id = int(record.user_id)
            self.name = str(record.name)
            self.auth_level = int(record.auth_level)
        else:
            self.user_id = user_id
            self.name = name
            self.auth_level = auth_level

    def __repr__(self):
        return "User: {} - Name: {} - Auth Level: {}".format(self.user_id, self.name, self.auth_level)
