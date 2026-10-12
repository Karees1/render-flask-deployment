# Express (Node)

Uses `better-sqlite3` for brevity; swap for `pg` in production (see `redirect-design.md` for the schema).

```js
import express from "express";
import Database from "better-sqlite3";
import crypto from "node:crypto";

const app = express();
const db = new Database("qr.db");
db.exec(`
  CREATE TABLE IF NOT EXISTS qr_links(
    slug TEXT PRIMARY KEY, destination TEXT NOT NULL, client TEXT, label TEXT,
    active INTEGER NOT NULL DEFAULT 1, fallback TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS qr_scans(slug TEXT, scanned_at TEXT DEFAULT CURRENT_TIMESTAMP, user_agent TEXT);
`);

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
const newSlug = (n = 6) =>
  Array.from(crypto.randomBytes(n), (b) => ALPHABET[b % 62]).join("");

function validDestination(s) {
  try { const u = new URL(s); return u.protocol === "https:" && !u.username && !!u.hostname; }
  catch { return false; }
}

export function createLink(destination, client, label) {
  if (!validDestination(destination)) throw new Error("destination must be an https URL");
  for (let i = 0; i < 5; i++) {
    const slug = newSlug();
    try {
      db.prepare("INSERT INTO qr_links(slug,destination,client,label) VALUES(?,?,?,?)")
        .run(slug, destination, client, label);
      return slug;
    } catch (e) { if (e.code !== "SQLITE_CONSTRAINT_PRIMARYKEY") throw e; }
  }
  throw new Error("could not allocate slug");
}

app.get("/q/:slug", (req, res) => {
  const row = db.prepare("SELECT * FROM qr_links WHERE slug=?").get(req.params.slug);
  if (!row) return res.sendStatus(404);
  res.set("Cache-Control", "no-store");
  if (!row.active) return res.redirect(302, row.fallback || "https://example.com");
  try { db.prepare("INSERT INTO qr_scans(slug,user_agent) VALUES(?,?)")
          .run(row.slug, (req.get("user-agent") || "").slice(0, 300)); } catch {}
  const u = new URL(row.destination);
  u.searchParams.set("utm_source", u.searchParams.get("utm_source") ?? "qr");
  u.searchParams.set("utm_medium", u.searchParams.get("utm_medium") ?? "print");
  if (row.label) u.searchParams.set("utm_campaign", u.searchParams.get("utm_campaign") ?? row.label);
  res.redirect(302, u.toString());   // explicit 302, not the default
});

app.listen(process.env.PORT || 3000);
```

Notes:
- Express's `res.redirect(url)` defaults to 302, but pass it explicitly so nobody "optimizes" it to 301.
- Behind a proxy (Render, Heroku) set `app.set("trust proxy", 1)` if you add rate limiting by IP.
- Add `express-rate-limit` on `/q/:slug` to slow slug enumeration.
