# Print guidelines

## Size

| Medium | Minimum | Comfortable |
|---|---|---|
| Business card | 18 mm | 22 to 25 mm |
| Brochure / flyer | 20 mm | 25 to 30 mm |
| Poster (scanned at 1 m) | 80 mm | 100 mm+ |
| Banner / billboard | rule: 10:1 distance:size, so 3 m away needs a 30 cm code | |

Sizes include the data area only; the quiet zone is added around it. When in doubt go bigger.

## Colors and contrast

- Dark modules on a light background. Never invert.
- **Ink:** squares are **100% K only** (`0 0 0 100`), never RGB black or four-ink rich black: at ~0.6 mm per square the plates can misregister and blur the edges. The background is knock-out white (no ink), so the quiet zone stays white on coloured stock.
- Contrast ratio of at least 4:1. Brand colors are fine if the dark is dark enough (navy, deep green, black).
- Avoid red as the dark color (some scanners read it poorly) and avoid gradients on the modules.
- Placing a code over a photo: put it on a solid white tile with a full quiet zone.

## Structure

- **Quiet zone:** at least 4 modules of empty space on every side. Don't crop it and don't let design elements enter it.
- **Error correction:** M for general print, Q for rough surfaces (packaging, outdoor), H only with a logo.
- **Shorter URL = fewer modules = bigger modules at the same size = more reliable.** This is the main reason to use a short redirect domain.

## Print shop checklist

- Send the **PDF** (vector, CMYK). Do not rasterize, resize with smoothing, recompress, or colour-convert it.
- Ask the shop to keep the artwork as supplied: no colour management, no "enhance", no trim of the white border (it is the quiet zone).
- **First batch is the proof.** If there is no earlier proof, order a small run (20 to 50) or a sample of the QR area, and scan it before approving the full run or handing any out.
- Print at 100%, no "fit to page" scaling.
- Matte or uncoated stock is better than glossy (glare).
- Request a proof and scan it with an iPhone and an Android before the full run.

## Always add a call to action

A bare QR gets ignored. Put a short line next to it: "Scan to book a visit". Optionally print the short URL underneath as a fallback for people who can't scan.

## Copy-paste brief for the print shop

```
QR code artwork, vector PDF, supplied at final size (page = artwork, 1:1).
- Do not scale, crop, rasterise or colour-convert. The white border is part of the code.
- Squares are 100% K (single ink). Background is no ink (paper/knock-out white).
- Keep the artwork on a light area with the white border intact; nothing inside it.
- Print at 100%. Matte or uncoated stock preferred; avoid foil, spot-gloss or emboss over the code.
- Please send a sample / proof of the code area before the full run.
```
