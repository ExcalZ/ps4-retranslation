import sys,re
sys.path.insert(0,"tools")
from emu68k import CPU
from buildflags import strips_built, skipped
import os
lst=open(os.environ.get("PS4_LST","ps4disasm/ps4.lst"),encoding="utf-8",errors="replace").read()  # PS4_LST/PS4_ROM: another build (menuharness)
def sym(n):
    m=re.search(r"/\s*([0-9A-F]{6}) :\s+"+re.escape(n)+r":",lst); assert m,n
    return int(m.group(1),16)
ENTRY=sym("VWFMenu_DrawString")
STRIPS = strips_built(lst)
rom=open(os.environ.get("PS4_ROM","ps4disasm/ps4built.bin"),"rb").read()
idx=open("ps4disasm/vwf/menustripidx.bin","rb").read()
stripmap = open("ps4disasm/vwf/menustripmap.bin", "rb").read()
POOLTOP=0xFF5400+0x100
PLANE=0xFF1000
def entry_addr(table,n):
    a=sym(table)
    for _ in range(n): 
        while rom[a]<0xFE: a+=1
        a+=1
    return a
def stocklen(a):
    n=0
    while rom[a]<0xFE: a+=1; n+=1
    return n
def run(a0):
    mem=bytearray(0x1000000); mem[:len(rom)]=rom
    for i in range(0x80): mem[PLANE+i]=0xAA
    cpu=CPU(mem,ENTRY); cpu.a[0]=a0; cpu.a[1]=PLANE; cpu.setd_w(2,0xE680)
    for _ in range(200000):
        if cpu.step(): break
    else: raise SystemExit("no exit")
    n=(cpu.a[1]-PLANE)//2
    cells=[cpu.rw(PLANE+2*i)&0x7FF for i in range(n)]
    return cells, cpu.a[0]-a0, int.from_bytes(mem[POOLTOP:POOLTOP+2],"big")
def text_of_entry(a):
    """Translated text of a name-table entry, from the composed-name tables."""
    import menustrip as _ms
    _names = open("ps4disasm/vwf/menunames.bin", "rb").read()
    _nidx = open("ps4disasm/vwf/menunameidx.bin", "rb").read()
    flat = int.from_bytes(stripmap[(a - sym("InventoryNames")) * 2:][:2], "big")
    off = int.from_bytes(_nidx[flat*2:flat*2+2], "big")
    inv = {v: k for k, v in _ms.code.items()}
    out = ""
    while _names[off] < 0xFE:
        out += inv[_names[off]]; off += 1
    return out
ok=True
CASES=[("TechniqueNames",0,"FOI/Feuer"),("TechniqueNames",1,"GIFOI/Gifeuer"),
       ("InventoryNames",0,"DAGGER"),("InventoryNames",1,"HUNT-KNIFE")]
for table,n,label in CASES:
    a=entry_addr(table,n); slen=stocklen(a)
    flat = int.from_bytes(open("ps4disasm/vwf/menustripmap.bin","rb").read()[(a-sym("InventoryNames"))*2:][:2],"big")
    strip_cells = idx[flat*4+2]
    cells,adv,top = run(a)
    want_written = max(strip_cells, slen)
    if not STRIPS:
        # the composed build gives an ink-less trailing cell the blank tile
        # instead of a slot, so it costs one fewer (see the check at the end)
        import menustrip as _ms
        _c, _span = _ms.compose(text_of_entry(a))
        strip_cells = sum(1 for t in range(_c) if any(_span[y*16+t] for y in range(8)))
    # a0 must be left ON the terminator: the caller re-reads it to end
    # the draw.  This used to assert slen+1 and so certified the bug.
    good = len(cells)==want_written and adv==slen and top==strip_cells
    ok &= good
    blanks = sum(1 for c in cells if c==0x680)
    print("  %s %-14s stock %2d chars, strip %d cells -> wrote %2d cells (%d blank), a0 +%d, pooltop %d"
          %("ok  " if good else "FAIL",label,slen,strip_cells,len(cells),blanks,adv,top))

