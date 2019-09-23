import datetime


class StockItem:
    def __init__(self,
                 sku,
                 product_id=None,
                 description=None,
                 category=None,
                 classification=None,
                 calibre=None,
                 unit_cost=None,
                 unit_weight=None,
                 nec_weight=None,
                 case_size=None,
                 hse_no=None,
                 ce_no=None,
                 serial_no=None,
                 duration=None,
                 low_noise=None,
                 notes=None,
                 preview_link=None,
                 hidden=None,
                 stock_on_hand=None,
                 shots=None
                 ):
        if sku is None or type(sku) in (str, int):
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
            record = sku
            self.sku = record.sku
            self.description = record.description
            self.classification = int(record.classification)
            self.calibre = int(record.calibre) if record.calibre is not None else None
            self.unit_cost = float(record.unit_cost) if record.unit_cost is not None else None
            self.unit_weight = float(record.unit_weight) if record.unit_weight is not None else None
            self.nec_weight = float(record.nec_weight) if record.nec_weight is not None else None
            self.case_size = int(record.case_size) if record.case_size is not None else None
            self.hse_no = record.hse_no
            self.ce_no = record.ce_no
            self.serial_no = record.serial_no
            self.duration = float(record.duration) if record.duration is not None else None
            self.low_noise = record.low_noise in ("True", 1, True)
            self.notes = record.notes
            self.preview_link = record.preview_link
            self.category = int(record.category) if record.category is not None else None
            self.hidden = record.hidden in ("True", 1, True)
            self.product_id = record.product_id
            self.stock_on_hand = int(record.stock_on_hand) if record.stock_on_hand is not None else None
            self.shots = int(record.shots) if record.shots is not None else None

    def __repr__(self):
        return "sku: {}, desc: {}".format(self.sku, self.description)


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
