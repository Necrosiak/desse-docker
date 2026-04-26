#!/usr/bin/env python3
"""
NetworkMemories — Demon's Souls Admin Panel (Flask)
Access: http://YOUR_SERVER_IP:8080/admin
Auth via env: ADMIN_USER / ADMIN_PASSWORD
"""

import os
import pickle
import hashlib
import socket
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template_string, request,
                   redirect, url_for, session, jsonify)

app = Flask(__name__)
app.secret_key = os.environ.get("ADMIN_SECRET_KEY", "change-me-in-env")

DB_DIR        = Path(os.environ.get("DB_DIR", "./db"))
SERVER_IP     = os.environ.get("SERVER_IP", "127.0.0.1")
DESSE_PORT    = int(os.environ.get("DESSE_PORT", 18000))
ADMIN_USER    = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS    = os.environ.get("ADMIN_PASSWORD", "")
ADMIN_HOST    = os.environ.get("ADMIN_HOST", "0.0.0.0")
ADMIN_PORT    = int(os.environ.get("ADMIN_PORT", 8080))


def read_db(name):
    path = DB_DIR / f"{name}.pkl"
    if not path.exists():
        return []
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return []


def write_db(name, data):
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with open(DB_DIR / f"{name}.pkl", "wb") as f:
        pickle.dump(data, f)


