#!/usr/bin/env python3
"""Generate a QR code as a press-ready vector PDF or a crisp PNG for digital sharing.

    pip install segno reportlab
    python make_qr.py --url https://go.example.com/q/k7Xp2 --size-mm 30 --out card.pdf
    python make_qr.py --url https://go.example.com/q/k7Xp2 --px 1024 --out share.png

The format follows the --out extension.

PDF (for printers): --size-mm is the TOTAL size including the quiet zone; the page is
sized exactly to the code, so printers get 1:1 scale. Colour is DeviceCMYK, not RGB:
the squares are 100% K (single-ink black, "0 0 0 1 k") on a knock-out white (no ink)
background, drawn as one seamless path. RGB black is often converted to a four-ink
"rich black" by the shop's RIP, and on squares well under 1 mm the plates can misregister
and blur the code. Use --dark-cmyk only for a brand colour, and prefer pure K.

PNG (for chat, email, slides): --px is the target width; the scale is a whole number of
pixels per module so edges stay sharp (the real width is printed). RGB, with --dark and
--light as hex colours (these two options apply to PNG only).
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


def parse_cmyk(s: str):
    try:
        vals = [float(x) for x in s.split(",")]
    except ValueError:
        vals = []
    if len(vals) != 4 or not all(0 <= v <= 100 for v in vals):
        raise argparse.ArgumentTypeError("expected C,M,Y,K as four numbers 0-100, e.g. 0,0,0,100")
    return vals


def cmyk_to_hex(c: float, m: float, y: float, k: float) -> str:
    """Naive conversion, only used for the contrast check."""
    r, g, b = (round(255 * (1 - v / 100) * (1 - k / 100)) for v in (c, m, y))
    return f"#{r:02x}{g:02x}{b:02x}"


def write_cmyk_pdf(qr, path: str, size_mm: float, cmyk, title: str) -> None:
    from reportlab.pdfgen import canvas  # imported here so PNG-only use needs just segno

    size = size_mm * MM_TO_PT
    module = size / qr.symbol_size(border=QUIET_ZONE)[0]
    pdf = canvas.Canvas(path, pagesize=(size, size), pageCompression=0)
    pdf.setTitle(title)
    pdf.setCreator("qr-builder skill")

    pdf.setFillColorCMYK(0, 0, 0, 0)  # knock-out white: no ink, protects the quiet zone on coloured stock
    pdf.rect(0, 0, size, size, stroke=0, fill=1)

    pdf.setFillColorCMYK(*(v / 100 for v in cmyk))
    path_obj = pdf.beginPath()
    for row_i, row in enumerate(qr.matrix):
        col = 0
        while col < len(row):  # merge horizontal runs into one rectangle each
            if row[col]:
                start = col
                while col < len(row) and row[col]:
                    col += 1
                path_obj.rect((QUIET_ZONE + start) * module, size - (QUIET_ZONE + row_i + 1) * module,
                              (col - start) * module, module)
            else:
                col += 1
    pdf.drawPath(path_obj, stroke=0, fill=1)  # one path: no hairline seams between squares
    pdf.showPage()
    pdf.save()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", required=True, help="Short redirect URL to encode (https)")
    p.add_argument("--out", required=True, help="Output path ending in .pdf or .png")
    p.add_argument("--size-mm", type=float, default=25, help="PDF: total size in mm incl. quiet zone (default 25)")
    p.add_argument("--px", type=int, default=1024, help="PNG: target width in pixels (default 1024)")
    p.add_argument("--ec", choices=["m", "q", "h"], default="m", help="Error correction (default m; use h only with a logo)")
    p.add_argument("--dark", default=None, help="PNG only: module colour as hex (default #000000)")
    p.add_argument("--light", default=None, help="PNG only: background colour as hex (default #ffffff)")
    p.add_argument("--dark-cmyk", type=parse_cmyk, default=[0, 0, 0, 100], metavar="C,M,Y,K",
                   help="PDF only: module colour, 0-100 each (default 0,0,0,100 = pure K black)")
    a = p.parse_args()

    u = urlparse(a.url)
    if u.scheme != "https" or not u.netloc:
        p.error("--url must be an absolute https URL")

    ext = a.out.lower().rsplit(".", 1)[-1]
    if ext not in ("pdf", "png"):
        p.error("--out must end in .pdf or .png")

    if ext == "pdf":
        if a.dark or a.light:
            p.error("--dark/--light are RGB hex and apply to PNG only; PDFs are CMYK, use --dark-cmyk "
                    "(the background is always knock-out white)")
        dark_hex, light_hex = cmyk_to_hex(*a.dark_cmyk), "#ffffff"
    else:
        dark_hex, light_hex = a.dark or "#000000", a.light or "#ffffff"
    if luminance(dark_hex) >= luminance(light_hex):
        p.error("modules must be darker than the background (inverted codes fail on many scanners)")
    if contrast(dark_hex, light_hex) < 4:
        p.error(f"contrast {contrast(dark_hex, light_hex):.1f}:1 is too low; need at least 4:1")

    qr = segno.make(a.url, error=a.ec, micro=False, boost_error=False)
    total_modules = qr.symbol_size(border=QUIET_ZONE)[0]

    if ext == "png":
        scale = max(1, a.px // total_modules)
        qr.save(a.out, kind="png", scale=scale, border=QUIET_ZONE, dark=dark_hex, light=light_hex)
        print(f"wrote {a.out}: {scale * total_modules}px wide, version {qr.version}, EC {qr.error}, "
              f"{total_modules} modules incl. quiet zone, {scale}px/module")
        return 0

    write_cmyk_pdf(qr, a.out, a.size_mm, a.dark_cmyk, f"QR code {a.url}")
    module_mm = a.size_mm / total_modules
    c, m, y, k = a.dark_cmyk
    ink = "pure K black (single ink)" if (c, m, y) == (0, 0, 0) else f"CMYK {c:g}/{m:g}/{y:g}/{k:g}"
    print(f"wrote {a.out}: {a.size_mm} mm, version {qr.version}, EC {qr.error}, "
          f"{total_modules} modules incl. quiet zone, {module_mm:.2f} mm/module, {ink}")
    if (c, m, y) != (0, 0, 0):
        print("WARNING: colour uses C/M/Y inks; at this module size the plates can misregister and blur the code. "
              "Prefer pure K (0,0,0,100).", file=sys.stderr)
    if module_mm < 0.4:
        print("WARNING: modules < 0.4 mm; may not print or scan reliably. Increase --size-mm or shorten the URL.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
