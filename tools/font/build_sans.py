"""Lowe Sans: Geist (SIL OFL 1.1, assets/fonts/OFL-Geist.txt) reproportioned to the measured proportions of
ABC Diatype at weight 500, the face on davidricogomez.com. No outlines are taken from any other font.
Measurements only (measurements-diatype.json): cap height, x-height, ascender/descender, stem weight and the
advance width of each character.
  - instance Geist at weight 515 (its capital I stem then matches the measured 111/1000 em)
  - scale so the capitals are 700/1000 em
  - lowercase: x-height 530 -> 485, ascenders to the cap height, descenders deeper (-148 -> -206)
  - each character set to the measured advance width (outline scaled by at most +-8%, the rest in the spacing)
  - l (and l-slash) drawn as a plain straight stem, no tail (her request 2026-10-09)
Run: python3 build_sans.py  (writes LoweSans-Regular.ttf / .woff2; copy the .woff2 to assets/fonts/)"""
import json, unicodedata
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from fontTools.varLib.instancer import instantiateVariableFont

m = json.load(open("measurements-diatype.json")); W = m["w"]
f = instantiateVariableFont(TTFont("Geist-Variable.woff2"), {"wght": 515})
f.flavor = None
K = m["cap"] / 710.0                                  # Geist caps 710 -> 700
glyf, hmtx, cmap = f["glyf"], f["hmtx"], f.getBestCmap()
rev = {}
for u, n in cmap.items(): rev.setdefault(n, u)
XO, XN = 530.0, round(m["x"])                         # lowercase x-height: Geist units -> final
AO, AN = 710.0, float(m["asc"])                       # ascenders: Geist units -> final
DS = -m["desc"] / (150.0 * K)                         # descender stretch
FLOAT_DY = round(XN - XO * K)                         # dots and accents on lowercase: moved down whole

def lower(n):
    u = rev.get(n); return u is not None and unicodedata.category(chr(u)) == "Ll"

def vmap(y):                                          # lowercase vertical map, input Geist units, output final
    if y <= 0: return y * K * DS
    if y <= XO: return y * (XN / XO)
    return XN + (y - XO) * (AN - XN) / (AO - XO)

horiz = {}                                            # glyph -> (x scale, dx, new advance)
for n in f.getGlyphOrder():
    adv, lsb = hmtx[n]; A = adv * K
    u = rev.get(n); ch = chr(u) if u else None
    if ch in W and A > 0:
        T = W[ch]; s = max(0.92, min(1.08, T / A)); horiz[n] = (s, (T - A * s) / 2, round(T))
    else:
        horiz[n] = (1.0, 0.0, round(A))

# composites (accented letters) inherit their base glyph's horizontal change when they share its width
for n in f.getGlyphOrder():
    gl = glyf[n]
    if gl.isComposite() and gl.components:
        base = gl.components[0].glyphName
        if base in horiz and round(hmtx[n][0] * K) == round(hmtx[base][0] * K) and (rev.get(n) is None or chr(rev[n]) not in W):
            horiz[n] = horiz[base]

for n in f.getGlyphOrder():
    gl = glyf[n]; s, dx, adv = horiz[n]; lc = lower(n)
    if gl.isComposite():
        for i, c in enumerate(gl.components):
            c.x = round(c.x * K * s) + (round(dx) if i == 0 else 0)
            c.y = round(c.y * K + (FLOAT_DY if (lc and i > 0) else 0))
    elif gl.numberOfContours > 0:
        co = gl.coordinates; start = 0
        for e in gl.endPtsOfContours:
            ys = [co[i][1] for i in range(start, e + 1)]
            floating = lc and min(ys) > XO + 25
            for i in range(start, e + 1):
                x, y = co[i]
                y2 = (y * K + FLOAT_DY) if floating else (vmap(y) if lc else y * K)
                co[i] = (round(x * K * s + dx), round(y2))
            start = e + 1
    hmtx[n] = (max(0, adv), hmtx[n][1])

