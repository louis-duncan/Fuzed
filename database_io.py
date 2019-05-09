import sqlite3
import sql
import random
import os
import pickle
import time
import datetime

class DatabaseTimeoutError(Exception):
    pass

class Database:
    def __init__(self, database_path):
        self.database_path = database_path
        self.uid = os.environ["USERNAME"] + "@" + os.environ["COMPUTERNAME"]
        self._has_handle = False
        self._handle_path = self.database_path+"-handle.dat"

    def open_database_connection(self) -> sql.SQL:
        conn = sqlite3.connect(self.database_path)
        bliss: sql.SQL = sql.SQL(conn)
        return bliss

    def take_handle(self, timeout=10):
        start_time = time.time()
        # Get the handle that currenly exists.
        try:
            with open(self._handle_path, "br") as fh:
                current_handle = pickle.load(fh)
        except FileNotFoundError:
            current_handle = None

        # If we can take the handle:
        if current_handle is None or current_handle.has_expired():
            new_handle = Handle(self.uid)
            with open(self._handle_path, "bw") as fh:
                current_handle = pickle.dump(new_handle, fh)
        else:
            pass #todo



    def release_handle(self):
        pass


class Handle:
    def __init__(self, uid, ttl=30):
        self.uid = uid
        self._expiry = datetime.datetime.now() + datetime.timedelta(seconds=ttl)

    def has_expired(self):
        return datetime.datetime.now() > self._expiry