# Pressure reclamation is safe only during a managed field-window lifetime.
# Window_Create/Destroy records and remaps its covered cells; battle's private
# window copies do not.  The destination address cannot distinguish them --
# loc_199E draws the battle Tech list at $FFFF8600 inside Plane_A_Buffer.
PLANE_A = int(re.search(r"^Plane_A_Buffer\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)",
                        open("ps4disasm/ps4.constants.asm", encoding="utf-8",
                             errors="replace").read(), re.M).group(1), 16) & 0xFFFFFF
CONSTANTS = open("ps4disasm/ps4.constants.asm", encoding="utf-8",
                 errors="replace").read()
def vwfaddr(name):
    m = re.search(r"^" + re.escape(name) +
                  r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)", CONSTANTS, re.M)
    assert m, name
    return 0xFF5400 + int(m.group(1), 16)
REUSE = vwfaddr("VWFMenu_StripReuseOK")
FIELD_DEPTH = vwfaddr("VWFMenu_FieldReuseDepth")
FIELD_BLOCKED = vwfaddr("VWFMenu_FieldReuseBlocked")
RECLAIM_INHIBIT = vwfaddr("VWFMenu_ReclaimInhibit")
GAME_MODE = int(re.search(r"^Game_Mode_Index\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)",
                          CONSTANTS, re.M).group(1), 16) & 0xFFFFFF

def run_full(a0, plane, reuse=False, live_slots=(), mode=0,
             field_depth=0, field_blocked=0, reclaim_inhibit=0):
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    for i in range(0x80): mem[plane + i] = 0xAA
    mem[POOLTOP:POOLTOP+2] = SLOTS.to_bytes(2, "big")
    import menuharness as _H
    _L = _H.SlotLayout()
    for i in range(SLOTS): mem[_L.ref(i)] = 0
    for slot in live_slots: mem[_L.ref(slot)] = 1
    mem[REUSE] = int(reuse)
    mem[FIELD_DEPTH] = field_depth
    mem[FIELD_BLOCKED] = field_blocked
    mem[RECLAIM_INHIBIT] = reclaim_inhibit
    mem[GAME_MODE:GAME_MODE+2] = mode.to_bytes(2, "big")
    cpu = CPU(mem, ENTRY); cpu.a[0] = a0; cpu.a[1] = plane; cpu.setd_w(2, 0xE680)
    for _ in range(400000):
        if cpu.step(): break
    else: raise SystemExit("no exit")
    n = (cpu.a[1] - plane) // 2
    return ([cpu.rw(plane + 2*i) & 0x7FF for i in range(n)],
            int.from_bytes(mem[POOLTOP:POOLTOP+2], "big"), mem)

REFS = vwfaddr("VWFMenu_Refs")
STRIPOF = vwfaddr("VWFMenu_StripOf")
STRIPNEXT = vwfaddr("VWFMenu_StripNext")
SLOTS = int(re.search(r"^VWFMENU_SLOTS\s*=\s*(\d+)", CONSTANTS, re.M).group(1))

def seed_strip(mem, strip_index, slots):
    """Install one valid circular strip chain in logical cell order."""
    for pos, slot in enumerate(slots):
        owner = strip_index if pos == 0 else 0xFFFF
        mem[STRIPOF+slot*2:STRIPOF+slot*2+2] = owner.to_bytes(2, "big")
        mem[STRIPNEXT+slot] = slots[(pos + 1) % len(slots)]

if STRIPS:   # a strip fails atomically; a composed name is charged per cell
    for table, n, label in CASES[:2]:
        a = entry_addr(table, n)
        cells, top, _ = run_full(a, PLANE_A)
        ink = [c for c in cells if c != 0x680]
        good = not ink and top <= SLOTS
        ok &= good
        print("  %s %-14s unscoped full pool -> %2d cells, %2d with ink"
              % ("ok  " if good else "FAIL", label, len(cells), len(ink)))
else:
    skipped('unscoped full pool blanks the whole strip')

