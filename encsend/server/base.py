# -*- coding: utf-8 -*-

import aioodbc

from ..utils import get_signing_key


class ServerBase:
    """ Base server class """
    def __init__(self, loop, host, port, dsn, signature_path=None):
        """
        :param loop: asyncio event loop
        :param host: tcp server host
        :type host: str
        :param port: tcp server port
        :type port: int
        :param dsn: Data Source Name, information about database driver,
            server, database, etc
        :type dsn: str
        :param signature_path: custom path to signature key file
        :type signature_path: str or None
        """
        self.loop = loop
        self.host = host
        self.port = port
        self.dsn = dsn
        self.signature_path = signature_path
        self.init_keys()

    async def init_db(self):
        self.db_pool = await aioodbc.create_pool(dsn=self.dsn, loop=self.loop)

    def init_keys(self):
        self.signing_key = get_signing_key(self.signature_path)
        self.private_key = self.signing_key.to_curve25519_private_key()
