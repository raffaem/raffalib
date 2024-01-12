#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import hashlib
import random
import time
from pathlib import Path
import logging

from dataclasses import dataclass
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

from .SQLiteDB import SQLiteDB

@dataclass
class GeoCodingID():
    ids:list[int]
    downloaded:bool

class GeoCodingDB(SQLiteDB):

    def _new_geolocator(self):
        if self.user_agent is None:
            unix_time = datetime.datetime.now().timestamp()
            self.user_agent = hashlib.md5(str(unix_time).encode("utf8")).hexdigest()
        logging.info(f"Creating new geolocator with user_agent={self.user_agent}")
        self.geolocator = Nominatim(user_agent=self.user_agent)

    def __init__(self, fp: Path, user_agent: str = None):
        super().__init__(fp)
        self.user_agent = user_agent
        self._new_geolocator()
        query = """
        CREATE TABLE IF NOT EXISTS geocoding (
            id INTEGER PRIMARY KEY NOT NULL,
            error TEXT,
            input TEXT,
            addresstype TEXT,
            bounding_box_x1 REAL,
            bounding_box_y1 REAL,
            bounding_box_x2 REAL,
            bounding_box_y2 REAL,
            class TEXT,
            display_name TEXT,
            importance REAL,
            lat REAL,
            licence TEXT,
            lon REAL,
            name TEXT,
            osm_id INTEGER,
            osm_type TEXT,
            place_id INTEGER,
            place_rank INTEGER,
            type TEXT
        )
        """
        self.con.cursor().execute(query)
        query = "CREATE INDEX IF NOT EXISTS geocoding_input ON geocoding(input)"
        self.con.cursor().execute(query)

    def _do_geocode(self, address, attempt=1, max_attempts=10, sleep_range=(10, 20)):
        try:
            return self.geolocator.geocode(address, exactly_one=False)
        except (GeocoderTimedOut, GeocoderUnavailable):
            if attempt <= max_attempts:
                sleep_time = random.uniform(*sleep_range)
                logging.info(
                    f"Caught exception. Sleeping for {sleep_time:.2f} seconds then retrying"
                )
                time.sleep(sleep_time)
                self._new_geolocator()
                logging.info("Retrying")
                return self._do_geocode(
                    address,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    sleep_range=sleep_range,
                )
            raise

    def _get_ids_from_input(self, address: str):
        query = "SELECT id FROM geocoding WHERE input=?"
        rows = self.con.cursor().execute(query, [address]).fetchall()
        if not rows:
            return None
        return [row["id"] for row in rows]

    def geocode(self, address: str, verbose: bool = False):
        # If we already have the location, return it
        ids = self._get_ids_from_input(address)
        if ids:
            if verbose:
                logging.info(f"Address '{address}' already processed")
            return GeoCodingID(ids=ids, downloaded=False)
        # Otherwise, geocode the new address
        if verbose:
            logging.info(f'Geolocating "{address}"')
        locs = self._do_geocode(address)
        # Save geolocation into db
        if not locs:
            loclist = [{"input": address, "error": "404"}]
        else:
            loclist = list()
            for loc in locs:
                d = loc.raw
                d["bounding_box_x1"] = d["boundingbox"][0]
                d["bounding_box_y1"] = d["boundingbox"][1]
                d["bounding_box_x2"] = d["boundingbox"][2]
                d["bounding_box_y2"] = d["boundingbox"][3]
                del d["boundingbox"]
                d["input"] = address
                loclist.append(d)
        self.insert_into_many("geocoding", loclist)
        ids = self._get_ids_from_input(address)
        return GeoCodingID(ids=ids, downloaded=True)
