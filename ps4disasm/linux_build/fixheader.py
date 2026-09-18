#!/usr/bin/env python3
import sys
import io

def readbytes(f, chunksize = 8192):
    while True:
        chunk = f.read(chunksize)
        if not chunk:
            break
        for b in chunk:
            yield b

with open(sys.argv[1], 'rb') as f:
    header = f.read(512)
    # header[0x18e] and header[0x18f] will be checksum
    rombytes = readbytes(f)
    cksum = 0
    while True:
        try:
            hi = next(rombytes)
            lo = next(rombytes)
            cksum += hi*256 + lo
        except StopIteration:
            break
    cksum &= 0xFFFF
    
with open(sys.argv[1], 'r+b', buffering=0) as f:
    f.seek(0x18E)
    f.write(bytes([((cksum & 0xFF00) >> 8), (cksum & 0xFF)]))

