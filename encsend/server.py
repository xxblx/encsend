# -*- coding: utf-8 -*-

import asyncio
import json
from datetime import datetime
from time import mktime

import aioodbc
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError, CryptoError
from nacl.public import SealedBox
from nacl.signing import VerifyKey

from .sql import INSERT, SELECT
from .utils import get_signing_key

try:
    from . import conf
except ImportError:
    from . import conf_default as conf
finally:
    HOST, PORT, DSN = conf.HOST, conf.PORT, conf.DSN


class EncSendServer:
    def __init__(self, loop, host, port, dsn, signature_path=None):
        self.loop = loop
        self.host = host
        self.port = port
        self.dsn = dsn
        self.signature_path = signature_path

    async def init_db(self):
        self.db_pool = await aioodbc.create_pool(dsn=self.dsn, loop=self.loop)

    def init_keys(self):
        self.signing_key = get_signing_key(self.signature_path)
        self.private_key = self.signing_key.to_curve25519_private_key()

    async def tcp_server(self, reader, writer):
        data = await reader.read()
        writer.close()
        datetime_now = datetime.now()
        message, host_id = await self.read_message(data)

        if message is not None:
            now = mktime(datetime_now.utctimetuple())
            values = (message, host_id, now)

            # with aioodbc <= 0.3.2 this code will not work because of
            # https://github.com/aio-libs/aioodbc/issues/114
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(INSERT['messages'], values)

    async def read_message(self, data):
        """ Read and decrypt incoming message, check it's signature

        :param data: incoming data
        :type data: bytes
        :return: tuple with message and host_id if message was decrypted
            and signature verified, otherwise - None
        :rtype: (bytes, int) or None
        """

        # TODO: check magic byte
        unsealed_box = SealedBox(self.private_key)
        try:
            json_data = unsealed_box.decrypt(data, encoder=HexEncoder)
        except CryptoError:
            return
        dct = json.loads(json_data.decode())

        if dct.keys() != {'host', 'message'}:
            return

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SELECT['hosts'], (dct['host'],))
                host_id = await cur.fetchall()

        # Host wasn't found in DB
        if not host_id:
            return

        # Check signature
        verify_key = VerifyKey(dct['host'].encode(), encoder=HexEncoder)
        try:
            message = verify_key.verify(dct['message'].encode(),
                                        encoder=HexEncoder)
        except BadSignatureError:
            return

        return message, host_id[0][0]

    def start(self):
        self.init_keys()
        self.loop.run_until_complete(self.init_db())
        self.coro = asyncio.start_server(self.tcp_server, self.host, self.port,
                                         loop=self.loop)
        self.server = self.loop.run_until_complete(self.coro)

    async def wait(self):
        await self.server.wait_closed()
        await self.db_pool.wait_closed()

    def stop(self):
        self.server.close()
        self.db_pool.close()


def start_encsend_server(host=HOST, port=PORT, dsn=DSN, path=None):
    loop = asyncio.get_event_loop()
    encsend_server = EncSendServer(loop=loop, host=HOST, port=PORT, dsn=DSN,
                                   signature_path=path)
    encsend_server.start()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        encsend_server.stop()
        loop.run_until_complete(encsend_server.wait())
        loop.close()