# A full pool of dead slots is recoverable automatically only after Mark has
# established a complete field window lifetime.  The retry itself sweeps and
# then lets StripEnsure gather any sufficient set of dead slots.
for table, n, label in CASES[:2]:
    a = entry_addr(table, n)
    cells, top, _ = run_full(a, PLANE_A, mode=0xC, field_depth=1)
    ink = [c for c in cells if c != 0x680]
    good = bool(ink) and top == SLOTS
    ok &= good
    print("  %s %-14s managed field pressure -> %2d cells, %2d with ink"
          % ("ok  " if good else "FAIL", label, len(cells), len(ink)))

# Mode $C alone is deliberately insufficient, and neither battle nor the
# no-sweep animation-remap path may reuse even if a tracked field window is
# otherwise open.
if STRIPS:   # the sweep gate: composed text takes Refs=0 slots without one
    guard_cases = [("field without capability", 0xC, 0, 0, 0),
                   ("battle with capability", 0x14, 1, 0, 0),
                   ("no-sweep inhibited", 0xC, 1, 0, 1),
                   ("untracked nested child", 0xC, 1, 1, 0)]
    for label, mode, depth, blocked, inhibit in guard_cases:
        a = entry_addr("TechniqueNames", 1)
        cells, top, _ = run_full(a, PLANE_A, mode=mode, field_depth=depth,
                                 field_blocked=blocked, reclaim_inhibit=inhibit)
        ink = [c for c in cells if c != 0x680]
        good = not ink and top == SLOTS
        ok &= good
        print("  %s %-24s -> %2d with ink"
              % ("ok  " if good else "FAIL", label, len(ink)))
else:
    skipped('reclaim-capability guard cases')

# The explicit RemapRegion scope still bypasses the automatic capability gate:
# it has already swept and is synchronously repointing the restored cells.
# With that scope open, a full pool of dead slots must supply a strip without
# moving PoolTop beyond the cap.
for table, n, label in CASES[:2]:
    a = entry_addr(table, n)
    cells, top, _ = run_full(a, PLANE_A, reuse=True)
    ink = [c for c in cells if c != 0x680]
    good = bool(ink) and top == SLOTS
    ok &= good
    print("  %s %-14s scoped full pool -> %2d cells, %2d with ink"
          % ("ok  " if good else "FAIL", label, len(cells), len(ink)))

