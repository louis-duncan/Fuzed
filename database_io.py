import binascii
import hashlib
import random
import sqlite3

import sql
import os
import pickle
import time
from database_structs import *


DATABASE_PATH = None


class DatabaseTimeoutError(Exception):
    pass


class NewSQL(sql.SQL):
    def __init__(self, connection, handle_path, uid):

        super().__init__(connection)

        self._handle_path = handle_path
        self._uid = uid

    def __enter__(self):
        self._take_handle()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.connection.close()
        self._release_handle()

    def _take_handle(self, attempts=30, delay=1):
        # Get the handle that currently exists.
        if attempts == 0:
            raise DatabaseTimeoutError
        current_handle = self._get_handle()

        # If we can take the handle:
        if (current_handle is None) or current_handle.expired() or (current_handle.holder == self._uid):
            new_handle = Handle(self._uid)
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
            if current_handle.holder != self._uid:
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

    def has_handle(self):
        current_handle = self._get_handle()
        return (current_handle is not None) and (current_handle.holder == self._uid) and (not current_handle.expired())
    
    def commit(self):
        self.connection.commit()


class DatabaseHandler:
    def __init__(self, database_path):
        self.database_path = database_path
        self.uid = os.environ["USERNAME"] + "@" + os.environ["COMPUTERNAME"]
        self._handle_path = self.database_path + "-handle.dat"

        self.__signed_in_user = None

    def open_database_connection(self):
        sql_conn = sqlite3.connect(self.database_path)
        return NewSQL(sql_conn, self._handle_path, self.uid)

    def who_has_handle(self):
        with open(self._handle_path, "br") as fh:
            handle: Handle = pickle.load(fh)

        if handle is None:
            print("Handle not currently held.")
        else:
            print("Handle {} currently held by {} until {}, expired: {}".format(self._handle_path,
                                                                                handle.holder,
                                                                                handle.expiry.ctime(),
                                                                                handle.expired()))

    def get_item(self, con: NewSQL, sku: str) -> StockItem:
        record = con.one("SELECT * FROM stock_items WHERE sku IS ?", (sku, ))
        return StockItem(record)

    def update_item(self, con: NewSQL, item):
        q = "UPDATE stock_items SET"
        args = []
        for k in item.__dict__.keys():
            if k != "sku":
                q += " " + k + "=?,"
                args.append(item.__dict__[k])
        q = q.strip(",")
        args.append(item.sku)
        q += " WHERE sku=?"
        con.run(q, args)
        con.commit()

    def get_items_by_category(self, con, categories, text_filter=""):
        if type(categories) in (list, tuple):
            q = "SELECT * FROM stock_items WHERE category IN ({})"
            q.format(str(categories).strip("()[],"))
        elif categories == "*":
            q = "SELECT * FROM stock_items"
        else:
            raise (ValueError("Parameter categories must be list, tuple or '*'."))

        items = [self.record_to_item(con, i) for i in con.all(q)]

        if text_filter != "":
            for i in items:
                if text_filter.lower() in i.description.lower() or text_filter.lower() in i.notes.lower():
                    pass
                else:
                    items.remove(i)

        return items

    def get_stock_levels(self, con, sku):
        """Takes a SKU and returns the stock pn hand and the available stock.
        :type con: NewSQL
        """
        stock_on_hand = sum(con.all("SELECT stock_on_hand FROM stock_items WHERE sku=?", (sku,)))
        available = stock_on_hand - sum(con.all("SELECT quantity FROM show_items WHERE sku=?", (sku,)))
        return stock_on_hand, available

    def get_shows(self, con, open_only=True, text_filter=""):
        q = "SELECT * FROM shows"
        if open_only:
            q += " WHERE complete=0"

        shows = [self.record_to_show(con, s) for s in con.all(q)]

        if text_filter != "":
            for s in shows:
                text_filter = text_filter.lower()
                if text_filter in s.show_title.lower() or \
                        text_filter in s.show_description.lower() or \
                        text_filter in s.supervisor.lower():
                    pass
                else:
                    shows.remove(s)

        return shows

    def update_show(self, show_obj):
        pass

    def create_user(self, con: NewSQL, username, password, auth_level):
        pass_hash, pass_salt = hash_salt_gen(password)
        con.run("INSERT INTO users (name, auth_level, pass_hash, pass_salt) VALUES (?, ?, ?, ?)", (username.lower(),
                                                                                                   auth_level,
                                                                                                   pass_hash,
                                                                                                   pass_salt))
        con.commit()

    def get_users(self, con: NewSQL):
        return [User(r) for r in con.all("SELECT user_id, name, auth_level FROM users")]

    def validate_user(self, con, user_name, password, sign_in=False):
        assert type(user_name) in (str, int)
        if type(user_name) is str:
            user = con.one("SELECT * FROM users WHERE name=?", (user_name.lower(),))
        elif type(user_name) is int:
            user = con.one("SELECT * FROM users WHERE user_id=?", (user_name,))
        else:
            user = None

        if user is None:
            return False

        hasher = hashlib.sha3_256()
        hasher.update(password.encode())
        hasher.update(binascii.unhexlify(user.pass_salt))
        valid = hasher.hexdigest() == user.pass_hash

        if valid:
            con.run("UPDATE users SET last_login_time=?  WHERE user_id=?", (datetime.datetime.now(), user.user_id))
            con.connection.commit()

        if sign_in:
            self.__signed_in_user = User(user.user_id, user.name, user.auth_level)

        return valid

    def change_username(self, con, user_id, user_name):
        assert user_id not in con.all("SELECT name FROM users")
        con.run("UPDATE users SET name=? WHERE user_id=?", (user_name.lower(), user_id))
        con.commit()

    def change_auth_level(self, con, user_id, auth_level):
        assert type(auth_level) is int
        con.run("UPDATE users SET auth_level=? WHERE user_id=?", (auth_level, user_id))
        con.commit()

    def reset_user_password(self, con, user_name):
        new_password = "".join([chr(random.randint(0, 25) + 97) for i in range(8)])

        new_hash, new_salt = hash_salt_gen(new_password)

        con.run("UPDATE users SET pass_hash=?, pass_salt=? WHERE name=?",
                (new_hash, new_salt, user_name.lower()))
        con.connection.commit()

        return new_password

    def set_user_password(self, con, user_id, new_password):
        """
        :type con: NewSQL
        :param user_id: int
        :param new_password: str
        """

        # noinspection PyUnusedLocal
        new_hash, new_salt = hash_salt_gen(new_password)

        con.run("UPDATE users SET pass_hash=?, pass_salt=? WHERE user_id=?",
                (new_hash, new_salt, user_id))
        con.connection.commit()

        return True

    def signed_in_user(self):
        return self.__signed_in_user

    def get_user(self, con, user_id=None, user_name=None):
        assert user_id is not None or user_name is not None

        if user_id is not None:
            q = "SELECT * FROM users WHERE user_id=?"
            p = (user_id,)
        else:
            q = "SELECT * FROM users WHERE name=?"
            p = (user_name,)

        result = con.one(q, p)

        return result

    def delete_user(self, con, user_id):
        con.run("DELETE FROM users WHERE user_id=?", (user_id,))
        con.commit()

    def sign_out(self):
        self.__signed_in_user = None

    def get_show_changes(self, con, show_id):
        raw_changes = con.all("SELECT date_time, text FROM show_changes WHERE show_id=?", (show_id,))

        return [ShowChange(datetime.datetime.fromtimestamp(c.date_time / 1000), c.text) for c in raw_changes]

    def get_show_items(self, con, show_id):
        raw_items = con.all("SELECT sku, quantity FROM show_items WHERE show_id=?", (show_id,))
        items = [(StockItem(con.one("SELECT * FROM stock_items WHERE sku=?", (i.sku,))),
                  i.quantity) for i in raw_items]
        return items

    def get_categories(self, con):
        return con.all("SELECT category_text FROM stock_categories")

    def get_classifications(self, con):
        return con.all("SELECT classification_text FROM stock_classifications")

    def record_to_show(self, con, record):
        changes = self.get_show_changes(con, record.show_id)
        items = self.get_show_items(con, record.show_id)
        return Show(record.show_id,
                    record.show_title,
                    record.show_description,
                    record.supervisor,
                    datetime.datetime.fromtimestamp(record.date_time / 1000),
                    bool(record.complete),
                    changes,
                    items)

    def get_all_items(self, con):
        return [StockItem(i) for i in con.all("SELECT * FROM stock_items")]


class Handle:
    def __init__(self, uid, ttl=30):
        self.holder = uid
        self.expiry = datetime.datetime.now() + datetime.timedelta(seconds=ttl)

    def expired(self):
        return datetime.datetime.now() > self.expiry


def load_config(config_path="config.cfg"):
    with open(config_path, "r") as fh:
        lines = [l.strip() for l in fh]
    for l in lines:
        if not l.startswith("#"):
            parts = [p.strip() for p in l.split("=")]
            if len(parts) == 2 and parts[0].isupper():
                globals()[parts[0]] = parts[1]


def create_database(path):
    # Make tables
    # Create default user
    pass


def hash_salt_gen(password):
    new_salt = bytes([random.randint(0, 255) for i in range(32)])
    new_hex_salt = binascii.hexlify(new_salt)
    hasher = hashlib.sha3_256()
    hasher.update(password.encode())
    hasher.update(new_salt)
    new_hash = hasher.hexdigest()
    return new_hash, new_hex_salt


def init():
    load_config()
    if not os.path.exists(DATABASE_PATH):
        create_database(DATABASE_PATH)
    return DatabaseHandler(DATABASE_PATH)


if __name__ == "__main__":
    load_config()
    db = DatabaseHandler(DATABASE_PATH)
