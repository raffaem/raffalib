#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

class GenniResponse:
    def __init__(self, resp:Optional[dict], error:Optional[str]=None):
        if resp:
            self.gender = resp["Genni"]
            self.ethnicity = resp["Ethnea"]
            self.first = resp["First"]
            self.last = resp["Last"]
        else:
            self.gender=self.ethnicity=self.first=self.last=None
        self.error = error

     #def __init__(self, first:str, last:str, gender:str, ethnicity:str, error:Optional[str]):
     #   self.first=first
     #   self.last=last
     #   self.gender=gender
     #   self.ethnicity=ethnicity
     #   self.error=error

    def __str__(self):
        return str(self.__dict__)