if STRIPS:   # chain bookkeeping only exists in the strip build
    # Keep every third slot live, leaving free runs of at most two, then
    # request the Gifoie strip (three or four cells, depending on the face).
    # The allocator must chain that many scattered free slots in logical
    # draw order without growing PoolTop.
    a = entry_addr("TechniqueNames", 1)
    gif_idx = int.from_bytes(stripmap[(a - sym("InventoryNames")) * 2:][:2], "big")   # the map spans all five tables from InventoryNames
    gif_cells = idx[gif_idx * 4 + 2]
    blocked = set(range(2, SLOTS, 3))
    cells, top, mem = run_full(a, PLANE_A, reuse=True, live_slots=blocked)
    poolslot = open("ps4disasm/vwf/poolslot.bin", "rb").read()
    def slot_tile(n):
        """Slot -> VRAM tile.  poolslot.bin holds WORD offsets from $680 so
        the pool can name tiles in the $7C0 bank."""
        return 0x680 + int.from_bytes(poolslot[n * 2:n * 2 + 2], "big")
    chosen = [slot for slot in range(SLOTS) if slot not in blocked][:gif_cells]
    walk = [chosen[0]]
    for _ in range(gif_cells - 1):
        walk.append(mem[STRIPNEXT + walk[-1]])
    closed = mem[STRIPNEXT + walk[-1]] == walk[0]
    want_tiles = [slot_tile(slot) for slot in chosen]
    good = (cells[:gif_cells] == want_tiles and all(c == 0x680 for c in cells[gif_cells:])
            and walk == chosen and closed and top == SLOTS)
    ok &= good
    print("  %s %-14s fragmented pool -> chained slots %s"
          % ("ok  " if good else "FAIL", "GIFOI/Gifeuer", walk))

    # Reusing an interior slot must invalidate the old logical chain.  Hunter
    # Knife exposed this after a shorter strip was placed over one of its middle
    # cells: the surviving old head was found later and returned a half-overwritten
    # name.  A resident hit is valid only while every declared continuation and
    # link is intact; otherwise the allocator must build a replacement chain.
    hunter = entry_addr("InventoryNames", 1)
    hunter_idx = int.from_bytes(stripmap[(hunter - sym("InventoryNames")) * 2:][:2], "big")
    hunter_cells = idx[hunter_idx * 4 + 2]
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    mem[POOLTOP:POOLTOP+2] = SLOTS.to_bytes(2, "big")
    mem[REFS:REFS+SLOTS] = bytes([1]) * SLOTS
    mem[STRIPOF:STRIPOF+SLOTS*2] = b"\xff\xfe" * SLOTS
    seed_strip(mem, hunter_idx, list(range(hunter_cells)))
    mem[STRIPOF+4*2:STRIPOF+4*2+2] = ((hunter_idx + 1) & 0xFFFF).to_bytes(2, "big")
    mem[REFS+20:REFS+20+hunter_cells] = bytes(hunter_cells)
    mem[REUSE] = 1
    for i in range(0x80): mem[PLANE_A+i] = 0xAA
    cpu = CPU(mem, ENTRY); cpu.a[0] = hunter; cpu.a[1] = PLANE_A; cpu.setd_w(2, 0xE680)
    for _ in range(400000):
        if cpu.step(): break
    else: raise SystemExit("no exit")
    n = (cpu.a[1] - PLANE_A) // 2
    cells = [cpu.rw(PLANE_A + 2*i) & 0x7FF for i in range(n)]
    want_tiles = [slot_tile(20+i) for i in range(hunter_cells)]
    good = cells[:hunter_cells] == want_tiles and all(c == 0x680 for c in cells[hunter_cells:])
    ok &= good
    print("  %s %-14s stale owner rejected; %d-cell replacement starts at slot 20"
          % ("ok  " if good else "FAIL", "HUNT-KNIFE", hunter_cells))

    # A syntactically owned chain can still be malformed.  A premature loop must
    # not be accepted as a resident hit or trusted by later traversals.
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    mem[POOLTOP:POOLTOP+2] = SLOTS.to_bytes(2, "big")
    mem[REFS:REFS+SLOTS] = bytes([1]) * SLOTS
    mem[STRIPOF:STRIPOF+SLOTS*2] = b"\xff\xfe" * SLOTS
    seed_strip(mem, hunter_idx, list(range(hunter_cells)))
    mem[STRIPNEXT+3] = 1
    mem[REFS+20:REFS+20+hunter_cells] = bytes(hunter_cells)
    mem[REUSE] = 1
    for i in range(0x80): mem[PLANE_A+i] = 0xAA
    cpu = CPU(mem, ENTRY); cpu.a[0] = hunter; cpu.a[1] = PLANE_A; cpu.setd_w(2, 0xE680)
    for _ in range(400000):
        if cpu.step(): break
    else: raise SystemExit("no exit")
    n = (cpu.a[1] - PLANE_A) // 2
    cells = [cpu.rw(PLANE_A + 2*i) & 0x7FF for i in range(n)]
    want_tiles = [slot_tile(20+i) for i in range(hunter_cells)]
    good = cells[:hunter_cells] == want_tiles and all(c == 0x680 for c in cells[hunter_cells:])
    ok &= good
    print("  %s %-14s malformed link rejected; replacement starts at slot 20"
          % ("ok  " if good else "FAIL", "HUNT-KNIFE"))

    # Sweep treats a validated scattered chain as indivisible.  Even if only one
    # member is visible, every member stays live; unrelated holes stay reclaimable.
    SWEEP = sym("VWFMenu_Sweep")
    scattered = [0, 2, 5, 7, 11, 13, 17, 19][:hunter_cells]
    assert len(scattered) == hunter_cells, hunter_cells
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    mem[POOLTOP:POOLTOP+2] = (max(scattered) + 1).to_bytes(2, "big")
    mem[STRIPOF:STRIPOF+SLOTS*2] = b"\xff\xfe" * SLOTS
    seed_strip(mem, hunter_idx, scattered)
    visible = scattered[3]
    tile = slot_tile(visible)
    mem[PLANE_A:PLANE_A+2] = tile.to_bytes(2, "big")
    cpu = CPU(mem, SWEEP)
    for _ in range(400000):
        if cpu.step(): break
    else: raise SystemExit("sweep did not exit")
    live = [mem[REFS+slot] for slot in scattered]
    off_chain = [mem[REFS+slot] for slot in range(max(scattered) + 1)
                 if slot not in scattered]
    good = live == [1] * hunter_cells and not any(off_chain)
    ok &= good
    print("  %s %-14s one visible member pins scattered chain: %s"
          % ("ok  " if good else "FAIL", "strip sweep", live))

    # SaveRegion must find the head from an interior scattered member, persist its
    # logical offset, and RemapCell must follow the same chain back to that member.
    SAVE_REGION = sym("VWFMenu_SaveRegion")
    REMAP_CELL = sym("VWFMenu_RemapCell")
    SAVE_TOP = vwfaddr("VWFMenu_SaveTop")
    SAVE_STACK = vwfaddr("VWFMenu_SaveStack")
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    mem[POOLTOP:POOLTOP+2] = (max(scattered) + 1).to_bytes(2, "big")
    mem[STRIPOF:STRIPOF+SLOTS*2] = b"\xff\xfe" * SLOTS
    seed_strip(mem, hunter_idx, scattered)
    offset = 4
    slot = scattered[offset]
    tile = slot_tile(slot)
    mem[PLANE_A:PLANE_A+2] = tile.to_bytes(2, "big")
    cpu = CPU(mem, SAVE_REGION); cpu.a[0] = PLANE_A; cpu.setd_w(1, 1)
    for _ in range(400000):
        if cpu.step(): break
    else: raise SystemExit("save region did not exit")
    record_tile = int.from_bytes(mem[SAVE_STACK:SAVE_STACK+2], "big")
    record_index = int.from_bytes(mem[SAVE_STACK+2:SAVE_STACK+4], "big")
    record_offset = int.from_bytes(mem[SAVE_STACK+4:SAVE_STACK+6], "big")
    marker = int.from_bytes(mem[PLANE_A:PLANE_A+2], "big") & 0x7FF
    saved = (int.from_bytes(mem[SAVE_TOP:SAVE_TOP+2], "big") == 1
             and bool(record_tile & 0x8000) and record_index == hunter_idx
             and record_offset == offset and marker == 0x700)
    cpu = CPU(mem, REMAP_CELL); cpu.a[4] = PLANE_A
    for _ in range(400000):
        if cpu.step(): break
    else: raise SystemExit("remap cell did not exit")
    restored = int.from_bytes(mem[PLANE_A:PLANE_A+2], "big") & 0x7FF
    good = saved and restored == tile
    ok &= good
    print("  %s %-14s scattered member offset %d round-trips through save/remap"
          % ("ok  " if good else "FAIL", "strip reveal", offset))
