"""Audit and conservatively reflow translated dialogue against the real VWF.

Page controls ($FD/$F5), portrait changes, actions and narration are structural
and are never moved.  Within a plain speech run, words are greedily packed to
256 pixels and explicit {BR}s are regenerated at word boundaries.  The module
also reports changes so a human can reject dramatic/intentional short lines.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH_PATH = os.path.join(ROOT, "ps4disasm", "vwf", "diawidth.bin")
TOKEN = re.compile(r"(\{[^}]+\})")
PAGE = {"{ctl.FD}", "{ctl.F5}"}
BR = "{BR}"
# The renderer advances/wraps as soon as the cursor reaches 256, so a
# translator-authored row must finish below that boundary.  255 is the true
# safe packing ceiling even though the window itself is 256 pixels wide.
LIMIT = 255
KEEP = "{intent.BR}"

# These are dramatic/staged breaks rather than remnants of the old fixed-width
# layout.  Keep the list deliberately small and phrase-specific: the rest of
# each entry can still benefit from VWF reflow.
INTENTIONAL_BREAKS = {
    "lz1CC476#0016": (
        "Hm? A new face.{BR}Gah!",
        "That's a nasty weapon!{BR}S-stay back!",
    ),
    "lz1CC476#0017": ("Aaah!{BR}Put that away, please!",),
    "lz1CC476#0042": ("Oh? A customer.{BR}A rare sight.",),
    "lz1CC476#0088": ("Ah, never mind!{BR}Talking to myself!",),
    "lz1CC476#0103": ("Eeek! I'm changing!{BR}Get out, get out!!",),
    "lz1CC476#0104": ("Still changing!{BR}Get out, get out!!",),
    "lz1CC476#0105": ("Even now I'm changing!{BR}Get out, get out!!",),
    "lz1CC476#0107": ("My head... it hurts...{BR}What... what is this...?",),
    "lz1CD2E6#0010": ("Someone go check.{BR}N-not me, I'm busy.",),
    "lz1CD2E6#0003": ("It's further northeast.{BR}But...",),
    "lz1CD2E6#0035": ("What are those odd machines?{BR}Terrifying!",),
    "lz1CD2E6#0037": ("All safe now?{BR}Really! Whew!",),
    "lz1CD2E6#0043": ("You did it.{BR}Thank you.",),
    "lz1CD2E6#0042": ("You again.{BR}I'm in your debt.",),
    "lz1CD2E6#0073": ("I'm allowed outside now.{BR}Hehe!",),
    "lz1CD2E6#0092": ("Zio is dead... truly?{BR}Ah, at last we're safe...!",),
    "lz1CD2E6#0094": ("I saw it...!{BR}Those machine men fly!",),
    "lz1CD2E6#0103": ("Oh? Hahn!{BR}What a place this is!!",),
    "lz1D4FB6#0016": ("Whoa!{BR}The penguin food is gone!",),
}

IDX = {" ": 0}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): IDX[c] = 1 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"): IDX[c] = 27 + i
for c, i in zip(".',·:!?", range(53, 60)): IDX[c] = i
IDX['-'] = 60; IDX['"'] = 61; IDX['%'] = 63
for i, c in enumerate("0123456789"): IDX[c] = 64 + i
WIDTH = open(WIDTH_PATH, "rb").read()


def px(text):
    return sum(WIDTH[IDX[c]] if c in IDX else 8 for c in text)


def wrap_plain(text):
    """Repack one uninterrupted speech run while retaining edge breaks.

    Controls split runs before this function is called.  Consequently a break
    immediately beside a portrait/action control remains structural, while old
    fixed-width breaks inside ordinary prose are free to move.
    """
    leading = text.startswith(BR)
    trailing = text.endswith(BR)
    plain = text.replace(BR, " ")
    plain = re.sub(r"\s+", " ", plain).strip()
    if not plain:
        return BR if leading or trailing else ""
    words = plain.split(" ")
    rows, row = [], ""
    for word in words:
        trial = word if not row else row + " " + word
        if row and px(trial) > LIMIT:
            rows.append(row); row = word
        else:
            row = trial
    if row: rows.append(row)
    wrapped = BR.join(rows)
    if leading:
        wrapped = BR + wrapped
    if trailing:
        wrapped += BR
    return wrapped


def reflow(text, entry_id=None):
    """Reflow speech runs; controls remain byte-for-byte and in order."""
    for phrase in INTENTIONAL_BREAKS.get(entry_id, ()):
        if phrase not in text:
            raise ValueError(f"intentional-break phrase missing in {entry_id}: {phrase}")
        text = text.replace(phrase, phrase.replace(BR, KEEP), 1)
    parts = TOKEN.split(text)
    out = []
    run = []

    def flush():
        if run:
            out.append(wrap_plain("".join(run)))
            run.clear()

    for part in parts:
        if not part:
            continue
        if part == BR:
            run.append(part)
        elif part.startswith("{"):
            flush()
            out.append(part)
        else:
            run.append(part)
    flush()
    s = "".join(out)
    s = s.replace(BR + BR, BR)
    return s.replace(KEEP, BR)


def visible_rows(text):
    """Return visible row widths per page, ignoring zero-width controls."""
    pages = re.split(r"\{ctl\.(?:FD|F5)(?::[^}]*)?\}", text)
    return [
        [px(TOKEN.sub("", row)) for row in page.split(BR)]
        for page in pages
    ]


def is_narration(e):
    if e.get("region") == 2 and "seg_start" not in e:
        return True
    if e.get("stream") == 0x1D4FB6:
        m = re.search(r"#(\d+)$", e.get("id", ""))
        return bool(m and 58 <= int(m.group(1)) <= 65)
    return False


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "work", "dialogue_full.json")
    doc = json.load(open(path, encoding="utf-8"))
    ents = doc["entries"] if isinstance(doc, dict) else doc
    if "--breaks" in sys.argv:
        for e in ents:
            old = (e.get("en") or "").strip()
            if not old or is_narration(e):
                continue
            for match in re.finditer(r"([^{}]{0,45})\{BR\}([^{}]{0,45})", old):
                left, right = match.group(1), match.group(2)
                print(f"{e['id']} [{px(left):3}/{px(right):3}] "
                      f"{left!r} -> {right!r}")
        return
    changes = []
    for e in ents:
        old = (e.get("en") or "").strip()
        if not old or is_narration(e):
            continue
        new = reflow(old, e.get("id"))
        if new != old:
            changes.append((e, old, new))
    if "--patch" in sys.argv:
        out_path = sys.argv[sys.argv.index("--patch") + 1]
        patch = {e["id"]: new for e, _old, new in changes}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(patch, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"wrote {len(patch)} reviewed reflow entries to {out_path}")
        return
    print(f"{len(changes)} translated dialogue entries would change")
    for e, old, new in changes:
        print("\n" + e["id"])
        print(" OLD", old)
        print(" NEW", new)
        print(" OLD", visible_rows(old))
        print(" NEW", visible_rows(new))


if __name__ == "__main__":
    main()
