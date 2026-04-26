#!/bin/sh
# Generates dnsmasq config from environment, then starts.
set -e

: "${SERVER_IP:?SERVER_IP is required}"

cat > /etc/dnsmasq.conf <<EOF
# NetworkMemories — Demon's Souls DNS
# Auto-generated from environment — do not edit manually.

no-resolv
no-hosts
keep-in-foreground
log-queries

# Demon's Souls online service domains → SERVER_IP
address=/demonsouls.com/${SERVER_IP}
address=/ds.fromsoftware.jp/${SERVER_IP}
address=/nsa.fromsoftware.jp/${SERVER_IP}

# PSN auth / DNAS (PS3)
address=/auth.np.ac.playstation.net/${SERVER_IP}
address=/nsx.sec.np.ac.playstation.net/${SERVER_IP}

# Fallback DNS for everything else
server=8.8.8.8
server=8.8.4.4
EOF

echo "[dns] Resolving Demon's Souls domains → ${SERVER_IP}"
exec dnsmasq
