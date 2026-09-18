"""Extract / reinsert the PS4 script as an editable JSON file.

Addressing model (established by disassembly, see docs/devlog.md):

  There is no single pointer table for text. The lookup at $05CCB6 takes a
  base in a0 and an index in d0 and counts $FE terminators forward. Other
  regions are addressed by direct hardcoded pointers, sometimes on a fixed
  16-byte stride.

  Both are handled the same way: every address that executable code points
  at is treated as a fixed anchor. Messages between two anchors may be
  resized freely as long as the span keeps its byte count and its terminator
  count. A fixed-stride region simply yields fixed-size segments, which
  enforces the record width automatically.
"""
import json
import regions as regmod
from table import Table

TERM = 0xFE


def extract(rom: bytes, tbl: Table):
    entries = []
    for ri, lo, hi, term, anchors in regmod.build(rom):
        for si, (s, e) in enumerate(regmod.segments_for(anchors, hi)):
            i, idx = s, 0
            while i < e:
                j = rom.find(bytes([term]), i, e)
                if j < 0:
                    break          # trailing bytes with no terminator
                raw = rom[i:j]
                entries.append({
                    "id":        f"r{ri:02d}s{si:03d}#{idx:03d}",
                    "region":    ri,
                    "segment":   f"{ri:02d}:{si:03d}",
                    "seg_start": s,
                    "seg_end":   e,
                    "offset":    i,
                    "term":      term,
                    "raw_len":   (j + 1) - i,
                    "hex":       raw.hex(),
                    "jp":        tbl.decode_str(raw),
                    "en":        "",
                    "note":      "",
                })
                idx += 1
                i = j + 1
    return entries


def save(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 3, "entries": entries}, f,
                  ensure_ascii=False, indent=2)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["entries"]


def _groups(entries):
    g = {}
    for e in entries:
        g.setdefault(e["segment"], []).append(e)
    return g


def plan(entries, tbl: Table):
    rows, probs = [], []
    for seg, ents in sorted(_groups(entries).items()):
        s, e = ents[0]["seg_start"], ents[0]["seg_end"]
        capacity = e - s
        used = 0
        for ent in ents:
            text = ent.get("en", "").strip()
            if not text:
                used += ent["raw_len"]
                continue
            try:
                used += len(tbl.encode(text)) + 1
            except KeyError as ex:
                probs.append(f'{ent["id"]}: {ex}')
                used += ent["raw_len"]
        rows.append({"segment": seg, "start": s, "end": e,
                     "capacity": capacity, "used": used,
                     "free": capacity - used, "count": len(ents)})
        if used > capacity:
            probs.append(f"segment {seg} ({s:06X}-{e:06X}): "
                         f"{used} bytes needed, {capacity} available")
    return rows, probs


def reinsert(rom: bytes, entries, tbl: Table, strict=True):
    rows, probs = plan(entries, tbl)
    if probs and strict:
        raise ValueError("; ".join(probs))
    out = bytearray(rom)
    report = {"written": 0, "kept": 0, "problems": list(probs), "segments": rows}
    for seg, ents in sorted(_groups(entries).items()):
        s, e = ents[0]["seg_start"], ents[0]["seg_end"]
        buf = bytearray()
        for ent in ents:
            text = ent.get("en", "").strip()
            enc = None
            if text:
                try:
                    enc = tbl.encode(text)
                except KeyError:
                    enc = None
            if enc is None:
                enc = bytes.fromhex(ent["hex"])
                report["kept"] += 1
            else:
                report["written"] += 1
            buf += enc + bytes([ent.get("term", TERM)])
        if len(buf) > e - s:
            report["problems"].append(
                f"segment {seg} left unmodified (needs {len(buf)}, has {e-s})")
            continue
        # Reuse the original dead space after the segment's last terminator so
        # an untouched segment reproduces the ROM exactly, then zero-fill.
        # Never copy live message bytes: a stray $FE shifts every later index.
        orig = rom[s:e]
        last = orig.rfind(bytes([ents[0].get("term", TERM)]))
        dead = orig[last + 1:] if last >= 0 else b""
        buf += dead[:max(0, (e - s) - len(buf))]
        buf += bytes((e - s) - len(buf))
        out[s:e] = buf
    return bytes(out), report
