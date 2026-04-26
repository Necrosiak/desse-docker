#!/usr/bin/env python3
"""
NetworkMemories — Demon's Souls Server Emulator (desse-docker)
Forked from ymgve/desse — migrated to Python 3

Changes vs original:
  - Python 3 compatible (print, bytes/str, exceptions, urllib)
  - pycryptodome instead of pycrypto (same API, Python 3 maintained)
  - All config via environment variables (no hardcoded IPs)
  - Structured logging
  - Graceful shutdown handling
"""

import os
import sys
import socket
import struct
import threading
import hashlib
import logging
import signal
import time
import pickle
from pathlib import Path
from datetime import datetime

# --- Config from environment ---
SERVER_IP    = os.environ.get("SERVER_IP", "127.0.0.1")
BIND_ADDR    = os.environ.get("DESSE_BIND", "0.0.0.0")
PORT         = int(os.environ.get("DESSE_PORT", 18000))
DATA_DIR     = Path(os.environ.get("DATA_DIR", "./data"))
DB_DIR       = Path(os.environ.get("DB_DIR", "./db"))
LOG_LEVEL    = os.environ.get("LOG_LEVEL", "INFO").upper()
ACTIVE_REGIONS = [r.strip() for r in os.environ.get("ACTIVE_REGIONS", "EU,US,JP").split(",")]

# --- Logging ---
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("desse")

# --- Ensure required directories exist ---
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Crypto helpers
# Using pycryptodome (drop-in replacement for pycrypto, Python 3 compatible)
# Install: pip install pycryptodome
# ---------------------------------------------------------------------------
try:
    from Crypto.Cipher import AES, Blowfish
    from Crypto.Hash import MD5
except ImportError:
    log.critical("pycryptodome not found. Install with: pip install pycryptodome")
    sys.exit(1)


def read_db(name: str) -> list:
    """Load a list of entries from the persistent DB directory."""
    path = DB_DIR / f"{name}.pkl"
    if not path.exists():
        return []
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        log.warning(f"Could not read DB '{name}': {e}")
        return []


def write_db(name: str, data: list) -> None:
    """Persist a list of entries to the DB directory."""
    path = DB_DIR / f"{name}.pkl"
    with open(path, "wb") as f:
        pickle.dump(data, f)


# ---------------------------------------------------------------------------
# Shared in-memory state
# ---------------------------------------------------------------------------
lock = threading.Lock()

# Load persistent data
messages    = read_db("messages")
ghosts      = read_db("ghosts")
bloodstains = read_db("bloodstains")
sessions    = {}   # token → {username, region, timestamp}

# Seed from data/ directory on first run
def _seed_data():
    for name, store in [("messages", messages), ("bloodstains", bloodstains)]:
        src = DATA_DIR / f"{name}.pkl"
        if src.exists() and not store:
            try:
                with open(src, "rb") as f:
                    store.extend(pickle.load(f))
                log.info(f"Seeded {len(store)} {name} from {src}")
            except Exception as e:
                log.warning(f"Could not seed {name}: {e}")

_seed_data()


# ---------------------------------------------------------------------------
# Packet helpers
# ---------------------------------------------------------------------------
def pack_string(s: str) -> bytes:
    """Encode a string as length-prefixed UTF-16-LE."""
    encoded = s.encode("utf-16-le")
    return struct.pack(">H", len(encoded)) + encoded


def unpack_string(data: bytes, offset: int):
    """Decode a length-prefixed UTF-16-LE string. Returns (string, new_offset)."""
    length = struct.unpack_from(">H", data, offset)[0]
    offset += 2
    s = data[offset:offset + length].decode("utf-16-le", errors="replace")
    return s, offset + length


def make_packet(cmd: int, payload: bytes = b"") -> bytes:
    """Build a packet: [cmd:2][length:4][payload]"""
    return struct.pack(">HI", cmd, len(payload)) + payload


def read_packet(sock: socket.socket):
    """Read one packet from socket. Returns (cmd, payload) or raises."""
    header = _recv_exact(sock, 6)
    cmd, length = struct.unpack(">HI", header)
    payload = _recv_exact(sock, length) if length else b""
    return cmd, payload


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Client disconnected")
        buf += chunk
    return buf


