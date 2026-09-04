"""A Minecraft client that joins the network and types commands, for testing the login flow.

It exists because the thing most worth testing here - that a player who has not logged in is
held on the limbo, is refused every other command, and reaches the lobby once they register -
cannot be checked from a console. It needs something that speaks the protocol, and running a
real client against a headless server is not a thing a deploy script can do.

Not a general client. It knows exactly the packets a Velocity-plus-NanoLimbo connection sends,
which is enough to prove the flow and nothing more: no encryption (so it cannot join as a
premium account, which is itself a useful negative test), no world, no movement.

    scripts/mcjoin.py 127.0.0.1 25565 Tester 776 0x07 plain "zarejestruj haslo123 haslo123"

    <protocol>   776 for Minecraft 26.2
    <command id> serverbound Chat Command, which moves between versions: 0x07 from 26.1,
                 0x06 on 1.21.6, 0x05 on 1.21.2, 0x04 on 1.20.5. When it is wrong the proxy
                 logs "A packet did not decode successfully" and names the class it tried,
                 which is how to find the right one for a new version.
    <shape>      "plain" for the unsigned command packet (just the text) - the others exist
                 for older versions that signed their commands.

Run it with python3 -u: without that, output is block-buffered and a timeout kills the process
before anything is flushed, which looks exactly like a server that said nothing.
"""

import socket
import struct
import zlib
import sys
import time
import uuid


def varint(value):
    out = b""
    while True:
        piece = value & 0x7F
        value >>= 7
        out += bytes([piece | (0x80 if value else 0)])
        if not value:
            return out


def string(text):
    raw = text.encode("utf-8")
    return varint(len(raw)) + raw


# -1 until the server sends Set Compression. After that every frame carries an extra
# "uncompressed length" varint, and anything at or above the threshold is deflated. A client
# that ignores this reads the next packet as garbage and simply goes quiet, which looks exactly
# like a server that stopped talking.
compression = -1


def packet(packet_id, body):
    payload = varint(packet_id) + body

    if compression < 0:
        return varint(len(payload)) + payload

    if len(payload) < compression:
        framed = varint(0) + payload
    else:
        framed = varint(len(payload)) + zlib.compress(payload)

    return varint(len(framed)) + framed


def read_varint(sock):
    result = 0
    for index in range(5):
        byte = sock.recv(1)
        if not byte:
            raise EOFError
        result |= (byte[0] & 0x7F) << (7 * index)
        if not byte[0] & 0x80:
            return result
    raise ValueError("varint too long")


def read_varint_buffer(buffer, index=0):
    result = 0
    shift = 0
    while True:
        byte = buffer[index]
        index += 1
        result |= (byte & 0x7F) << (7 * shift)
        shift += 1
        if not byte & 0x80:
            return result, index


def read_string(buffer, index):
    length, index = read_varint_buffer(buffer, index)
    return buffer[index:index + length].decode("utf-8", "replace"), index + length


host, port, name, protocol = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
# The serverbound Chat Command id moves between protocol versions, so it is an argument here
# rather than a constant that would be wrong on the next one.
CHAT_COMMAND_ID = int(sys.argv[5], 0)
# The payload shape moved too: "plain" is the unsigned packet (just the text), "signed" is the
# session one that carries a timestamp, a salt and an empty acknowledgement block.
SHAPE = sys.argv[6]
commands = sys.argv[7:]

sock = socket.create_connection((host, port), timeout=10)
sock.sendall(packet(0x00, varint(protocol) + string(host) + struct.pack(">H", port) + varint(2)))
sock.sendall(packet(0x00, string(name) + uuid.uuid5(uuid.NAMESPACE_OID, name).bytes))
print("state=LOGIN")

state = "LOGIN"
sent = 0
next_command_at = None
deadline = time.time() + 40
sock.settimeout(1.0)

while time.time() < deadline:
    if next_command_at is not None and time.time() >= next_command_at:
        if sent < len(commands):
            command = commands[sent]
            sent += 1
            # Serverbound chat command: the command text, then an empty signature array and
            # a message-count/acknowledged block. NanoLimbo does not verify any of it, and the
            # proxy intercepts the command before the backend sees it.
            if SHAPE == "plain":
                body = string(command)
            elif SHAPE == "signed":
                body = (string(command)
                        + struct.pack(">q", int(time.time() * 1000))
                        + struct.pack(">q", 0)
                        + varint(0)
                        + varint(0) + bytes(3))
            else:
                body = (string(command)
                        + struct.pack(">q", int(time.time() * 1000))
                        + struct.pack(">q", 0)
                        + varint(0)
                        + varint(0) + bytes(3) + bytes(1))
            sock.sendall(packet(CHAT_COMMAND_ID, body))
            print("-> /%s" % command)
            next_command_at = time.time() + 2
        else:
            next_command_at = None

    try:
        length = read_varint(sock)
        body = b""
        while len(body) < length:
            chunk = sock.recv(length - len(body))
            if not chunk:
                raise EOFError
            body += chunk
    except socket.timeout:
        continue
    except Exception as error:
        print("closed:", type(error).__name__)
        break

    if compression >= 0:
        uncompressed, index = read_varint_buffer(body)
        body = body[index:] if uncompressed == 0 else zlib.decompress(body[index:])

    packet_id, offset = read_varint_buffer(body)

    if state == "LOGIN" and packet_id == 0x03:
        compression, _ = read_varint_buffer(body, offset)
        print("-> compression on, threshold=%d" % compression)
        continue

    if state == "LOGIN" and packet_id == 0x02:
        sock.sendall(packet(0x03, b""))
        state = "CONFIG"
        print("-> Login Acknowledged, state=CONFIG")
        continue

    if state == "CONFIG":
        if packet_id == 0x0E:
            # Known Packs. Echoing the server's own list back is the shortest valid answer.
            sock.sendall(packet(0x07, body[offset:]))
            print("-> Known Packs response")
        elif len(body) == 1:
            # A configuration packet whose whole payload is its id is Finish Configuration.
            # Measured on the decompressed body, not the frame: once compression is on the
            # frame carries an extra length varint and is never one byte.
            sock.sendall(packet(0x03, b""))
            state = "PLAY"
            print("-> Acknowledge Finish Configuration, state=PLAY")
            next_command_at = time.time() + 1
        continue

    # In PLAY, decode as UTF-8 before looking for anything - the interesting messages are
    # Polish, and a byte-wise filter turns every accented letter into noise that then fails to
    # match the very words being looked for.
    text = body[offset:].decode("utf-8", "replace")
    readable = "".join(character if character.isprintable() else "." for character in text)

    if any(word in readable for word in (
            "LOGOWANIE", "REJESTRACJA", "Błąd", "hasło", "LANDMC", "Najpierw", "Witaj", "Konto")):
        print("PLAY id=0x%02X %s" % (packet_id, readable[:300]))

sock.close()
