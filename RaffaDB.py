#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import sqlite3

class RaffaDB:

    def __init__(self, dbfp):
        self.dbfp = dbfp
        self.con = sqlite3.Connection(self.dbfp)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

    def __del__(self):
        if self.con:
            self.close()

    def close(self):
        if self.con:
            self.con.close()
            self.con = None

    def close_and_unlink(self):
        self.close()
        if self.dbfp.is_file():
            self.dbfp.unlink()

    def commit(self):
        self.con.commit()