# ---------------------------------------------------------------------------
# Client handler
# ---------------------------------------------------------------------------
class ClientHandler(threading.Thread):
    def __init__(self, conn: socket.socket, addr):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.region = None
        self.username = None
        self.token = None

    def run(self):
        log.info(f"Connection from {self.addr}")
        try:
            self._handle()
        except ConnectionError:
            log.debug(f"Client {self.addr} disconnected")
        except Exception as e:
            log.exception(f"Error handling client {self.addr}: {e}")
        finally:
            if self.token:
                with lock:
                    sessions.pop(self.token, None)
            self.conn.close()

    def _handle(self):
        while True:
            cmd, payload = read_packet(self.conn)
            log.debug(f"[{self.addr}] CMD 0x{cmd:04X} ({len(payload)}B)")

            handler = {
                0x0001: self._cmd_hello,
                0x0100: self._cmd_auth,
                0x0200: self._cmd_get_messages,
                0x0201: self._cmd_add_message,
                0x0300: self._cmd_get_ghosts,
                0x0301: self._cmd_add_ghost,
                0x0400: self._cmd_get_bloodstains,
                0x0401: self._cmd_add_bloodstain,
                0x0500: self._cmd_matchmaking_search,
                0x0501: self._cmd_matchmaking_register,
            }.get(cmd)

            if handler:
                handler(payload)
            else:
                log.warning(f"[{self.addr}] Unknown command 0x{cmd:04X}")
                self.conn.sendall(make_packet(0xFFFF, b"\x00"))

    # --- Command handlers ---

    def _cmd_hello(self, _):
        log.debug(f"[{self.addr}] Hello")
        self.conn.sendall(make_packet(0x0001, b"\x01"))

    def _cmd_auth(self, payload):
        try:
            username, offset = unpack_string(payload, 0)
            region_byte = payload[offset] if offset < len(payload) else 0
            region_map = {0: "JP", 1: "US", 2: "EU"}
            self.region = region_map.get(region_byte, "EU")

            if self.region not in ACTIVE_REGIONS:
                log.info(f"Region {self.region} not active — rejecting {username}")
                self.conn.sendall(make_packet(0x0100, b"\x00"))
                return

            self.username = username
            self.token = hashlib.sha256(
                f"{username}{self.addr}{time.time()}".encode()
            ).hexdigest()[:16]

            with lock:
                sessions[self.token] = {
                    "username": username,
                    "region": self.region,
                    "timestamp": datetime.utcnow().isoformat(),
                    "addr": str(self.addr),
                }

            log.info(f"Auth OK: {username} [{self.region}] from {self.addr}")
            self.conn.sendall(make_packet(0x0100, b"\x01" + self.token.encode()))
        except Exception as e:
            log.exception(f"Auth error: {e}")
            self.conn.sendall(make_packet(0x0100, b"\x00"))

    def _cmd_get_messages(self, _):
        with lock:
            region_msgs = [m for m in messages if m.get("region") == self.region]
        data = struct.pack(">I", len(region_msgs))
        for m in region_msgs[:50]:  # cap at 50
            data += pack_string(m.get("text", ""))
            data += struct.pack(">I", m.get("rating", 0))
        self.conn.sendall(make_packet(0x0200, data))

    def _cmd_add_message(self, payload):
        text, _ = unpack_string(payload, 0)
        with lock:
            messages.insert(0, {
                "text": text,
                "region": self.region,
                "author": self.username,
                "timestamp": datetime.utcnow().isoformat(),
                "rating": 0,
            })
            if len(messages) > 500:
                messages.pop()
            write_db("messages", messages)
        self.conn.sendall(make_packet(0x0201, b"\x01"))

    def _cmd_get_ghosts(self, _):
        with lock:
            region_ghosts = [g for g in ghosts if g.get("region") == self.region]
        data = struct.pack(">I", len(region_ghosts))
        for g in region_ghosts[:20]:
            data += g.get("data", b"")
        self.conn.sendall(make_packet(0x0300, data))

    def _cmd_add_ghost(self, payload):
        with lock:
            ghosts.insert(0, {
                "data": payload,
                "region": self.region,
                "author": self.username,
                "timestamp": datetime.utcnow().isoformat(),
            })
            if len(ghosts) > 200:
                ghosts.pop()
            write_db("ghosts", ghosts)
        self.conn.sendall(make_packet(0x0301, b"\x01"))

    def _cmd_get_bloodstains(self, _):
        with lock:
            region_bs = [b for b in bloodstains if b.get("region") == self.region]
        data = struct.pack(">I", len(region_bs))
        for b in region_bs[:30]:
            data += b.get("data", b"")
        self.conn.sendall(make_packet(0x0400, data))

    def _cmd_add_bloodstain(self, payload):
        with lock:
            bloodstains.insert(0, {
                "data": payload,
                "region": self.region,
                "author": self.username,
                "timestamp": datetime.utcnow().isoformat(),
            })
            if len(bloodstains) > 200:
                bloodstains.pop()
            write_db("bloodstains", bloodstains)
        self.conn.sendall(make_packet(0x0401, b"\x01"))

    def _cmd_matchmaking_search(self, payload):
        """Return list of players in the same region looking for co-op."""
        with lock:
            candidates = [
                s for s in sessions.values()
                if s.get("region") == self.region
                and s.get("username") != self.username
            ]
        data = struct.pack(">I", len(candidates))
        for c in candidates:
            data += pack_string(c["username"])
        self.conn.sendall(make_packet(0x0500, data))

    def _cmd_matchmaking_register(self, _):
        """Acknowledge registration in matchmaking pool (handled via sessions)."""
        self.conn.sendall(make_packet(0x0501, b"\x01"))


# ---------------------------------------------------------------------------
# Main server
# ---------------------------------------------------------------------------
def main():
    log.info(f"NetworkMemories — Demon's Souls Server")
    log.info(f"Server IP  : {SERVER_IP}")
    log.info(f"Bind       : {BIND_ADDR}:{PORT}")
    log.info(f"Regions    : {', '.join(ACTIVE_REGIONS)}")
    log.info(f"Data dir   : {DATA_DIR}")
    log.info(f"DB dir     : {DB_DIR}")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((BIND_ADDR, PORT))
    server.listen(64)
    log.info(f"Listening on {BIND_ADDR}:{PORT} ...")

    def _shutdown(sig, frame):
        log.info("Shutting down gracefully...")
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    while True:
        try:
            conn, addr = server.accept()
            ClientHandler(conn, addr).start()
        except OSError:
            break


if __name__ == "__main__":
    main()
