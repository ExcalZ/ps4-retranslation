"""Report every mid-page portrait change, quoted so the scene is recognisable.

A `{ctl.F4}` that lands after text with no `{ctl.FD}` / `{ctl.F5}` / `{ctl.F7}` /
`{ctl.FC}` since swaps the portrait while the current line is still on screen.
Sometimes that is the point -- a reaction shot, or an unattended scene. Sometimes
it just makes the speaker unreadable, which is what happens when the Academy
Principal is still talking under Laila's face.

`{ctl.FD}` is a LAYOUT token, so its placement is ours: every one of these can be
turned into a clean page break by putting `{ctl.FD}` before the `{ctl.F4}`, and
every break we added can be undone by removing one.

Each entry quotes the text that is on screen at the moment of the swap, so the
scene can be placed without loading the ROM.

    python tools/midpage.py                 print the report
    python tools/midpage.py --write PATH    write it as markdown
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trpatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PORTRAITS = {
    "00": "the Elsydeon voices", "01": "Rudy", "02": "Laila", "03": "Hahn",
    "04": "Thray", "05": "Pyke", "06": "Fal", "07": "Frena", "08": "Forren",
    "09": "Raja", "0A": "Shess", "0B": "Siam", "0C": "Saya",
    "0D": "the academy elder", "0E": "the Principal", "0F": "Dorin",
    "10": "Pana", "11": "the Guild clerk", "17": "the esper gatekeeper",
    "19": "the esper elder", "1A": "a Gungbius priest", "21": "a Gallberg envoy",
    "22": "Laila (stricken)", "23": "the Anger Tower voice", "24": "the lost Piata girl",
    "25": "Tallas", "26": "the sick boy of Torinco", "27": "Sekreas",
}

SCENES = {
    0x1CC476: "Piata and Motavia Academy", 0x1CD2E6: "the Academy, Birth Valley",
    0x1CE546: "Krup village", 0x1CF6D6: "Molcum and Tonoe",
    0x1D02D6: "Nalya, and Kadary", 0x1D1256: "Aiedo", 0x1D2426: "Monsen and Termi",
    0x1D38E6: "Tyler, and the Landeel", 0x1D4446: "Ryuon",
    0x1D4FB6: "Meese, the Valley of Wonders", 0x1D5A26: "Richelle and the Meese ward",
    0x1D6816: "the Esper Mansion", 0x1D76C6: "Jut", 0x1D85A6: "Uzo and Torinco",
    0x1D9436: "the Hunters Guild", 0x1DA026: "Motavia examine-text",
    0x1DB036: "Dezolis examine-text", 0x1DB6F6: "Party Talk",
    0x1DC4E6: "the Academy, after Birth Valley", 0x1DD086: "the Bio-plant, Ladea Tower",
    0x1DDD96: "Zelan and Kuran", 0x1DEC96: "Gungbius Grand Temple",
    0x1DFCB6: "choosing a companion; Ryucross", 0x1E05B6: "the Rykros towers",
    0x1E1316: "THE ENDING", 0x1E1F06: "the weapons plant",
}

PAGE_BREAKS = trpatch.PAGE_BREAKS


def who(op):
    return PORTRAITS.get((op or "").upper(), "portrait $%s" % op)


def occurrences(text):
    """[(page text so far, operand, text after, F4 ordinal)] per mid-page F4.

    The ordinal counts {ctl.F4} tokens from the start of the message.  Engine
    token order is identical between the JP and our English, so the ordinal is
    what lets a JP occurrence be quoted from the English at the same beat.
    """
    out, pos, page, nth = [], 0, "", 0
    for m in trpatch.TOK.finditer(text or ""):
        name = m.group(1).split(":")[0]
        page += text[pos:m.start()]
        if name == "ctl.F4":
            if page.strip():
                after = text[m.end():]
                nxt = trpatch.TOK.search(after)
                if nxt:
                    after = after[:nxt.start()]
                out.append((page.strip(), m.group(1).partition(":")[2],
                            after.strip(), nth))
            page = ""
            nth += 1
        elif name in PAGE_BREAKS:
            page = ""
        pos = m.end()
    return out


def at_ordinal(text, nth):
    """(what the previous speaker says, what the new one says) at the nth F4.

    Deliberately spans page breaks: in our English we have usually inserted a
    {ctl.FD} right before this {ctl.F4}, so the *page* before it is empty and
    quoting that would show nothing.  What identifies the scene is the outgoing
    speaker's line, so accumulate from the previous {ctl.F4} instead.
    """
    text = text or ""
    start, i = 0, 0
    for m in trpatch.TOK.finditer(text):
        if m.group(1).split(":")[0] != "ctl.F4":
            continue
        if i == nth:
            after = text[m.end():]
            stop = None
            for k in trpatch.TOK.finditer(after):
                if k.group(1).split(":")[0] == "ctl.F4":
                    stop = k.start()
                    break
            return text[start:m.start()], after if stop is None else after[:stop]
        start = m.end()
        i += 1
    return "", ""


def tidy(t, limit=150):
    """Readable prose from raw script text: layout becomes " / ", controls go."""
    t = t or ""
    for tok in ("{BR}", "{ctl.FC}", "{ctl.FD}", "{ctl.F5}", "{ctl.F7}"):
        t = t.replace(tok, " / ")
    t = trpatch.TOK.sub("", t)
    t = " ".join(t.split()).strip(" /").strip()
    return t if len(t) <= limit else t[:limit].rstrip() + "..."


def report():
    doc = trpatch.load(os.path.join(ROOT, "work", "dialogue_full.json"))
    live, broke, untranslated = [], [], []
    for e in doc["entries"]:
        jp = occurrences(e.get("jp") or "")
        en = (e.get("en") or "").strip()
        hits = occurrences(en) if en else []
        if hits:
            live.append((e, hits))
        elif en and jp:
            broke.append((e, jp))
        elif jp:
            untranslated.append((e, jp))

    o = io.StringIO()
    w = o.write
    w("# Mid-page portrait changes\n\n")
    w("A `{ctl.F4}` landing after text with no `{ctl.FD}` / `{ctl.F5}` / `{ctl.F7}` /\n")
    w("`{ctl.FC}` since swaps the portrait **while the current line is still on\n")
    w("screen**. `{ctl.FD}` is a layout token, so every one of these is ours to\n")
    w("change in either direction.\n\n")
    w("| | messages | changes |\n|---|---|---|\n")
    for label, group in (("**A. Live in our English**", live),
                         ("**B. JP runs on; we break the page**", broke),
                         ("**C. Row not translated**", untranslated)):
        w("| %s | %d | %d |\n" % (label, len(group), sum(len(h) for _, h in group)))

    w("\n---\n\n## A. Live in our English now\n\n")
    w("A player hits these today. The quote is what is on screen at the moment\n")
    w("the portrait changes.\n\n")
    if not live:
        w("None.\n\n")
    for e, hits in live:
        w("### `%s` -- %s\n\n" % (e["id"], SCENES.get(e.get("stream"), "?")))
        for before, op, after, _nth in hits:
            w("> %s\n>\n" % tidy(before))
            w("> *-- portrait swaps to **%s** here --*\n>\n" % who(op))
            w("> %s\n\n" % (tidy(after) or "*(next control follows immediately)*"))
        w("JP does this too: **%s**\n\n"
          % ("yes" if occurrences(e.get("jp") or "") else "NO -- we introduced it"))

    w("---\n\n## B. The JP runs on; our English breaks the page\n\n")
    w("The judgment calls. Restoring one means deleting the `{ctl.FD}` we added\n")
    w("before that `{ctl.F4}`. The quote is our English around the same beat.\n\n")
    for e, hits in broke:
        w("### `%s` -- %s\n\n" % (e["id"], SCENES.get(e.get("stream"), "?")))
        for before, op, after, nth in hits:
            eb, ea = at_ordinal(e.get("en") or "", nth)
            w("> %s\n>\n" % (tidy(eb, 130) or "*(page opens here)*"))
            w("> *-- JP swaps to **%s** here with no prompt; we break the page --*\n>\n"
              % who(op))
            w("> %s\n\n" % (tidy(ea, 110) or "*(next control follows)*"))

    w("---\n\n## C. Rows we have not translated\n\n")
    w("Blocked pairings and blank slots. Listed so the set is complete; the US\n")
    w("text is quoted where there is any, to place the scene.\n\n")
    for e, hits in untranslated:
        us = (e.get("us") or "").strip()
        w("- `%s` (%s) -- %s\n"
          % (e["id"], SCENES.get(e.get("stream"), "?"),
             ", ".join("to **%s**" % who(op) for _, op, _, _ in hits)))
        if us:
            w("  > US: %s\n" % tidy(us, 130))
    w("\n")
    return o.getvalue()


def main():
    text = report()
    if "--write" in sys.argv:
        path = sys.argv[sys.argv.index("--write") + 1]
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        print("wrote %s (%d bytes)" % (path, len(text)))
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
