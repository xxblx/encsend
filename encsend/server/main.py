# -*- coding: utf-8 -*-

import asyncio
import json
from datetime import datetime
from time import mktime

from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError, CryptoError
from nacl.public import SealedBox
from nacl.signing import VerifyKey

from .base import ServerBase
from ..sql import INSERT, SELECT

try:
    from .. import conf
except ImportError:
    from .. import conf_default as conf
finally:
    HOST, PORT, DSN = conf.HOST, conf.PORT, conf.DSN


class EncSendServer(ServerBase):
    """ EncSend server side implementation """
    async def tcp_server(self, reader, writer):
        data = await reader.read()
        writer.close()
        datetime_now = datetime.now()
        message, host_id = await self.read_message(data)

        if message is not None:
            # unix timestamp
            now = mktime(datetime_now.utctimetuple())
            values = (message, host_id, now)

            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(INSERT['messages'], values)

    async def read_message(self, data):
        """ Read and decrypt incoming message, check it's signature

        :param data: incoming data
        :type data: bytes
        :return: tuple with message and host_id if message was decrypted
            and signature verified, otherwise - None
        :rtype: (str, int) or None
        """
        # TODO: check magic byte
        unsealed_box = SealedBox(self.private_key)
        try:
            json_data = unsealed_box.decrypt(data, encoder=HexEncoder)
        except CryptoError:
            return
        dct = json.loads(json_data.decode())

        # a dictionary has invalid structure
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

        return message.decode(), host_id[0][0]

    def start(self):
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
    """ Start encsend server

    :param host: tcp server host
    :type host: str
    :param port: tcp server port
    :type port: int
    :param dsn: Data Source Name, information about database driver,
        server, database, etc
    :type dsn: str
    :param path: path to signature key file, if path is `None`
        default path is used
    :type path: str or None
    """
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
