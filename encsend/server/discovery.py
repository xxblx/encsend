# -*- coding: utf-8 -*-

import asyncio
import socket
from datetime import datetime

from .base import ServerBase

try:
    from .. import conf
except ImportError:
    from .. import conf_default as conf
finally:
    DISCOVERY_ADDR, DSN = conf.DISCOVERY_ADDR, conf.DSN
    DISCOVERY_HOST, DISCOVERY_PORT = conf.DISCOVERY_HOST, conf.DISCOVERY_PORT


class DiscoveryServer(ServerBase):
    """ EncSend Discovery server """
    def __init__(self, loop, host, port, dsn, signature_path, broadcast_addr):
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
        :param broadcast_addr: address where broadcast message
            should be sent
        :type broadcast_addr: str
        """
        super().__init__(loop, host, port, dsn, signature_path)
        self.broadcast_addr = broadcast_addr

    def connection_made(self, transport):
        self.transport = transport
        sock = self.transport.get_extra_info('socket')
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast()

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
#        print('Send %r to %s' % (message, addr))
#        self.transport.sendto(data, addr)

    def connection_lost(self, exc):
        pass

    def broadcast(self):
        self.transport.sendto(str(datetime.now()).encode(),
                              (self.broadcast_addr, self.port))
        self.loop.call_later(5, self.broadcast)


def start_discovery_server(host=DISCOVERY_HOST, port=DISCOVERY_PORT,
                           addr=DISCOVERY_ADDR, dsn=DSN, path=None):
    """ Start encsend discovery server

    :param host: discovery server host
    :type host: str
    :param port: discovery server port
    :type port: int
    :param addr: where to send broadcast messages
    :type addr: str
    :param dsn: Data Source Name, information about database driver,
        server, database, etc
    :type dsn: str
    :param path: path to signature key file, if path is `None`
        default path is used
    :type path: str or None
    """
    loop = asyncio.get_event_loop()
    coro = loop.create_datagram_endpoint(
        lambda: DiscoveryServer(loop, host, port, dsn, path, addr),
        local_addr=(host, port)
    )
    transport, protocol = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        transport.close()
        loop.close()
