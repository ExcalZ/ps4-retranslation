"""Render a single-file, offline HTML patcher around a BPS patch.

    python tools/webpatch.py PATCH.bps OUT.html --title "Game: My Hack" \
        [--game "Game (USA)"] [--subtitle "v1.0"] [--out-name "Game - My Hack v1.0"]
        [--template release/patcher_template.html]

The page runs entirely in the player's browser from a local file: drop a ROM
on it, it verifies the source CRC32 the patch carries, applies the patch and
offers the result for saving.  Mega Drive specifics it handles for you:
interleaved .smd dumps are detected by structure (not by header bytes, which
vary between dumpers) and deinterleaved before patching, and the result can
be saved as a plain .bin or re-interleaved as .smd.

Why this exists rather than "use Flips": Flips cannot convert .smd, and a
BPS made against an .smd source is either huge (interleaving defeats the
delta encoder against a plain target) or produces an .smd whose header block
count overflows a byte above 4 MB.  Doing the conversion in the page keeps
one canonical patch.

The expected source size and CRC32 come from the patch itself.  Everything
else is a @TOKEN@ in the template; see TOKENS for what a caller may set.
"""
import base64
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bps

# In this repository the template lives in release/; an exported copy
# (tools/export_mdtools.py) keeps it beside this script.
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = next((p for p in (
    os.path.join(os.path.dirname(_HERE), "release", "patcher_template.html"),
    os.path.join(_HERE, "patcher_template.html")) if os.path.exists(p)),
    os.path.join(_HERE, "patcher_template.html"))

# Caller-settable tokens and what the page uses them for.
TOKENS = {
    "TITLE": "page heading and browser tab",
    "SUBTITLE": "line under the heading (version, language...)",
    "GAME": "how the expected ROM is named in the drop zone and error text",
    "PATCH": "file name of the .bps shipped beside the page, for the footnote",
    "OUT_NAME": "saved file name without extension (.bin / .smd is appended)",
    "README_NOTE": "optional sentence appended to the footnote (may be empty)",
    "HINT": "optional sentence appended to the wrong-ROM error (may be empty)",
}


def render_patcher(patch: bytes, out_path: str, template: str = DEFAULT_TEMPLATE,
                   tokens: dict | None = None) -> None:
    hdr = bps.info(patch)
    values = {"README_NOTE": "", "HINT": "", "PATCH": "the .bps file"}
    values.update(tokens or {})
    values.setdefault("SUBTITLE", "")
    values.setdefault("GAME", "the original")
    values["PATCH_B64"] = base64.b64encode(patch).decode("ascii")
    values["SRC_CRC32"] = "%08X" % hdr["source_crc"]
    values["SRC_SIZE"] = "{:,}".format(hdr["source_size"])
    text = open(template, encoding="utf-8").read()
    for k, v in values.items():
        text = text.replace("@%s@" % k, v)
    left = sorted(set(re.findall(r"@[A-Z][A-Z0-9_]*@", text)))
    if left:
        raise SystemExit("%s: unfilled token(s): %s" % (os.path.basename(template), ", ".join(left)))
    open(out_path, "w", encoding="utf-8", newline="\n").write(text)


def main(argv):
    if len(argv) < 2 or argv[0].startswith("-"):
        sys.exit(__doc__)
    patch_path, out_path = argv[0], argv[1]

    def opt(name, default=None):
        flag = "--" + name
        return argv[argv.index(flag) + 1] if flag in argv else default

    stem = os.path.splitext(os.path.basename(patch_path))[0]
    tokens = {
        "TITLE": opt("title", stem),
        "SUBTITLE": opt("subtitle", ""),
        "GAME": opt("game", "the original"),
        "PATCH": os.path.basename(patch_path),
        "OUT_NAME": opt("out-name", stem),
    }
    patch = open(patch_path, "rb").read()
    render_patcher(patch, out_path, opt("template", DEFAULT_TEMPLATE), tokens)
    hdr = bps.info(patch)
    print("%s: %d bytes; expects a %s-byte source with CRC32 %08X"
          % (out_path, os.path.getsize(out_path), "{:,}".format(hdr["source_size"]), hdr["source_crc"]))


if __name__ == "__main__":
    main(sys.argv[1:])