# l without the tail (Cecily, 2026-10-09): a plain straight stem, as thick as the i's and centred in the l's
# width, baseline to ascender like Diatype's. l-slash gets the same stem with its bar across it.
from fontTools.pens.ttGlyphPen import TTGlyphPen
glyf["dotlessi"].recalcBounds(glyf)
SX0, SX1 = glyf["dotlessi"].xMin, glyf["dotlessi"].xMax                 # the i's stem
def stem_glyph(adv, bar=False):
    w = SX1 - SX0; x0 = round((adv - w) / 2); x1 = x0 + w; cx = (x0 + x1) / 2
    pen = TTGlyphPen(None)
    pen.moveTo((x0, 0)); pen.lineTo((x0, AN)); pen.lineTo((x1, AN)); pen.lineTo((x1, 0)); pen.closePath()
    if bar:
        pen.moveTo((round(cx - 118), 262)); pen.lineTo((round(cx - 118), 344)); pen.lineTo((round(cx + 118), 462)); pen.lineTo((round(cx + 118), 380)); pen.closePath()
    return pen.glyph(), x0
for gname, bar in (("l", False), ("lslash", True)):
    if gname in glyf.keys():
        adv = hmtx[gname][0]; glyf[gname], lsb = stem_glyph(adv, bar)
        hmtx[gname] = (adv, lsb)                     # bounds-based lsb is set again below

# hinting no longer matches the outlines
for t in ("prep", "fpgm", "cvt ", "gasp"):
    if t in f: del f[t]
for n in f.getGlyphOrder():
    gl = glyf[n]
    if hasattr(gl, "program"):
        p = ttProgram.Program(); p.fromBytecode(b""); gl.program = p
for n in f.getGlyphOrder():
    gl = glyf[n]
    if gl.numberOfContours != 0: gl.recalcBounds(glyf); hmtx[n] = (hmtx[n][0], gl.xMin)

# kerning roughly follows the new size
def scale_vr(vr):
    if vr is None: return
    for a in ("XAdvance", "XPlacement"):
        if getattr(vr, a, None): setattr(vr, a, round(getattr(vr, a) * K))
if "GPOS" in f:
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            st = getattr(st, "ExtSubTable", st)
            if st.__class__.__name__ != "PairPos": continue
            if st.Format == 1:
                for ps in st.PairSet:
                    for pv in ps.PairValueRecord: scale_vr(pv.Value1); scale_vr(pv.Value2)
            elif st.Format == 2:
                for c1 in st.Class1Record:
                    for c2 in c1.Class2Record: scale_vr(c2.Value1); scale_vr(c2.Value2)

# vertical metrics like the measured face, so line spacing behaves the same
f["hhea"].ascent, f["hhea"].descent, f["hhea"].lineGap = 968, -358, 0
os2 = f["OS/2"]; os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = 968, -358, 0
os2.usWinAscent, os2.usWinDescent = 1000, 400; os2.sxHeight, os2.sCapHeight = XN, round(m["cap"])
os2.fsSelection |= 1 << 7                              # use typo metrics
os2.usWeightClass = 400

name = f["name"]
for rec in list(name.names):
    if rec.nameID in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25): name.removeNames(nameID=rec.nameID)
for nid, s in ((1, "Lowe Sans"), (2, "Regular"), (3, "1.000;LoweSans-Regular"), (4, "Lowe Sans Regular"), (6, "LoweSans-Regular"),
               (0, "Copyright (c) 2023 Vercel, in collaboration with basement.studio. Lowe Sans modifications 2026 Cecily Lowe."),
               (5, "Version 1.000"), (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1."), (14, "https://openfontlicense.org")):
    name.setName(s, nid, 3, 1, 0x409)
for t in ("STAT", "MVAR", "HVAR", "fvar", "gvar", "avar"):
    if t in f: del f[t]
f.save("LoweSans-Regular.ttf")
f.flavor = "woff2"; f.save("LoweSans-Regular.woff2")
print("built")
