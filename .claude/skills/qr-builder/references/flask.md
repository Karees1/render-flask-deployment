# Flask

Uses SQLite for simplicity. On Render, SQLite on the default disk is **wiped on every deploy**: use Render Postgres (swap the connection string) or attach a persistent disk.

```python
import secrets, sqlite3, string
from urllib.parse import urlparse, urlencode, urlsplit, urlunsplit, parse_qsl
from flask import Flask, abort, redirect, request, g

app = Flask(__name__)
DB = "qr.db"
ALPHABET = string.ascii_letters + string.digits
HOME = "https://example.com"

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.executescript("""
          CREATE TABLE IF NOT EXISTS qr_links(
            slug TEXT PRIMARY KEY, destination TEXT NOT NULL, client TEXT, label TEXT,
            active INTEGER NOT NULL DEFAULT 1, fallback TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
          CREATE TABLE IF NOT EXISTS qr_scans(
            slug TEXT, scanned_at TEXT DEFAULT CURRENT_TIMESTAMP, user_agent TEXT);""")
    return g.db

@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d: d.close()

def valid_destination(url):
    u = urlparse(url)
    return u.scheme == "https" and bool(u.hostname) and not u.username

def new_slug(n=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(n))

def create_link(destination, client, label):
    if not valid_destination(destination):
        raise ValueError("destination must be an https URL")
    for _ in range(5):
        slug = new_slug()
        try:
            with db() as c:
                c.execute("INSERT INTO qr_links(slug,destination,client,label) VALUES(?,?,?,?)",
                          (slug, destination, client, label))
            return slug
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("could not allocate slug")

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
                c.execute("INSERT INTO qr_scans(slug,user_agent) VALUES(?,?)",
                          (slug, (request.user_agent.string or "")[:300]))
        except sqlite3.Error:
            pass
        parts = urlsplit(row["destination"])
        q = dict(parse_qsl(parts.query))
        q.setdefault("utm_source", "qr"); q.setdefault("utm_medium", "print")
        if row["label"]: q.setdefault("utm_campaign", row["label"])
        resp = redirect(urlunsplit(parts._replace(query=urlencode(q))), 302)
    resp.headers["Cache-Control"] = "no-store"
    return resp
```

## Create a link, then the PDF

```python
with app.app_context():
    print(create_link("https://app.example.com/welcome", "Acme", "spring-brochure"))  # -> k7Xp2q
```
```bash
python .claude/skills/qr-builder/scripts/make_qr_pdf.py --url https://go.example.com/q/k7Xp2q --out acme.pdf
```

## Render notes

- `render.yaml` here runs `python main.py` (the dev server). For production use `gunicorn main:app`.
- Free-tier services sleep; the first scan after idle can take 30s+. Use an always-on plan for client work.
- Do not commit the database or any admin token; set them as Render environment variables.
