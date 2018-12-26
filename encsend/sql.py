# -*- coding: utf-8 -*-

CREATE = {
    'messages': """
CREATE TABLE IF NOT EXISTS messages_t (
    message_id INTEGER PRIMARY KEY,
    message TEXT,
    host_id INTEGER,
    datetime INTEGER
)
""",

    'hosts': """
CREATE TABLE IF NOT EXISTS hosts_t (
    host_id INTEGER PRIMARY KEY,
    host_key TEXT UNIQUE,
    host TEXT,
    port INTEGER
)
"""
}

INSERT = {
    'messages': """
INSERT INTO messages_t (message, host_id, datetime) VALUES(?, ?, ?)
""",

    'hosts': """
INSERT INTO hosts_t (host_key, host, port) VALUES(?, ?, ?)
"""
}

SELECT = {
    'hosts': """
SELECT host_id FROM hosts_t WHERE host_key = ?
""",

    'hosts-ls': """
SELECT host_id, host_key, host, port FROM hosts_t
""",

    'hosts-id': """
SELECT host_key, host, port FROM hosts_t WHERE host_id = ?
""",

    'hosts-key': """
SELECT host, port FROM hosts_t WHERE host_key = ?
""",

    'messages': """
SELECT message_id, message, host_id, datetime FROM messages_t
"""
}

DELETE = {
    'messages-id': """
DELETE FROM messages_t WHERE message_id = ?
""",
    'messages-all': """
DELETE FROM messages_t
"""
}
