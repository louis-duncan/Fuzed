import binascii
import hashlib
import sqlite3
import sql
import random
import os
import pickle
import time
import datetime
import database_structs

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

    def get_stock_item(self, sku):
        pass

    def search_items(self, text, classification):
        pass

    def update_stock_item(self, stock_item_obj):
        pass

    def get_show(self, show_id):
        pass

    def update_show(self, show_obj):
        pass

    def validate_user(self, user_name, password, sign_in=True):
        with self._open_database_connection() as con:
            user = con.one("SELECT * FROM users WHERE name=?", (user_name,))
        self._release_handle()

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
            self._release_handle()
            self.__signed_in_user = user.user_id
        else:
            pass
        return valid

    def signed_in_user(self):
        return self.__signed_in_user

    def get_user(self, user_id=None, user_name=None):
        assert user_id is not None or user_name is not None
        if user_id is not None:
            q = "SELECT * FROM users WHERE user_id=?"
            p = (user_id,)
        else:
            q = "SELECT * FROM users WHERE name=?"
            p = (user_name,)
        with self._open_database_connection() as con:
            result = con.one(q, p)
        self._release_handle()
        return result

    def sign_out(self):
        self.__signed_in_user = None




class Handle:
    def __init__(self, uid, ttl=30):
        self.holder = uid
        self._expiry = datetime.datetime.now() + datetime.timedelta(seconds=ttl)

    def expired(self):
        return datetime.datetime.now() > self._expiry
