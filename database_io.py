import binascii
import hashlib
import sqlite3
import sql
import os
import pickle
import time
import datetime
from database_structs import *


class DatabaseTimeoutError(Exception):
    pass


class Database:
    def __init__(self, database_path):
        self.database_path = database_path
        self.uid = os.environ["USERNAME"] + "@" + os.environ["COMPUTERNAME"]
        self._handle_path = self.database_path+"-handle.dat"

    def _open_database_connection(self):
        # Get the handle
        self._take_handle()  # Will throw a DatabaseTimeoutError if the connection fails.

        # If we're here we got the handle, so open the database and return the db_object.
        conn = sqlite3.connect(self.database_path)
        bliss: sql.SQL = sql.SQL(conn)

        return bliss

    def _take_handle(self, attempts=5, delay=2):
        # Get the handle that currently exists.
        if attempts == 0:
            raise DatabaseTimeoutError
        current_handle = self._get_handle()

        # If we can take the handle:
        if (current_handle is None) or current_handle.expired() or (current_handle.holder == self.uid):
            new_handle = Handle(self.uid)
            with open(self._handle_path, "bw") as fh:
                pickle.dump(new_handle, fh)
        # Else wait and try again.
        else:
            time.sleep(delay)
            self._take_handle(attempts=attempts - 1)

    def _release_handle(self):
        current_handle = self._get_handle()

        if current_handle is None:
            pass
        else:
            if current_handle.holder != self.uid:
                pass
            else:
                # The only case in which the program needs to make any changes.
                with open(self._handle_path, "bw") as fh:
                    pickle.dump(None, fh)

    def _get_handle(self):
        try:
            with open(self._handle_path, "br") as fh:
                current_handle = pickle.load(fh)
        except FileNotFoundError:
            current_handle = None
        return current_handle

    def _has_handle(self):
        current_handle = self._get_handle()
        return (current_handle is not None) and (current_handle.holder == self.uid) and (not current_handle.expired())


class DatabaseHandler(Database):
    def __init__(self, database_path):
        super().__init__(database_path)
        self.__signed_in_user = None

    def get_items_by_category(self, categories, text_filter="", release=True):
        if type(categories) in (list, tuple):
            q = "SELECT * FROM stock_items WHERE category IN ({})"
            q.format(str(categories).strip("()[],"))
        elif categories == "*":
            q = "SELECT * FROM stock_items"
        else:
            raise(ValueError("Parameter categories must be list, tuple or '*'."))

        with self._open_database_connection() as con:
            items = [self.record_to_item(i) for i in con.all(q)]

        if release:
            self._release_handle()

        if text_filter != "":
            for i in items:
                if text_filter.lower() in i.description.lower() or text_filter.lower() in i.notes.lower():
                    pass
                else:
                    items.remove(i)

        return items

    def update_stock_item(self, stock_item_obj):
        pass

    def get_shows(self, open_only=True, text_filter="", release=True):
        q = "SELECT * FROM shows"
        if open_only:
            q += " WHERE complete=0"

        with self._open_database_connection() as con:
            shows = [self.record_to_show(s, False) for s in con.all(q)]

        if release:
            self._release_handle()

        if text_filter != "":
            for s in shows:
                text_filter = text_filter.lower()
                if text_filter in s.show_title.lower() or\
                        text_filter in s.show_description.lower() or\
                        text_filter in s.supervisor.lower():
                    pass
                else:
                    shows.remove(s)

        return shows

    def update_show(self, show_obj):
        pass

    def validate_user(self, user_name, password, sign_in=True, release=True):
        with self._open_database_connection() as con:
            user = con.one("SELECT * FROM users WHERE name=?", (user_name,))

        if user is None:
            return

        hasher = hashlib.sha3_256()
        hasher.update(password.encode())
        hasher.update(binascii.unhexlify(user.pass_salt))
        valid = hasher.hexdigest() == user.pass_hash

        if sign_in and valid:
            with self._open_database_connection() as con:
                con.run("UPDATE users SET last_login_time=?  WHERE user_id=?", (datetime.datetime.now(), user.user_id))
                con.connection.commit()
            self.__signed_in_user = user.user_id
        else:
            pass

        if release:
            self._release_handle()

        return valid

    def signed_in_user(self):
        return self.__signed_in_user

    def get_user(self, user_id=None, user_name=None, release=True):
        assert user_id is not None or user_name is not None
        if user_id is not None:
            q = "SELECT * FROM users WHERE user_id=?"
            p = (user_id,)
        else:
            q = "SELECT * FROM users WHERE name=?"
            p = (user_name,)
        with self._open_database_connection() as con:
            result = con.one(q, p)
        if release:
            self._release_handle()
        return result

    def sign_out(self):
        self.__signed_in_user = None

    def get_show_changes(self, show_id, release=True):
        with self._open_database_connection() as con:
            raw_changes = con.all("SELECT date_time, text FROM show_changes WHERE show_id=?", (show_id,))

        if release:
            self._release_handle()

        return [ShowChange(datetime.datetime.fromtimestamp(c.date_time / 1000), c.text) for c in raw_changes]

    def record_to_item(self, record):
        return StockItem(record.sku,
                         record.description,
                         record.category,
                         record.classification,
                         record.calibre,
                         record.unit_cost,
                         record.unit_weight,
                         record.nec_weight,
                         record.case_size,
                         record.hse_no,
                         record.ce_no,
                         record.serial_no,
                         record.duration,
                         record.low_noise,
                         record.notes,
                         record.preview_link,
                         bool(record.hidden))

    def record_to_show(self, record, release=True):
        changes = self.get_show_changes(record.show_id, release)
        return Show(record.show_id,
                    record.show_title,
                    record.show_description,
                    record.supervisor,
                    datetime.datetime.fromtimestamp(record.date_time / 1000),
                    bool(record.complete),
                    changes)


class Handle:
    def __init__(self, uid, ttl=30):
        self.holder = uid
        self._expiry = datetime.datetime.now() + datetime.timedelta(seconds=ttl)

    def expired(self):
        return datetime.datetime.now() > self._expiry


if __name__ == "__main__":
    db = DatabaseHandler("database.sqlite")