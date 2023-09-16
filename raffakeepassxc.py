import logging
import json
import base64

import keepassxc_proxy_client
import keepassxc_proxy_client.protocol
from keepassxc_proxy_client.protocol import ResponseUnsuccesfulException

# WARNING: This is python-gnupg (https://pypi.org/project/python-gnupg/), NOT gnupg (https://pypi.org/project/gnupg/)
import gnupg

def get_keepassxc(kpxcencfp, gpg=None):

    if not gpg:
        gpg = gnupg.GPG()

    keepassxc = keepassxc_proxy_client.protocol.Connection()

    try:
        keepassxc.connect()
    except FileNotFoundError:
        raise Exception("KeePassXC is not open")

    try:
        dbhash = keepassxc.get_databasehash()
        logging.debug("Database hash: "+dbhash)
    except ResponseUnsuccesfulException as e:
        # Database not opened
        raise Exception("Database not opened")

    if not kpxcencfp.is_file():
        logging.debug("Creating new KeePassXC association")
        keepassxc.associate()
        logging.debug("Test associate: ", keepassxc.test_associate())
        assert(keepassxc.test_associate())
        name, public_key = keepassxc.dump_associate()
        public_key_str = base64.b64encode(public_key).decode('ascii')
        outd = {
            "name": name,
            "pk": public_key_str
        }
        outdd = json.dumps(outd, ensure_ascii=False, indent=4, sort_keys=True)
        outenc = gpg.encrypt(outdd, "raffaele.mancuso4@unibo.it")
        assert(outenc.ok)
        with open(kpxcencfp, "wb") as fh:
            fh.write(outenc.data)
    else:
        logging.debug("Reading existing KeePassXC association from file")
        with open(kpxcencfp, "rb") as fh:
            outenc = fh.read()
        outdd = gpg.decrypt(outenc)
        assert(outdd.ok)
        outd = json.loads(outdd.data)
        keepassxc.load_associate(name=outd["name"], public_key=base64.b64decode(outd["pk"]))
        assert(keepassxc.test_associate())

    return keepassxc
