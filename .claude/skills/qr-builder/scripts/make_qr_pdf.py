#!/usr/bin/env python3
"""Generate a print-ready, vector QR code PDF at an exact physical size.

    pip install segno
    python make_qr_pdf.py --url https://go.example.com/q/k7Xp2 --size-mm 30 --out card.pdf

--size-mm is the TOTAL size including the quiet zone. Output is a single-page PDF
sized exactly to the code, so printers get 1:1 scale.
"""
import argparse
import sys
from urllib.parse import urlparse

import segno

MM_TO_PT = 72 / 25.4
QUIET_ZONE = 4  # modules; the QR spec minimum


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", required=True, help="Short redirect URL to encode (https)")
    p.add_argument("--out", required=True, help="Output .pdf path")
    p.add_argument("--size-mm", type=float, default=25, help="Total size in mm incl. quiet zone (default 25)")
    p.add_argument("--ec", choices=["m", "q", "h"], default="m", help="Error correction (default m; use h only with a logo)")
    p.add_argument("--dark", default="#000000", help="Module color (default black)")
    p.add_argument("--light", default="#ffffff", help="Background color (default white)")
    a = p.parse_args()

    u = urlparse(a.url)
    if u.scheme != "https" or not u.netloc:
        p.error("--url must be an absolute https URL")
    if luminance(a.dark) >= luminance(a.light):
        p.error("--dark must be darker than --light (inverted codes fail on many scanners)")
    if contrast(a.dark, a.light) < 4:
        p.error(f"contrast {contrast(a.dark, a.light):.1f}:1 is too low; need at least 4:1")

    qr = segno.make(a.url, error=a.ec, micro=False, boost_error=False)
    total_modules = qr.symbol_size(border=QUIET_ZONE)[0]
    scale = a.size_mm * MM_TO_PT / total_modules  # points per module
    module_mm = a.size_mm / total_modules
    qr.save(a.out, kind="pdf", scale=scale, border=QUIET_ZONE, dark=a.dark, light=a.light)

    print(f"wrote {a.out}: {a.size_mm} mm, version {qr.version}, EC {qr.error}, "
          f"{total_modules} modules incl. quiet zone, {module_mm:.2f} mm/module")
    if module_mm < 0.4:
        print("WARNING: modules < 0.4 mm; may not print or scan reliably. Increase --size-mm or shorten the URL.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
