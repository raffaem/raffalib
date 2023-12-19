#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import sqlite3
from pathlib import Path
from typing import Any, Optional

class SQLiteDB:

    def __init__(self, dbfp:Path|str, commit_on_close:bool=False) -> None:
        self.commit_on_close = commit_on_close
        self.dbfp = Path(dbfp)
        self.dbfp.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.Connection(self.dbfp)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        self.set_foreign_keys(True)
        # For litestream
        self.cur.execute("PRAGMA busy_timeout = 5000;")
        # self.cur.execute("PRAGMA journal_mode=WAL;")
        # commit before turning synchronous to normal
        # otherwise sqlite3 fails with
        # OperationalError: Safety level may not be changed inside a transaction
        # self.con.commit()
        # self.cur.execute("PRAGMA synchronous = NORMAL;")
        # self.cur.execute("PRAGMA wal_autocheckpoint = 0;")

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if not self.con:
            return
        if self.commit_on_close:
            self.commit()
        self.con.close()
        self.con = None

    def unlink(self) -> None:
        if self.dbfp.is_file():
            self.dbfp.unlink()
            self.dbfp = None

    def close_and_unlink(self) -> None:
        self.close()
        self.unlink()

    def commit(self) -> None:
        self.con.commit()

    def get_foreign_keys(self) -> bool:
        foreign_keys = int(self.cur.execute("PRAGMA foreign_keys;").fetchone()["foreign_keys"])
        assert(foreign_keys in [0,1])
        return foreign_keys == 1

    def set_foreign_keys(self, fk:bool) -> None:
        fks = "ON" if fk else "OFF"
        self.cur.execute(f"PRAGMA foreign_keys = {fks};")
        assert(self.get_foreign_keys()==fk)


    def get_max_id(self, table:str, col:str="id") -> int:
        #self.logger.warning("Using get_max_id. Are you sure?")
        query = f"SELECT MAX({col}) AS max_id FROM {table}"
        return self.con.cursor().execute(query).fetchone()["max_id"]


    def insert_into(self,
                    table:str,
                    data:dict[str,Any],
                    crs:Optional[str]=None) -> sqlite3.Cursor:
        if crs:
            assert(crs in ["ROLLBACK", "ABORT", "FAIL", "IGNORE", "REPLACE"])
        col_names = ",".join(list(data.keys()))
        col_phs = [":"+x for x in list(data.keys())]
        col_phs = ",".join(col_phs)
        or_statement = ("OR " + crs) if crs else ""
        query = f"INSERT {or_statement} INTO {table} ({col_names}) VALUES ({col_phs});"
        return self.con.cursor().execute(query, data)


    def insert_into_many(self,
                         table:str,
                         data:list[dict[str,Any]],
                         crs:Optional[str]=None) -> sqlite3.Cursor:
        if crs:
            assert(crs in ["ROLLBACK", "ABORT", "FAIL", "IGNORE", "REPLACE"])
        keys = set(data[0].keys())
        for d in data[1:]:
           assert(set(d.keys())==keys)
        col_names = ",".join(keys)
        col_phs = [":"+x for x in keys]
        col_phs = ",".join(col_phs)
        or_statement = ("OR " + crs) if crs else ""
        query = f"INSERT {or_statement} INTO {table} ({col_names}) VALUES ({col_phs});"
        return self.con.cursor().executemany(query, data)


    def get_tables(self) -> list[str]:
        query = """
        SELECT
            name
        FROM
            sqlite_schema
        WHERE
            type ='table' AND
            name NOT LIKE 'sqlite_%';
        """
        rows = orbisdb.con.cursor().execute(query).fetchall()
        tables = [row["name"] for row in rows]
        return tables

    def get_columns(self, table:str) -> list[str]:
        query = f"""
        SELECT sql FROM sqlite_master
        WHERE tbl_name = '{table}' AND type = 'table'
        """
        rows = self.con.cursor().execute(query).fetchall()
        row = rows[0]
        row = dict(row)
        pos = row["sql"].find("(")
        pos2 = row["sql"].find(")")
        cols = row["sql"][pos+1:pos2].split(",")
        cols = [col.replace("\t"," ") for col in cols]
        cols = [col.strip().split(" ")[0] for col in cols]
        cols = [col.replace("\"","").replace("'","") for col in cols]
        return cols

    def drop_table(self, table_name, fail_if_not_exists=False) -> None:
        query = f"DROP TABLE "
        if not fail_if_not_exists:
            query += "IF EXISTS"
        query += f" {table_name}"
        self.con.cursor().execute(query)
