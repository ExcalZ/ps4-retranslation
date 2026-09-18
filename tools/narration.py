"""Measure narration lines against the 256px wrap, and diff build vs drafts.

The narration engine (RunText2) wraps at 256 pixels.  Under the old fixed
font that was 32 characters; under the VWF it is closer to 40, and the
pre-Piata beats were written to a 16-character budget that no longer exists.
This reports what each line costs now and how much room it has left, so
wording can be iterated without a build.

Slots:
  attract mode  TitleText / TitleText2 in ps4.asm, $FF-terminated dc.b lines
  pre-Piata     dialogue 17.asm entries $3A-$3F, drawn through RunText2
                after DialogueTree17 is loaded at ps4.asm:150923

Usage:
  python tools/narration.py                 report the build's own lines
  python tools/narration.py <line> [...]    measure candidate wording
"""
import json, os, re, sys

LIMIT = 256
ASM = "ps4disasm/ps4.asm"
TREE17 = "ps4disasm/script/dialogue 17.asm"
WIDTHS = "ps4disasm/vwf/diawidth.bin"

W = open(WIDTHS, "rb").read()
CODE = {' ': 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): CODE[c] = 1 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): CODE[c] = 27 + i
for i, c in enumerate("0123456789"):                 CODE[c] = 64 + i
CODE['.'] = 0x35; CODE["'"] = 0x36; CODE[','] = 0x37; CODE[':'] = 0x39
CODE['!'] = 0x3A; CODE['?'] = 0x3B; CODE['-'] = 0x3C; CODE['%'] = 0x3F


def measure(s):
    """Return (pixels, [characters with no charset code])."""
    px, bad = 0, []
    for ch in s:
        c = CODE.get(ch)
        if c is None or c >= len(W):
            bad.append(ch)
            px += 8
        else:
            px += W[c]
    return px, bad


def build_lines():
    """The narration as it stands in the disassembly."""
    src = open(ASM, encoding="utf-8", errors="replace").read().split("\n")
    out = []
    i = next(i for i, l in enumerate(src) if l.startswith("TitleText:"))
    while i < len(src):
        l = src[i]
        if re.match(r"^[A-Za-z_]\w*:", l) and not l.startswith(("TitleText", "TitleText2")):
            break
        for m in re.finditer(r'"([^"]*)"', l):
            if m.group(1).strip():
                out.append(("attract", i + 1, m.group(1)))
        i += 1
    t = open(TREE17, encoding="utf-8", errors="replace").read().split("\n")
    spans, idx, start = {}, 0, 0
    for j, l in enumerate(t):
        if re.match(r"^\s*dc\.b\s+\$FF\s*$", l):
            spans[idx] = (start, j); idx += 1; start = j + 1
    for e in range(0x3A, 0x40):
        if e in spans:
            a, b = spans[e]
            for l in t[a:b + 1]:
                for m in re.finditer(r'"([^"]*)"', l):
                    if m.group(1).strip():
                        out.append(("piata $%02X" % e, a + 1, m.group(1)))
    return out


def source_map():
    """jp/en source text from the extraction, keyed by entry id."""
    out = {}
    for f in ("work/dialogue_full.json", "work/script_translated.json"):
        if not os.path.exists(f):
            continue
        d = json.load(open(f, encoding="utf-8"))
        ent = d["entries"] if isinstance(d, dict) and "entries" in d else d
        for x in ent:
            if isinstance(x, dict) and "id" in x:
                out[x["id"]] = (x.get("jp") or "", x.get("en") or "")
    return out


def sidebyside(path="work/narration_lines.txt"):
    """Write build line, draft line and source together, with widths."""
    src = source_map()
    drafts = {}
    for f in ("work/patch_narration.json", "work/patch_prologue.json"):
        if os.path.exists(f):
            d = json.load(open(f, encoding="utf-8"))
            drafts[f] = d["entries"] if isinstance(d, dict) and "entries" in d else d
    nl = chr(10)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("Narration, side by side.  Limit %d px." % LIMIT + nl)
        fh.write("BUILD = what ps4disasm ships.  DRAFT = your retranslation." + nl)
        fh.write("SOURCE = the extraction's jp field, where the id matches." + nl + nl)
        fh.write("== in the build ==" + nl)
        for slot, ln, text in build_lines():
            px, _ = measure(text)
            fh.write("%-11s %-7s %3dpx (+%2d chars)  %s"
                     % (slot, ln, px, (LIMIT - px) // 6.2, text) + nl)
        for f, d in drafts.items():
            fh.write(nl + "== %s ==" % f + nl)
            for k in sorted(d):
                jp, en = src.get(k, ("", ""))
                for line in str(d[k]).replace("{BR}", nl).split(nl):
                    line = re.sub(r"\{[^}]*\}", "", line).strip()
                    if not line:
                        continue
                    px, bad = measure(line)
                    fh.write("%-14s %3dpx (+%2d chars)%s  %s"
                             % (k, px, (LIMIT - px) // 6.2,
                                "  UNMAPPED " + "".join(sorted(set(bad))) if bad else "", line) + nl)
                if jp:
                    fh.write("%-14s %s %s" % ("", "SOURCE:", jp) + nl)
    print("wrote %s" % path)


def report(rows, title):
    print("\n%s" % title)
    print("  %-11s %-6s %4s %5s %6s  %s" % ("slot", "line", "px", "spare", "+chars", "flag"))
    worst = 0
    for slot, ln, s in rows:
        px, bad = measure(s)
        worst = max(worst, px)
        flag = "OVER" if px > LIMIT else ("unmapped %s" % "".join(sorted(set(bad))) if bad else "")
        print("  %-11s %-6s %4d %5d %6d  %s" % (slot, ln, px, LIMIT - px, (LIMIT - px) // 6.2, flag))
    print("  %d lines, widest %d px of %d" % (len(rows), worst, LIMIT))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--lines":
        sidebyside()
    elif len(sys.argv) > 1:
        report([("candidate", "-", a) for a in sys.argv[1:]], "candidate wording")
    else:
        rows = build_lines()
        report(rows, "narration as it stands in the build")
        drafts = {}
        for f in ("work/patch_narration.json", "work/patch_prologue.json"):
            if os.path.exists(f):
                d = json.load(open(f, encoding="utf-8"))
                drafts[f] = d["entries"] if isinstance(d, dict) and "entries" in d else d
        for f, d in drafts.items():
            rs = []
            for k, v in d.items():
                for line in str(v).replace("{BR}", "\n").split("\n"):
                    line = re.sub(r"\{[^}]*\}", "", line).strip()
                    if line:
                        rs.append((k.split("#")[0], k.split("#")[1], line))
            report(rs, "drafts: %s" % f)
