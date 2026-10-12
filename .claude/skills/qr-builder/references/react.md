# React SPA (Vite / CRA)

A client-side React app **cannot do an HTTP 302**. The browser has already downloaded your JS bundle by then, and a `window.location` redirect depends on JS running (slower, breaks for scanners that preview links, and gives no server-side scan log).

Pick one:

## Option A (recommended): put the redirect in a small backend

Use `flask.md` or `express.md` on a short domain (`go.example.com`) and keep the React app as the *destination*. The QR encodes the backend URL; React is never in the redirect path.

## Option B: host-level redirect for a fixed set of codes

If the destinations rarely change, use your host's redirect rules. They are real 302s without a backend, but changing one means a redeploy.

Netlify / Cloudflare Pages `public/_redirects`:
```
/q/k7Xp2q  https://app.example.com/welcome  302
```
Vercel `vercel.json` (use `"permanent": false`):
```json
{ "redirects": [{ "source": "/q/k7Xp2q", "destination": "https://app.example.com/welcome", "permanent": false }] }
```

## Option C: serverless function next to the SPA

Vercel `api/q/[slug].ts` or Netlify Functions return `302` with `Location` after a lookup in a hosted DB (Supabase, Upstash). Same contract as `redirect-design.md`.

## Showing the QR inside React (e.g. a client dashboard)

Fetch the PDF/SVG from the backend, or render on the client with `qrcode.react`:
```jsx
import { QRCodeSVG } from "qrcode.react";
<QRCodeSVG value="https://go.example.com/q/k7Xp2q" level="M" marginSize={4} size={256} />
```
Offer a "Download PDF" button that hits the backend generator for print. Don't rely on screenshots of the on-screen code.

## Deep linking into the SPA

The destination can be any SPA route (`https://app.example.com/offer/spring`). Make sure the host rewrites unknown paths to `index.html` so the route resolves on first load.
