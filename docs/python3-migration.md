# Python 2 → 3 Migration Notes

This document describes all changes made to migrate the original
`ymgve/desse` codebase from Python 2.6/2.7 to Python 3.11.

---

## Dependency Change

| Original | Fork |
|---|---|
| `pycrypto` (unmaintained, Python 2) | `pycryptodome` (maintained, Python 3) |

`pycryptodome` is a drop-in replacement — the import paths are identical:
```python
from Crypto.Cipher import AES  # works with both
```

Install: `pip install pycryptodome`

---

## print statement → print() function

```python
# Python 2
print "Connected:", addr

# Python 3
print("Connected:", addr)
```

---

## Exception syntax

```python
# Python 2
except Exception, e:

# Python 3
except Exception as e:
```

---

## bytes vs str

Python 3 enforces strict separation between `bytes` and `str`.

```python
# Python 2 — strings are bytes by default
data = "hello"
sock.send(data)

# Python 3 — must be explicit
data = b"hello"          # bytes literal
sock.send(data)

# Encoding strings to bytes
sock.send("hello".encode("utf-8"))

# Decoding bytes to string
text = received_bytes.decode("utf-8")
```

---

## Integer division

```python
# Python 2 — integer division by default
result = 5 / 2    # → 2

# Python 3 — float division by default
result = 5 // 2   # → 2  (use // for integer division)
```

---

## urllib changes

```python
# Python 2
import urllib2
response = urllib2.urlopen(url)

# Python 3
import urllib.request
response = urllib.request.urlopen(url)
```

---

## Dictionary methods

```python
# Python 2 — returns lists
dict.keys(), dict.values(), dict.items()

# Python 3 — returns views (iterate directly, or wrap in list())
list(dict.keys())
```

---

## Config: IP hardcoding → environment variables

**Original `info.ss`:**
```
server_ip = 1.2.3.4
```

**Original `remote.conf`:**
```
A demonsouls.com 1.2.3.4
```

**Fork:** All configuration is now via `.env` / environment variables.
The `emulator.py` reads:
```python
SERVER_IP = os.environ.get("SERVER_IP", "127.0.0.1")
PORT      = int(os.environ.get("DESSE_PORT", 18000))
```

The DNS container generates its config from env at startup — no manual
editing of `info.ss` or `remote.conf` required.

---

## Structural improvements

| Original | Fork |
|---|---|
| `python emulator.py` (bare) | Dockerized, runs as non-root user |
| IP in `info.ss` | `SERVER_IP` env var |
| DNS via external FakeDns | Integrated dnsmasq container |
| `db/` created manually | Auto-created by container |
| No admin interface | Flask admin panel on port 8080 |
| No backup | `scripts/backup.sh` |
