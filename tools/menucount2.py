"""Count live window-text cells, correcting for scroll.

menucount.py counted the whole 64x32 nametable.  That over-counts: the
visible window is 40x28 cells, and the rest of the plane can hold stale
entries left by earlier screens.  Plane A's position is set by the
HScroll table (VRAM $F400, first word) and VSRAM (first word), so only
cells inside the scrolled viewport are actually on screen.
"""
import sys, zipfile, math
W=open("ps4disasm/vwf/menuwidth.bin","rb").read()
FONT_LO,FONT_HI=0x681,0x6D7; SPACE=0x680
def parts(p):
    z=zipfile.ZipFile(p)
    return z.read("MD1600.VDP - VRAM.bin"), z.read("MD1600.VDP - VSRAM.bin")
def cells_of(run):
    r=list(run)
    while r and r[-1]==0: r.pop()
    if not r: return 0
    return max(1, math.ceil(sum(W[c] for c in r)/8))
for p in sys.argv[1:]:
    v,vs = parts(p)
    h = int.from_bytes(v[0xF400:0xF402],"big")           # plane A hscroll
    if h & 0x8000: h -= 0x10000
    vv = int.from_bytes(vs[0:2],"big") & 0x7FF           # plane A vscroll
    nm=[(((v[0xC000+i*2]<<8)|v[0xC000+i*2+1]))&0x7FF for i in range(64*32)]
    def at(sx,sy):
        col = ((sx*8 - h)//8) % 64
        row = ((sy*8 + vv)//8) % 32
        return nm[row*64+col]
    whole=sum(1 for i in range(64*32) if FONT_LO<=nm[i]<=FONT_HI)
    vis=0; runs=[]
    for sy in range(28):
        cur=[]
        for sx in range(40):
            t=at(sx,sy)
            if FONT_LO<=t<=FONT_HI:
                vis+=1; cur.append(t-0x680)
            elif t==SPACE and cur: cur.append(0)
            else:
                if any(cur): runs.append(cur)
                cur=[]
        if any(cur): runs.append(cur)
    vwf=sum(cells_of(r) for r in runs)
    print("  %-38s hscroll=%-5d vscroll=%-4d  whole plane %3d  visible %3d  VWF %3d"%(
        p.split("/")[-1].replace(".exs","").replace("ps4us-bugfix-maxinventory-",""),
        h,vv,whole,vis,vwf))
