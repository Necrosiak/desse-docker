# Demon's Souls Server — Docker

> **NetworkMemories** fork of [ymgve/desse](https://github.com/ymgve/desse)  
> Fully dockerized Demon's Souls server emulator (PS3 / RPCS3)

---

## What's new in this fork

- ✅ **Python 3.11** — migrated from Python 2.6/2.7 (EOL since 2020)
- ✅ **pycryptodome** instead of unmaintained pycrypto
- ✅ Full Docker setup — zero manual installs
- ✅ All config via `.env` — no hardcoded IPs (`info.ss` / `remote.conf` replaced)
- ✅ Integrated DNS container (dnsmasq) — no external FakeDns needed
- ✅ Admin panel at `:8080/admin` — view/delete messages, ghosts, bloodstains
- ✅ Graceful shutdown + structured logging
- ✅ Backup & restore scripts
- ✅ Regional matchmaking: EU / US / JP

---

## Requirements

- Docker ≥ 24 + Docker Compose v2
- A Linux server (or WSL2) with a public IP
- PS3 with Demon's Souls disc **or** RPCS3 emulator

---

## Quick Start

```bash
# 1. Clone your fork
git clone https://github.com/NetworkMemories/desse-docker.git
cd desse-docker

# 2. Initialize
make init
# → Creates .env from .env.example

# 3. Edit .env — required:
#    SERVER_IP, ADMIN_PASSWORD, ADMIN_SECRET_KEY
nano .env

# 4. Build
make build

# 5. (Linux) Free port 53 before starting DNS
make disable-systemd-resolved

# 6. Start everything
make run-daemon

# 7. Configure PS3/RPCS3 DNS → SERVER_IP
```

---

## Key `.env` Variables

| Variable | Description | Default |
|---|---|---|
| `SERVER_IP` | Your public server IP | **required** |
| `ADMIN_PASSWORD` | Admin panel password | **required** |
| `ADMIN_SECRET_KEY` | Flask session key (random string) | **required** |
| `DESSE_PORT` | Server port | `18000` |
| `ACTIVE_REGIONS` | Active regions: EU,US,JP | `EU,US,JP` |
| `LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | `INFO` |

---

## Services & Ports

| Service | Port | Description |
|---|---|---|
| `desse-server` | 18000 | Demon's Souls game server |
| `desse-dns` | 53/udp+tcp | DNS (resolves DS domains → SERVER_IP) |
| `desse-admin` | 8080 | Admin panel (Flask) |

---

## DNS Domains Captured

The DNS container redirects these to `SERVER_IP`:
- `*.demonsouls.com`
- `ds.fromsoftware.jp`
- `nsa.fromsoftware.jp`
- `auth.np.ac.playstation.net`
- `nsx.sec.np.ac.playstation.net`

---

## PS3 / RPCS3 Network Setup

**PS3:**
1. Network Settings → Custom
2. Set **Primary DNS** → `YOUR_SERVER_IP`
3. Save & connect

**RPCS3:**
1. Configuration → Network
2. Set **DNS** → `YOUR_SERVER_IP`
3. Network Status: Connected

---

## Admin Panel

`http://YOUR_SERVER_IP:8080/admin`

Login with `ADMIN_USER` / `ADMIN_PASSWORD` from `.env`.

**Pages:**
- **Dashboard** — server status, counts per region
- **Messages** — list + delete
- **Ghosts** — list + delete
- **Bloodstains** — list + delete
- **`/api/status`** — JSON status (no auth, for monitoring)

---

## Matchmaking & Regions

Players only see summon signs from their own region (EU / US / JP).
Pre-seeded messages and bloodstains from the original repo are loaded from
`data/` on first start.

---

## `make` Commands

```
make help                     List all commands
make init                     First-time setup
make build                    Build all containers
make run-daemon               Start everything (background)
make stop                     Stop services
make logs                     Follow all logs
make logs-server              Server logs only
make backup                   Backup db/ directory
make restore                  Restore latest backup
make disable-systemd-resolved Free port 53 (Linux)
make enable-systemd-resolved  Re-enable after shutdown
```

---

## Troubleshooting

See [`docs/troubleshooting.md`](docs/troubleshooting.md)

---

## Python 3 Migration

See [`docs/python3-migration.md`](docs/python3-migration.md) for a full
breakdown of all changes vs the original Python 2 codebase.

---

## Credits

- Original server: [ymgve](https://github.com/ymgve/desse)
- This fork: [NetworkMemories](https://network-memories.com)
