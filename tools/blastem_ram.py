"""Extract the 68K work RAM image from a BlastEm native savestate.

BlastEm's `BLSTSZ` format is a compact binary serialization with no section
table we can parse, but it stores the 64K work RAM uncompressed and contiguous.
We locate it by content: a savestate we can already read (an Exodus .exs, which
exposes MD1600.RAM.bin directly) supplies windows of RAM that the game copies
from ROM at boot and never changes, and those appear verbatim in the BlastEm
image.  The offset that the majority of those windows agree on is the base.

The result is byte-for-byte the same 64K image Exodus exposes, so every reader
written against .exs works unchanged.
"""
import collections, os, zipfile

RAM_SIZE = 0x10000
_REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "work", "rebuilt-status.exs")


def is_blastem(path):
    with open(path, "rb") as f:
        return f.read(6) == b"BLSTSZ"


def _reference():
    return zipfile.ZipFile(_REF).read("MD1600.RAM.bin")


def find_base(data, ref=None, votes_needed=20):
    """Offset of the work RAM inside a BlastEm savestate, or None."""
    ref = ref or _reference()
    votes = collections.Counter()
    for addr in range(0, RAM_SIZE, 0x40):
        win = ref[addr:addr + 32]
        if len(set(win)) < 6:            # flat runs match everywhere
            continue
        i = data.find(win)
        if i >= 0 and data.find(win, i + 1) < 0:      # unique match only
            votes[i - addr] += 1
    if not votes:
        return None
    base, n = votes.most_common(1)[0]
    if n < votes_needed or base < 0 or base + RAM_SIZE > len(data):
        return None
    return base


def work_ram(path):
    """The 64K work RAM image from a BlastEm .state or an Exodus .exs."""
    if not is_blastem(path):
        return zipfile.ZipFile(path).read("MD1600.RAM.bin")
    data = open(path, "rb").read()
    base = find_base(data)
    if base is None:
        raise ValueError("%s: could not locate work RAM; the reference state "
                         "%s must come from the same game"
                         % (os.path.basename(path), os.path.basename(_REF)))
    return data[base:base + RAM_SIZE]
