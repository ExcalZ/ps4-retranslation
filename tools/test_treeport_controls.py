"""Regression checks for dialogue-tree control operands."""

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dialogue
import treeport


def source_bytes(lines):
    """Assemble the small dc.b/dc.w subset used by dialogue sources."""
    out = bytearray()
    for line in lines:
        code = line.split(";", 1)[0]
        if "dc.b" in code:
            if '"' in code:
                text = code.split('"', 1)[1].rsplit('"', 1)[0]
                out.extend(bytes(len(text)))
            else:
                out.extend(int(x, 16) for x in re.findall(
                    r"\$([0-9A-Fa-f]{2})(?![0-9A-Fa-f])", code))
        elif "dc.w" in code:
            for word in re.findall(r"\$([0-9A-Fa-f]{4})(?![0-9A-Fa-f])", code):
                value = int(word, 16)
                out.extend((value >> 8, value & 0xFF))
    return bytes(out)


def engine_from_source(data, tree=None):
    engine, i = [], 0
    while i < len(data):
        code = data[i]
        if code < 0xF0:
            i += 1
            continue
        if code == 0xFF:
            break
        width = treeport.TREE_EXTRA_OPERANDS.get(
            code, dialogue.ctrl_width(data, i))
        # $F4 carries the extra Game_Mode_Routine == 4 byte in Party Talk;
        # read the source the same way canonical_engine reads the US tree, or
        # every message in that tree mismatches by construction.
        if code == 0xF4:
            width = treeport.f4_width(tree)
        ops = tuple(data[i + 1:i + 1 + width])
        assert len(ops) == width, f"truncated ${code:02X} control"
        if code not in treeport.LAYOUT:
            engine.append((code, ops))
        i += 1 + width
    return engine


def sanctioned(number, index):
    """Expected controls for a message OVERRIDES writes with JP controls.

    Not a skip: the message is still asserted, against the Japanese row's own
    controls instead of the US build's.  A deviation is only allowed to be the
    one that was signed off -- see the note beside the entry in
    treeport.OVERRIDES.
    """
    spec = treeport.OVERRIDES.get((number, index))
    if not (isinstance(spec, tuple) and spec[1] == 'jp'):
        return None
    import json
    doc = json.load(open(Path(treeport.ROOT) / 'work' / 'dialogue_full.json',
                         encoding='utf-8'))
    row = next(e for e in doc['entries'] if e['id'] == spec[0])
    return treeport.jp_engine_full(row['hex'], row['id'].split('#')[0])


def main():
    checked = action_zero = deviations = 0
    for path in sorted(Path(treeport.SCRIPT).glob("dialogue *.asm")):
        number = int(path.stem.split()[-1])
        lines, messages = treeport.parse_tree(number)
        for index, start, end, expected in messages:
            actual = engine_from_source(source_bytes(lines[start:end]), number)
            allowed = sanctioned(number, index)
            if allowed is not None:
                # Assert against the Japanese row instead, then fall through:
                # the panel-load check below still has to run, or the five
                # {F2:00} loads in this very message stop being guarded.
                expected = allowed
                deviations += 1
            assert actual == expected, (
                f"tree {number} message ${index:X}: source controls {actual!r} "
                f"do not match canonical US controls {expected!r}")
            checked += 1
            for code, ops in actual:
                if code == 0xF2 and ops[:1] == (0,):
                    assert len(ops) == 3, (
                        f"tree {number} message ${index:X}: action $00 has "
                        f"{len(ops) - 1} panel-id byte(s), expected 2")
                    action_zero += 1

    principal = treeport.canonical_engine(33)[0x17]
    assert principal[:3] == [
        (0xF2, (0x00, 0x00, 0x00)),
        (0xF2, (0x00, 0x00, 0x01)),
        (0xF4, (0x0E,)),
    ]
    assert [ops for code, ops in principal if code == 0xF2] == [
        (0x00, 0x00, 0x00),
        (0x00, 0x00, 0x01),
        (0x00, 0x00, 0x02),
        (0x00, 0x00, 0x03),
    ]
    print(f"treeport controls: {checked} messages, {action_zero} panel loads, "
          f"{deviations} sanctioned deviation(s) OK")


if __name__ == "__main__":
    main()
