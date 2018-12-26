# -*- coding: utf-8 -*-

import json
import socket

import pyodbc
from nacl.encoding import HexEncoder
from nacl.public import SealedBox
from nacl.signing import VerifyKey

from .sql import SELECT
from .utils import get_signing_key
try:
    from . import conf
except ImportError:
    from . import conf_default as conf
finally:
    DSN = conf.DSN


class EncSendClient:
    """ EncSend client side implementation """
    def __init__(self, dsn, signature_path=None):
        """
        :param dsn: Data Source Name, information about database driver,
            server, database, etc
        :type dsn: str
        :param signature_path: custom path to signature key file
        :type signature_path: str or None
        """
        self.db_connection = pyodbc.connect(dsn)
        self.db_cursor = self.db_connection.cursor()
        self.signature_path = signature_path
        self.init_keys()

    def init_keys(self):
        self.signing_key = get_signing_key(self.signature_path)
        self.verify_key = self.signing_key.verify_key

    def send_message(self, message, host_key=None, host_id=None):
        """ Send encrypted message to another host

        If both args `host_key` and `host_id` are entered, `host_key`
        is used and `host_id` is ignored

        :param message: unencrypted message
        :type message: str or bytes
        :param host_key: hex encoded host's verify key, used for selecting
            host and port from db, for extracting public key
            for encrypting
        :type host_key: str or None
        :param host_id: internal host's id, used for selecting `host_key`,
            host and port from db
        :type host_id: int or None
        """
        if not isinstance(message, bytes):
            message = message.encode()

        if host_key is not None:
            host, port = self.get_host_by_key(host_key)
        elif host_id is not None:
            host_key, host, port = self.get_host_by_id(host_key)

        encrypted = self.encrypt_message(message, host_key.encode())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(encrypted)

    def encrypt_message(self, message, host_key):
        """ Encrypt, sign and encode a message with host's key.

        Method creates a dictionary with two keys: message - signed
        message, host - current host's hex encoded verify key, serializes
        it to json, encrypts and encodes the result

        :param message: message for the host
        :type message: bytes
        :param host_key: hex encoded the host's verify key
        :type host_key: bytes
        :return: signed, encrypted and hex encoded message
        :rtype: bytes
        """
        verify_key = VerifyKey(host_key, encoder=HexEncoder)
        public_key = verify_key.to_curve25519_public_key()
        sealed_box = SealedBox(public_key)

        signed = self.signing_key.sign(message, encoder=HexEncoder)
        dct = {
            'host': self.verify_key.encode(encoder=HexEncoder).decode(),
            'message': signed.decode()
        }
        json_data = json.dumps(dct)
        encrypted = sealed_box.encrypt(json_data.encode(), encoder=HexEncoder)
        return encrypted

    def get_host_by_key(self, host_key):
        """ Get host details by it's verify key

        :param host_key: hex encoded the host's verify key
        :type host_key: str
        :return: tuple with host and port
        :rtype: (str, int)
        """
        self.db_cursor.execute(SELECT['hosts-key'], (host_key,))
        return self.db_cursor.fetchall()[0]

    def get_host_by_id(self, host_id):
        """ Get host details by host's interal id

        :param host_id: host's internal id
        :type host_id: int
        :return: tuple with host's verify key, host and port
        :rtype: (str, str, int)
        """
        self.db_cursor.execute(SELECT['hosts-id'], (host_id,))
        return self.db_cursor.fetchall()[0]

    def close(self):
        self.db_connection.close()


def send_message(message, dsn=DSN, path=None, host_key=None, host_id=None):
    """ Send encrypted message to another host

    :param message: unencrypted message
    :type message: str or bytes
    :param dsn: Data Source Name, information about database driver,
        server, database, etc
    :type dsn: str
    :param path: path to signature key file, if path is `None`
        default path is used
    :type path: str or None
    :param host_key: hex encoded host's verify key, used for selecting
        host and port from db, for extracting public key
        for encrypting
    :type host_key: str or None
    :param host_id: internal host's id, used for selecting `host_key`,
        host and port from db
    :type host_id: int or None
    """
    client = EncSendClient(dsn, path)
    client.send_message(message, host_key, host_id)
    client.close()
