"""Apply translation-specific source edits to the US disassembly.

ps4.asm contains a few non-UTF-8 bytes, so ordinary text patchers cannot edit
it safely.  These replacements are deliberately ASCII-only and byte-exact;
each must occur once, and an already-applied edit is accepted idempotently.

  python tools/disasmport.py          report only
  python tools/disasmport.py --write  apply edits
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM = os.path.join(ROOT, "ps4disasm", "ps4.asm")


def b(s):
    return s.encode("ascii")


EDITS = [
    ("reset VWF at battle load", b(
        "\tmove.b\t#0, (HW_Write_Mode).l\n"
        "\tlea\t(Camera_Y_Pos_FG).w, a0\n"
        "\tlea\t($FFFFEF80).w, a1\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmoveq\t#0, d0\n"
        "\tmove.l\td0, (a1)+\n"
        "\tmove.l\td0, (a1)+\n"
        "\tmove.l\td0, (a1)+\n"
        "\tmove.l\td0, (a1)+\n"
        "\tjsr\t(ClearPlanes_A_B_Buf).l\n"
        "\tori.b\t#$10, (VDP_Reg1_Val+1).w\n"), b(
        "\tmove.b\t#0, (HW_Write_Mode).l\n"
        "\tlea\t(Camera_Y_Pos_FG).w, a0\n"
        "\tlea\t($FFFFEF80).w, a1\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmove.l\t(a0)+, (a1)+\n"
        "\tmoveq\t#0, d0\n"
        "\tmove.l\td0, (a1)+\n"
        "\tmove.l\td0, (a1)+\n"
        "\tmove.l\td0, (a1)+\n"
        "\tmove.l\td0, (a1)+\n"
        "\tjsr\t(ClearPlanes_A_B_Buf).l\n"
        "\tif vwf_menu=1\n"
        "\tjsr\t(VWFMenu_Reset).l\n"
        "\tendif\n"
        "\tori.b\t#$10, (VDP_Reg1_Val+1).w\n")),
    ("reset VWF at field-map load", b(
        "GameMode_LoadFieldMap:\n"
        "\tmove.w\t#$8B00, (a6)\n"), b(
        "GameMode_LoadFieldMap:\n"
        "\tif vwf_menu=1\n"
        "\tjsr\t(VWFMenu_Reset).l\n"
        "\tendif\n"
        "\tmove.w\t#$8B00, (a6)\n")),
    ("widen Tech open/copy window", b(
        "loc_18F2:\n"
        "\tmoveq\t#$C, d1\n"), b(
        "loc_18F2:\n"
        "\tmoveq\t#$E, d1\n")),
    ("widen Tech copy-out", b(
        "\tmovea.l\t(sp)+, a1\n"
        "\tmovea.l\ta3, a0\n"
        "\tmoveq\t#$C, d1\n"
        "\tmoveq\t#9, d2\n"
        "\tjsr\t(loc_27DD04).l\n"
        "\tmovea.l\ta3, a1\n"
        "\trts\n"
        "loc_193C:\n"), b(
        "\tmovea.l\t(sp)+, a1\n"
        "\tmovea.l\ta3, a0\n"
        "\tmoveq\t#$E, d1\n"
        "\tmoveq\t#9, d2\n"
        "\tjsr\t(loc_27DD04).l\n"
        "\tmovea.l\ta3, a1\n"
        "\trts\n"
        "loc_193C:\n")),
    ("widen Tech reveal window", b(
        "Battle_TechNextWin:\n"
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$C, d1\n"), b(
        "Battle_TechNextWin:\n"
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$E, d1\n")),
    ("widen Tech previous-page copy", b(
        "loc_E8C:\n"
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$C, d1\n"), b(
        "loc_E8C:\n"
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$E, d1\n")),
    ("widen Tech cleanup window", b(
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$C, d1\n"
        "\tmoveq\t#9, d2\n"
        "\trts\n\n"
        "Battle_BackFromTechs:"), b(
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$E, d1\n"
        "\tmoveq\t#9, d2\n"
        "\trts\n\n"
        "Battle_BackFromTechs:")),
    ("widen active Tech window", b(
        "loc_18DA:\n"
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$C, d1\n"), b(
        "loc_18DA:\n"
        "\tjsr\tloc_199E(pc)\n"
        "\tmoveq\t#$E, d1\n")),
    ("release Tech strips after selection", b(
        "Battle_TechSelected:\n"
        "\tbsr.s\tloc_1BC6\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tmove.w\t#$10, ($FFFF418C).l\n"), b(
        "Battle_TechSelected:\n"
        "\tbsr.s\tloc_1BC6\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; the private Tech pages are gone; release their strips\n"
        "\tmove.w\t#$10, ($FFFF418C).l\n")),
    ("release Tech strips after cancel", b(
        "Battle_BackFromTechs:\n"
        "\tbsr.s\tloc_1BC6\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tmove.w\t#$10, ($FFFF418C).l\n"), b(
        "Battle_BackFromTechs:\n"
        "\tbsr.s\tloc_1BC6\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; do not charge the next character for this menu\n"
        "\tmove.w\t#$10, ($FFFF418C).l\n")),
    ("release Skill strips after selection", b(
        "Battle_SkillSelected:\n"
        "\tbsr.s\tloc_1F4E\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n"), b(
        "Battle_SkillSelected:\n"
        "\tbsr.s\tloc_1F4E\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; the private Skill pages are no longer reachable\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n")),
    ("release Skill strips after cancel", b(
        "Battle_BackFromSkills:\n"
        "\tbsr.s\tloc_1F4E\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n"), b(
        "Battle_BackFromSkills:\n"
        "\tbsr.s\tloc_1F4E\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; restore the command-level pool lifetime\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n")),
    ("release Item strips after selection", b(
        "Battle_ItemSelected:\n"
        "\tbsr.s\tloc_23CA\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n"), b(
        "Battle_ItemSelected:\n"
        "\tbsr.s\tloc_23CA\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; item-page strips die with the closing window\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n")),
    ("release Item strips after cancel", b(
        "Battle_BackFromItems:\n"
        "\tbsr.s\tloc_23CA\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n"), b(
        "Battle_BackFromItems:\n"
        "\tbsr.s\tloc_23CA\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; keep later Tech and Skill menus below the cap\n"
        "\tmove.w\t#$12, ($FFFF418C).l\n")),
    ("release prior battle-results text", b(
        "loc_4624:\n"
        "\tlea\t($FFFF3500).l, a0\n"), b(
        "loc_4624:\n"
        "\tif vwf_menu=1\n"
        "\ttst.b\t(VWFMenu_BattleResultActive).l\n"
        "\tbne.s\tloc_4624_NewVWF\n"
        "\tmove.w\t(VWFMenu_PoolTop).l, (VWFMenu_BattleResultMark).l\n"
        "\tst\t(VWFMenu_BattleResultActive).l\n"
        "\tnop\n\tnop\n\tnop\n\tnop\n\tnop\n\tnop\t\t\t\t; preserve native-savestate addresses\n"
        "loc_4624_NewVWF:\n"
        "\tendif\t\t\t; result panels are double-buffered until commit\n"
        "\tlea\t($FFFF3500).l, a0\n")),
    ("mark player action text", b(
        "loc_4A94:\n"
        "\tbset\t#7, (Battle_Routine_2).l\n"
        "\tbne.w\tloc_4B42\n"
        "\tmoveq\t#$C, d1\n"), b(
        "loc_4A94:\n"
        "\tbset\t#7, (Battle_Routine_2).l\n"
        "\tbne.w\tloc_4B42\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_PoolTop).l, (VWFMenu_BattleActionMark).l\n"
        "\tendif\t\t\t; exact floor beneath this player action-name window\n"
        "\tmoveq\t#$C, d1\n")),
    ("release closed player action text", b(
        "loc_4B6E:\n"
        "\tlea\t($FFFF8916).w, a0\n"
        "\tmoveq\t#$47, d7\n"
        "\ttrap\t#0\n"
        "\tlea\t($FFFF29A0).l, a0\n"
        "\tlea\t($FFFF8900).w, a1\n"
        "\tmoveq\t#$28, d1\n"
        "\tmoveq\t#3, d2\n"
        "\tjsr\t(PlaneMapToRAM).l\n"
        "\tlea\t($FFFF8900).w, a1\n"
        "\tmove.w\t$36(a4), d0\n"
        "\tadda.w\td0, a1\n"
        "\tmoveq\t#$C, d1\n"
        "\tmoveq\t#3, d2\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\taddq.w\t#1, $32(a4)\n"), b(
        "loc_4B6E:\n"
        "\tlea\t($FFFF8916).w, a0\n"
        "\tmoveq\t#$47, d7\n"
        "\ttrap\t#0\n"
        "\tlea\t($FFFF29A0).l, a0\n"
        "\tlea\t($FFFF8900).w, a1\n"
        "\tmoveq\t#$28, d1\n"
        "\tmoveq\t#3, d2\n"
        "\tjsr\t(PlaneMapToRAM).l\n"
        "\tlea\t($FFFF8900).w, a1\n"
        "\tmove.w\t$36(a4), d0\n"
        "\tadda.w\td0, a1\n"
        "\tmoveq\t#$C, d1\n"
        "\tmoveq\t#3, d2\n"
        "\tjsr\tloc_FF8(pc)\n"
        "\trts\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleActionMark).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; the player action-name window is fully gone\n"
        "\taddq.w\t#1, $32(a4)\n")),
    ("mark enemy action text", b(
        "loc_B4E0:\n"
        "\taddq.w\t#1, $2(a4)\n"
        "\tst\t($FFFFEE48).w\n"
        "\tlea\t($FFFF3700).l, a0\n"), b(
        "loc_B4E0:\n"
        "\taddq.w\t#1, $2(a4)\n"
        "\tst\t($FFFFEE48).w\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_PoolTop).l, (VWFMenu_BattleEnemyMark).l\n"
        "\tendif\t\t\t; exact floor beneath this enemy action-name window\n"
        "\tlea\t($FFFF3700).l, a0\n")),
    ("release closed enemy action text", b(
        "loc_B59A:\n"
        "\tclr.b\t($FFFFEE48).w\n"
        "loc_B59E:\n"), b(
        "loc_B59A:\n"
        "\tclr.b\t($FFFFEE48).w\n"
        "\tif vwf_menu=1\n"
        "\tmove.w\t(VWFMenu_BattleEnemyMark).l, (VWFMenu_PoolTop).l\n"
        "\tendif\t\t\t; the enemy action-name window is fully gone\n"
        "loc_B59E:\n")),
    ("translated party-name table", b(
        "CharNameData:\n"
        "\tdc.b\t\"Chaz\", $FF\n"
        "\tdc.b\t\"Alys\", $FF\n"
        "\tdc.b\t\"Hahn\", $FF\n"
        "\tdc.b\t\"Rune\", $FF\n"
        "\tdc.b\t\"Gryz\", $FF\n"
        "\tdc.b\t\"Rika\", $FF\n"
        "\tdc.b\t\"Demi\", $FF\n"
        "\tdc.b\t\"Wren\", $FF\n"
        "\tdc.b\t\"Raja\", $FF\n"
        "\tdc.b\t\"Kyra\", $FF\n"
        "\tdc.b\t\"Seth\", $FF\n"), b(
        "CharNameData:\n"
        "\tdc.b\t\"Rudy\", $FF\n"
        "\tdc.b\t\"Laila\", $FF\n"
        "\tdc.b\t\"Hahn\", $FF\n"
        "\tdc.b\t\"Thray\", $FF\n"
        "\tdc.b\t\"Pyke\", $FF\n"
        "\tdc.b\t\"Fal\", $FF\n"
        "\tdc.b\t\"Frena\", $FF\n"
        "\tdc.b\t\"Forren\", $FF\n"
        "\tdc.b\t\"Raja\", $FF\n"
        "\tdc.b\t\"Shess\", $FF\n"
        "\tdc.b\t\"Siam\", $FF\n")),
    ("restore one-character reveal for slow fixed text", b(
        "loc_69ABE:\n"
        "\tif vwf_menu=1\n"
        "\tsubq.l\t#1, a0\t; the composer consumes the whole run\n"
        "\tmove.b\t#1, (VWFMenu_WrapFlag).l\n"
        "\tjsr\t(VWFMenu_DrawString).l\n"
        "\telse\n"
        "\ttst.b\td1\n"
        "\tbpl.s\tloc_69AC6\n"
        "\taddi.w\t#$C0, d1\n"
        "loc_69AC6:\n"
        "\tadd.w\td2, d1\n"
        "\tmove.w\td1, (a1)+\n"
        "\tendif\n"), b(
        "loc_69ABE:\n"
        "\tif vwf_menu=1\n"
        "\tjsr\t(VWFMenu_DrawWindowRun).l\n"
        "\telse\n"
        "\ttst.b\td1\n"
        "\tbpl.s\tloc_69AC6\n"
        "\taddi.w\t#$C0, d1\n"
        "loc_69AC6:\n"
        "\tadd.w\td2, d1\n"
        "\tmove.w\td1, (a1)+\n"
        "\tendif\n")),
    ("field Tech message uses full translated names (first draw)", b(
        "loc_60B32:\n"
        "\tbset\t#0, (Window_Init_Flag).w\n"
        "\tbne.w\tloc_6107C\n"
        "\tlea\t(TechniqueNames).l, a0\n"), b(
        "loc_60B32:\n"
        "\tbset\t#0, (Window_Init_Flag).w\n"
        "\tbne.w\tloc_6107C\n"
        "\tlea\t(VWFField_TechNames).l, a0\n")),
    ("field Tech message uses full translated names (redraw)", b(
        "\tmove.w\t(sp)+, (Saved_Window_Index).w\n"
        "\tmove.w\t(sp)+, (Window_Index).w\n"
        "\tlea\t(TechniqueNames).l, a0\n"), b(
        "\tmove.w\t(sp)+, (Saved_Window_Index).w\n"
        "\tmove.w\t(sp)+, (Window_Index).w\n"
        "\tlea\t(VWFField_TechNames).l, a0\n")),
    ("found item message uses full translated name", b(
        "loc_66C7C:\n"
        "\tlea\t(InventoryNames).l, a0\n"), b(
        "loc_66C7C:\n"
        "\tlea\t(VWFField_ItemNames).l, a0\n")),
    ("chest swap old item uses full translated name", b(
        "loc_67B96:\n"
        "\tclr.w\t(a4)\n"
        "\tbsr.w\tloc_69F6A\n"
        "\tmoveq\t#0, d0\n"
        "\tmove.b\t(Windows_Opened_Num).w, d0\n"
        "\tsubq.w\t#2, d0\n"
        "loc_67BA4:\n"
        "\tmove.l\td0, -(sp)\n"
        "\tmove.b\t#2, (Window_Render_Mode).w\n"
        "\tbsr.w\tWindow_Destroy\n"
        "\tmove.l\t(sp)+, d0\n"
        "\tdbf\td0, loc_67BA4\n"
        "\tbsr.w\tloc_67AA2\n"
        "\tlea\t(InventoryNames).l, a0\n"), b(
        "loc_67B96:\n"
        "\tclr.w\t(a4)\n"
        "\tbsr.w\tloc_69F6A\n"
        "\tmoveq\t#0, d0\n"
        "\tmove.b\t(Windows_Opened_Num).w, d0\n"
        "\tsubq.w\t#2, d0\n"
        "loc_67BA4:\n"
        "\tmove.l\td0, -(sp)\n"
        "\tmove.b\t#2, (Window_Render_Mode).w\n"
        "\tbsr.w\tWindow_Destroy\n"
        "\tmove.l\t(sp)+, d0\n"
        "\tdbf\td0, loc_67BA4\n"
        "\tbsr.w\tloc_67AA2\n"
        "\tlea\t(VWFField_ItemNames).l, a0\n")),
    ("chest swap found item uses full translated name", b(
        "\tmove.b\t#$FB, (a1)+\n"
        "\tmove.b\t#$FB, (a1)+\n"
        "\tlea\t(InventoryNames).l, a0\n"
        "\tmove.w\t($FFFFE3FE).w, d0\n"), b(
        "\tmove.b\t#$FB, (a1)+\n"
        "\tmove.b\t#$FB, (a1)+\n"
        "\tlea\t(VWFField_ItemNames).l, a0\n"
        "\tmove.w\t($FFFFE3FE).w, d0\n")),
    ("used found item uses full translated name", b(
        "loc_67D3E:\n"
        "\tmove.b\t#SFXID_HealTechCast, (Sound_Index).l\n"
        "\tbsr.w\tloc_67AA2\n"
        "\ttst.w\t($FFFFE3F8).w\n"
        "\tbeq.s\tloc_67DA8\n"
        "\tlea\t(InventoryNames).l, a0\n"), b(
        "loc_67D3E:\n"
        "\tmove.b\t#SFXID_HealTechCast, (Sound_Index).l\n"
        "\tbsr.w\tloc_67AA2\n"
        "\ttst.w\t($FFFFE3F8).w\n"
        "\tbeq.s\tloc_67DA8\n"
        "\tlea\t(VWFField_ItemNames).l, a0\n")),
    ("replacement found item uses full translated name", b(
        "loc_67DA8:\n"
        "\tlea\t(InventoryNames).l, a0\n"), b(
        "loc_67DA8:\n"
        "\tlea\t(VWFField_ItemNames).l, a0\n")),
    ("replacement old item uses full translated name", b(
        "\tmove.b\t#$FB, (a1)+\n"
        "\tmove.b\t#$FB, (a1)+\n"
        "\tlea\t(InventoryNames).l, a0\n"
        "\tmove.w\t($FFFFE3FA).w, d0\n"), b(
        "\tmove.b\t#$FB, (a1)+\n"
        "\tmove.b\t#$FB, (a1)+\n"
        "\tlea\t(VWFField_ItemNames).l, a0\n"
        "\tmove.w\t($FFFFE3FA).w, d0\n")),
    ("dynamic field item windows force VWF", b(
        "\tmoveq\t#1, d4\n"
        "\tlea\t($FFFFE200).w, a0\n"
        "\tbsr.w\tLoadWindowTiles\n"), b(
        "\tmoveq\t#1, d4\n"
        "\tlea\t($FFFFE200).w, a0\n"
        "\tjsr\t(VWFField_LoadWindowTiles).l\n"), 7),
    ("shop confirmations use translated dialogue item names", b(
        "\tlea\t(InventoryNames2).l, a0\n"
        "\tjsr\t(GetOffsetByID_FF_Delim).l\n"), b(
        "\tlea\t(VWFDialogue_ItemNames).l, a0\n"
        "\tjsr\t(GetOffsetByID_FF_Delim).l\n"), 2),
    ("remap revealed VWF cells before animated close DMA", b(
        "loc_688A8:\n"
        "\tjsr\t(DMAPlane_A_VInt).l\n"), b(
        "loc_688A8:\n"
        "\tif vwf_menu=1\n"
        "\tmove.l\td0, -(sp)\n"
        "\tmove.w\t(VWFMenu_RemapIdx).l, d0\n"
        "\tjsr\t(VWFMenu_RemapRegion_NoSweep).l\n"
        "\tmove.l\t(sp)+, d0\n"
        "\tendif\n"
        "\tjsr\t(DMAPlane_A_VInt).l\n")),
    ("remap final revealed VWF cells before close DMA", b(
        "loc_688D4:\n"
        "\tandi.b\t#9, (Window_Render_Mode).w\n"
        "\tbsr.w\tloc_688E6\n"
        "\tjsr\t(DMAPlane_A_VInt).l\n"), b(
        "loc_688D4:\n"
        "\tandi.b\t#9, (Window_Render_Mode).w\n"
        "\tbsr.w\tloc_688E6\n"
        "\tif vwf_menu=1\n"
        "\tmove.l\td0, -(sp)\n"
        "\tmove.w\t(VWFMenu_RemapIdx).l, d0\n"
        "\tjsr\t(VWFMenu_RemapRegion_NoSweep).l\n"
        "\tmove.l\t(sp)+, d0\n"
        "\tendif\n"
        "\tjsr\t(DMAPlane_A_VInt).l\n")),
    ("battle full-pack message", b(
        "loc_27E784:\n"
        "\tdc.b\t\"But itempack full!\"\n"
        "\tdc.b\t$FF\n"), b(
        "loc_27E784:\n"
        "\tdc.b\t\"But pack is full!\"\n"
        "\tdc.b\t$FF\n")),
    ("battle declined-item grammar", b(
        "loc_3688:\n"
        "\tmove.w\t#2, ($FFFF4190).l\n"
        "\tjsr\tloc_4624(pc)\n"
        "\tmoveq\t#0, d0\n"
        "\tmove.b\t(Dropped_Item).l, d0\n"
        "\tjsr\t(loc_27DE56).l\n"
        "\tlea\t($FFFF0896).l, a1\n"
        "\tst\td1\n"
        "\tjsr\t(loc_27DB92).l\n"
        "\tlea\t($FFFF0896).l, a1\n"
        "\tjsr\tloc_4640(pc)\n"
        "\tst\td1\n"
        "\tlea\t(loc_27E7C6).l, a0\n"
        "\tjsr\t(loc_27DB92).l\n"
        "\tlea\t($FFFF0996).l, a1\n"
        "\tclr.b\td1\n"
        "\tjsr\tloc_464A(pc)\n"
        "\tjsr\tloc_4660(pc)\n"
        "\tjmp\t(PlaneMapToRAM).l\n"), b(
        "loc_3688:\n"
        "\tmove.w\t#2, ($FFFF4190).l\n"
        "\tjsr\tloc_4624(pc)\n"
        "\tlea\t($FFFF0896).l, a1\n"
        "\tst\td1\n"
        "\tlea\t(loc_27E7C6).l, a0\n"
        "\tjsr\t(loc_27DB92).l\n"
        "\tlea\t($FFFF0896).l, a1\n"
        "\tjsr\tloc_4640(pc)\n"
        "\tmoveq\t#0, d0\n"
        "\tmove.b\t(Dropped_Item).l, d0\n"
        "\tjsr\t(loc_27DE56).l\n"
        "\tjsr\t(loc_27DB92).l\n"
        "\tlea\t($FFFF0896).l, a1\n"
        "\tjsr\tloc_4640(pc)\n"
        "\tst\td1\n"
        "\tlea\t(loc_27E7CE).l, a0\n"
        "\tjsr\t(loc_27DB92).l\n"
        "\tlea\t($FFFF0996).l, a1\n"
        "\tclr.b\td1\n"
        "\tjsr\tloc_464A(pc)\n"
        "\tjsr\tloc_4660(pc)\n"
        "\tjmp\t(PlaneMapToRAM).l\n")),
    ("battle declined-item strings", b(
        "loc_27E7C6:\n"
        "\tdc.b\t\" give up.\"\n"
        "\tdc.b\t$FF\n\n"
        "\teven\n\n"
        "loc_27E7D0:\n"), b(
        "loc_27E7C6:\n"
        "\tdc.b\t\"Gave up \"\n"
        "\tdc.b\t$FF\n\n"
        "loc_27E7CE:\n"
        "\tdc.b\t\".\", $FF\n\n"
        "\teven\n\n"
        "loc_27E7D0:\n")),
]


# Upgrade source trees generated by an earlier revision of this patcher.  The
# substitutions are applied in memory before the canonical edit checks, so
# both report-only and --write remain idempotent.
MIGRATIONS = [
    (b(
        "loc_69ABE:\n"
        "\tif vwf_menu=1\n"
        "\t; Immediate menu text can consume and compose a whole run.  Slow\n"
        "\t; field messages must retain the stock one-character delay; map\n"
        "\t; their fixed glyph through the permanent font one at a time.\n"
        "\ttst.w\td4\n"
        "\tbeq.s\tloc_69AC6\n"
        "\tsubq.l\t#1, a0\t; the composer consumes the whole run\n"
        "\tmove.b\t#1, (VWFMenu_WrapFlag).l\n"
        "\tjsr\t(VWFMenu_DrawString).l\n"
        "\tbra.s\tloc_69ACA\n"
        "\tendif\n"
        "loc_69AC6:\n"
        "\ttst.w\td1\n"
        "\tbeq.s\tloc_69AC8\t; space uses the blank at $680\n"
        "\tcmpi.w\t#65, d1\n"
        "\tbcc.s\tloc_69AC8\t; codes 65+ live at $680+code\n"
        "\taddi.w\t#$13F, d1\t; codes 1-64 use the copy at $7C0\n"
        "loc_69AC8:\n"
        "\tadd.w\td2, d1\n"
        "\tmove.w\td1, (a1)+\n"), b(
        "loc_69ABE:\n"
        "\tif vwf_menu=1\n"
        "\tjsr\t(VWFMenu_DrawWindowRun).l\n"
        "\tbra.s\tloc_69ACA\n"
        "\telse\n"
        "\ttst.b\td1\n"
        "\tbpl.s\tloc_69AC6\n"
        "\taddi.w\t#$C0, d1\n"
        "loc_69AC6:\n"
        "\tadd.w\td2, d1\n"
        "\tmove.w\td1, (a1)+\n"
        "\tendif\n")),
    (b("\tbsr.w\tVWFField_LoadWindowTiles\n"),
     b("\tjsr\t(VWFField_LoadWindowTiles).l\n")),
    (b(
        "loc_69ABE:\n"
        "\tif vwf_menu=1\n"
        "\tjsr\t(VWFMenu_DrawWindowRun).l\n"
        "\tbra.s\tloc_69ACA\n"
        "\telse\n"), b(
        "loc_69ABE:\n"
        "\tif vwf_menu=1\n"
        "\tjsr\t(VWFMenu_DrawWindowRun).l\n"
        "\telse\n")),
]


def main():
    write = "--write" in sys.argv
    data = open(ASM, "rb").read()
    migrated = 0
    for old, new in MIGRATIONS:
        n = data.count(old)
        if n:
            data = data.replace(old, new)
            migrated += n
    changed = 0
    for edit in EDITS:
        name, old, new = edit[:3]
        expected = edit[3] if len(edit) > 3 else 1
        old_n, new_n = data.count(old), data.count(new)
        if old_n == expected and new_n == 0:
            print("  ready   " + name)
            if write:
                data = data.replace(old, new, expected)
                changed += expected
        elif old_n == 0 and new_n == expected:
            print("  present " + name)
        else:
            raise SystemExit("%s: old=%d new=%d" % (name, old_n, new_n))
    if write and (changed or migrated):
        open(ASM, "wb").write(data)
    ready = sum(data.count(edit[1]) for edit in EDITS)
    print("%d edit(s) %s" % ((changed + migrated) if write else (ready + migrated),
                            "written" if write else "ready"))


if __name__ == "__main__":
    main()
