# EncSend

EncSend is a tool for sending encrypted messages between hosts. 

EncSend was created just for fun. Don't use it in the production with any kinds of sensitive data. I am not a Cryptography Enthusiast or a Security Engineer, I can't grant reliability of this tool and safety of your data. Note, every crypto tool has to be audited by experts before using, and this one wasn't.

EncSend is free and opensource software, it is licensed under GNU GPL 3 (or newer) license. Check `LICENSE` for details.

# Usage
* Copy `encsend/conf_default.py` to `encsend/conf.py`, edit `conf.py`. Otherwise you should use `--dsn`, `--path`, `--host`, `--port` arguments in next steps.
* Run init
```
encsend-cmd.py init
```
* See help for additional details
`encsend-cmd.py --help`

## Receiving messages
* Add a host, this host will be able to send messages to you
```
encsend-cmd.py host-add -k somehost_hex_encoded_verify_key --host localhost --port 8888 
```
* Start a server
```
encsend-cmd.py server
```

## Sending messages
* Receiver has to add your host
* Send a message
```
encsend-cmd.py message-send -k receiver_hex_encoded_verify_key -m message
```
* or you can use internal host's id
```
encsend-cmd.py host-ls
encsend-cmd.py message-send --id receiver_internal_id -m message
```

# How it works
* Every host has singing key and verify key, private key and public key
* Messages are signed with author's signing key, after that messages are encrypted with SealedBox from pynacl/libsodium, that's why only receiver are able to decrypt a message and auth an author

## EncSend uses
* Python 3.6+ and asyncio
* PyNaCl and libsodium
* aioodbc and pyodbc

## Sending messages
* Get a text message, encode it to bytes, the result is `message`
* Get receiver's verify key, host and port from db
* Sign `message` with your signing key, the result is `signed`
* Place `signed` and your hex encoded verify key to json `{"host": "some_hex_encoded_data", "message": "some_signed_message"}`, the resuls is `json_data`
* Get curve25519 public key from receiver's verify key 
* Create `SealedBox` with public key, encrypt `json_data` and use `HexEncoder`
* Send the result to receiver

## Receiving messages
* Recieve some data
* _TODO: check magic byte_
* Get curve25519 private key from your signing key
* Create `SealedBox` with private key
* Decrypt data, use `HexEncoder`, the result is `json_data`
* Check does sender exist in your db
* Check signature of `json_data['message']`
* Decode `json_data['message']` and save the result

