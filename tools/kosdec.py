"""Kosinski decompressor for the US dialogue trees.

ps4disasm/script/compress_script.py only encodes (via compressors/koscmp);
this is the inverse, so the US text in `script/dialogue N.bin` - and the same
bytes inside `Phantasy Star IV [Bugfix v1.5].bin` - can be read without an
emulator.  Checked by decompressing all 43 trees and by matching tree 10
against the RAM copy in a BlastEm state.

    python tools/kosdec.py "ps4disasm/script/dialogue 10.bin" out.unc [offset]
"""
import sys


def kosdec(data, pos=0):
    out = bytearray()
    class B:
        pass
    st = B(); st.pos = pos; st.desc = 0; st.bits = 0
    def read_desc():
        st.desc = data[st.pos] | (data[st.pos+1] << 8); st.pos += 2; st.bits = 16
    def bit():
        b = st.desc & 1; st.desc >>= 1; st.bits -= 1
        if st.bits == 0: read_desc()   # Kosinski refills eagerly, before the next data byte
        return b
    read_desc()
    while True:
        if bit():
            out.append(data[st.pos]); st.pos += 1; continue
        if bit():
            lo = data[st.pos]; hi = data[st.pos+1]; st.pos += 2
            off = ((hi & 0xF8) << 5) | lo; off -= 0x2000
            cnt = hi & 7
            if cnt == 0:
                b3 = data[st.pos]; st.pos += 1
                if b3 == 0: break
                if b3 == 1: continue
                cnt = b3 + 1
            else:
                cnt += 2
        else:
            cnt = (bit() << 1); cnt |= bit(); cnt += 2
            off = data[st.pos] - 0x100; st.pos += 1
        for _ in range(cnt):
            out.append(out[len(out) + off])
    return bytes(out), st.pos
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    o, end = kosdec(d, int(sys.argv[3], 0) if len(sys.argv) > 3 else 0)
    open(sys.argv[2], 'wb').write(o)
    print(len(o), 'bytes; compressed consumed', end)
