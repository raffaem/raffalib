#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import hashlib
import random
import time
from pathlib import Path
import logging
import requests
import json

from dataclasses import dataclass

from ..SQLiteDB import SQLiteDB
from ..Logger import Logger

@dataclass
class GeoCodingID:
    ids:list[int]
    downloaded:bool

@dataclass
class NominatimQuery:

    query:dict[str,str] = None

    def update_query(self, d:dict[str,str]) -> None:
        d.update(query)

    # Free-form query
    # See: https://nominatim.org/release-docs/latest/api/Search/#free-form-query
    @staticmethod
    def from_free_form(q:str):
        return NominatimQuery(query={"q":q})

    # Structured query
    # See: https://nominatim.org/release-docs/latest/api/Search/#structured-query
    @staticmethod
    def from_structured(amenity:str=None,
                        street:str=None,
                        city:str=None,
                        county:str=None,
                        state:str=None,
                        country:str=None,
                        postalcode:str=None):
        return NominatimQuery(query={
            "amenity": amenity,
            "street": street,
            "city": city,
            "county": county,
            "state": state,
            "country": country,
            "postalcode": postalcode
            })

class NominatimDB(SQLiteDB):

    def __init__(self, fp: Path, logger:Logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = Logger()
        super().__init__(fp)

    def ini_db(self,  if_not_exists:bool=True) -> None:
        # If not exists statement
        if if_not_exists:
            if_not_exists = "IF NOT EXISTS"
        else:
            if_not_exists = ""
        # Tabe `geocoding`
        query = f"""
        CREATE TABLE {if_not_exists} geocoding (
            id INTEGER PRIMARY KEY NOT NULL,
            input TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            nres INTEGER,
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
        # Table `addresses_to_geocoding`
        query = f"""
        CREATE TABLE {if_not_exists} addresses_to_geocoding
        (
            id INTEGER PRIMARY KEY,
            addresses_id INTEGER REFERENCES addresses(id),
            geocoding_id INTEGER REFERENCES geocoding(id),
            UNIQUE(addresses_id, geocoding_id)
        )
        """
        self.con.cursor().execute(query)
        # Indexes
        query = "CREATE INDEX IF NOT EXISTS geocoding_input ON geocoding(input)"
        self.con.cursor().execute(query)

    def _get_geocoding_ids_from_input(self, inputtxt: str):
        query = "SELECT id FROM geocoding WHERE input=?"
        rows = self.con.cursor().execute(query, [inputtxt]).fetchall()
        if not rows:
            return None
        return [row["id"] for row in rows]

    def geocode(self,
                query:NominatimQuery,
                limit:int=10,
                verbose:bool=False,
                error_sleep_time:tuple[int,int]=(20,30),
                max_attempts:int=10):
        """
        Geocode an  address using Nominatim API
        :param query: The query to search
        :type query: NominatimQuery
        :param limit: The maximum number of search results to return
        :type limit: int
        :param verbose: Be chatty
        :type verbose: bool
        :param error_sleep_time: A tuple indicating the minimum and maximum seconds to sleep before retrying in case of errors
        :type error_sleep_time: tuple[int,int]
        :param max_attempts: The maximum number of attempts to perform in case of errors
        :type max_attemps: int
        """
        # If we already have the location, return it
        geocoding_ids = self._get_geocoding_ids_from_input(address)
        if geocoding_ids:
            if verbose:
                logging.info(f"Address '{address}' already processed")
            return GeoCodingID(ids=geocoding_ids, downloaded=False)
        # Otherwise, geocode the new address
        if verbose:
            logging.info(f'Geolocating "{address}"')
        # Query the API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "format": "json",
            "limit": limit
            }
        query.update_query(params)
        resp = None
        for attempt in range(1, max_attempts+1):
            if attempt > 1:
                logging.info(f"Attempt={attempt}")
            try:
                resp = requests.get(url, params=params)
            except requests.ConnectionError:
                sleep_time = random.uniform(*error_sleep_time)
                msg = f"ConnectionError for {url}\n" \
                      f"Waiting {sleep_time} then retrying..."
                self.logger.log_exception()
                self.logger.error(msg)
                time.sleep(sleep_time)
                continue
            else:
                break
        if resp is None:
            raise Exception("Max attempts exceeded without being able to download the url")
        # Handle HTTP errors
        if resp.status_code != 200:
            locs = []
            nres = None
        else:
            # Parse response as JSON
            # WARNING: This can return an empty list
            locs = json.loads(resp.text)
            nres = len(locs)
        # Insert into `geocoding` table
        loclist = list()
        if locs:
            for loc in locs:
                loc["input"] = address
                loc["status_code"] = resp.status_code
                loc["nres"] = nres
                if "boundingbox" in loc:
                    loc["bounding_box_x1"] = loc["boundingbox"][0]
                    loc["bounding_box_y1"] = loc["boundingbox"][1]
                    loc["bounding_box_x2"] = loc["boundingbox"][2]
                    loc["bounding_box_y2"] = loc["boundingbox"][3]
                    del loc["boundingbox"]
                loclist.append(loc)
        else:
            loc = {
                   "input": address,
                   "status_code": resp.status_code,
                   "nres": nres
                  }
            loclist.append(loc)
        default_keys = {"osm_type":"", "osm_id":""}
        self.insert_into_many("geocoding", loclist, default_keys=default_keys)
        geocoding_ids = self._get_geocoding_ids_from_input(address)
        # Return geocoding.id
        return GeoCodingID(ids=geocoding_ids, downloaded=True)
