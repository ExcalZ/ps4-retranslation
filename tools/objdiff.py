"""Compare every battle object between the JP ROM and the US build.

    python tools/objdiff.py            (report to stdout, a few minutes)

Pairs objects by (group, index) through the nine dispatch tables (the
`subi.w #base,d0 / lea table,a0 / movea.l (a0,d0.w),a0 / jsr (a0)` chain
at loc_366DE..), runs BlastEm's dis.exe -o on both ROMs - following the
`jmp (d8,pc,d0.w)` phase dispatches that dis.exe stops at - normalises ROM
addresses, pc displacements and branch targets, and prints a unified diff
for every object whose instruction stream differs, plus which of them
carry the tech-sealed check (`btst #4,$16(a1)`).

Written for the Soldier Fiend Giresta fix (work/STATUS.md 2026-09-13): of
577 objects, 15 differ; of the 36 with a sealed check only $378 (Soldier
Fiend Giresta, the missing snapshot clears) and $2F8 (a moved sound
effect) do.  Compares against work/ps4us_bugfix.bin, so `bugfixes` blocks
show up as differences too.
"""
import os, re, struct, subprocess, sys, difflib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DIS = r"blastem-win32-0.6.2\dis.exe"
JP, US = "work/rom.bin", "work/ps4us_bugfix.bin"

def tables(path):
    d = open(path, "rb").read()
    out = {}
    for m in re.finditer(rb"\x04\x40(..)\x41\xF9(....)\x20\x70\x00\x00\x4E\x90", d):
        base = struct.unpack(">H", m.group(1))[0]
        out[base] = struct.unpack(">I", m.group(2))[0]
    m = re.search(rb"\x0C\x40\x00\x40\x6C.\x41\xF9(....)\x20\x70\x00\x00\x4E\x90", d)
    out[0] = struct.unpack(">I", m.group(1))[0]
    return d, out

jp, jpt = tables(JP)
us, ust = tables(US)
bounds = sorted(jpt) + [0x8C0 + 0x200]
assert sorted(jpt) == sorted(ust)

def entry(d, table, i):
    return struct.unpack(">I", d[table + i*4: table + i*4 + 4])[0]

pairs = []
for gi, base in enumerate(sorted(jpt)):
    end = bounds[gi + 1]
    n = (end - base) // 4
    for i in range(n):
        a, b = entry(jp, jpt[base], i), entry(us, ust[base], i)
        if not (0x200 <= a < 0x300000 and 0x200 <= b < 0x300000):
            break
        pairs.append((base + i*4, a, b))

cache = {}
def dis_one(path, addr):
    try:
        return subprocess.run([DIS, path, "-o", "0x%X" % addr], capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""

def dis(path, addr):
    """dis.exe -o follows jsr/bra/bcc but not `jmp (d8,pc,d0.w)`; the game
    dispatches object phases through those onto a table of bra.w.  Follow
    them: every bra.w after such a jmp is another start address."""
    key = (path, addr)
    if key in cache:
        return cache[key]
    d = jp if path == JP else us
    seen = {}
    work = [addr]
    while work:
        a = work.pop()
        if a in seen or not (0x200 <= a < len(d)):
            continue
        text = dis_one(path, a)
        seen[a] = text
        for ln in text.splitlines():
            m = re.match(r"([0-9A-F]+): jmp \((-?\d+), pc, d\d\.w\)", ln)
            if m:
                base = int(m.group(1), 16) + 2 + int(m.group(2))
                t = base
                while d[t] == 0x60 and d[t+1] == 0x00:          # bra.w
                    work.append(t + 2 + struct.unpack(">h", d[t+2:t+4])[0])
                    t += 4
    lines = {}
    for text in seen.values():
        for ln in text.splitlines():
            if ":" in ln:
                lines[int(ln.split(":")[0], 16)] = ln
    cache[key] = "\n".join(lines[k] for k in sorted(lines))
    return cache[key]

def norm(text):
    lines = []
    for ln in text.splitlines():
        if ":" not in ln: continue
        addr, ins = ln.split(":", 1)
        ins = ins.strip()
        ins = re.sub(r"<[0-9A-F]+>", "", ins)
        ins = re.sub(r"#-?\d+ $", "#d", ins)                       # branch disp
        ins = re.sub(r"\(-?\d+, pc\)", "(pc)", ins)
        ins = re.sub(r"\$([0-9A-F]{4,6})\b", lambda m: "$ROM" if int(m.group(1),16) < 0x400000 else "$"+m.group(1), ins)
        lines.append((int(addr, 16), ins.strip()))
    return lines

report = []
for idx, a, b in pairs:
    la, lb = norm(dis(JP, a)), norm(dis(US, b))
    sa = [x[1] for x in la]; sb = [x[1] for x in lb]
    sealed = any("btst.b #4, (22, a1)" in x for x in sa)
    if sa != sb:
        diff = [l for l in difflib.unified_diff(sa, sb, lineterm="", n=1) if not l.startswith(("---", "+++"))]
        report.append((idx, a, b, sealed, len(sa), len(sb), diff))
    elif sealed:
        report.append((idx, a, b, sealed, len(sa), len(sb), None))

print("%d objects paired; %d differ" % (len(pairs), sum(1 for r in report if r[6])))
for idx, a, b, sealed, na, nb, diff in report:
    if diff is None:
        continue
    print("\n=== obj $%03X  JP %06X  US %06X  %s  (%d vs %d lines)" % (idx, a, b, "SEALED-CHECK" if sealed else "", na, nb))
    for l in diff[:60]:
        print("   " + l)
    if len(diff) > 60: print("   ... %d more" % (len(diff) - 60))
print("\nsealed-check objects that match:", ["$%03X" % r[0] for r in report if r[6] is None])
