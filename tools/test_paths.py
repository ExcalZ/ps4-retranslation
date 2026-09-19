import sys,re
sys.path.insert(0,"tools")
from emu68k import CPU
from buildflags import strips_built
import os
lst=open(os.environ.get("PS4_LST","ps4disasm/ps4.lst"),encoding="utf-8",errors="replace").read()  # PS4_LST/PS4_ROM: another build (menuharness)
def sym(n):
    m=re.search(r"/\s*([0-9A-F]{4,6}) :\s+"+re.escape(n)+r":",lst); assert m,n
    return int(m.group(1),16)
STRIPS=strips_built(lst)
ENTRY,COMPOSE=sym("VWFMenu_DrawString"),sym("VWFMenu_DrawString_Compose")
# the name path is DrawStrip or DrawName depending on the build; both report as "strip"
STRIP=sym("VWFMenu_DrawStrip" if STRIPS else "VWFMenu_DrawName")
rom=open(os.environ.get("PS4_ROM","ps4disasm/ps4built.bin"),"rb").read()
PLANE=0xFF1000
def run(at):
    mem=bytearray(0x1000000); mem[:len(rom)]=rom
    cpu=CPU(mem,ENTRY); cpu.a[0]=at; cpu.a[1]=PLANE; cpu.setd_w(2,0xE680)
    kind=None
    for _ in range(200000):
        if cpu.pc==STRIP and kind is None: kind="strip"
        if cpu.pc==COMPOSE: return "compose",None
        if cpu.step(): break
    else: raise SystemExit("no exit")
    n=(cpu.a[1]-PLANE)//2
    return (kind or "fixed"),[cpu.rw(PLANE+2*i)&0x7FF for i in range(n)]
CHROME = re.search(r":\s+VWFMenu_DrawString_Pad:", lst) is not None   # vwf_menu_chrome=1 build
CASES=[("WinTiles_MainOptions",sym("WinTiles_MainOptions"),"compose" if CHROME else "fixed"),
       ("CharStatsOverview",sym("WinTiles_CharStatsOverview"),"compose" if CHROME else "fixed"),
       ("COMBAT label",sym("loc_2AA446"),"compose" if CHROME else "fixed"),("MACRO string",sym("WinTiles_MACROString"),"compose" if CHROME else "fixed"),
       ("party-name source",sym("CharNameData"),"compose"),
       ("InventoryNames",sym("InventoryNames"),"strip"),
       ("TechniqueNames",sym("TechniqueNames"),"strip"),
       ("SkillNames",sym("SkillNames"),"strip"),
       ("PlaceNames",sym("PlaceNames"),"strip"),
       ("InventoryNames2",sym("InventoryNames2"),"strip"),
       ("EnemyNames",sym("EnemyNames"),"compose"),
       # Combos and vehicle attacks share a bank below both other ranges and
       # were fixed-width until VWFMENU_COMBO_LO/HI existed. VehicleData is
       # the ceiling; it is data, so it must still land on the fixed path.
       ("ComboNames",sym("ComboNames"),"compose"),
       ("VehicleAttackNames",sym("VehicleAttackNames"),"compose"),
       # With the fixed alphabet removed, any alphabet-bearing run composes
       # even outside a named range. VehicleSkillData is never rendered as
       # text, but exercising it here proves the fallback is content-based.
       ("VehicleSkillData",sym("VehicleSkillData"),"compose"),
       # The guild job titles compose so they can say what the JP says;
       # "The Ranch Owner of Mile" is 23 characters and would never have
       # fit the 16-cell fixed field.
       ("GuildText_RanchOwner",sym("GuildText_RanchOwner"),"compose"),
       ("GuildText_ListingPending",sym("GuildText_ListingPending"),"compose"),
       ("Event_RuneHealingChaz",sym("Event_RuneHealingChaz"),"compose"),
       # the spaceship destination menu composes (tools/spacemenu.py)
       ("space prompt",sym("loc_2AAA46"),"compose"),
       ("space confirm tail",sym("loc_2AAA60"),"compose"),
       ("space names",sym("loc_2AAA7A"),"compose"),
       ("SpaceMenuText_End",sym("SpaceMenuText_End"),"compose"),
       # battle status-effect messages compose; the label after them is chrome
       ("battle effect msgs",sym("loc_27E5D2")+2,"compose"),
       ("BattleEffectText_End",sym("BattleEffectText_End"),"compose"),
       # the battle menus, flow messages and the macro window's ATTACK /
       # DEFENSE all compose (VWFMENU_FLOW_LO/HI)
       ("COMD/MACRO/RUN",sym("loc_27E6E8"),"compose"),
       ("Surprise Attack!",sym("loc_27E6FC"),"compose"),
       ("DEFENSE",sym("loc_27E70E"),"compose"),
       ("retreated",sym("loc_27E716"),"compose"),
       ("Cannot escape!",sym("loc_27E722"),"compose"),
       ("defeated",sym("loc_27E732"),"compose"),
       ("recovered",sym("loc_27E74A"),"compose"),
       ("ATTACK",sym("loc_27E756"),"compose"),
       ("vehicle ATTACK/OPTION/RUN",sym("loc_27E75E"),"compose"),
       # battle result tails compose; the Yes/No prompts between them stay fixed
       ("result found",sym("loc_27E76E"),"compose"),
       ("result pack full",sym("loc_27E784"),"compose"),
       ("result Yes",sym("loc_27E7BE"),"compose"),
       ("result was",sym("loc_27E7C6"),"compose"),
       ("result used",sym("loc_27E7DF"),"compose"),
       ("BattleResultText_End",sym("BattleResultText_End"),"compose" if CHROME else "fixed")]   # = the battle Use/DSC menu
