# -*- coding: utf-8 -*-

import json

import pyodbc
from nacl.encoding import HexEncoder
from nacl.public import SealedBox
from nacl.signing import VerifyKey

from .sql import SELECT
from .utils import get_signing_key


class EncSendClient:
    def __init__(self, dsn, signature_path=None):
        self.connection = pyodbc.connect(dsn)
        self.cursor = self.connection.cursor()
        self.signature_path = signature_path

    def init_keys(self):
        self.signing_key = get_signing_key(self.signature_path)
        self.verify_key = self.signing_key.verify_key

    def send_message(self, message, host_key=None, host_id=None):
        if host_key is not None:
            host, port = self.get_host_by_key(host_key)
        elif host_id is not None:
            host_key, host, port = self.get_host_by_id(host_key)

        encrypted = self.encrypt_message(message, host_key)
        # TODO: send encrypted message
        raise NotImplementedError

    def ecnrypt_message(self, message, host_key):
        verify_key = VerifyKey(host_key.encode(), encoder=HexEncoder)
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
        self.cursor.execute(SELECT['hosts-key'], (host_key,))
        return self.cursor.fetchall()[0]

    def get_host_by_id(self, host_id):
        self.cursor.execute(SELECT['hosts-id'], (host_id,))
        return self.cursor.fetchall()[0]