def check_server_online():
    try:
        s = socket.create_connection((SERVER_IP, DESSE_PORT), timeout=1)
        s.close()
        return True
    except Exception:
        return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("auth"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# --- CSS shared ---
STYLE = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0a0a0a; color: #ddd; font-family: monospace; }
header { background: #111; border-bottom: 1px solid #222; padding: 1rem 2rem;
         display: flex; justify-content: space-between; align-items: center; }
header h1 { color: #a00; font-size: .9rem; letter-spacing: 2px; text-transform: uppercase; }
nav a { color: #666; text-decoration: none; margin-right: 1.5rem; font-size: .8rem; }
nav a:hover { color: #ddd; }
main { padding: 2rem; max-width: 1100px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
.card { background: #111; border: 1px solid #222; padding: 1.2rem; }
.card .label { font-size: .7rem; color: #555; text-transform: uppercase; letter-spacing: 1px; }
.card .value { font-size: 2rem; margin-top: .3rem; }
.value.ok { color: #3a3; } .value.warn { color: #c00; }
section { margin-bottom: 2rem; }
section h2 { font-size: .75rem; color: #555; text-transform: uppercase; letter-spacing: 1px;
             border-bottom: 1px solid #1a1a1a; padding-bottom: .5rem; margin-bottom: 1rem; }
table { width: 100%; border-collapse: collapse; font-size: .8rem; }
th { text-align: left; color: #555; font-weight: normal; padding: .4rem .6rem;
     border-bottom: 1px solid #1a1a1a; font-size: .7rem; text-transform: uppercase; }
td { padding: .5rem .6rem; border-bottom: 1px solid #111; }
tr:hover td { background: #111; }
.btn { display: inline-block; padding: .2rem .6rem; font-family: monospace; font-size: .72rem;
       cursor: pointer; border: 1px solid #333; background: none; color: #999; }
.btn:hover { border-color: #a00; color: #a00; }
.btn-danger { border-color: #500; color: #c44; }
.alert { padding: .6rem 1rem; border-left: 3px solid #a00; background: #1a0000;
         margin-bottom: 1rem; font-size: .8rem; }
.badge { display: inline-block; padding: .1rem .4rem; font-size: .68rem; border: 1px solid #333; }
.eu { border-color: #44f; color: #44f; }
.us { border-color: #4a4; color: #4a4; }
.jp { border-color: #fa0; color: #fa0; }
input[type=text], input[type=password] { width: 100%; padding: .6rem; background: #0d0d0d;
  border: 1px solid #222; color: #ddd; font-family: monospace; margin-bottom: 1rem; }
input:focus { outline: none; border-color: #a00; }
.box { background: #111; border: 1px solid #222; padding: 2rem; width: 340px;
       position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); }
</style>
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        u = request.form.get("user", "")
        p = request.form.get("pass", "")
        if u == ADMIN_USER and hashlib.sha256(p.encode()).hexdigest() == hashlib.sha256(ADMIN_PASS.encode()).hexdigest():
            session["auth"] = True
            return redirect(url_for("dashboard"))
        error = "Invalid credentials."
    return render_template_string(f"""<!DOCTYPE html><html><head><title>Admin</title>{STYLE}</head><body>
<div class="box">
  <h1 style="color:#a00;margin-bottom:1.5rem;font-size:.9rem;letter-spacing:2px">// Admin Panel</h1>
  {{% if error %}}<div class="alert">{{{{ error }}}}</div>{{% endif %}}
  <form method="POST">
    <label style="font-size:.75rem;color:#555">Username</label>
    <input type="text" name="user" autofocus>
    <label style="font-size:.75rem;color:#555">Password</label>
    <input type="password" name="pass">
    <button type="submit" class="btn" style="width:100%;padding:.7rem">Login</button>
  </form>
  <div style="text-align:center;color:#333;font-size:.7rem;margin-top:1.5rem">NetworkMemories · Demon's Souls</div>
</div>
</body></html>""", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@app.route("/admin")
@login_required
def dashboard():
    messages    = read_db("messages")
    ghosts      = read_db("ghosts")
    bloodstains = read_db("bloodstains")
    online      = check_server_online()

    # Count by region
    regions = {}
    for item in messages:
        r = item.get("region", "?")
        regions[r] = regions.get(r, 0) + 1

    return render_template_string(f"""<!DOCTYPE html><html><head><title>Admin — DeSSE</title>{STYLE}</head><body>
<header>
  <h1>// NetworkMemories · Demon's Souls Admin</h1>
  <nav>
    <a href="/admin">Dashboard</a>
    <a href="/admin/messages">Messages</a>
    <a href="/admin/ghosts">Ghosts</a>
    <a href="/admin/bloodstains">Bloodstains</a>
    <a href="/logout">Logout</a>
  </nav>
</header>
<main>
<div class="grid">
  <div class="card"><div class="label">Server</div>
    <div class="value {{'ok' if online else 'warn'}}">{{'Online' if online else 'Offline'}}</div></div>
  <div class="card"><div class="label">Messages</div>
    <div class="value">{{{{ messages|length }}}}</div></div>
  <div class="card"><div class="label">Ghosts</div>
    <div class="value">{{{{ ghosts|length }}}}</div></div>
  <div class="card"><div class="label">Bloodstains</div>
    <div class="value">{{{{ bloodstains|length }}}}</div></div>
</div>
<section>
  <h2>Server Info</h2>
  <table>
    <tr><th>Server IP</th><td>{{{{ server_ip }}}}</td></tr>
    <tr><th>Port</th><td>{{{{ desse_port }}}}</td></tr>
    <tr><th>Messages by region</th><td>{{{{ regions }}}}</td></tr>
    <tr><th>DB directory</th><td>{{{{ db_dir }}}}</td></tr>
  </table>
</section>
</main></body></html>""",
        messages=messages, ghosts=ghosts, bloodstains=bloodstains,
        online=online, regions=regions,
        server_ip=SERVER_IP, desse_port=DESSE_PORT, db_dir=str(DB_DIR))


@app.route("/admin/messages")
@login_required
def view_messages():
    messages = read_db("messages")
    rows = ""
    for i, m in enumerate(messages):
        r = m.get("region", "?")
        rows += f"""<tr>
          <td>{i}</td>
          <td><span class="badge {r.lower()}">{r}</span></td>
          <td>{m.get('author','—')}</td>
          <td>{m.get('text','')[:80]}</td>
          <td>{m.get('timestamp','—')[:16]}</td>
          <td><form method="POST" action="/admin/messages/delete">
            <input type="hidden" name="index" value="{i}">
            <button class="btn btn-danger">Delete</button></form></td>
        </tr>"""
    return render_template_string(f"""<!DOCTYPE html><html><head><title>Messages — Admin</title>{STYLE}</head><body>
<header><h1>// Messages ({len(messages)})</h1>
<nav><a href="/admin">← Dashboard</a><a href="/logout">Logout</a></nav></header>
<main><table><thead><tr><th>#</th><th>Region</th><th>Author</th><th>Text</th><th>Date</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></main></body></html>""")


@app.route("/admin/messages/delete", methods=["POST"])
@login_required
def delete_message():
    idx = int(request.form.get("index", -1))
    messages = read_db("messages")
    if 0 <= idx < len(messages):
        messages.pop(idx)
        write_db("messages", messages)
    return redirect(url_for("view_messages"))


@app.route("/admin/ghosts")
@login_required
def view_ghosts():
    ghosts = read_db("ghosts")
    rows = ""
    for i, g in enumerate(ghosts):
        r = g.get("region", "?")
        rows += f"""<tr>
          <td>{i}</td>
          <td><span class="badge {r.lower()}">{r}</span></td>
          <td>{g.get('author','—')}</td>
          <td>{len(g.get('data', b''))} bytes</td>
          <td>{g.get('timestamp','—')[:16]}</td>
          <td><form method="POST" action="/admin/ghosts/delete">
            <input type="hidden" name="index" value="{i}">
            <button class="btn btn-danger">Delete</button></form></td>
        </tr>"""
    return render_template_string(f"""<!DOCTYPE html><html><head><title>Ghosts — Admin</title>{STYLE}</head><body>
<header><h1>// Ghosts ({len(ghosts)})</h1>
<nav><a href="/admin">← Dashboard</a><a href="/logout">Logout</a></nav></header>
<main><table><thead><tr><th>#</th><th>Region</th><th>Author</th><th>Size</th><th>Date</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></main></body></html>""")


@app.route("/admin/ghosts/delete", methods=["POST"])
@login_required
def delete_ghost():
    idx = int(request.form.get("index", -1))
    ghosts = read_db("ghosts")
    if 0 <= idx < len(ghosts):
        ghosts.pop(idx)
        write_db("ghosts", ghosts)
    return redirect(url_for("view_ghosts"))


@app.route("/admin/bloodstains")
@login_required
def view_bloodstains():
    bloodstains = read_db("bloodstains")
    rows = ""
    for i, b in enumerate(bloodstains):
        r = b.get("region", "?")
        rows += f"""<tr>
          <td>{i}</td>
          <td><span class="badge {r.lower()}">{r}</span></td>
          <td>{b.get('author','—')}</td>
          <td>{len(b.get('data', b''))} bytes</td>
          <td>{b.get('timestamp','—')[:16]}</td>
          <td><form method="POST" action="/admin/bloodstains/delete">
            <input type="hidden" name="index" value="{i}">
            <button class="btn btn-danger">Delete</button></form></td>
        </tr>"""
    return render_template_string(f"""<!DOCTYPE html><html><head><title>Bloodstains — Admin</title>{STYLE}</head><body>
<header><h1>// Bloodstains ({len(bloodstains)})</h1>
<nav><a href="/admin">← Dashboard</a><a href="/logout">Logout</a></nav></header>
<main><table><thead><tr><th>#</th><th>Region</th><th>Author</th><th>Size</th><th>Date</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></main></body></html>""")


@app.route("/admin/bloodstains/delete", methods=["POST"])
@login_required
def delete_bloodstain():
    idx = int(request.form.get("index", -1))
    bloodstains = read_db("bloodstains")
    if 0 <= idx < len(bloodstains):
        bloodstains.pop(idx)
        write_db("bloodstains", bloodstains)
    return redirect(url_for("view_bloodstains"))


@app.route("/api/status")
def api_status():
    """Simple JSON status endpoint (no auth — for monitoring)."""
    return jsonify({
        "server_online": check_server_online(),
        "messages": len(read_db("messages")),
        "ghosts": len(read_db("ghosts")),
        "bloodstains": len(read_db("bloodstains")),
    })


if __name__ == "__main__":
    app.run(host=ADMIN_HOST, port=ADMIN_PORT, debug=False)
