# Troubleshooting — Demon's Souls

## PS3/RPCS3 can't reach the server

1. Check DNS is resolving:
   ```bash
   nslookup demonsouls.com YOUR_SERVER_IP
   # Expected: address = YOUR_SERVER_IP
   ```
2. Check port 53 is free: `sudo ss -tulnp | grep :53`
3. If `systemd-resolved` is on port 53: `make disable-systemd-resolved`
4. Check DNS container: `make logs-dns`

---

## Server starts but no matchmaking

- Matchmaking is **regional** — EU players only see EU summon signs, etc.
- If testing alone, all your sessions go into the same region anyway.
- Check `ACTIVE_REGIONS` in `.env` includes your region (`EU,US,JP`).

---

## `pycryptodome` import error

The Docker image handles this automatically. If running outside Docker:
```bash
pip install pycryptodome
# NOT pycrypto — that's the old Python 2 version
```

---

## Admin panel not loading (port 8080)

1. Check the container is running: `docker ps | grep desse-admin`
2. Check logs: `make logs-admin`
3. Ensure `ADMIN_PASSWORD` and `ADMIN_SECRET_KEY` are set in `.env`
4. If behind a firewall, open port 8080

---

## Ghosts / messages not persisting after restart

The `db/` directory must be writable and mounted as a volume. Check:
```bash
ls -la db/
docker inspect desse-server | grep -A5 Mounts
```

---

## Clean reset (wipe all data)

```bash
make backup      # save first
make down
rm -rf db/
make run-daemon  # starts fresh
```
