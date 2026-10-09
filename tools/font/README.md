# Lowe Grotesk

The site's typeface. It is Archivo (SIL Open Font License 1.1, assets/fonts/OFL.txt), reproportioned to match
the lettering on architecture.yale.edu (Gerstner Programm), from measurements only: cap height, x-height,
ascenders/descenders, stem weight and each character's advance width (measurements.json, taken from the
rendered page at 1000px). No outlines come from any other font.

Rebuild: put Archivo[wdth,wght].ttf here as Archivo-var.ttf, then `python3 build.py`; copy the .woff2 to assets/fonts/.

# Lowe Sans (2026-10-09, the site's typeface now)

Geist (SIL Open Font License 1.1, assets/fonts/OFL-Geist.txt) reproportioned to ABC Diatype at weight 500, the
face on davidricogomez.com, from measurements only (measurements-diatype.json): cap height, x-height,
ascenders/descenders, stem weight and each character's advance width. No outlines come from any other font.

Rebuild: `python3 build_sans.py` (reads Geist-Variable.woff2 here); copy LoweSans-Regular.woff2 to assets/fonts/.
Lowe Sans is the site's font for good (Cecily, 2026-10-09). Lowe Grotesk stays only as an archive.
