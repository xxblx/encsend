#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

import pyodbc

from encsend.client import send_message
from encsend.server import start_encsend_server
from encsend.sql import CREATE, DELETE, INSERT, SELECT
from encsend.utils import create_signing_key, get_verify_key_hex
try:
    from encsend.conf import DSN
except ImportError:
    from encsend.conf_default import DSN


def create_tables(dsn):
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        cur.execute(CREATE['messages'])
        cur.execute(CREATE['hosts'])


def insert_host(key, dsn, host, port):
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        cur.execute(INSERT['hosts'], (key, host, port))


def select_hosts(dsn):
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        cur.execute(SELECT['hosts-ls'])
        print('\t'.join(['id', 'key', 'host', 'port']))
        for row in cur.fetchall():
            print('\t'.join(map(str, row)))


def select_messages(dsn):
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        cur.execute(SELECT['messages'])
        print('\t'.join(['id', 'message', 'host_id', 'datetime']))
        for row in cur.fetchall():
            print('\t'.join(map(str, row)))


def delete_message(dsn, message_id):
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        cur.execute(DELETE['messages-id'], (message_id,))


def delete_all_messages(dsn):
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        cur.execute(DELETE['messages-all'])


def main():
    parser = argparse.ArgumentParser(prog='encsend')

    subparsers = parser.add_subparsers()

    init_parser = subparsers.add_parser('init')
    init_parser.set_defaults(used='init')
    init_parser.add_argument('--dsn', type=str, default=DSN)
    init_parser.add_argument('-p', '--path', type=str, default=None,
                             help='path to signing key file')

    server_parser = subparsers.add_parser('server')
    server_parser.set_defaults(used='server')
    server_parser.add_argument('--dsn', type=str, default=DSN)
    server_parser.add_argument('-p', '--path', type=str, default=None,
                               help='path to signing key file')
    server_parser.add_argument('--host', type=str, default='127.0.0.1')
    server_parser.add_argument('--port', type=int, default=8888)

    host_add_parser = subparsers.add_parser('host-add')
    host_add_parser.set_defaults(used='host-add')
    host_add_parser.add_argument('--dsn', type=str, default=DSN)
    host_add_parser.add_argument('-k', '--key', type=str, required=True,
                                 help='host\'s hex encoded verify key')
    host_add_parser.add_argument('--host', type=str, required=True)
    host_add_parser.add_argument('--port', type=str, required=True)

    host_ls_parser = subparsers.add_parser('host-ls')
    host_ls_parser.set_defaults(used='host-ls')
    host_ls_parser.add_argument('--dsn', type=str, default=DSN)

    message_ls_parser = subparsers.add_parser('message-ls')
    message_ls_parser.set_defaults(used='message-ls')
    message_ls_parser.add_argument('--dsn', type=str, default=DSN)

    message_rm_parser = subparsers.add_parser('message-rm')
    message_rm_parser.set_defaults(used='message-rm')
    message_rm_parser.add_argument('--dsn', type=str, default=DSN)
    message_rm_parser.add_argument('--id', type=int, default=None)
    message_rm_parser.add_argument('-a', '--all', action='store_true',
                                   default=False)

    message_send_parser = subparsers.add_parser('message-send')
    message_send_parser.set_defaults(used='message-send')
    message_send_parser.add_argument('--dsn', type=str, default=DSN)
    message_send_parser.add_argument('-p', '--path', type=str, default=None,
                                     help='path to signing key file')
    message_send_parser.add_argument('-k', '--key', type=str, default=None,
                                     help='host\'s hex encoded verify key')
    message_send_parser.add_argument('--id', type=int, default=None,
                                     help='host\'s id')
    message_send_parser.add_argument('-m', '--message', type=str,
                                     required=True)

    verify_key_parser = subparsers.add_parser(
        'verify-key',
        help='print this host\'s verify key'
    )
    verify_key_parser.set_defaults(used='verify-key')
    verify_key_parser.add_argument('-p', '--path', type=str, default=None,
                                   help='path to signing key file')

    args = parser.parse_args()
    if 'used' not in args:
        return

    if args.used == 'init':
        create_tables(args.dsn)
        create_signing_key(args.path)
    elif args.used == 'server':
        start_encsend_server(args.host, args.port, args.dsn)
    elif args.used == 'host-add':
        insert_host(args.key, args.dsn, args.host, args.port)
    elif args.used == 'host-ls':
        select_hosts(args.dsn)
    elif args.used == 'message-ls':
        select_messages(args.dsn)
    elif args.used == 'message-rm':
        if args.all:
            delete_all_messages(args.dsn)
        else:
            delete_message(args.dsn, args.id)
    elif args.used == 'message-send':
        send_message(args.message, args.dsn, args.path, args.key, args.id)
    elif args.used == 'verify-key':
        key = get_verify_key_hex(args.path)
        print(key.decode())


if __name__ == '__main__':
    main()
