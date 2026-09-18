"""Which way the BUILT rom was configured, for tests that depend on it.

Read off the listing rather than ps4.options.asm: the options file says what
the next build will be, the listing says what ps4built.bin is, and a test
runs against the latter.  `vwf_menu_strips` is the one option whose two
settings both build and both have tests (work/plan-strips-vs-composition.md):

    strips_built(lst)  True when names draw from prerendered strips
                       (VWFMenu_DrawStrip assembled), False when they are
                       composed from VWFMenu_NameText (VWFMenu_DrawName).
"""
import re


def strips_built(lst):
    """`lst` is the text of ps4disasm/ps4.lst, which every harness test
    already holds for its symbol lookups."""
    has_strip = re.search(r":\s+VWFMenu_DrawStrip:", lst) is not None
    has_name = re.search(r":\s+VWFMenu_DrawName:", lst) is not None
    assert has_strip != has_name, "the listing has both or neither name path"
    return has_strip


def skipped(label, reason="composed-name build (vwf_menu_strips=0)"):
    print("  skip %-40s %s" % (label, reason))
