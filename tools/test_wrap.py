import sys,re
sys.path.insert(0,"tools")
from emu68k import CPU
import os
lst=open(os.environ.get("PS4_LST","ps4disasm/ps4.lst"),encoding="utf-8",errors="replace").read()  # PS4_LST/PS4_ROM: another build (menuharness)
def sym(n):
    m=re.search(r"/\s*([0-9A-F]{6}) :\s+"+re.escape(n)+r":",lst); assert m,n
    return int(m.group(1),16)
def ram(n):
    m=re.search(r"^"+re.escape(n)+r"\s*=.*$",open("ps4disasm/ps4.constants.asm",encoding="utf-8").read(),re.M)
    return m.group(0)
ENTRY=sym("VWFMenu_DrawString")
def const_offset(name):
    src=open("ps4disasm/ps4.constants.asm",encoding="utf-8").read()
    m=re.search(r"^"+re.escape(name)+r"\s*=\s*VWF_RAM_Base\+\$([0-9A-Fa-f]+)",src,re.M)
    assert m,name
    return int(m.group(1),16)
FLAG=0xFF5400+const_offset("VWFMenu_WrapFlag")
rom=open(os.environ.get("PS4_ROM","ps4disasm/ps4built.bin"),"rb").read()
ROW=0xFF1000                  # $80-aligned row base
code={' ':0}
for i,c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): code[c]=1+i
def run(s, col, flag):
    mem=bytearray(0x1000000); mem[:len(rom)]=rom
    at=0xFF0000
    for i,c in enumerate(s): mem[at+i]=code[c]
    mem[at+len(s)]=0xFF
    for i in range(0x100): mem[ROW+i]=0xAA
    mem[FLAG]=flag
    cpu=CPU(mem,ENTRY); cpu.a[0]=at; cpu.a[1]=ROW+col*2; cpu.setd_w(2,0xE680)
    for _ in range(30000):
        if cpu.step(): break
    else: raise SystemExit("no exit")
    return ([i for i in range(0,0x100,2) if mem[ROW+i]!=0xAA or mem[ROW+i+1]!=0xAA],
            cpu.a[1]-ROW)
ok=True
# ITEM is composed (proportional) since every run with a letter goes through
# the composer, so measure how many cells it takes rather than assume the
# fixed font's four; the wrap behaviour under test is the same for any n >= 2.
w,_=run("ITEM",10,1)
n=len(w)
exp=[20+2*i for i in range(n)]
print("  mid-row : cells at byte offsets %s   (expect %s)"%(w,exp)); ok &= w==exp and n>=2
w,_=run("ITEM",62,1)
exp=sorted(((62+i)%64)*2 for i in range(n))
print("  wrap on : cells at byte offsets %s   (expect %s)"%(w,exp)); ok &= w==exp
w,_=run("ITEM",62,0)
exp=[124+2*i for i in range(n)]
print("  wrap off: cells at byte offsets %s   (expect %s)"%(w,exp)); ok &= w==exp
# LoadWindowTiles applies its own fold at loc_69ACA the instant this returns.
# So DrawString must leave a1 exactly where stock's per-character loop would
# have left it - UN-folded - and let that one fold stand.  Folding the last
# cell ourselves left a1 at column 0, which is the very condition loc_69ACA
# tests, so it folded a second time and every cell after drew one row too
# high: 500 Meseta on the party screen put its "00" on the line above.
# Model the caller here: fold at most once, then check the column.
for c in range(52,64,2):
    _,a1=run("ITEM",c,1)
    folded = a1-0x80 if a1 % 0x80 == 0 else a1      # loc_69ACA
    want = ((c+n) % 64)*2
    print("  %d cells from col %2d: a1=ROW+%-3d -> caller fold -> ROW+%-3d "
          "(want %d)"%(n,c,a1,folded,want)); ok &= folded==want
print("ALL PASS" if ok else "FAILURES ABOVE")
# The ok flag used to be printed and thrown away, so this file passed the
# build no matter what it found.
import sys as _sys; _sys.exit(0 if ok else 1)

