# Redirect design (stack-independent)

## Data model

`qr_links`
| column | type | notes |
|---|---|---|
| `slug` | text, unique | random base62, 6 to 8 chars |
| `destination` | text | full https URL |
| `client` | text | for filtering and billing |
| `label` | text | e.g. "Spring brochure 2026" |
| `active` | bool | default true |
| `fallback` | text, null | where to send when inactive; default site home |
| `created_at` | timestamp | |

`qr_scans` (optional but recommended)
| column | type | notes |
|---|---|---|
| `slug` | text | FK |
| `scanned_at` | timestamp | |
| `user_agent` | text | to split iOS/Android/desktop |
| `referer` | text, null | usually empty for QR |

Don't store raw IPs. If you want rough geography, derive country at request time and store only that.

## Route contract

`GET /q/<slug>`
1. Look up the slug. Unknown: 404 (or redirect to the main site).
2. Not active: 302 to `fallback` or the home page.
3. Log the scan **without blocking the redirect**. A logging failure must never break a redirect.
4. Respond `302` with `Location: <destination>` and `Cache-Control: no-store`.

## Open redirect prevention

- The destination comes **only** from the database. Never `?to=` or `?next=`.
- Validate on write: scheme must be `https`, host must be non-empty, reject `javascript:`, `data:`, and credentials in the URL (`user:pass@`).
- Optional: an allowlist of destination domains per client.
- Rate-limit slug lookups to slow enumeration.

## Deep links to native apps

For links that should open a mobile app:
- Prefer **universal links (iOS) / app links (Android)** on an https URL. The destination stays a normal https URL and the OS opens the app if installed.
- For a single QR that sends iPhone to the App Store and Android to Play: branch on `User-Agent` inside the redirect route. Keep a `destination_ios` / `destination_android` column and fall back to `destination`.

## UTM tagging

Append UTM params at redirect time, not into the printed URL, so they can change too: `utm_source=qr&utm_medium=print&utm_campaign=<label>`.

## Slugs

Generate with a CSPRNG (`secrets` in Python, `crypto.randomBytes` in Node). Check for collision on insert and retry. Never use auto-increment ids as slugs.

## Operational notes

- Host the redirect on its own short domain or subdomain (`go.example.com`). Put renewal on a calendar: this domain is a permanent liability once anything is printed.
- Keep the redirect service tiny and fast. Free-tier hosts that sleep (like Render free) give a 30s+ cold start on a scan. For paid clients use an always-on instance, or put the redirect on an edge/serverless platform.
- Back up the `qr_links` table. Losing it breaks every printed code.