else:
    skipped('scattered chain: fragmented/stale/malformed/sweep/reveal')

# Mark is called only after SaveMarkPush -> SaveRegion and before Window_Draw.
# SaveMarkPop is called only after the normal RemapRegion pass returns.  The
# counters must therefore track nested/root lifetimes exactly and fail closed
# for the first window beyond the fixed mark/save-stack depth.
def call_routine(mem, label):
    cpu = CPU(mem, sym(label))
    for _ in range(200000):
        if cpu.step(): return
    raise SystemExit(label + " did not exit")

WINDOWS_OPEN = int(re.search(r"^Windows_Opened_Num\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)",
                             CONSTANTS, re.M).group(1), 16) & 0xFFFFFF
mem = bytearray(0x1000000); mem[:len(rom)] = rom
mem[WINDOWS_OPEN] = 0
call_routine(mem, "VWFMenu_Mark")
root_open = mem[FIELD_DEPTH] == 1 and mem[FIELD_BLOCKED] == 0
mem[WINDOWS_OPEN] = 1
call_routine(mem, "VWFMenu_Mark")
nested_open = mem[FIELD_DEPTH] == 2 and mem[FIELD_BLOCKED] == 0
call_routine(mem, "VWFMenu_SaveMarkPop")
nested_close = mem[FIELD_DEPTH] == 1 and mem[FIELD_BLOCKED] == 0
mem[WINDOWS_OPEN] = 0
call_routine(mem, "VWFMenu_SaveMarkPop")
root_close = mem[FIELD_DEPTH] == 0 and mem[FIELD_BLOCKED] == 0
mem[WINDOWS_OPEN] = 16
call_routine(mem, "VWFMenu_Mark")
untracked_open = mem[FIELD_DEPTH] == 0 and mem[FIELD_BLOCKED] == 1
call_routine(mem, "VWFMenu_SaveMarkPop")
untracked_close = mem[FIELD_DEPTH] == 0 and mem[FIELD_BLOCKED] == 0
good = all((root_open, nested_open, nested_close, root_close,
            untracked_open, untracked_close))
