#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import logging
import json
import base64

import keepassxc_proxy_client
import keepassxc_proxy_client.protocol
from keepassxc_proxy_client.protocol import ResponseUnsuccesfulException

# WARNING: This is python-gnupg (https://pypi.org/project/python-gnupg/), NOT gnupg (https://pypi.org/project/gnupg/)
import gnupg as python_gnupg

class RaffaKeePassXC:
    """
    This class creates a KeePassXC association and store it in an encrypted file
    """

    def __init__(self, kpxcencfp, gpg=None):
    
        if not gpg:
            self.gpg = python_gnupg.GPG()
        else:
            self.gpg = gpg
    
        self.keepassxc = keepassxc_proxy_client.protocol.Connection()
    
        try:
            self.keepassxc.connect()
        except FileNotFoundError:
            raise Exception("KeePassXC is either not open " \
                            "or is open but browser integration is not enabled")
    
        try:
            dbhash = self.keepassxc.get_databasehash()
            logging.debug("Database hash: "+dbhash)
        except ResponseUnsuccesfulException as e:
            # Database not opened
            raise Exception("Database not opened")
    
        if not kpxcencfp.is_file():
            logging.debug("Creating new KeePassXC association")
            self.keepassxc.associate()
            logging.debug("Test associate: " + str(self.keepassxc.test_associate()))
            assert(self.keepassxc.test_associate())
            name, public_key = self.keepassxc.dump_associate()
            public_key_str = base64.b64encode(public_key).decode('ascii')
            outd = {
                "name": name,
                "pk": public_key_str
            }
            outdd = json.dumps(outd, ensure_ascii=False, indent=4, sort_keys=True)
            outenc = self.gpg.encrypt(outdd, "raffaele.mancuso4@unibo.it")
            if not outenc.ok:
                raise Exception("GPG returned an error. "\
                                "Is the private key enrolled within GPG?")
            with open(kpxcencfp, "wb") as fh:
                fh.write(outenc.data)
        else:
            logging.debug("Reading existing KeePassXC association from file")
            with open(kpxcencfp, "rb") as fh:
                outenc = fh.read()
            outdd = self.gpg.decrypt(outenc)
            assert(outdd.ok)
            outd = json.loads(outdd.data)
            self.keepassxc.load_associate(name=outd["name"], public_key=base64.b64decode(outd["pk"]))
            assert(self.keepassxc.test_associate())
