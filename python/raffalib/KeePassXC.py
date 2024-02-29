#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import base64
import json
import logging

# WARNING: This is python-gnupg (https://pypi.org/project/python-gnupg/)
#          NOT gnupg (https://pypi.org/project/gnupg/)
import gnupg as python_gnupg
import keepassxc_proxy_client
import keepassxc_proxy_client.protocol
from keepassxc_proxy_client.protocol import ResponseUnsuccesfulException


class RaffaKeePassXC:
    """
    This class creates a KeePassXC
    association and store it
    in an encrypted file
    """

    def __init__(
        self, kpxcencfp, newgpg=None, passphrase=None
    ):
        if not newgpg:
            self.gpg = python_gnupg.GPG()
        else:
            self.gpg = newgpg

        self.keepassxc = keepassxc_proxy_client.protocol.Connection()

        try:
            self.keepassxc.connect()
        except FileNotFoundError:
            raise Exception(
                "KeePassXC is either not open "
                "or is open but browser integration is not enabled"
            )

        try:
            dbhash = self.keepassxc.get_databasehash()
            logging.debug("Database hash: " + dbhash)
        except ResponseUnsuccesfulException:
            # Database not opened
            raise Exception("Database not opened")

        if not kpxcencfp.is_file():
            logging.debug(
                "Creating new KeePassXC association"
            )
            self.keepassxc.associate()
            logging.debug(
                "Test associate: "
                + str(self.keepassxc.test_associate())
            )
            assert self.keepassxc.test_associate()
            (
                name,
                public_key,
            ) = self.keepassxc.dump_associate()
            public_key_str = base64.b64encode(
                public_key
            ).decode("ascii")
            outd = {"name": name, "pk": public_key_str}
            outdd = json.dumps(
                outd,
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            )
            outenc = self.gpg.encrypt(
                outdd, "raffaele.mancuso4@unibo.it"
            )
            if not outenc.ok:
                raise Exception(
                    "GPG returned an error. "
                    "Is the private key enrolled within GPG?"
                )
            with open(kpxcencfp, "wb") as fh:
                fh.write(outenc.data)
        else:
            logging.debug(
                "Reading existing KeePassXC association from file"
            )
            fh = open(kpxcencfp, "rb")
            outdd = self.gpg.decrypt_file(
                fh, passphrase=passphrase
            )
            fh.close()
            if not outdd.ok:
                msg = f"Failed to decrypt file '{kpxcencfp}'\n"
                msg += f"Content='{outenc}'\n"
                msg += f"outdd='{str(outdd)}'"
                raise Exception(msg)
            outd = json.loads(outdd.data)
            self.keepassxc.load_associate(
                name=outd["name"],
                public_key=base64.b64decode(
                    outd["pk"]
                ),
            )
            if not self.keepassxc.test_associate():
                msg = f"Failed to associate key read from file '{kpxcencfp}'\n"
                raise Exception(msg)
