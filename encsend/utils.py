# -*- coding: utf-8 -*-

import os

from nacl.encoding import HexEncoder
from nacl.signing import SigningKey


def get_config_dir(make_dir=False):
    _evar = 'XDG_CONFIG_HOME'
    if _evar in os.environ and os.environ[_evar]:
        path = os.environ[_evar]
    else:
        path = os.path.join(os.path.expanduser('~'), '.config', 'encsend')

    if make_dir:
        os.makedirs(path, exist_ok=True)

    return path


def get_signing_key_path(make_dir=False):
    """ Get default path to signing key """

    conf_dir_path = get_config_dir(make_dir)
    return os.path.join(conf_dir_path, 'host_signature')


def get_signing_key(path=None):
    if path is None:
        path = get_signing_key_path()
    with open(path, 'rb') as f:
        signature_bytes = f.read()

    return SigningKey(signature_bytes)


def get_verify_key_hex(path=None):
    """ Return HEX encoded verify key

    :param path: path to signature key file, if path is `None`
        default path is used
    :type path: str or None
    :return: HEX encoded verify key
    :rtype: bytes
    """
    signing_key = get_signing_key(path)
    verify_key = signing_key.verify_key
    return verify_key.encode(encoder=HexEncoder)


def create_signing_key(path=None):
    if path is None:
        path = get_signing_key_path(make_dir=True)
    signing_key = SigningKey.generate()
    signing_key_bytes = signing_key.encode()
    with open(path, 'wb') as f:
        f.write(signing_key_bytes)