ok &= good
print("  %s %-14s root/nested/untracked lifecycle"
      % ("ok  " if good else "FAIL", "field capability"))

# Exercise the real remap entries and their shared epilogue directly.  The
# region walk is irrelevant to this ownership test, so Ready skips it after
# running an optional nested entry; normal remap's sweep is an rts stub.  Two
# distinct emulated stacks ensure the nested call cannot overwrite the outer
# invocation's tag.
REMAP_NORMAL = sym("VWFMenu_RemapRegion")
SWEEP = sym("VWFMenu_Sweep")
REMAP_NO_SWEEP = sym("VWFMenu_RemapRegion_NoSweep")
REMAP_READY = sym("VWFMenu_RemapRegion_Ready")
REMAP_NEXT_ROW = sym("VWFMenu_RemapRegion_NextRow")
def remap_to_exit(mem, entry, stack, nested=None):
    cpu = CPU(mem, entry, sp=stack)
    def ready(c):
        if nested: nested()
        c.pc = REMAP_NEXT_ROW + 4      # skip the four-byte DBF at the loop tail
    cpu.on_pc[REMAP_READY] = ready
    cpu.run()

mem = bytearray(0x1000000); mem[:len(rom)] = rom
mem[SWEEP:SWEEP+2] = b"Nu"             # normal entry's liveness pass is irrelevant
mem[RECLAIM_INHIBIT] = 0
no_sweep_kept = []
def nested_no_sweep():
    remap_to_exit(mem, REMAP_NO_SWEEP, 0xFFD000)
def outer_no_sweep_ready():
    nested_no_sweep()
    no_sweep_kept.append(mem[RECLAIM_INHIBIT])
remap_to_exit(mem, REMAP_NO_SWEEP, 0xFFE000, outer_no_sweep_ready)
nested_no_sweep_ok = no_sweep_kept == [1] and mem[RECLAIM_INHIBIT] == 0

mem[RECLAIM_INHIBIT] = 0
normal_kept = []
def nested_normal():
    remap_to_exit(mem, REMAP_NORMAL, 0xFFD000)
def outer_normal_ready():
    nested_normal()
    normal_kept.append(mem[RECLAIM_INHIBIT])
remap_to_exit(mem, REMAP_NO_SWEEP, 0xFFE000, outer_normal_ready)
normal_inside_no_sweep_ok = normal_kept == [1] and mem[RECLAIM_INHIBIT] == 0
good = nested_no_sweep_ok and normal_inside_no_sweep_ok
ok &= good
print("  %s %-14s nested/re-entry keeps outer inhibit"
      % ("ok  " if good else "FAIL", "no-sweep remap"))

