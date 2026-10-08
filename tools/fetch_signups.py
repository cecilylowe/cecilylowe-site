#!/usr/bin/env python3
"""The subscriber list now lives in the Google Sheet "cecilylowe.com newsletter" in Cecily's Drive
(written by the Apps Script in signups/). This opens it. The old Netlify copy is in fetch_signups_netlify.py.
"""
import webbrowser
webbrowser.open("https://docs.google.com/spreadsheets/d/1MnzTH8JKeUa38l8z3C2QLC28ane81VL4VB4RtoJwOFI/edit")
