# Netlify static site (no backend)

Best fit when the destination is itself a static site on Netlify's free tier. No extra host, no cold starts, nothing else to renew. Trade-off: **no per-scan logging** (count landing visits with a privacy-friendly analytics script keyed on `utm_medium=print`), and re-pointing needs a push + redeploy (~30s).

Worked example: the Boiler Techniques site (`netlify.toml`, `qr/README.md`, `scripts/check_qr_redirects.py` in the BoilerTech repo).

```toml
[[redirects]]
  from = "/q/xRp2MY"
  to = "/?utm_source=qr&utm_medium=print&utm_campaign=cards"
  status = 302          # NOT optional: Netlify defaults to 301 (cached forever)
  force = true

# ... one block per placement, then the catch-all LAST:
[[redirects]]
  from = "/q/*"
  to = "/?utm_source=qr&utm_medium=unknown&utm_campaign=fallback"
  status = 302
  force = true
```

## Rules

- **One slug per placement** (cards, brochure, digital share) so UTMs show which one works.
- `to` may be a same-site path or any https URL (use that to point a code at a different app later).
- Specific slugs first, `/q/*` last, or the catch-all shadows them. Netlify uses the first match.
- Slugs avoid look-alike characters (`0 O o 1 l I`) because the short link is printed under the code.
- Add a checker that fails the push on any non-302, missing `force`, duplicate, or misordered rule (see BoilerTech `scripts/check_qr_redirects.py`).

## Verifying without deploying

`netlify dev` needs network access that sandboxes may block. Instead parse the real file with Netlify's own engine:
`@netlify/redirect-parser` (`parseAllRedirects`) + `@netlify/redirect-matcher` (`createMatcher(...).match({scheme, host, path, query, headers, cookies})`), both bundled in `netlify-cli`. Assert each slug returns `status 302`. Afterwards, once deployed: `curl -I https://<site>/q/<slug>`.

## Gotchas

- **Branch deploys use a different URL.** The printed `https://<site>/q/<slug>` only works after the change is deployed to the **production** branch. Don't send anything to print until `curl -I` on the live URL shows 302.
- Free-plan limits are metered (credits, bandwidth). Page weight is the real cost at volume: 100K scans x ~0.8 MB is ~80 GB/month if nothing is cached. Compress images (WebP, lazy-load).
- A `netlify.app` subdomain isn't ours long-term. Plan a custom domain; old codes keep working.
