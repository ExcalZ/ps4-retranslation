#!/usr/bin/env python3
"""Generate and assemble the English source build without JP-ROM patching.

Usage:
    python tools/sourcebuild.py [output.bin]

The newer disassembly stores dialogue uncompressed and assembles both VWF
engines directly.  This is intentionally separate from ps4tool's legacy ROM
patch pipeline: its absolute JP addresses overlap live code and title assets
in the source layout.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DISASM = ROOT / "ps4disasm"


def run(args: list[str], cwd: Path = ROOT) -> None:
    shown = " ".join(args)
    print(f"\n> {shown}")
    subprocess.run(args, cwd=cwd, check=True)


def require_source_options() -> None:
    options = (DISASM / "ps4.options.asm").read_text(encoding="utf-8")
    needed = ("dialogue_uncompressed = 1", "vwf_menu = 1")
    missing = [line for line in needed if line not in options]
    if missing:
        raise SystemExit("source-build options are not enabled: "
                         + ", ".join(missing))
    # Both settings build: 1 draws names from prerendered strips, 0 composes
    # their translated text through the pool (see work/plan-strips-vs-
    # composition.md).  Say which, so a measurement build is never mistaken
    # for the shipping one.
    m = re.search(r"^vwf_menu_strips\s*=\s*([01])", options, re.M)
    if not m:
        raise SystemExit("vwf_menu_strips must be set to 0 or 1")
    print("vwf_menu_strips = %s (%s)" % (m.group(1),
          "prerendered strips" if m.group(1) == "1" else "composed names"))
    # The experimental flags (work/STATUS.md, 2026-09-15): both 0 is the
    # shipping ROM, both 1 is work/ps4en_exp.bin.  Say which this is.
    for flag in ("vwf_menu_hash", "vwf_menu_chrome"):
        m = re.search(r"^%s\s*=\s*([01])" % flag, options, re.M)
        print("%s = %s" % (flag, m.group(1) if m else "?"))


def main() -> int:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "ps4en.bin"
    require_source_options()

    # A fresh clone has neither ps4built.bin nor ps4.lst: both are build
    # products and ignored by git.  menustrip.py reads the built ROM and
    # checkbuild.py pins its anchors off the listing, so assemble once first.
    # (checkbuild always reads the PREVIOUS listing: after a build that broke
    # an anchor, one plain build.bat is needed before this passes again.)
    if not (DISASM / "ps4built.bin").exists() or not (DISASM / "ps4.lst").exists():
        print("no previous build: assembling once to produce ps4built.bin and ps4.lst")
        run(["cmd", "/c", str(DISASM / "build.bat")], DISASM)

    run([sys.executable, str(TOOLS / "treeport.py"), "--write"])
    run([sys.executable, str(TOOLS / "test_treeport_controls.py")])
    run([sys.executable, str(TOOLS / "titleport.py"), "--write"])
    run([sys.executable, str(TOOLS / "itemdesc.py"), "--write"])
    run([sys.executable, str(TOOLS / "soundtest.py"), "--write"])
    run([sys.executable, str(TOOLS / "shoptext.py"), "--write"])
    run([sys.executable, str(TOOLS / "examinecredits.py"), "--write"])
    run([sys.executable, str(TOOLS / "spacenames.py"), "--write"])
    run([sys.executable, str(TOOLS / "enemynames.py"), "--write"])
    run([sys.executable, str(TOOLS / "combonames.py"), "--write"])
    run([sys.executable, str(TOOLS / "guildnames.py"), "--write"])
    run([sys.executable, str(TOOLS / "spacemenu.py"), "--write"])
    # The 8x8 generators read work/script_translated.json, so a name change
    # leaves ps4disasm/vwf/*.bin stale. Nothing here used to run them:
    # checkbuild did, but only as a side effect of comparing them against a
    # fresh generation, so it reported the change as a FAILURE and rewrote the
    # files -- which made the very next build pass. Renaming one technique
    # (Rebirther -> Reverser) cost two builds that way, twice in one day.
    # Regenerate first; that also makes "edited a generator without re-running
    # it" impossible rather than merely detected.
    for gen in ("menuvwf.py", "fixwinfont.py", "fieldstrings.py",
                "menupool.py", "menustrip.py"):
        run([sys.executable, str(TOOLS / gen)])
    run([sys.executable, str(TOOLS / "checkbuild.py")])
    run([sys.executable, str(TOOLS / "trpatch.py"), "check",
         str(ROOT / "work" / "dialogue_full.json"), "--budget"])
    run([sys.executable, str(TOOLS / "trpatch8.py"), "check",
         str(ROOT / "work" / "script_translated.json")])
    run(["cmd", "/c", str(DISASM / "build.bat")], DISASM)

    built = DISASM / "ps4built.bin"
    if not built.exists() or built.stat().st_size != 0x400000:
        raise SystemExit("assembler did not produce a 4 MiB ps4built.bin")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(built, output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest().upper()
    print(f"\nwrote {output}")
    print(f"SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