# The location banner picks a PRE-CENTRED window by length: WinGroup_PlaceName
# widens one cell per index and steps its X origin left every second index.
# The caller used to count characters, which is a cell each only in fixed-width
# Japanese -- and worse, it counts bytes in PlaceNames, which still holds the
# US names because menu lists read strips keyed by its offsets, not its text.
# So the box was sized by a US name while displaying ours.  VWFMenu_StripCells
# reports what will actually be drawn.
CELLS = sym("VWFMenu_StripCells")
def call_cells(a0):
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    cpu = CPU(mem, CELLS); cpu.a[0] = a0
    for _ in range(200000):
        if cpu.step(): break
    else: raise SystemExit("no exit")
    return cpu.d[1] & 0xFFFF, cpu.a[0]

bad = kept = 0
n_place = 0
a = sym("PlaceNames")
while n_place < 54:
    flat = int.from_bytes(stripmap[(a - sym("InventoryNames")) * 2:][:2], "big")
    want = idx[flat * 4 + 2]
    got, a0_after = call_cells(a)
    if got != want: bad += 1
    if a0_after != a: kept += 1
    n_place += 1
    while rom[a] < 0xFE: a += 1
    a += 1
good = bad == 0 and kept == 0
ok &= good
print("  %s %-14s %d place names: %d disagree with the strip table, %d move a0"
      % ("ok  " if good else "FAIL", "banner width", n_place, bad, kept))

# The banner centres a name on its composed width, so the draw must not pad
# it out to the stock entry's character count: SPACEPORT -> AIRPORT is five
# cells and was drawn as nine, four blanks through the right frame.
NOPAD = vwfaddr("VWFMenu_NoPad")
a = sym("PlaceNames")
wide = None
while True:
    flat = int.from_bytes(stripmap[(a - sym("InventoryNames")) * 2:][:2], "big")
    if flat == 0xFFFF: break
    if stocklen(a) > idx[flat * 4 + 2]:
        wide = (a, idx[flat * 4 + 2], stocklen(a)); break
    while rom[a] < 0xFE: a += 1
    a += 1
assert wide, "no place name whose stock entry is longer than its cells"
def run_nopad(a0, flag):
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    for i in range(0x80): mem[PLANE + i] = 0xAA
    mem[NOPAD] = flag
    cpu = CPU(mem, ENTRY); cpu.a[0] = a0; cpu.a[1] = PLANE; cpu.setd_w(2, 0xE680)
    for _ in range(400000):
        if cpu.step(): break
    return (cpu.a[1] - PLANE) // 2, cpu.a[0] - a0
padded, unpadded = run_nopad(wide[0], 0), run_nopad(wide[0], 1)
good = padded[0] == wide[2] and unpadded[0] == wide[1] and padded[1] == unpadded[1] == wide[2]
ok &= good
print("  %s %-14s stock %d chars, %d cells: padded draw %d cells, banner draw %d"
      % ("ok  " if good else "FAIL", "banner no-pad", wide[2], wide[1], padded[0], unpadded[0]))