if CHROME:
    # $FC is handled by the caller; the following text must enter compose.
    CASES.append(("Miracle recovery", sym("VWFMenu_AllAlliesRecoveredStr") + 1, "compose"))
ok=True
for name,addr,want in CASES:
    kind,cells=run(addr); good=kind==want; ok&=good
    t="" if cells is None else "  "+" ".join("$%03X"%c for c in cells[:8])
    print("  %s %-20s $%06X -> %-8s%s"%("ok  " if good else "FAIL",name,addr,kind,t))
# Every status-effect message has to fit the 16-cell interior of the 18x3
# battle message window, with the widest party name in front of the ones
# that take one ($F2 prefix).  Measured with the composer's own widths.
import math, menustrip
def cells(t): return max(1, math.ceil(sum(menustrip.glyph_of(c, t)[1] for c in t) / 8))
a, hi = sym("loc_27E5D2"), sym("BattleEffectText_End")
inv = {v: k for k, v in menustrip.code.items()}
import json
_d = json.load(open("work/script_translated.json", encoding="utf-8"))
_enemies = [e.get("en") or "" for e in _d["entries"] if e.get("segment") == "02:001"]
widest_enemy = max(_enemies, key=cells)
worst = (0, "")
while a < hi:
    b = a
    while rom[b] != 0xFF: b += 1
    raw = rom[a:b]
    if raw:
        prefix = widest_enemy if raw[0] == 0xF2 else ""
        text = "".join(inv.get(c, "?") for c in raw if c < 0x80)
        worst = max(worst, (cells(prefix + text), prefix + text))
    a = b + 1
# the window is BATTLE_EFFECT_W wide, two of which are frame
W = int(re.search(r"^BATTLE_EFFECT_W = (\d+)", open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read(), re.M).group(1))
good = worst[0] <= W - 2
ok &= good
print("  %s battle effect messages fit %d cells: widest %d %r" % ("ok  " if good else "FAIL", W - 2, worst[0], worst[1]))
# The flow messages fit their windows with the widest name in front: the
# 18x3 transient window holds 16 cells, the 20x5 defeat window 18.  An
# enemy's " recovered!" goes in the defeat window; a party member's, and
# " retreated!", in the transient one; " defeated...!" follows a party name.
_party = [e.get("en") or "" for e in _d["entries"] if e.get("segment") == "03:000"]
widest_party = max(_party, key=cells)
def rom_text(label):
    a = sym(label); b = a
    while rom[b] != 0xFF: b += 1
    return "".join(inv.get(c, "?") for c in rom[a:b] if c < 0x80)
for label, prefix, room in (("loc_27E6FC", "", 16), ("loc_27E722", "", 16),
                            ("loc_27E716", widest_party, 16), ("loc_27E74A", widest_party, 16),
                            ("loc_27E74A", widest_enemy, 18), ("loc_27E732", widest_party, 18)):
    # the tail starts on the cell after the name's last one
    n = (cells(prefix) if prefix else 0) + cells(rom_text(label))
    good = n <= room
    ok &= good
    print("  %s flow message fits %2d cells: %2d %r" % ("ok  " if good else "FAIL", room, n, prefix + rom_text(label)))
# The two battle menus: the draw steps a fixed entry size, so every entry
# must carry its terminator inside that size, and each label must fit the
# five cells between the cursor column and the frame.
def entries(label, sizes):
    a = sym(label); out = []
    for size in sizes:
        out.append((size, rom[a:a + size])); a += size
    return out
# the command menu steps lea 9(a0),a0 then addq.w #8,a0; the vehicle menu addq.w #7 twice
for label, sizes, room in (("loc_27E6E8", (9, 8, 6), 5), ("loc_27E75E", (7, 7, 4), 5)):
    for size, e in entries(label, sizes):
        if 0xFF not in e:
            ok = False
            print("  FAIL %s entry %s has no terminator within %d bytes" % (label, e.hex(), size))
            continue
        text = "".join(inv.get(c, "?") for c in e[:e.index(0xFF)] if c < 0x80 and c != 0x67)
        good = cells(text) <= room
        ok &= good
        print("  %s %s entry %-8r %d bytes, %d of %d cells" % ("ok  " if good else "FAIL", label, text, size, cells(text), room))
