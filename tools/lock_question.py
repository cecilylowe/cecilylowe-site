#!/usr/bin/env python3
"""Encrypt the private part of the ? page so only the password can open it.

The readable source lives in _private/question-inside.html, which is never committed. This script
encrypts it (PBKDF2-SHA256 -> AES-256-CBC + HMAC-SHA256) and writes only the ciphertext into
question.html, between the LOCKED markers. The page decrypts it in the browser with crypto-js.

Usage:  QPASS='the password' python3 tools/lock_question.py
Run it again after any change to _private/question-inside.html, or to change the password.
"""
import base64, hashlib, hmac, json, os, re, sys
from pathlib import Path
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SITE = Path(__file__).resolve().parent.parent
ITER = 30000                                   # matches the page script

pw = os.environ.get("QPASS")
if not pw:
    sys.exit("Set QPASS to the password.")
plain = ("CL1:" + (SITE / "_private/question-inside.html").read_text()).encode()
salt, iv = os.urandom(16), os.urandom(16)
key = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER, dklen=64)
enc_key, mac_key = key[:32], key[32:]
padder = padding.PKCS7(128).padder()
data = padder.update(plain) + padder.finalize()
ct = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).encryptor()
ct = ct.update(data) + ct.finalize()
mac = hmac.new(mac_key, iv + ct, hashlib.sha256).digest()
blob = {k: base64.b64encode(v).decode() for k, v in
        {"salt": salt, "iv": iv, "ct": ct, "mac": mac}.items()}
blob["iter"] = ITER

page = SITE / "question.html"
s = page.read_text()
new = '<!--LOCKED-->\n<script type="application/json" id="locked">' + json.dumps(blob) + '</script>\n<!--/LOCKED-->'
s, n = re.subn(r"<!--LOCKED-->.*?<!--/LOCKED-->", lambda m: new, s, flags=re.S)
if n != 1:
    sys.exit("LOCKED markers not found in question.html")
page.write_text(s)
print(f"locked {len(plain)} bytes -> question.html")
