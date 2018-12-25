# -*- coding: utf-8 -*-

import os

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


def create_signing_key(path=None):
    if path is None:
        path = get_signing_key_path(make_dir=True)
    signing_key = SigningKey.generate()
    signing_key_bytes = signing_key.encode()
    with open(path, 'wb') as f:
        f.write(signing_key_bytes)
