---
name: qr-builder
description: Build print-ready QR codes that route through a short redirect link we control, so clients can print cards, brochures, and signage once and re-point them to any website or app later. Use when asked to create QR codes, add a QR redirect route to a Flask, Express, Next.js, or React project, export a QR as PDF, or advise on QR print sizing.
---

# QR Builder

Print-ready QR codes for physical material (business cards, brochures, flyers, banners) that route to our websites and apps.

## The one rule

**Never encode the final destination in a printed QR code. Encode a short redirect link we control.**

```
printed QR  ->  https://go.example.com/q/k7Xp2  ->  302  ->  https://real-destination.com/landing
```

Printed paper can't be edited, but the redirect row can. Campaign ended, app moved, domain changed: update one database row and every card in the field follows. It also gives us scan counts for free.

A short URL also makes a *simpler QR* (fewer modules), which scans more reliably at small print sizes.

## Workflow

1. **Collect inputs** (ask if missing):
   - Destination URL (https only)
   - Client / campaign name (used for the slug and for filtering analytics)
   - Print size in mm (default 25 mm; see `references/print-guidelines.md`)
   - Brand colors (default black on white; keep dark-on-light)
2. **Pick the stack** and read the matching reference:
   | Project | Reference |
   |---|---|
   | Flask | `references/flask.md` |
   | Express / Node | `references/express.md` |
   | Next.js (App Router) | `references/nextjs.md` |
   | React SPA (Vite/CRA) | `references/react.md` |
   | Static site on Netlify (no backend) | `references/netlify-static.md` |
   | Any other / design questions | `references/redirect-design.md` |
3. **Add the redirect route** if the project doesn't have one yet (`/q/<slug>`, HTTP 302, DB lookup, scan logging).
4. **Create the link record** (slug + destination + client + active flag).
5. **Generate the PDF**:
   ```bash
   pip install segno
   python .claude/skills/qr-builder/scripts/make_qr.py \
     --url https://go.example.com/q/k7Xp2 --size-mm 30 --out client-card.pdf
   ```
   Output is a vector PDF at exact physical size with the quiet zone included (print shops can scale it without pixelation). For WhatsApp, email, and slides use a PNG: `--px 1024 --out share.png`. Never send a PNG to a printer.
6. **Verify** before handing over: `curl -I <short url>` must return 302 with the right `Location`, and scan the PDF with a phone, on screen and (ideally) as a test print at final size.

## Non-negotiables

- **302, not 301.** Browsers cache 301s permanently, which defeats re-pointing.
- **https only**, and the redirect domain must be one we own long-term. If the domain lapses, every printed code dies. Use a dedicated short domain or subdomain.
- **No open redirects.** Destinations come from the database, never from a query parameter. See `references/redirect-design.md`.
- **Slugs are random and non-sequential** (e.g. 6 to 8 chars base62), so codes can't be enumerated.
- **Error correction M or Q** for print (not L). Not H unless a logo overlays the code, since H makes the code denser.
- **Quiet zone of at least 4 modules.** The script enforces this.
- **Dark modules on a light background.** Never invert; many scanners fail.
- Never ship a code without scanning the final file.

## Handling client requests

- "Can we change where the card goes?" Yes: update the record's destination. Don't reprint.
- "Can we see scans?" Yes, from the scan log (`references/redirect-design.md`).
- "Our campaign ended." Set `active=false` and have the route redirect to a fallback page rather than 404.
- "Can we add our logo to the middle?" Only with error correction H, a logo covering at most 15% of the area, and a real scan test.