if not STRIPS:
    # The composed-name build must produce the SAME cells the strip would
    # have, only content-allocated: the 1bpp keys the composer records are
    # exactly what tools/menustrip.py rendered the strip from.  And a second
    # copy of a name, or a name sharing a prefix, must cost fewer cells.
    import menustrip
    KEYS = vwfaddr("VWFMenu_Keys")
    def draw_seq(entries):
        """Draw several table entries in turn; return PoolTop after each."""
        mem = bytearray(0x1000000); mem[:len(rom)] = rom
        tops, keys = [], []
        plane = PLANE
        for a0 in entries:
            for i in range(0x80): mem[plane + i] = 0xAA
            cpu = CPU(mem, ENTRY); cpu.a[0] = a0; cpu.a[1] = plane; cpu.setd_w(2, 0xE680)
            for _ in range(400000):
                if cpu.step(): break
            else: raise SystemExit("no exit")
            tops.append(int.from_bytes(mem[POOLTOP:POOLTOP+2], "big"))
            plane += 0x80
        keys = [bytes(mem[KEYS+s*8:KEYS+s*8+8]) for s in range(tops[-1])]
        return tops, keys
    names = open("ps4disasm/vwf/menunames.bin", "rb").read()
    nameidx = open("ps4disasm/vwf/menunameidx.bin", "rb").read()
    def text_of(a):
        flat = int.from_bytes(stripmap[(a - sym("InventoryNames")) * 2:][:2], "big")
        off = int.from_bytes(nameidx[flat*2:flat*2+2], "big")
        inv = {v: k for k, v in menustrip.code.items()}
        out = ""
        while names[off] < 0xFE:
            out += inv[names[off]]; off += 1
        return out
    hunter = entry_addr("InventoryNames", 1)
    tops, keys = draw_seq([hunter])
    want = [bytes(menustrip.compose(text_of(hunter))[1][y*16+t] for y in range(8))
            for t in range(menustrip.compose(text_of(hunter))[0])]
    good = keys == want
    ok &= good
    print("  %s %-14s composed keys are the strip's own 1bpp cells (%d)"
          % ("ok  " if good else "FAIL", text_of(hunter), len(want)))
    tops, _ = draw_seq([hunter, hunter])
    good = tops[1] == tops[0]
    ok &= good
    print("  %s %-14s drawn twice costs %d then %d cells"
          % ("ok  " if good else "FAIL", text_of(hunter), tops[0], tops[1] - tops[0]))
    # two names sharing a leading word share their leading cells
    inv_names = [entry_addr("InventoryNames", i) for i in range(160)]
    by_text = {text_of(a): a for a in inv_names}
    pair = None
    for t1 in by_text:
        for t2 in by_text:
            if t1 != t2 and t1.split(" ")[0] == t2.split(" ")[0] and len(t1.split(" ")[0]) >= 3:
                pair = (t1, t2); break
        if pair: break
    assert pair, "no prefix-sharing item pair"
    t1, t2 = pair
    c1 = menustrip.compose(t1)[0]; c2 = menustrip.compose(t2)[0]
    tops, _ = draw_seq([by_text[t1], by_text[t2]])
    shared = c1 + c2 - tops[1]
    good = tops[0] == c1 and 0 < shared < c2
    ok &= good
    print("  %s %-14s + %s: %d + %d cells cost %d (%d shared)"
          % ("ok  " if good else "FAIL", t1, t2, c1, c2, tops[1], shared))
    # A name whose ink ends on a cell boundary composes a trailing blank
    # cell.  That cell points at $680 and takes no slot; allocating it hit
    # the zero key of a never-uploaded slot and showed garbage (Resta,
    # Ceramic Shield, 2026-09-10 playtest).
    tail = None
    for a in inv_names:
        cells, span = menustrip.compose(text_of(a))
        if all(span[y*16 + cells - 1] == 0 for y in range(8)):
            tail = (a, cells); break
    assert tail, "no item name ends in a blank cell"
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    for i in range(0x80): mem[PLANE + i] = 0xAA
    cpu = CPU(mem, ENTRY); cpu.a[0] = tail[0]; cpu.a[1] = PLANE; cpu.setd_w(2, 0xE680)
    for _ in range(400000):
        if cpu.step(): break
    n = (cpu.a[1] - PLANE) // 2
    cells = [cpu.rw(PLANE + 2*i) & 0x7FF for i in range(n)]
    top_after = int.from_bytes(mem[POOLTOP:POOLTOP+2], "big")
    good = cells[tail[1] - 1] == 0x680 and top_after == tail[1] - 1 and n == max(tail[1], stocklen(tail[0]))
    ok &= good
    print("  %s %-14s blank tail cell is $680, %d cells cost %d slots"
          % ("ok  " if good else "FAIL", text_of(tail[0]), tail[1], top_after))

print("ALL PASS" if ok else "FAILURES ABOVE")
# The ok flag used to be printed and thrown away, so this file passed the
# build no matter what it found.
import sys as _sys; _sys.exit(0 if ok else 1)
