"""Build full translated name tables used by dynamic field messages.

Menu lists use prerendered strips, so their underlying US-era tables can still
contain RES and other width-driven abbreviations.  Field messages used to copy
those bytes and consequently displayed ``RES is used!``.  These two tables are
ID-identical but contain the actual translations from script_translated.json.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ps4disasm", "vwf")
SCRIPT = os.path.join(ROOT, "work", "script_translated.json")

CODE = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): CODE[c] = 1 + i
for i, c in enumerate("0123456789"): CODE[c] = 27 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): CODE[c] = 57 + i
CODE['-'] = 0x31; CODE['!'] = 0x32; CODE['?'] = 0x33; CODE[':'] = 0x34
CODE['.'] = 0x53; CODE["'"] = 0x54; CODE[','] = 0x55; CODE['ü'] = 0x57

TABLES = (("00:001", 160, "fielditemnames.bin"),
          ("00:002",  40, "fieldtechnames.bin"),
          ("00:003",  54, "fieldskillnames.bin"))   # "MEDICE is used!" read the US table

# RunText uses the dialogue charset, whose lowercase block differs from the
# menu charset above.  Shops build confirmation sentences in RAM, so they need
# a full translated item table in that encoding rather than the US-era alias
# table that happens to share the menu-list ordinals.
DIA_CODE = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): DIA_CODE[c] = 1 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): DIA_CODE[c] = 27 + i
DIA_CODE['.'] = 0x35; DIA_CODE["'"] = 0x36; DIA_CODE[','] = 0x37
DIA_CODE[':'] = 0x39; DIA_CODE['!'] = 0x3A; DIA_CODE['?'] = 0x3B
DIA_CODE['-'] = 0x3C; DIA_CODE['%'] = 0x3F
for i, c in enumerate("0123456789"): DIA_CODE[c] = 0x40 + i


def encode(text):
    bad = sorted(set(text) - set(CODE))
    if bad:
        raise ValueError("unsupported field-name character(s) %r in %r" % (bad, text))
    return bytes(CODE[c] for c in text)


def encode_dialogue(text):
    bad = sorted(set(text) - set(DIA_CODE))
    if bad:
        raise ValueError("unsupported dialogue-name character(s) %r in %r" %
                         (bad, text))
    return bytes(DIA_CODE[c] for c in text)


def main():
    doc = json.load(open(SCRIPT, encoding="utf-8"))
    entries = doc["entries"] if isinstance(doc, dict) else doc
    widths = open(os.path.join(OUT, "menuwidth.bin"), "rb").read()
    os.makedirs(OUT, exist_ok=True)
    for segment, expected, filename in TABLES:
        rows = [e for e in entries if e.get("segment") == segment]
        if len(rows) != expected:
            raise SystemExit("%s has %d rows, expected %d" %
                             (segment, len(rows), expected))
        blob = bytearray()
        widest = (0, "")
        for e in rows:
            # Four unused item IDs are called NOTHING in the US table and
            # have no translation row.  Keep a safe visible sentinel if an
            # event ever reaches one accidentally, while preserving ordinals.
            text = (e.get("en") or "").strip() or "NOTHING"
            raw = encode(text)
            blob += raw + b"\xFE"
            if segment == "00:001":
                sentence = text + " is procured!"
                pixels = sum(widths[CODE[c]] for c in sentence)
                if pixels > 192:
                    raise SystemExit("%s is %dpx in the 192px field window: %s" %
                                     (e["id"], pixels, sentence))
                used = pixels
            else:
                sentence = text + " is used!"
                used = sum(widths[CODE[c]] for c in sentence)
                if used > 192:
                    raise SystemExit("%s is %dpx in the 192px field window: %s" %
                                     (e["id"], used, sentence))
            widest = max(widest, (used, sentence))
        open(os.path.join(OUT, filename), "wb").write(blob)
        unit = "px"
        print("%-20s %4d bytes, widest %d%s: %s" %
              (filename, len(blob), widest[0], unit, widest[1]))

    items = [e for e in entries if e.get("segment") == "00:001"]
    dialogue = bytearray()
    for e in items:
        text = (e.get("en") or "").strip() or "NOTHING"
        dialogue += encode_dialogue(text) + b"\xFF"
    path = os.path.join(OUT, "dialogueitemnames.bin")
    open(path, "wb").write(dialogue)
    print("%-20s %4d bytes" % ("dialogueitemnames.bin", len(dialogue)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
