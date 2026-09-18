"""Find VWF dialogue pages separated by unnecessary $FD waits.

This is deliberately an audit, not an automatic rewrite.  A candidate is only
reported when two adjacent prose pages can be repacked into one two-row page.
Speaker portraits, event actions, delays, conditional prompts, and narration
exclude a boundary; dramatic pacing still requires contextual review.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dialogue_reflow as dr
import trpatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = "{ctl.FD}"
PAGE_SPLIT = re.compile(r"(\{ctl\.(?:FD|F5)(?::[^}]*)?\})")
TOKEN_BODY = re.compile(r"\{([^}]+)\}")

# Contextually reviewed waits which only reflect the former fixed-width page
# budget.  Store the exact text around each boundary so a later wording change
# fails loudly instead of removing an unrelated wait by ordinal.
REVIEWED_MERGES = {
    "lz1CC476#0000": ("hunter?{ctl.FD}Please",),
    "lz1CC476#0020": ("birth rate...{ctl.FD}Hard",),
    "lz1CC476#0021": ("birth rate...{ctl.FD}Hard",),
    "lz1CC476#0022": ("birth rate...{ctl.FD}Hard",),
    "lz1CC476#0028": ("very back.{ctl.FD}He's",),
    "lz1CC476#0031": ("and the{ctl.FD}monsters",),
    "lz1CC476#0032": ("and the{ctl.FD}monsters",),
    "lz1CC476#0036": ("planets,{ctl.FD}but",),
    "lz1CC476#0042": ("inn{ctl.FD}does",),
    "lz1CC476#0044": ("night with{ctl.FD}those",),
    "lz1CC476#0067": ("town any more.{ctl.FD}What",),
    "lz1CC476#0073": ("do with the{ctl.FD}monsters",),
    "lz1CC476#0077": ("I study geology.{ctl.FD}The soil",),
    "lz1CC476#0079": ("Mile are{ctl.FD}running",),
    "lz1CC476#0087": ("Motavia Academy.{ctl.FD}Me?",),
    "lz1CC476#0091": ("its{ctl.FD}good name",),
    "lz1CC476#0093": ("written a page.{ctl.FD}Oh",),
    "lz1CC476#0096": ("it, I{ctl.FD}haven't",),
    "lz1CC476#0100": ("come home.{ctl.FD}What",),
    "lz1CC476#0101": ("time she was{ctl.FD}gone",),
    "lz1CC476#0106": ("all this time?{ctl.FD}When",),
    "lz1CC476#0108": (
        "still no{ctl.FD}sign",
        "children. The{ctl.FD}responsibility",
        "word gets{ctl.FD}out!",
    ),
    "lz1CC476#0109": ("lost Laila.{ctl.FD}I'd better",),
    "lz1CD2E6#0001": ("outside?{ctl.FD}It keeps",),
    "lz1CD2E6#0004": ("in Zema.{ctl.FD}The ones",),
    "lz1CD2E6#0005": ("spreading?{ctl.FD}A man",),
    "lz1CD2E6#0006": ("lately.{ctl.FD}Young",),
    "lz1CD2E6#0007": ("sand...{ctl.FD}I'd swear",),
    "lz1CD2E6#0008": ("sand...{ctl.FD}Up overnight",),
    "lz1CD2E6#0011": ("lives!!!!{ctl.FD}That one's",),
    "lz1CD2E6#0012": ("bad harvests{ctl.FD}mean",),
    "lz1CD2E6#0014": ("Don't{ctl.FD}bother",),
    "lz1CD2E6#0016": ("farm, but...{ctl.FD}with",),
    "lz1CD2E6#0018": ("ranch, but...{ctl.FD}overfed",),
    "lz1CD2E6#0027": ("village.{ctl.FD}Too late",),
    "lz1CD2E6#0028": ("helps{ctl.FD}the family",),
    "lz1CD2E6#0031": ("the inn{ctl.FD}together",),
    "lz1CD2E6#0032": ("guild hunters?{ctl.FD}The worms",),
    "lz1CD2E6#0036": ("face...{ctl.FD}Ah, it's",),
    "lz1CD2E6#0041": ("roam...{ctl.FD}but machines",),
    "lz1CD2E6#0051": ("about...{ctl.FD}I've",),
    "lz1CD2E6#0053": ("Birth Valley.{ctl.FD}They call",),
    "lz1CD2E6#0054": ("but...{ctl.FD}the silence",),
    "lz1CD2E6#0062": ("This is Zema.{ctl.FD}Birth Valley",),
    "lz1CD2E6#0063": ("This is Zema.{ctl.FD}Birth Valley",),
    "lz1CD2E6#0064": ("This is Zema.{ctl.FD}Strange",),
    "lz1CD2E6#0065": ("This is Zema.{ctl.FD}A safe",),
    "lz1CD2E6#0066": ("Stranded,{ctl.FD}surely",),
    "lz1CD2E6#0067": ("bridge is fixed?{ctl.FD}Then",),
    "lz1CD2E6#0068": ("now these{ctl.FD}strange",),
    "lz1CD2E6#0071": ("right?{ctl.FD}I'd love",),
    "lz1CD2E6#0074": ("Life...{ctl.FD}Why it",),
    "lz1CD2E6#0075": ("something must{ctl.FD}be done",),
    "lz1CD2E6#0077": ("machines.{ctl.FD}I'm counting",),
    "lz1CD2E6#0093": ("won't{ctl.FD}settle?",),
    "lz1CD2E6#0096": ("black.{ctl.FD}When",),
    "lz1CD2E6#0097": ("people!{ctl.FD}Nothing",),
    "lz1CD2E6#0103": (
        "Eh? Did he?{ctl.FD}I'm hale",
        "never mind!{ctl.FD}Right!",
    ),
    "lz1CD2E6#0108": (
        "prowling{ctl.FD}the village",
        "it seems.{ctl.FD}They harm",
    ),
    "lz1CD2E6#0109": ("behind them...!{ctl.FD}Indeed",),
    "lz1D4FB6#0008": ("did you hear?{ctl.FD}They say",),
    "lz1D4FB6#0010": ("did you hear?{ctl.FD}The Parmanian",),
    "lz1D4FB6#0055": (
        "hunter. Put your{ctl.FD}back into it!",
        "of Laila{ctl.FD}herself!",
        "herself!{ctl.FD}Come on",
    ),
    "lz1D4FB6#0056": ("'just come'.{ctl.FD}We'll",),
}

REVIEWED_WORDING = {
    # 大崩壊, consistently distinguished from an ordinary collapse.
    "lz1CC476#0036": (("the Collapse", "the Great Collapse"),),
}


def visible(text):
    return re.sub(r"\s+", " ", dr.TOKEN.sub("", text).replace(dr.BR, " ")).strip()


def prose_only(text, allow_leading_portrait=False):
    """Allow guards and, on the left page, an already-active portrait."""
    if allow_leading_portrait:
        text = re.sub(r"^(?:(?:\{ctl\.FA(?::[^}]*)?\})|(?:\{ctl\.F4(?::[^}]*)?\}))*", "", text)
    for body in TOKEN_BODY.findall(text):
        name = body.split(":", 1)[0]
        if name == "BR" or name == "ctl.FA":
            continue
        return False
    return True


def candidates(entry):
    text = (entry.get("en") or "").strip()
    if not text or dr.is_narration(entry):
        return []
    parts = PAGE_SPLIT.split(text)
    out, ordinal = [], 0
    for i in range(1, len(parts), 2):
        ctl = parts[i]
        if ctl != FD:
            continue
        ordinal += 1
        left, right = parts[i - 1], parts[i + 1]
        if not visible(left) or not visible(right):
            continue
        if not prose_only(left, allow_leading_portrait=True) or not prose_only(right):
            continue
        trial_parts = list(parts)
        # $FD separates visible prose without carrying a printable space. Once
        # removed, restore the word/sentence boundary before rewrapping.
        trial_parts[i] = " "
        trial = dr.reflow("".join(trial_parts), entry.get("id"))
        if trpatch.check_line(entry, trial):
            continue
        # Locate the newly joined page by counting remaining page controls
        # before this boundary.  It must render in no more than two rows.
        page_index = sum(1 for p in parts[1:i:2] if p in (FD, "{ctl.F5}"))
        widths = dr.visible_rows(trial)[page_index]
        if len(widths) > 2 or max(widths, default=0) > dr.LIMIT:
            continue
        out.append({
            "ordinal": ordinal,
            "left": visible(left),
            "right": visible(right),
            "widths": widths,
            "trial": trial,
        })
    return out


def apply_reviewed(entry):
    text = (entry.get("en") or "").strip()
    for old, new in REVIEWED_WORDING.get(entry.get("id"), ()):
        if old not in text:
            continue
        text = text.replace(old, new, 1)
    for boundary in REVIEWED_MERGES.get(entry.get("id"), ()):
        if boundary not in text:
            # Historical reviewed boundaries are retained here as policy and
            # audit documentation after they have been applied.
            continue
        text = text.replace(boundary, boundary.replace(FD, " "), 1)
    return dr.reflow(text, entry.get("id"))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "work", "dialogue_full.json")
    entries = json.load(open(path, encoding="utf-8"))["entries"]
    if "--reviewed-patch" in sys.argv:
        out_path = sys.argv[sys.argv.index("--reviewed-patch") + 1]
        patch = {}
        for entry in entries:
            if entry.get("id") not in REVIEWED_MERGES and entry.get("id") not in REVIEWED_WORDING:
                continue
            new = apply_reviewed(entry)
            if new != (entry.get("en") or "").strip():
                patch[entry["id"]] = new
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(patch, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"wrote {len(patch)} reviewed page-merge entries to {out_path}")
        return
    found = []
    for entry in entries:
        for candidate in candidates(entry):
            found.append((entry, candidate))
    print(f"{len(found)} safe-shape page-wait candidate(s); contextual review required")
    for entry, c in found:
        print(f"\n{entry['id']} FD#{c['ordinal']} -> {c['widths']}")
        print(" LEFT ", c["left"])
        print(" RIGHT", c["right"])
        print(" NEW  ", c["trial"])


if __name__ == "__main__":
    main()
