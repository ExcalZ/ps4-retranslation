"""Render Mega Drive tile data (1bpp or 4bpp planar-linear) to PNG for inspection."""
import png

def decode_1bpp(data, ntiles, tw=8, th=8):
    """1bpp: each tile row = 1 byte, MSB-first."""
    tiles=[]
    per = th * (tw//8)
    for t in range(ntiles):
        blk = data[t*per:(t+1)*per]
        if len(blk)<per: break
        g=[]
        for y in range(th):
            row=[]
            for xb in range(tw//8):
                b=blk[y*(tw//8)+xb]
                for bit in range(7,-1,-1):
                    row.append(255 if (b>>bit)&1 else 0)
            g.append(row)
        tiles.append(g)
    return tiles

def decode_4bpp(data, ntiles):
    """Mega Drive 4bpp: 32 bytes/tile, 2 pixels per byte, high nibble first."""
    tiles=[]
    for t in range(ntiles):
        blk=data[t*32:(t+1)*32]
        if len(blk)<32: break
        g=[]
        for y in range(8):
            row=[]
            for x in range(4):
                b=blk[y*4+x]
                row.append((b>>4)*17)
                row.append((b&0xF)*17)
            g.append(row)
        tiles.append(g)
    return tiles

def sheet(tiles, cols, path, gap=1):
    if not tiles: 
        print("no tiles"); return
    th=len(tiles[0]); tw=len(tiles[0][0])
    rowsN=(len(tiles)+cols-1)//cols
    W=cols*(tw+gap)+gap; H=rowsN*(th+gap)+gap
    img=[bytearray([64])*W for _ in range(H)]
    for i,t in enumerate(tiles):
        cx=(i%cols)*(tw+gap)+gap; cy=(i//cols)*(th+gap)+gap
        for y in range(th):
            for x in range(tw):
                img[cy+y][cx+x]=t[y][x]
    png.write_gray(path, img, W, H)
    print(f"wrote {path} ({W}x{H}, {len(tiles)} tiles)")

def sheet_scaled(tiles_, cols, path, scale=4, gap=1):
    if not tiles_:
        print("no tiles"); return
    th=len(tiles_[0]); tw=len(tiles_[0][0])
    rowsN=(len(tiles_)+cols-1)//cols
    W=(cols*(tw+gap)+gap)*scale; H=(rowsN*(th+gap)+gap)*scale
    img=[bytearray([64])*W for _ in range(H)]
    for i,t in enumerate(tiles_):
        cx=((i%cols)*(tw+gap)+gap)*scale; cy=((i//cols)*(th+gap)+gap)*scale
        for y in range(th):
            for x in range(tw):
                v=t[y][x]
                for sy in range(scale):
                    row=img[cy+y*scale+sy]
                    for sx in range(scale):
                        row[cx+x*scale+sx]=v
    png.write_gray(path, img, W, H)
    print(f"wrote {path} ({W}x{H}, {len(tiles_)} tiles)")