# Chrome (vwf_menu_chrome=1).  The menus and captions compose plainly; the
# PAD labels position themselves with spaces that advance to the next cell
# boundary (a lone space between two glyphs stays a word space), and their
# colons are the stock tile in one cell.  Model that rule with the composer's
# own widths and assert every colon, cursor tile, control code and label
# lands on the column the fixed-width string put it, and that every composed
# label ends before whatever the numeric path draws to its right.
if CHROME:
    for name, addr, want in (("field menu", sym("WinTiles_MainOptions"), "compose"),
                             ("title menu", sym("WinTiles_ContStartEraseString"), "compose"),
                             ("MUMBLE caption", sym("WinTiles_MumblString"), "compose"),
                             ("USE/LOOK/DISCARD", sym("WinTiles_ItemAction"), "compose"),
                             ("YES/NO", sym("loc_2AA126"), "compose"),
                             ("STATUS/ORDER", sym("loc_2AA3B4"), "compose"),
                             ("Exp/Next", sym("loc_2AA422"), "compose"),
                             ("ITEM caption", sym("WinTiles_ItemString"), "compose"),
                             ("EQUIP caption", sym("loc_2AA0B2"), "compose"),
                             ("WHO?", sym("loc_2AA02E"), "compose"),
                             ("SYS menu", sym("SystemTileData"), "compose"),
                             ("chest DISCARD/USE", sym("loc_2AA81E"), "compose"),
                             ("shop buy/sell", sym("loc_2AE1AE"), "compose"),
                             ("Victory!", sym("loc_27E5B0"), "compose"),
                             ("battle Use/DSC", sym("loc_27E7E6"), "compose"),
                             ("level up", sym("loc_27E7EE"), "compose"),
                             ("mastered", sym("loc_27E876"), "compose"),
                             ("debug check window", sym("loc_2AA65C"), "compose"),
                             ("map STATUS", sym("loc_2AA6CE"), "compose"),
                             ("slot summary Chaz:LV", sym("loc_2A9F04"), "compose"),
                             ("LOOK description", sym("InventoryDescriptions2"), "compose"),
                             ("/2-Handed", sym("VWFMenu_2HandedStr"), "compose")):
        kind, cells_ = run(addr); good = kind == want; ok &= good
        print("  %s %-22s $%06X -> %s" % ("ok  " if good else "FAIL", name, addr, kind))

    def pad_walk(raw, start=0):
        """One PAD-range line under the pad rule.  Returns (marks, blank cells
        after the last glyph, pixel end of the last glyph) where marks list
        ('text'|'colon'|'gfx'|'ctl', column) for every run of glyphs, colon,
        graphic and $F8 control, columns counted from `start`."""
        px, marks, last, in_run, run_start = 0, [], 0, False, True
        run_from, pad_blanks = 0, 0          # the last pad run: glyph end before it, cells it left empty
        i = 0
        while i < len(raw):
            c = raw[i]
            if c == 0:
                nxt = raw[i + 1] if i + 1 < len(raw) else 0xFF
                pad = (run_start or in_run or nxt == 0 or nxt == 0x34 or nxt >= 0x80
                       or menustrip.width[nxt] == 0)
                if pad:
                    if not in_run:
                        run_from = px
                    px = (px | 7) + 1 if px & 7 else px + 8
                    in_run = True
                    pad_blanks = (px - ((run_from | 7) + 1 if run_from & 7 else run_from)) // 8
                else:
                    px += menustrip.width[0]
                    in_run = False
                run_start = False
            elif c == 0x34:
                assert px & 7 == 0, "colon off a cell boundary at %d" % px
                marks.append(("colon", start + px // 8)); px += 8; in_run = False; run_start = True
            elif c == 0xF8:
                marks.append(("ctl", start + px // 8)); break
            elif c >= 0xF0:
                break
            elif c >= 0x80 or menustrip.width[c] == 0:
                assert px & 7 == 0; marks.append(("gfx", start + px // 8)); px += 8; in_run = False; run_start = True
            else:
                if not marks or marks[-1][0] != "text" or in_run:
                    marks.append(("text", start + px // 8))
                px += menustrip.width[c]; last = px; in_run = False; run_start = False
            i += 1
        return marks, pad_blanks, last, run_from

    def lines_of(label, end):
        a, out = sym(label), []
        while a < sym(end):
            b = a
            while rom[b] < 0xF0: b += 1
            if b > a: out.append(rom[a:b + 1])          # keep the control that ends the line
            if rom[b] == 0xFE or rom[b] == 0xFF: break
            a = b + 1
            if rom[a - 1] == 0xF8: a += 1        # $F8 carries one parameter byte
        return out

    def text_of(raw):
        return "".join(inv.get(c, "?") for c in raw if c < 0x80)

    # (table, end label, expected marks per line, pixel limit of the composed text)
    for label, end, want, limit in (
            ("loc_2AA3E6", "loc_2AA422", [[("text", 0), ("colon", 7)]] * 6, 7 * 8),
            ("loc_2AA3C6", "loc_2AA3E6", [[("text", 1), ("colon", 5)]] * 2, 5 * 8),
            ("loc_2AA034", "WinTiles_2HandString", [[("text", 0), ("ctl", 11)]] * 4, 11 * 8),
            ("WinTiles_Meseta", "WinTiles_CharStatsOverview", [[("text", 8)]], 12 * 8),
            ("WinTiles_CharStatsOverview", "DyingString", [[("text", 5)]], 8 * 8),
            ("loc_2AA4B6", "loc_2AA4C4", [[("text", 0), ("gfx", 2)]] * 3, 2 * 8),
            ("loc_2AA53E", "loc_2AA55E", [[("text", 0), ("text", 4), ("text", 6), ("text", 8), ("text", 10), ("text", 12), ("text", 14)],
                                          [("gfx", 4), ("gfx", 6), ("gfx", 8), ("gfx", 10), ("gfx", 12)]], 17 * 8),
            ("loc_2AA58A", "loc_2AA618", [[("text", 5), ("text", 10), ("text", 15)]] + [[("gfx", 0), ("text", 2), ("text", 8), ("text", 14)]] * 6, 19 * 8)):
        got = [pad_walk(l)[:3] for l in lines_of(label, end)][:len(want)]
        good = [m for m, _, _ in got] == want and all(last <= limit for _, _, last in got)
        ok &= good
        print("  %s %-12s pad columns %s%s" % ("ok  " if good else "FAIL", label,
              [m for m, _, _ in got] if not good else "as stock", "" if good else " (want %s, ends %s, limit %d)" % (want, [last for _, _, last in got], limit)))
    # Exp/Next compose their own colons and must end before the number at column 4
    for l in lines_of("loc_2AA422", "loc_2AA42C")[:2]:
        t = text_of(l)
        good = menustrip.compose(t)[0] <= 3
        ok &= good
        print("  %s Exp/Next label %-8r %d cells from column 1, number at 4" % ("ok  " if good else "FAIL", t, menustrip.compose(t)[0]))
    # Level up.  The value is drawn on the first blank cell after the text -
    # two cells for an attribute, three for HP/TP - and the "!" follows it,
    # so the pads must leave exactly that many blank cells.  The whole line
    # fits the 20-wide results window (18 inside); the Level line follows a
    # party name on the same row.
    def strings_of(label, end):
        a, out = sym(label), []
        while a < sym(end):
            b = a
            while rom[b] < 0xFE: b += 1
            out.append(rom[a:b]); a = b + 1
        return out
    def string_at(label):
        a = sym(label); b = a
        while rom[b] < 0xFE: b += 1
        return rom[a:b]

    # Regression checks for the layout fixes reported from the live build.
    # Validate the emitted ROM where possible: the save window keeps the
    # ninth column needed by Slot 3, the result value and EXP insertion point
    # both move beside the four-cell label, and status starts one cell earlier.
    good = rom[sym("WinGroup_System") + 8] == 9
    ok &= good
    print("  %s save-slot window is 9 cells wide" % ("ok  " if good else "FAIL"))
    victory = rom[sym("Battle_VictoryMessage"):sym("Battle_VictoryMessage") + 0x200]
    good = (bytes.fromhex("43F9FFFF08A0") in victory
            and bytes.fromhex("41F9FFFF08A0") in victory)
    ok &= good
    print("  %s Each got value and EXP anchor begin at column 16" % ("ok  " if good else "FAIL"))

    # loc_3138 compacts the formatter's five-cell numeric field in place.
    # A one-digit value leaves four old source cells behind; the proportional
    # " EXP" suffix occupies only three of them, so the last stale digit used
    # to render again as "7 EXP 7". Execute the routine and require the entire
    # vacated tail to be blank while a1 remains the suffix insertion point.
    # The body lives in the extension (VWFMenu_BattleExpCompact); loc_3138
    # itself must stay the stock 22 bytes so ps4.asm addresses never move.
    good = (sym("Battle_CheckItemDrop") - sym("loc_3138") == 22
            and rom[sym("loc_3138"):sym("loc_3138") + 6]
            == bytes.fromhex("4EF9") + sym("VWFMenu_BattleExpCompact").to_bytes(4, "big"))
    ok &= good
    print("  %s loc_3138 is a stock-sized jmp to VWFMenu_BattleExpCompact" %
          ("ok  " if good else "FAIL"))
    mem = bytearray(0x1000000); mem[:len(rom)] = rom
    number = 0xFF1800
    for i, word in enumerate([0xE680, 0xE680, 0xE680, 0xE680, 0xE7E1]):
        mem[number + i * 2:number + i * 2 + 2] = word.to_bytes(2, "big")
    # emu68k does not implement the stock routine's `subq.w #2,a0`, so enter
    # at its copy loop with the exact register state the one-digit scan leaves.
    cpu = CPU(mem, sym("VWFMenu_BattleExpCompact_Copy"))
    cpu.a[7] -= 4; cpu.wl(cpu.a[7], 0)       # saved a2 restored before rts
    cpu.a[0] = number + 8; cpu.a[1] = number; cpu.a[2] = number + 10
    cpu.d[7] = 0
    for _ in range(200):
        if cpu.step(): break
    words = [cpu.rw(number + i * 2) for i in range(5)]
    good = cpu.a[1] == number + 2 and words == [0xE7E1] + [0xE680] * 4
    ok &= good
    print("  %s single-digit EXP compaction clears its stale formatter tail" %
          ("ok  " if good else "FAIL"))

    forced_call = bytes.fromhex("4EB9") + sym("VWFField_LoadWindowTiles").to_bytes(4, "big")
    save_main = rom[sym("SaveGame"):sym("loc_594C2")]
    save_overwrite = rom[sym("loc_5974E"):sym("loc_59808")]
    chest_money = rom[sym("loc_66B34"):sym("loc_66C7C")]
    good = forced_call in save_main and forced_call in save_overwrite and forced_call in chest_money
    ok &= good
    print("  %s RAM-built Save and money-chest messages force the VWF" %
          ("ok  " if good else "FAIL"))

    order_return = rom[sym("loc_5E650"):sym("loc_5E6DE")]
    constants = open("ps4disasm/ps4.constants.asm", encoding="utf-8").read()
    ram_base = int(re.search(r"^VWF_RAM_Base\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)",
                             constants, re.M).group(1), 16)
    remap_off = int(re.search(r"^VWFMenu_RemapIdx\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)",
                              constants, re.M).group(1), 16)
    remap_store = bytes.fromhex("33D1") + (ram_base + remap_off).to_bytes(4, "big")
    # ORDER calls the extension wrapper (same size as the stock jsr), which
    # names the region and then jumps on to loc_6881E.
    wrapper = sym("VWFMenu_OrderRestore")
    good = (bytes.fromhex("4EB9") + wrapper.to_bytes(4, "big") in order_return
            and rom[wrapper:wrapper + 12]
            == remap_store + bytes.fromhex("4EF9") + sym("loc_6881E").to_bytes(4, "big"))
    ok &= good
    print("  %s ORDER direct restore initializes the VWF remap region" %
          ("ok  " if good else "FAIL"))
    # The vehicle command window is composed text that stays up while the
    # skill list opens and rewinds to the base, so the base must be taken
    # after ATTACK/OPTION/RUN are drawn (third loc_27DB92), not before.
    veh = rom[sym("Battle_VehOpenMainOptions"):sym("Battle_VehMainOptions")]
    draw = bytes.fromhex("4EB9") + sym("loc_27DB92").to_bytes(4, "big")
    vwf_off = lambda n: int(re.search(r"^%s\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)" % n,
                                      constants, re.M).group(1), 16)
    capture = (bytes.fromhex("33F9") + (ram_base + vwf_off("VWFMenu_PoolTop")).to_bytes(4, "big")
               + (ram_base + vwf_off("VWFMenu_BattleBase")).to_bytes(4, "big"))
    third = -1
    for _ in range(3):
        third = veh.find(draw, third + 1)
    good = (veh.count(capture) == 1 and third >= 0 and veh.find(capture) > third
            and sym("Battle_VehMainOptions") - sym("Battle_VehOpenMainOptions") == 0xDC)
    ok &= good
    print("  %s vehicle pool base is taken above ATTACK/OPTION/RUN" % ("ok  " if good else "FAIL"))
    # The macro set/erase prompts build "<letter>-MACRO ..." in RAM.  The
    # letter must be a charset code (1..8) so the run composes; the stock
    # $80+n named the $7C0 letter copy, which the field pool owns now, and
    # the prompt showed whatever glyph had been composed there ("s-MACRO").
    opt = int(re.search(r"^Window_Option_Index_2\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)", constants, re.M).group(1), 16) & 0xFFFF
    want = bytes.fromhex("1038") + opt.to_bytes(2, "big") + bytes.fromhex("06000001")
    good = all(want in rom[sym(r):sym(r) + 0x20] for r in ("Win_MacroSetupMsg", "Win_MacroEraseMsg"))
    ok &= good
    print("  %s macro prompts compose their slot letter (charset code, not $80+n)" % ("ok  " if good else "FAIL"))
    # Battle transient surfaces that must mark and rewind the pool, each a
    # six-byte jsr to an extension wrapper inside the routine that owns it:
    # the MACRO browser (every preview redraw rewound), the main options
    # window (its labels die when it closes) and the Defend action box.
    hooks = [("Battle_OpenMacroLetters", 0x40, "VWFMenu_BattleMacroOpen"),
             ("loc_4E22", 0x20, "VWFMenu_BattleMacroPreview"),
             ("Battle_CloseMacro", 0x20, "VWFMenu_BattleMacroClose"),
             ("Battle_MacroSelected", 0x20, "VWFMenu_BattleMacroClose"),
             ("Battle_OpenMainOptions", 0x30, "VWFMenu_BattleOptionsOpen"),
             ("Battle_MainOptionSelected", 0x20, "VWFMenu_BattleOptionsClose"),
             ("loc_49AC", 0x20, "VWFMenu_BattleDefendOpen"),
             ("loc_4A40", 0x50, "VWFMenu_BattleDefendClosed")]
    missing = [w for r, span, w in hooks
               if bytes.fromhex("4EB9") + sym(w).to_bytes(4, "big") not in rom[sym(r):sym(r) + span]]
    good = not missing
    ok &= good
    print("  %s battle MACRO/options/Defend surfaces mark and rewind the pool%s"
          % ("ok  " if good else "FAIL", "" if good else " (missing %s)" % missing))
    # The mid-battle enemy rebuild (Zol Slug Fusion, the Life Deleter and
    # Twin Arms combines) recomposes both group-name boxes through the
    # wrapper that then lifts every battle mark above them; the stock jsr
    # must not survive there.
    rebuild = rom[sym("loc_14D46"):sym("loc_14D46") + 0xA0]
    good = (rebuild.count(bytes.fromhex("4EB9") + sym("VWFMenu_BattleRebuildNames").to_bytes(4, "big")) == 2
            and bytes.fromhex("4EB9") + sym("EnemyGroup_SetupNames").to_bytes(4, "big") not in rebuild)
    ok &= good
    print("  %s enemy rebuild recomposes the name boxes and lifts the marks above them" % ("ok  " if good else "FAIL"))
    overview = rom[sym("Win_CharStatsOverview_Main"):sym("Win_CharStatsOverview_Main") + 0x400]
    good = bytes.fromhex("5A40") in overview and bytes.fromhex("5C40") not in overview
    ok &= good
    print("  %s status text replaces the pad cell and the complete Level label" % ("ok  " if good else "FAIL"))
    # The whole status words live in the extension and must fit the six-cell
    # (48 px) field they are drawn in; the clear string must cover it.
    def menu_px(text):
        return sum(widths[1 + ord(c) - ord("A")] for c in text)
    widths = open("ps4disasm/vwf/menuwidth.bin", "rb").read()
    par, poi = rom[sym("VWFMenu_ParalyzedStr"):sym("VWFMenu_ParalyzedStr") + 10], rom[sym("VWFMenu_PoisonedStr"):sym("VWFMenu_PoisonedStr") + 9]
    words = ["".join(chr(ord("A") + b - 1) for b in x[:-1]) for x in (par, poi)]
    clear = rom[sym("VWFMenu_StatusLevelClear"):sym("VWFMenu_StatusLevelClear") + 8]
    good = (words == ["PARALYZED", "POISONED"] and par[-1] == 0xFE and poi[-1] == 0xFE
            and all(menu_px(w) <= 48 for w in words + ["DYING"])
            and clear[:7] == bytes(6) + bytes([0xFE])
            and bytes.fromhex("24FC") + sym("VWFMenu_ParalyzedStr").to_bytes(4, "big") in overview + rom[sym("loc_583BE"):sym("loc_583BE") + 0x80])
    ok &= good
    print("  %s status words are whole (%s) and fit the six-cell field" % ("ok  " if good else "FAIL", ", ".join("%s %dpx" % (w, menu_px(w)) for w in words)))

    miracle = string_at("VWFMenu_AllAlliesRecoveredStr")
    left, right = miracle[1:].split(bytes([0x78, 0x79]), 1)
    good = (miracle[0] == 0xFC and text_of(left) == "Everybody's "
            and text_of(right) == " recovered!")
    ok &= good
    print("  %s Miracle says Everybody's HP recovered!" % ("ok  " if good else "FAIL"))
    target = sym("VWFMenu_AllAlliesRecoveredStr").to_bytes(4, "big")
    good = rom.count(target) >= 8       # seven call-site pointers plus the chrome table
    ok &= good
    print("  %s all Miracle result pointers use the corrected string" % ("ok  " if good else "FAIL"))

    professions = [text_of(s) for s in strings_of("VWFMenu_ProfessionNameData", "VWFMenu_ProfessionNameData_End")[:8]]
    expected_professions = ["Hunter", "Scholar", "Wizard", "Berserker",
                            "Newman", "Android", "Priest", "Esper"]   # PSO/PSU spelling
    good = professions == expected_professions and max(cells(p) for p in professions) <= 8
    ok &= good
    print("  %s title-cased professions fit the 8-cell field" % ("ok  " if good else "FAIL"))
    status_info = rom[sym("Win_StatusCharList"):sym("Win_StatusExp")]
    forced = bytes.fromhex("4EB9") + sym("VWFField_LoadWindowTiles").to_bytes(4, "big")
    good = status_info.count(forced) == 1
    ok &= good
    print("  %s status profession uses the forced VWF renderer" % ("ok  " if good else "FAIL"))

    copy_name = bytes.fromhex("4EB9") + sym("VWFMenu_CopyCharName").to_bytes(4, "big")
    for label, end, kind in (("Win_TechMessage", "loc_60772", "Tech"),
                             ("Win_SkillMessage", "loc_61AC4", "Skill")):
        body = rom[sym(label):sym(end)]
        good = copy_name in body and forced in body
        ok &= good
        print("  %s DYING-target %s warning composes its translated name and sentence" %
              ("ok  " if good else "FAIL", kind))

    statuses = [text_of(string_at(x)) for x in ("DyingString", "ParalyzedString", "PoisonedString")]
    good = statuses == ["DYING", "PARA ", "POIS "]
    ok &= good
    print("  %s status strings overwrite the trailing Level digit" % ("ok  " if good else "FAIL"))
    for label in ("DyingString", "ParalyzedString", "PoisonedString"):
        kind, _ = run(sym(label))
        good = kind == "compose"
        ok &= good
        print("  %s %-15s uses VWF party-status tiles" %
              ("ok  " if good else "FAIL", label))
    ailment_draw = rom[sym("loc_5834C"):sym("loc_5835C")]
    good = (sym("VWFMenu_StatusLevelClear").to_bytes(4, "big") in ailment_draw
            and ailment_draw.count(bytes.fromhex("4EB9") + sym("LoadWindowTiles").to_bytes(4, "big")) == 2)
    ok &= good
    print("  %s ailments clear the entire old Level field before drawing" %
          ("ok  " if good else "FAIL"))
    clear_kind, clear_tiles = run(sym("VWFMenu_StatusLevelClear"))
    # The field starts at window X+5, the pad cell before Level: Level composes
    # into three cells at X+6..8 and its two-digit value occupies X+9..10.  A
    # longer physical clear crosses the party window's right edge and paints
    # blank tiles over the field map.
    good = clear_kind == "fixed" and len(clear_tiles) == 6 and all((t & 0x7FF) == 0x680 for t in clear_tiles)
    ok &= good
    print("  %s the ailment clear emits exactly six physical blank cells" %
          ("ok  " if good else "FAIL"))

    command = string_at("loc_27E6E8")[1:]
    good = text_of(command) == "COMMAND" and cells("COMMAND") <= 5
    ok &= good
    print("  %s COMMAND fits the five-cell battle label field" % ("ok  " if good else "FAIL"))
    compose_head = rom[sym("VWFMenu_DrawString_Compose"):sym("VWFMenu_DrawString_Next")]
    command_cmp = bytes.fromhex("B1FC") + (sym("loc_27E6E8") + 1).to_bytes(4, "big")
    good = command_cmp in compose_head and bytes.fromhex("7602") in compose_head
    ok &= good
    print("  %s COMMAND receives its two-pixel centering lead" % ("ok  " if good else "FAIL"))

    for label, end in (("loc_43B18", "loc_43D0C"),
                       ("loc_43D20", "loc_43F14"),
                       ("loc_43F28", "loc_440EC")):
        slot_draw = rom[sym(label):sym(end)]
        helper = bytes.fromhex("4EB9") + sym("VWFMenu_LoadSaveSlotName").to_bytes(4, "big")
        good = (bytes.fromhex("06400009") in slot_draw
                and helper in slot_draw
                and sym("loc_2A9F04").to_bytes(4, "big") not in slot_draw)
        ok &= good
        print("  %s %s draws Rudy and a right-aligned level" %
              ("ok  " if good else "FAIL", label))

    load_helper = rom[sym("VWFMenu_LoadSaveSlotName"):sym("VWFMenu_LoadSaveSlotLevel")]
    good = (sym("CharNameData").to_bytes(4, "big") in load_helper
            and (bytes.fromhex("4EB9") + sym("VWFField_LoadWindowTiles").to_bytes(4, "big")) in load_helper
            and bytes.fromhex("0C3D4E3D44FE") == rom[sym("VWFMenu_LoadSaveSlotLevel"):sym("VWFMenu_LoadSaveSlotLevel") + 6])
    ok &= good
    print("  %s Load Game anchors translated Rudy and spells out Level" %
          ("ok  " if good else "FAIL"))

    shop = string_at("loc_2AE1AE")
    shop_text = "".join(inv.get(c, "?") for c in shop if c < 0x80 and c != 0x67)
    good = shop_text == " Buy Sell"
    ok &= good
    print("  %s merchant choices are capitalized Buy / Sell" % ("ok  " if good else "FAIL"))
    for l in [string_at(x) for x in ("loc_27E7EE", "loc_27E7FE", "loc_27E810", "loc_27E820", "loc_27E830", "loc_27E842", "loc_27E852")]:
        t = text_of(l)
        marks, blanks, last, before = pad_walk(l)
        if "Level" in t:
            good = cells(widest_party) + cells(t.strip("'").strip()) + 1 <= 18
            print("  %s level line %-28r after %r: %d cells" % ("ok  " if good else "FAIL", t, widest_party, cells(widest_party) + cells(t) + 1))
        else:
            n = 3 if t.startswith("Max") else 2
            total = -(-before // 8) + blanks + 1          # text cells, the value's cells, the "!"
            good = blanks == n and total <= 18
            print("  %s level up %-30r %d blank cells for the value (want %d), %d cells" % ("ok  " if good else "FAIL", t, blanks, n, total))
        ok &= good

    # Glue across separate DrawString invocations.  Battle results and the run
    # message draw a party name, scan the plane for its first blank cell, then
    # invoke the renderer again for an apostrophe/space-led tail.  The second
    # call must reopen the name's final pool cell at its pixel remainder, not
    # start a fresh cell.  Exercise the cached-party replay path as well as the
    # first composition: that is the path these battle windows normally take.
    _constants = open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read()
    def ramaddr(name):
        m = re.search(r"^%s\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)" % re.escape(name), _constants, re.M)
        assert m, name
        return int(m.group(1), 16) & 0xFFFFFF
    def vwfram(name):
        base = ramaddr("VWF_RAM_Base")
        m = re.search(r"^%s\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)" % re.escape(name), _constants, re.M)
        assert m, name
        return (base + int(m.group(1), 16)) & 0xFFFFFF
    _slotraw = open("ps4disasm/vwf/poolslot.bin", "rb").read()
    _tile_slot = {0x680 + int.from_bytes(_slotraw[i:i + 2], "big"): i // 2
                  for i in range(0, len(_slotraw), 2)}
    _keys, _refs = vwfram("VWFMenu_Keys"), vwfram("VWFMenu_Refs")
    _glue_end = vwfram("VWFMenu_GlueEnd")
    _glue_phase = vwfram("VWFMenu_GluePhase")
    _glue_slot = vwfram("VWFMenu_GlueSlot")
    _bucket, _next = vwfram("VWFMenu_Bucket"), vwfram("VWFMenu_StripNext")
    _bucket_n = int(re.search(r"^VWFMENU_BUCKETS\s*=\s*(\d+)", _constants, re.M).group(1))
    _hash = re.search(r":\s+VWFMenu_KeyHash:", lst) is not None
    _char_stats, _game_mode = ramaddr("Character_Stats"), ramaddr("Game_Mode_Index")

    def draw_on(mem, source, plane):
        cpu = CPU(mem, ENTRY); cpu.a[0] = source; cpu.a[1] = plane; cpu.setd_w(2, 0xE680)
        for _ in range(400000):
            if cpu.step(): return cpu.a[1]
        raise SystemExit("glue draw did not return")

    def reset_vwf(mem):
        cpu = CPU(mem, sym("VWFMenu_Reset"))
        for _ in range(400000):
            if cpu.step(): return
        raise SystemExit("VWF reset did not return")

    def bucket_has(mem, key, slot):
        bucket = 0
        for b in key: bucket ^= b
        head = mem[_bucket + (bucket & (_bucket_n - 1))]
        for _ in range(len(_slotraw) // 2):
            if not head: return False
            cur = head - 1
            if cur == slot: return True
            head = mem[_next + cur]
        return False

    for tail_label in ("loc_27E7EE", "loc_27E716"):
        mem = bytearray(0x1000000); mem[:len(rom)] = rom
        mem[_game_mode:_game_mode + 2] = (0x14).to_bytes(2, "big")
        reset_vwf(mem)
        # Address registers retain the 68000's sign-extended RAM address;
        # CPU memory helpers alone mask it to the 24-bit bytearray index.
        forren = (_char_stats | 0xFF000000) + 7 * 0x80
        # First draw populates Forren's party-cache entry; the second is the
        # cache replay whose final cell must become the glue source.
        draw_on(mem, forren, PLANE)
        base = PLANE + 0x100
        name_end = draw_on(mem, forren, base)
        name_glue = (int.from_bytes(mem[_glue_end:_glue_end + 4], "big"),
                     mem[_glue_phase], mem[_glue_slot])
        name_cells, name_span = menustrip.compose("Forren")
        join = name_cells - 1
        name_tile = int.from_bytes(mem[base + join * 2:base + join * 2 + 2], "big") & 0x7FF
        name_slot = _tile_slot.get(name_tile, -1)
        name_key = bytes(name_span[y * 16 + join] for y in range(8))
        tail = rom_text(tail_label)
        glued_end = draw_on(mem, sym(tail_label), name_end)
        joined_cells, joined_span = menustrip.compose("Forren" + tail)
        name_phase = sum(menustrip.glyph_of(ch, "Forren")[1] for ch in "Forren") & 7
        tile = int.from_bytes(mem[base + join * 2:base + join * 2 + 2], "big") & 0x7FF
        slot = _tile_slot.get(tile, -1)
        want_key = bytes(joined_span[y * 16 + join] for y in range(8))
        got_key = bytes(mem[_keys + slot * 8:_keys + slot * 8 + 8]) if slot >= 0 else b""
        good = (name_end == base + name_cells * 2 and
                name_glue == (name_end, name_phase, name_slot) and
                glued_end == base + joined_cells * 2 and
                slot >= 0 and slot != name_slot and got_key == want_key and
                mem[_refs + slot] != 0 and
                bytes(mem[_keys + name_slot * 8:_keys + name_slot * 8 + 8]) == name_key and
                mem[_refs + name_slot] != 0 and
                (not _hash or (bucket_has(mem, got_key, slot) and
                               bucket_has(mem, name_key, name_slot))))
        ok &= good
        print("  %s glue %-20r %d+%d separate cells -> %d continuous; tile $%03X slot %d%s" %
              ("ok  " if good else "FAIL", tail, name_cells, cells(tail), joined_cells,
               tile, slot, " indexed" if _hash else " resident"))
# an enemy's battle record composes its name from EnemyNames by the id at $68
ES = int(re.search(r"^Enemy_Stats\s*=\s*ramaddr\(\$([0-9A-Fa-f]+)\)", open("ps4disasm/ps4.constants.asm", encoding="utf-8", errors="replace").read(), re.M).group(1), 16)
mem = bytearray(0x1000000); mem[:len(rom)] = rom
mem[(ES & 0xFFFFFF) + 0x68:(ES & 0xFFFFFF) + 0x6A] = (2).to_bytes(2, "big")
cpu = CPU(mem, ENTRY); cpu.a[0] = ES & 0xFFFFFFFF; cpu.a[1] = PLANE; cpu.setd_w(2, 0xE680)
kind = "fixed"
for _ in range(200000):
    if cpu.pc == COMPOSE: kind = "compose"; break
    if cpu.step(): break
good = kind == "compose"
ok &= good
print("  %s enemy battle record -> %s" % ("ok  " if good else "FAIL", kind))
# Table layout: entry N is message id N+1.  The per-fighter loop shows ids 7,
# $E, $1B, $1C (sleep, wake, poison, paralysis) - all $F2-prefixed - and id
# 13 is Mental UP, which the US had overwritten with " has slept!".
def entry(n):
    a = sym("loc_27E5D2")
    for _ in range(n):
        while rom[a] != 0xFF: a += 1
        a += 1
    b = a
    while rom[b] != 0xFF: b += 1
    return rom[a:b]
layout = {7: "fell asleep", 0xE: "woke up", 0x1B: "poisoned", 0x1C: "paralyzed"}
good = all(entry(i - 1)[:1] == bytes([0xF2]) and w in "".join(inv.get(c, "?") for c in entry(i - 1) if c < 0x80) for i, w in layout.items()) and "Mental Power" in "".join(inv.get(c, "?") for c in entry(12) if c < 0x80)
ok &= good
print("  %s status table: ids 7/$E/$1B/$1C carry names, id 13 is Mental UP" % ("ok  " if good else "FAIL"))
# every result tail after the widest item name fits the 18-cell result box
_items = [e.get("en") or "" for e in _d["entries"] if e.get("segment") == "00:001"]
widest_item = max(_items, key=cells)
worst = (0, "")
for lo, hi in ((sym("loc_27E76E"), sym("loc_27E784")), (sym("loc_27E7C6"), sym("BattleResultText_End"))):
    a = lo
    while a < hi:
        b = a
        while rom[b] != 0xFF: b += 1
        t = "".join(inv.get(c, "?") for c in rom[a:b] if c < 0x80)
        if t.startswith(" "):
            worst = max(worst, (cells(widest_item + t), widest_item + t))
        a = b + 1
good = worst[0] <= 18
ok &= good
print("  %s result tails fit the 18-cell box: widest %d %r" % ("ok  " if good else "FAIL", worst[0], worst[1]))
print("ALL PASS" if ok else "FAILURES ABOVE")
# The ok flag used to be printed and thrown away, so this file passed the
# build no matter what it found.
import sys as _sys; _sys.exit(0 if ok else 1)
