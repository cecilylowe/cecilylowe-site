"""Lowe Grotesk: Archivo (SIL OFL 1.1) reproportioned to the measured proportions of the lettering on
architecture.yale.edu. No outlines are taken from any other font. Measurements only: cap height, x-height,
ascender/descender, stem weight and the advance width of each character.
  - instance Archivo at width 92, weight 410 (best fit to stem weight and average widths)
  - scale so the capitals are 706/1000 em
  - lowercase: x-height 541 -> 482, ascenders 744 -> 706, descenders deeper (179 -> 211)
  - each character set to the measured advance width (outline scaled by at most +-8%, the rest in the spacing)"""
import json, unicodedata
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

g = json.load(open("measurements.json")); W = g["w"]
f = instantiateVariableFont(TTFont("Archivo-var.ttf"), {"wdth": 92, "wght": 410})
K = 706.05 / 686.0                                   # Archivo caps 686 at upm 1000 -> 706
glyf, hmtx, cmap = f["glyf"], f["hmtx"], f.getBestCmap()
rev = {}
for u, n in cmap.items(): rev.setdefault(n, u)
XO, XN, AO, AN, DS = 541 / K, 482.0, 744 / K, 706.0, 1.18   # (old values in unscaled units)

def lower(n):
    u = rev.get(n); return u is not None and unicodedata.category(chr(u)) == "Ll"

def vmap(y):                                          # lowercase vertical map, input unscaled, output final
    if y <= 0: return y * K * DS
    if y <= XO: return y * (XN / XO)
    return XN + (y - XO) * (AN - XN) / (AO - XO)

FLOAT_DY = -48                                       # dots and accents: moved down whole, never squashed
horiz = {}                                            # glyph -> (f, dx, newadvance)
for n in f.getGlyphOrder():
    adv, lsb = hmtx[n]; A = adv * K
    u = rev.get(n); ch = chr(u) if u else None
    if ch in W and A > 0:
        T = W[ch]; s = max(0.92, min(1.08, T / A)); horiz[n] = (s, (T - A * s) / 2, round(T))
    else:
        horiz[n] = (1.0, 0.0, round(A))

# composites inherit their base glyph's horizontal change
for n in f.getGlyphOrder():
    gl = glyf[n]
    if gl.isComposite() and gl.components:
        base = gl.components[0].glyphName
        if horiz[n][0] == 1.0 and horiz[n][1] == 0.0: horiz[n] = (horiz[base][0], horiz[base][1], horiz[base][2]) if round(hmtx[n][0]*K) == round(hmtx[base][0]*K) else horiz[n]

for n in f.getGlyphOrder():
    gl = glyf[n]; s, dx, adv = horiz[n]; lc = lower(n)
    if gl.isComposite():
        for i, c in enumerate(gl.components):
            c.x = round(c.x * K * s + (0 if i == 0 else 0)); 
            c.y = round(c.y * K + (FLOAT_DY if (lc and i > 0) else 0))
            if i == 0: c.x = round(dx) + c.x
        gl.program = None if hasattr(gl, "program") else None
    elif gl.numberOfContours > 0:
        co = gl.coordinates; ends = gl.endPtsOfContours; start = 0
        for e in ends:
            ys = [co[i][1] for i in range(start, e + 1)]
            floating = lc and min(ys) > XO + 25
            for i in range(start, e + 1):
                x, y = co[i]
                y2 = (y * K + FLOAT_DY + (AN - AO * K) * 0) if floating else (vmap(y) if lc else y * K)
                co[i] = (round(x * K * s + dx), round(y2))
            start = e + 1
    lsb = 0
    if gl.numberOfContours > 0 and not gl.isComposite():
        gl.recalcBounds(glyf); lsb = gl.xMin
    hmtx[n] = (max(0, adv), lsb)

# hinting no longer matches the outlines
for t in ("prep", "fpgm", "cvt "):
    if t in f: del f[t]
for n in f.getGlyphOrder():
    gl = glyf[n]
    if hasattr(gl, "program"): from fontTools.ttLib.tables import ttProgram; p = ttProgram.Program(); p.fromBytecode(b""); gl.program = p
# composites: lsb from bounds
for n in f.getGlyphOrder():
    gl = glyf[n]
    if gl.isComposite(): gl.recalcBounds(glyf); hmtx[n] = (hmtx[n][0], gl.xMin)

# kerning roughly follows the new size
gpos = f["GPOS"].table
def scale_vr(vr):
    if vr is None: return
    for a in ("XAdvance", "XPlacement"):
        if hasattr(vr, a) and getattr(vr, a): setattr(vr, a, round(getattr(vr, a) * K))
for lk in gpos.LookupList.Lookup:
    for st in lk.SubTable:
        st = getattr(st, "ExtSubTable", st)
        if lk.LookupType in (2, 9) and getattr(st, "LookupType", 2) == 2 or st.__class__.__name__ == "PairPos":
            if getattr(st, "Format", 0) == 1:
                for ps in st.PairSet:
                    for pv in ps.PairValueRecord: scale_vr(pv.Value1); scale_vr(pv.Value2)
            elif getattr(st, "Format", 0) == 2:
                for c1 in st.Class1Record:
                    for c2 in c1.Class2Record: scale_vr(c2.Value1); scale_vr(c2.Value2)

# vertical metrics like the measured face, so line spacing behaves the same
for t, a, d in ((f["hhea"], "ascent", "descent"),):
    t.ascent, t.descent, t.lineGap = 1038, -278, 0
os2 = f["OS/2"]; os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = 1038, -278, 0
os2.usWinAscent, os2.usWinDescent = 1100, 420; os2.sxHeight, os2.sCapHeight = 482, 706
os2.fsSelection |= 1 << 7                              # use typo metrics

name = f["name"]
for rec in list(name.names):
    if rec.nameID in (1, 3, 4, 6, 16, 17, 21, 22, 25): name.removeNames(nameID=rec.nameID)
for nid, s in ((1, "Lowe Grotesk"), (2, "Regular"), (3, "1.000;LoweGrotesk-Regular"), (4, "Lowe Grotesk Regular"), (6, "LoweGrotesk-Regular"),
               (0, "Copyright 2020 The Archivo Project Authors (https://github.com/Omnibus-Type/Archivo). Lowe Grotesk modifications 2026 Cecily Lowe."),
               (5, "Version 1.000"), (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1."), (14, "https://openfontlicense.org")):
    name.setName(s, nid, 3, 1, 0x409)
if "STAT" in f: del f["STAT"]
f.save("LoweGrotesk-Regular.ttf")
f.flavor = "woff2"; f.save("LoweGrotesk-Regular.woff2")
print("built")
