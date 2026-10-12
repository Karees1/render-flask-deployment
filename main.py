import os
import sqlite3
from urllib.parse import parse_qsl, urlencode, urlparse, urlsplit, urlunsplit

from flask import Flask, abort, g, redirect, request
from markupsafe import escape

app = Flask(__name__)
DB = os.environ.get("QR_DB", "qr.db")
HOME = "https://boilertechniques.netlify.app/"

# Links seeded on startup (INSERT OR IGNORE). Render's disk is wiped on each deploy,
# so anything that must survive lives here until we move to Postgres.
SEED_LINKS = [
    # (slug, destination, client, label)
    ("IzgyMd", "https://boilertechniques.netlify.app/", "Boiler Techniques", "business-cards"),
]


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS qr_links(
          slug TEXT PRIMARY KEY, destination TEXT NOT NULL, client TEXT, label TEXT,
          active INTEGER NOT NULL DEFAULT 1, fallback TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS qr_scans(
          slug TEXT, scanned_at TEXT DEFAULT CURRENT_TIMESTAMP, user_agent TEXT);
        """
    )
    for slug, dest, client, label in SEED_LINKS:
        if not valid_destination(dest):
            raise ValueError(f"bad seed destination: {dest}")
        conn.execute(
            "INSERT OR IGNORE INTO qr_links(slug,destination,client,label) VALUES(?,?,?,?)",
            (slug, dest, client, label),
        )
    conn.commit()
    conn.close()


def valid_destination(url):
    u = urlparse(url)
    return u.scheme == "https" and bool(u.hostname) and not u.username


@app.route("/")
def home():
    name = request.args.get("name", "World")
    safe_name = escape(name)  # 👈 Escaping user input manually
    return f"Hello, {safe_name}!"


@app.get("/q/<slug>")
def qr_redirect(slug):
    row = db().execute("SELECT * FROM qr_links WHERE slug=?", (slug,)).fetchone()
    if row is None:
        abort(404)
    if not row["active"]:
        resp = redirect(row["fallback"] or HOME, 302)
    else:
        try:  # logging must never break the redirect
            with db() as c:
                c.execute(
                    "INSERT INTO qr_scans(slug,user_agent) VALUES(?,?)",
                    (slug, (request.user_agent.string or "")[:300]),
                )
        except sqlite3.Error:
            pass
        parts = urlsplit(row["destination"])
        q = dict(parse_qsl(parts.query))
        q.setdefault("utm_source", "qr")
        q.setdefault("utm_medium", "print")
        if row["label"]:
            q.setdefault("utm_campaign", row["label"])
        resp = redirect(urlunsplit(parts._replace(query=urlencode(q))), 302)
    resp.headers["Cache-Control"] = "no-store"
    return resp


init_db()

if __name__ == "__main__":
    app.run(debug=True)
