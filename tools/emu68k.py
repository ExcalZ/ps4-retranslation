"""A tiny 68000 interpreter, for executing patch routines against an oracle.

Not a general emulator - it decodes only the instruction subset the hand-built
patches in this project use, and raises on anything else rather than guessing.
That is deliberate: a silent wrong decode would produce confident, wrong
verification, which is worse than no verification.

Existing practice here has been to assemble a routine, disassemble it, and read
it back. That catches encoding slips but not logic, which is why the half-width
patch is still recorded as "not yet run under an emulator". This runs it.

Flags: only Z and C are modelled, because those are the only ones the routines
branch on. An instruction that would set others sets Z/C correctly and leaves
the rest alone.
"""


class Trap(Exception):
    pass


class CPU:
    SENTINEL = 0xDEAD00

    def __init__(self, mem, pc=0, sp=0xFFF000):
        self.m = mem                 # dict-like: bytearray with .base offset
        self.d = [0] * 8
        self.a = [0] * 8
        self.a[7] = sp
        self.pc = pc
        self.Z = False
        self.C = False
        self.N = False
        self._N_valid = False       # nothing has computed N yet
        self.steps = 0
        self.on_pc = {}          # addr -> callback(cpu), for observing calls
        self.a[7] -= 4
        self.wl(self.a[7], self.SENTINEL)

    # ---------------------------------------------------------- flags
    # N carries a validity bit.  Most handlers in here set Z and C but not N,
    # and a stale N makes bmi/bpl return a plausible WRONG answer instead of
    # raising - the single failure mode this interpreter exists to avoid.  It
    # already refuses to guess at an unknown opcode; this makes it refuse to
    # guess at an uncomputed condition too.
    #
    # Assigning Z marks N unknown; assigning N marks it known.  Audited across
    # every handler: none assigns N without assigning Z first, so a handler
    # that computes both ends up valid and one that computes only Z does not.
    # Instructions that touch no flags leave both alone, as the hardware does.
    @property
    def Z(self):
        return self._Z

    @Z.setter
    def Z(self, v):
        self._Z = v
        self._N_valid = False

    @property
    def N(self):
        return self._N

    @N.setter
    def N(self, v):
        self._N = v
        self._N_valid = True

    # ---------------------------------------------------------- memory
    def rb(self, addr): return self.m[addr & 0xFFFFFF]

    def wb(self, addr, v): self.m[addr & 0xFFFFFF] = v & 0xFF

    def rw(self, addr):
        a = addr & 0xFFFFFF
        return (self.m[a] << 8) | self.m[a + 1]

    def rl(self, addr):
        return (self.rw(addr) << 16) | self.rw(addr + 2)

    def ww(self, addr, v):
        self.wb(addr, (v >> 8) & 0xFF)
        self.wb(addr + 1, v & 0xFF)

    def wl(self, addr, v):
        for i in range(4):
            self.wb(addr + i, (v >> (8 * (3 - i))) & 0xFF)

    def fetch(self):
        w = self.rw(self.pc)
        self.pc += 2
        return w

    # ---------------------------------------------------------- helpers
    @staticmethod
    def _s16(v): return v - 0x10000 if v & 0x8000 else v

    def setd_w(self, r, v):
        self.d[r] = (self.d[r] & 0xFFFF0000) | (v & 0xFFFF)

    def setd_b(self, r, v):
        self.d[r] = (self.d[r] & 0xFFFFFF00) | (v & 0xFF)

    def run(self, limit=200000):
        while True:
            self.steps += 1
            if self.steps > limit:
                raise Trap(f'ran away past {limit} instructions')
            if self.step():
                return

    # ---------------------------------------------------------- decode
    def step(self):
        pc0 = self.pc
        cb = self.on_pc.get(pc0)
        if cb:
            cb(self)
        op = self.fetch()

        if op == 0x4E75:                                   # rts
            ret = self.rl(self.a[7])
            self.a[7] += 4
            if ret == self.SENTINEL:
                return True
            self.pc = ret
            return False

        if (op & 0xFFF0) == 0x4E40:                        # trap #n
            # The game's trap handlers (fill, copy, table dispatch) are plain
            # code behind the vector table; run them as the hardware would.
            self.a[7] -= 4
            self.wl(self.a[7], self.pc)
            self.a[7] -= 2
            self.wb(self.a[7], 0x27)
            self.wb(self.a[7] + 1, 0x00)
            self.pc = self.rl(0x80 + (op & 0xF) * 4)
            return False

        if op == 0x4E73:                                   # rte
            self.a[7] += 2
            self.pc = self.rl(self.a[7])
            self.a[7] += 4
            return False

        if op == 0x4EF9:                                   # jmp (xxx).l
            self.pc = (self.fetch() << 16) | self.fetch()
            return False

        if op == 0x4EBA:                                   # jsr d16(pc)
            base = self.pc
            tgt = (base + self._s16(self.fetch())) & 0xFFFFFF
            self.a[7] -= 4
            self.wl(self.a[7], self.pc)
            self.pc = tgt
            return False

        if op == 0x4EFA:                                   # jmp d16(pc)
            base = self.pc
            self.pc = (base + self._s16(self.fetch())) & 0xFFFFFF
            return False

        if (op & 0xFFC0) == 0x4E90:                        # jsr (An)
            tgt = self.a[op & 7] & 0xFFFFFF
            self.a[7] -= 4
            self.wl(self.a[7], self.pc)
            self.pc = tgt
            return False

        if op == 0x4EB9:                                   # jsr (xxx).l
            tgt = (self.fetch() << 16) | self.fetch()
            self.a[7] -= 4
            self.wl(self.a[7], self.pc)
            self.pc = tgt
            return False

        if (op & 0xFFF8) == 0x4840:                        # swap Dn
            r = op & 7
            v = self.d[r]
            self.d[r] = ((v << 16) | (v >> 16)) & 0xFFFFFFFF
            self.Z = (self.d[r] == 0)
            return False

        # move.w (xxx).l,Dn  /  move.w Dn,(xxx).l
        if (op & 0xF1FF) == 0x3039:
            ea = (self.fetch() << 16) | self.fetch()
            v = self.rw(ea)
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            return False
        if (op & 0xFFF8) == 0x33C0:
            v = self.d[op & 7] & 0xFFFF
            ea = (self.fetch() << 16) | self.fetch()
            self.wb(ea, v >> 8)
            self.wb(ea + 1, v & 0xFF)
            return False

        # move.w (xxx).l,(xxx).l
        if op == 0x33F9:
            src = (self.fetch() << 16) | self.fetch()
            dst = (self.fetch() << 16) | self.fetch()
            v = self.rw(src)
            self.wb(dst, v >> 8)
            self.wb(dst + 1, v & 0xFF)
            return False

        # move.w #imm,(xxx).l
        if op == 0x33FC:
            v = self.fetch()
            ea = (self.fetch() << 16) | self.fetch()
            self.wb(ea, v >> 8)
            self.wb(ea + 1, v & 0xFF)
            return False

        # move.w #imm,-(a7)
        if op == 0x3F3C:
            v = self.fetch()
            self.a[7] -= 2
            self.wb(self.a[7], v >> 8)
            self.wb(self.a[7] + 1, v & 0xFF)
            self.Z = (v == 0)
            return False

        # move.w Dn,(An)+
        if (op & 0xF1F8) == 0x30C0:
            an = (op >> 9) & 7
            v = self.d[op & 7] & 0xFFFF
            self.wb(self.a[an], v >> 8)
            self.wb(self.a[an] + 1, v & 0xFF)
            self.a[an] += 2
            return False

        # move.w Dn,-(a7)  /  move.w (a7)+,Dn
        if (op & 0xFFF8) == 0x3F00:
            v = self.d[op & 7] & 0xFFFF
            self.a[7] -= 2
            self.wb(self.a[7], v >> 8); self.wb(self.a[7] + 1, v & 0xFF)
            return False
        if (op & 0xF1FF) == 0x301F:
            v = self.rw(self.a[7]); self.a[7] += 2
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            return False

        # move.l An,Dn
        if (op & 0xF1F8) == 0x2008:
            v = self.a[op & 7]
            self.d[(op >> 9) & 7] = v
            self.Z = (v == 0)
            return False

        # lsr.l #n,Dn
        if (op & 0xF1F8) == 0xE088:
            n = ((op >> 9) & 7) or 8
            r = op & 7
            self.d[r] = (self.d[r] & 0xFFFFFFFF) >> n
            self.Z = (self.d[r] == 0)
            return False

        # addi.w #imm,Dn
        if (op & 0xFFF8) == 0x0640:
            imm = self.fetch(); r = op & 7
            v = ((self.d[r] & 0xFFFF) + imm) & 0xFFFF
            self.setd_w(r, v); self.Z = (v == 0)
            return False

        # subi.l #imm,Dn
        if (op & 0xFFF8) == 0x0480:
            imm = (self.fetch() << 16) | self.fetch()
            r = op & 7
            v = (self.d[r] - imm) & 0xFFFFFFFF
            self.d[r] = v
            self.Z = (v == 0)
            return False

        # subi.w #imm,Dn
        if (op & 0xFFF8) == 0x0440:
            imm = self.fetch()
            r = op & 7
            v = ((self.d[r] & 0xFFFF) - imm) & 0xFFFF
            self.setd_w(r, v)
            self.Z = (v == 0)
            return False

        # move.l An,-(a7)
        if (op & 0xFFF8) == 0x2F08:
            self.a[7] -= 4
            self.wl(self.a[7], self.a[op & 7])
            return False

        # movea.l (a7)+,An
        if (op & 0xF1FF) == 0x205F:
            self.a[(op >> 9) & 7] = self.rl(self.a[7]) & 0xFFFFFF
            self.a[7] += 4
            return False

        # addq.l #n,a7
        if (op & 0xF1FF) == 0x508F:
            self.a[7] += ((op >> 9) & 7) or 8
            return False

        # move.l #imm,Dn
        if (op & 0xF1FF) == 0x203C:
            v = (self.fetch() << 16) | self.fetch()
            self.d[(op >> 9) & 7] = v
            self.Z = (v == 0)
            return False

        # movem.l <list>,-(a7)  /  movem.l (a7)+,<list>
        if op in (0x48E7, 0x4CDF):
            mask = self.fetch()
            regs = self.d + self.a
            if op == 0x48E7:
                order = list(range(16))[::-1]
                for i, bit in enumerate(order):
                    if mask & (1 << i):
                        self.a[7] -= 4
                        self.wl(self.a[7], regs[bit])
            else:
                for i in range(16):
                    if mask & (1 << i):
                        v = self.rl(self.a[7])
                        self.a[7] += 4
                        if i < 8:
                            self.d[i] = v
                        else:
                            self.a[i - 8] = v & 0xFFFFFF
            return False
        if op == 0x4E71:                                   # nop
            return False

        # moveq #n,Dn
        if (op & 0xF100) == 0x7000:
            n = op & 0xFF
            n = n - 256 if n & 0x80 else n
            self.d[(op >> 9) & 7] = n & 0xFFFFFFFF
            self.Z = (n == 0)
            self.C = False
            return False

        # clr.l (An)+
        if (op & 0xFFF8) == 0x4298:
            an = op & 7
            self.wl(self.a[an], 0)
            self.a[an] += 4
            self.Z = True
            return False

        # movea.l An,Am
        if (op & 0xF1F8) == 0x2048:
            self.a[(op >> 9) & 7] = self.a[op & 7]
            return False

        # move.b (An)+,Dn
        if (op & 0xF1F8) == 0x1018:
            an = op & 7
            v = self.rb(self.a[an])
            self.a[an] += 1
            self.setd_b((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # move.b (An),Dn
        if (op & 0xF1F8) == 0x1010:
            v = self.rb(self.a[op & 7])
            self.setd_b((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # move.l #imm,(An)+
        if (op & 0xF1FF) == 0x20FC:
            v = (self.fetch() << 16) | self.fetch()
            an = (op >> 9) & 7
            self.wl(self.a[an], v)
            self.a[an] += 4
            self.Z = (v == 0)
            self.C = False
            return False

        # move.l An,(Am)+  /  move.l An,(Am)
        if (op & 0xF1F8) == 0x20C8:
            am = (op >> 9) & 7
            self.wl(self.a[am], self.a[op & 7]); self.a[am] += 4
            return False
        if (op & 0xF1F8) == 0x2088:
            self.wl(self.a[(op >> 9) & 7], self.a[op & 7])
            return False

        # move.l (An),(Am)+
        if (op & 0xF1F8) == 0x20D0:
            v = self.rl(self.a[op & 7])
            am = (op >> 9) & 7
            self.wl(self.a[am], v)
            self.a[am] += 4
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            self.C = False
            return False

        # move.b/move.w (d8,An,Xn.w),Dn
        if (op & 0xF1F8) in (0x1030, 0x3030):
            ext = self.fetch()
            an = op & 7
            ir = (ext >> 12) & 7
            idx = self.a[ir] if ext & 0x8000 else self.d[ir]
            if not (ext & 0x0800):                 # word index, sign extended
                idx = self._s16(idx & 0xFFFF)
            d8 = ext & 0xFF
            d8 = d8 - 256 if d8 & 0x80 else d8
            ea = (self.a[an] + d8 + idx) & 0xFFFFFF
            if (op & 0xF1F8) == 0x1030:
                v = self.rb(ea)
                self.setd_b((op >> 9) & 7, v)
            else:
                v = self.rw(ea)
                self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False

        # move.w (An),Dn  /  move.w Dn,(An)
        if (op & 0xF1F8) == 0x3010:
            v = self.rw(self.a[op & 7])
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False
        if (op & 0xF1F8) == 0x3080:
            an = (op >> 9) & 7
            v = self.d[op & 7] & 0xFFFF
            self.wb(self.a[an], v >> 8); self.wb(self.a[an] + 1, v & 0xFF)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False

        # move.w (d16,An),Dn
        if (op & 0xF1F8) == 0x3028:
            disp = self._s16(self.fetch())
            v = self.rw((self.a[op & 7] + disp) & 0xFFFFFF) & 0xFFFF
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False

        # move.w #imm,Dn
        if (op & 0xF1FF) == 0x303C:
            v = self.fetch()
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.C = False
            return False

        # move.w Dn,Dm
        if (op & 0xF1F8) == 0x3000:
            v = self.d[op & 7] & 0xFFFF
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.C = False
            return False

        # cmpi.b #imm,Dn
        if (op & 0xFFF8) == 0x0C00:
            imm = self.fetch() & 0xFF
            dst = self.d[op & 7] & 0xFF
            self.C = dst < imm
            self.Z = dst == imm
            return False

        # cmpi.w #imm,Dn
        if (op & 0xFFF8) == 0x0C40:
            imm = self.fetch()
            dst = self.d[op & 7] & 0xFFFF
            self.C = dst < imm
            self.Z = dst == imm
            return False

        # andi.w #imm,Dn
        if (op & 0xFFF8) == 0x0240:
            imm = self.fetch()
            v = (self.d[op & 7] & 0xFFFF) & imm
            self.setd_w(op & 7, v)
            self.Z = (v == 0)
            self.C = False
            return False

        # lea (abs).l,An
        if (op & 0xF1FF) == 0x41F9:
            self.a[(op >> 9) & 7] = (self.fetch() << 16) | self.fetch()
            return False

        # lea (d16,An),Am
        if (op & 0xF1F8) == 0x41E8:
            d = self._s16(self.fetch())
            self.a[(op >> 9) & 7] = (self.a[op & 7] + d) & 0xFFFFFF
            return False

        # adda.w Dn,An
        if (op & 0xF1F8) == 0xD0C0:
            self.a[(op >> 9) & 7] = (self.a[(op >> 9) & 7]
                                     + self._s16(self.d[op & 7] & 0xFFFF)) & 0xFFFFFF
            return False

        # add.w Dn,Dm
        if (op & 0xF1F8) == 0xD040:
            v = (self.d[(op >> 9) & 7] + self.d[op & 7]) & 0xFFFF
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            return False

        # addq.w / subq.w #n,Dn
        if (op & 0xF1F8) in (0x5040, 0x5140):
            n = (op >> 9) & 7 or 8
            r = op & 7
            a = self.d[r] & 0xFFFF
            if (op & 0x0100) == 0:
                v = a + n
                carry = v > 0xFFFF
            else:
                v = a - n
                carry = a < n
            v &= 0xFFFF
            self.setd_w(r, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = carry
            return False

        # tst.w (xxx).w
        if op == 0x4A78:
            ea = self._s16(self.fetch()) & 0xFFFFFF
            self.Z = (self.rw(ea) == 0)
            self.C = False
            return False

        # eor.w Dn,Dm
        if (op & 0xF1F8) == 0xB140:
            v = ((self.d[(op >> 9) & 7] & 0xFFFF) ^ (self.d[op & 7] & 0xFFFF))
            self.setd_w(op & 7, v)
            self.Z = (v == 0)
            return False

        # eor.l Dn,Dm
        if (op & 0xF1F8) == 0xB180:
            v = (self.d[(op >> 9) & 7] ^ self.d[op & 7]) & 0xFFFFFFFF
            self.d[op & 7] = v
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            self.C = False
            return False

        # eor.b Dn,Dm
        if (op & 0xF1F8) == 0xB100:
            v = ((self.d[(op >> 9) & 7] ^ self.d[op & 7]) & 0xFF)
            self.d[op & 7] = (self.d[op & 7] & 0xFFFFFF00) | v
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # move.b #imm,(xxx).l
        if op == 0x13FC:
            v = self.fetch() & 0xFF
            a = (self.fetch() << 16) | self.fetch()
            self.wb(a, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # move.w #imm,(An)+
        if (op & 0xF1FF) == 0x30FC:
            v = self.fetch() & 0xFFFF
            an = (op >> 9) & 7
            self.wb(self.a[an], v >> 8)
            self.wb(self.a[an] + 1, v & 0xFF)
            self.a[an] += 2
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False

        # cmp.w (An)+,Dn
        if (op & 0xF1F8) == 0xB058:
            an = op & 7
            src = self.rw(self.a[an]) & 0xFFFF
            self.a[an] += 2
            dst = self.d[(op >> 9) & 7] & 0xFFFF
            r = (dst - src) & 0xFFFF
            self.Z = (r == 0)
            self.N = bool(r & 0x8000)
            self.C = dst < src
            return False

        # clr.b / clr.w / tst.b  (xxx).w   and   move.b Dn,(xxx).w
        if op in (0x4238, 0x4278, 0x4A38):
            ea = self._s16(self.fetch()) & 0xFFFFFF
            if op == 0x4A38:
                v = self.rb(ea)
                self.Z = (v == 0)
                self.N = bool(v & 0x80)
            elif op == 0x4238:
                self.wb(ea, 0)
                self.Z = True
                self.N = False
            else:
                self.wb(ea, 0)
                self.wb(ea + 1, 0)
                self.Z = True
                self.N = False
            self.C = False
            return False

        if (op & 0xFFF8) == 0x11C0:                 # move.b Dn,(xxx).w
            v = self.d[op & 7] & 0xFF
            self.wb(self._s16(self.fetch()) & 0xFFFFFF, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # jmp d8(pc,Xn)   -- the window control-code dispatch
        if op == 0x4EFB:
            base = self.pc                      # the extension word's address
            ext = self.fetch()
            idx = self.a[(ext >> 12) & 7] if ext & 0x8000 else self.d[(ext >> 12) & 7]
            if ext & 0x0800:
                idx &= 0xFFFFFFFF
                if idx & 0x80000000:
                    idx -= 0x100000000
            else:
                idx &= 0xFFFF
                if idx & 0x8000:
                    idx -= 0x10000
            disp = ext & 0xFF
            if disp & 0x80:
                disp -= 256
            self.pc = (base + disp + idx) & 0xFFFFFF
            return False

        # move.w (xxx).l,d16(An)   -- source extension words come first
        if (op & 0xF1FF) == 0x3179:
            src = (self.fetch() << 16) | self.fetch()
            disp = self._s16(self.fetch())
            v = self.rw(src) & 0xFFFF
            ea = (self.a[(op >> 9) & 7] + disp) & 0xFFFFFF
            self.wb(ea, v >> 8)
            self.wb(ea + 1, v & 0xFF)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False

        # move.b Dn,Dm
        if (op & 0xF1F8) == 0x1000:
            v = self.d[op & 7] & 0xFF
            self.setd_b((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # move.b Dn,(An)
        if (op & 0xF1F8) == 0x1080:
            v = self.d[op & 7] & 0xFF
            self.wb(self.a[(op >> 9) & 7], v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # movea.w Dn,An   (sign-extends to 32 bits, touches no flags)
        if (op & 0xF1F8) == 0x3040:
            v = self.d[op & 7] & 0xFFFF
            self.a[(op >> 9) & 7] = v - 0x10000 if v & 0x8000 else v
            return False

        # clr.b (xxx).l
        if op == 0x4239:
            a = (self.fetch() << 16) | self.fetch()
            self.wb(a, 0)
            self.Z = True
            self.N = False
            self.C = False
            return False

        # sub.w Dm,Dn
        if (op & 0xF1F8) == 0x9040:
            dn = (op >> 9) & 7
            a = self.d[dn] & 0xFFFF
            b = self.d[op & 7] & 0xFFFF
            r = (a - b) & 0xFFFF
            self.setd_w(dn, r)
            self.Z = (r == 0)
            self.N = bool(r & 0x8000)
            self.C = a < b
            return False

        # move.l (An)+,(Am)   -- the strip copy into the VDP data port
        if (op & 0xF1F8) == 0x2098:
            sa = op & 7
            v = self.rl(self.a[sa])
            self.a[sa] += 4
            self.wl(self.a[(op >> 9) & 7], v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            self.C = False
            return False

        # adda.l Dn,An   (does not affect flags)
        if (op & 0xF1F8) == 0xD1C0:
            an = (op >> 9) & 7
            self.a[an] = (self.a[an] + self.d[op & 7]) & 0xFFFFFFFF
            return False

        # cmpi.b #imm,(An)
        if (op & 0xFFF8) == 0x0C10:
            imm = self.fetch() & 0xFF
            v = self.rb(self.a[op & 7])
            r = (v - imm) & 0xFF
            self.Z = (r == 0)
            self.N = bool(r & 0x80)
            self.C = v < imm
            return False

        # cmpi.b #imm,(An)+
        if (op & 0xFFF8) == 0x0C18:
            imm = self.fetch() & 0xFF
            an = op & 7
            v = self.rb(self.a[an])
            self.a[an] += 1
            r = (v - imm) & 0xFF
            self.Z = (r == 0)
            self.N = bool(r & 0x80)
            self.C = v < imm
            return False

        # move.w An,Dn
        if (op & 0xF1F8) == 0x3008:
            v = self.a[op & 7] & 0xFFFF
            self.setd_w((op >> 9) & 7, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            self.C = False
            return False

        # tst.b (xxx).l
        if op == 0x4A39:
            a = (self.fetch() << 16) | self.fetch()
            v = self.rb(a)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # move.l Dn,-(sp)
        if (op & 0xFFF8) == 0x2F00:
            v = self.d[op & 7] & 0xFFFFFFFF
            self.a[7] = (self.a[7] - 4) & 0xFFFFFFFF
            self.wl(self.a[7], v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            self.C = False
            return False

        # move.l (sp)+,Dn
        if (op & 0xF1FF) == 0x201F:
            v = self.rl(self.a[7])
            self.a[7] = (self.a[7] + 4) & 0xFFFFFFFF
            self.d[(op >> 9) & 7] = v
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            self.C = False
            return False

        # cmpa.l #imm,An
        if (op & 0xF1FF) == 0xB1FC:
            imm = (self.fetch() << 16) | self.fetch()
            an = (self.a[(op >> 9) & 7]) & 0xFFFFFFFF
            r = (an - imm) & 0xFFFFFFFF
            self.Z = (r == 0)
            self.N = bool(r & 0x80000000)
            self.C = an < imm
            return False

        # tst.b Dn
        if (op & 0xFFF8) == 0x4A00:
            self.Z = (self.d[op & 7] & 0xFF) == 0
            self.C = False
            self.N = bool(self.d[op & 7] & 0x80)
            return False

        # tst.w Dn
        if (op & 0xFFF8) == 0x4A40:
            self.Z = (self.d[op & 7] & 0xFFFF) == 0
            self.C = False
            self.N = bool(self.d[op & 7] & 0x8000)
            return False

        # lsl/lsr/asl/asr .w  #n,Dn  and  Dm,Dn
        # bit 3 clear selects the arithmetic form; for a left shift that is
        # identical to the logical one, for a right shift it sign-extends.
        if (op & 0xF1F8) in (0xE048, 0xE148, 0xE068, 0xE168,
                             0xE040, 0xE140, 0xE060, 0xE160):
            r = op & 7
            left = bool(op & 0x0100)
            byreg = bool(op & 0x0020)
            arith = not (op & 0x0008)
            cnt = (self.d[(op >> 9) & 7] & 63) if byreg else (((op >> 9) & 7) or 8)
            v = self.d[r] & 0xFFFF
            if left:
                v = (v << cnt) & 0xFFFF
            elif arith:
                sv = v - 0x10000 if v & 0x8000 else v
                v = (sv >> cnt) & 0xFFFF
            else:
                v = v >> cnt
            self.setd_w(r, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x8000)
            return False

        # or.b Dn,(An) / or.b Dn,(d16,An)
        if (op & 0xF1C0) == 0x8100:
            mode, reg = (op >> 3) & 7, op & 7
            if mode == 2:
                ea = self.a[reg]
            elif mode == 5:
                ea = (self.a[reg] + self._s16(self.fetch())) & 0xFFFFFF
            else:
                raise Trap(f'{pc0:06X}: or.b to unsupported mode {mode}')
            v = self.rb(ea) | (self.d[(op >> 9) & 7] & 0xFF)
            self.wb(ea, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80)
            self.C = False
            return False

        # dbf Dn,disp
        if (op & 0xFFF8) == 0x51C8:
            d = self._s16(self.fetch())
            r = op & 7
            v = (self.d[r] - 1) & 0xFFFF
            self.setd_w(r, v)
            if v != 0xFFFF:
                self.pc = pc0 + 2 + d
            return False

        # bsr with 8-bit or 16-bit displacement
        if (op & 0xFF00) == 0x6100:
            disp = op & 0xFF
            base = self.pc
            if disp == 0:
                disp = self._s16(self.fetch())
            elif disp & 0x80:
                disp -= 0x100
            self.a[7] -= 4
            self.wl(self.a[7], self.pc)
            self.pc = (base + disp) & 0xFFFFFF
            return False

        # Bcc / BRA with 8-bit or 16-bit displacement
        if (op & 0xFF00) in (0x6000, 0x6200, 0x6400, 0x6500, 0x6600, 0x6700, 0x6A00, 0x6B00, 0x6300,
                             0x6C00, 0x6D00, 0x6E00, 0x6F00):
            cond = op & 0xFF00
            d8 = op & 0xFF
            if d8 == 0:
                d = self._s16(self.fetch())
                base = pc0 + 2
            else:
                d = d8 - 256 if d8 & 0x80 else d8
                base = pc0 + 2
            if cond in (0x6A00, 0x6B00, 0x6C00, 0x6D00, 0x6E00, 0x6F00) and not self._N_valid:
                raise Trap('%06X: %s depends on N, which no preceding '
                           'instruction computed' %
                           (pc0, 'bpl' if cond == 0x6A00 else 'bmi'))
            take = {0x6000: True, 0x6400: not self.C, 0x6500: self.C,
                    0x6600: not self.Z, 0x6700: self.Z,
                    0x6A00: not self.N, 0x6B00: self.N,
                    0x6300: (self.C or self.Z),
                    0x6200: not (self.C or self.Z),
                    # signed compares: V is not modelled, so these hold only
                    # when the compare did not overflow - true of every
                    # small-magnitude compare in the window code
                    0x6C00: not self.N, 0x6D00: self.N,
                    0x6E00: not (self.N or self.Z), 0x6F00: (self.N or self.Z)}[cond]
            if take:
                self.pc = base + d
            return False

        # addq.l / subq.l #n,An   (full 32-bit, no flags either way)
        if (op & 0xF1F8) in (0x5088, 0x5188):
            n = (op >> 9) & 7 or 8
            r = op & 7
            d = n if (op & 0x0100) == 0 else -n
            self.a[r] = (self.a[r] + d) & 0xFFFFFFFF
            return False

        # or.l Dm,Dn   (data register destination)
        if (op & 0xF1F8) == 0x8080:
            dn = (op >> 9) & 7; dm = op & 7
            v = (self.d[dn] | self.d[dm]) & 0xFFFFFFFF
            self.d[dn] = v
            self.Z = (v == 0)
            return False

        # or.l Dn,(An)
        if (op & 0xF1F8) == 0x8190:
            dn = (op >> 9) & 7; an = op & 7
            addr = self.a[an]
            v = self.rl(addr) | self.d[dn]
            self.wl(addr, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            return False

        # or.l Dn,(d16,An)
        if (op & 0xF1F8) == 0x81A8:
            dn = (op >> 9) & 7; an = op & 7
            addr = (self.a[an] + self._s16(self.fetch())) & 0xFFFFFF
            v = self.rl(addr) | self.d[dn]
            self.wl(addr, v)
            self.Z = (v == 0)
            self.N = bool(v & 0x80000000)
            return False

        # lsl.l #n,Dn
        if (op & 0xF1F8) == 0xE188:
            n = (op >> 9) & 7 or 8
            r = op & 7
            v = (self.d[r] << n) & 0xFFFFFFFF
            self.d[r] = v
            self.Z = (v == 0)
            return False

        # move.b Dn,(xxx).w
        if (op & 0xF1FF) == 0x11C0:
            dn = (op >> 9) & 7
            addr = self._s16(self.fetch()) & 0xFFFFFF
            self.wb(addr, self.d[dn] & 0xFF)
            return False

        # move.l Dn,Dm
        if (op & 0xF1F8) == 0x2000:
            dm = (op >> 9) & 7; dn = op & 7
            self.d[dm] = self.d[dn]
            self.Z = (self.d[dm] == 0)
            return False

        # move.l (d16,An),Dn
        if (op & 0xF1F8) == 0x2028:
            dn=(op>>9)&7; an=op&7
            self.d[dn]=self.rl((self.a[an]+self._s16(self.fetch()))&0xFFFFFF)
            self.Z=(self.d[dn]==0); return False

        # move.l Dn,(An)
        if (op & 0xF1F8) == 0x2080:
            an=(op>>9)&7; dn=op&7
            self.wl(self.a[an], self.d[dn]); return False

        # move.l Dn,(d16,An)
        if (op & 0xF1F8) == 0x2140:
            an=(op>>9)&7; dn=op&7
            self.wl((self.a[an]+self._s16(self.fetch()))&0xFFFFFF, self.d[dn]); return False

        # cmp.l (An),Dn
        if (op & 0xF1F8) == 0xB090:
            dn=(op>>9)&7; an=op&7
            a=self.d[dn]&0xFFFFFFFF; b=self.rl(self.a[an])
            self.Z=(a==b); self.C=(a<b); return False

        # cmp.l (d16,An),Dn
        if (op & 0xF1F8) == 0xB0A8:
            dn=(op>>9)&7; an=op&7
            a=self.d[dn]&0xFFFFFFFF; b=self.rl((self.a[an]+self._s16(self.fetch()))&0xFFFFFF)
            self.Z=(a==b); self.C=(a<b); return False

        # cmp.w Dm,Dn
        if (op & 0xF1F8) == 0xB040:
            dn=(op>>9)&7; dm=op&7
            a=self.d[dn]&0xFFFF; b=self.d[dm]&0xFFFF
            self.Z=(a==b); self.C=(a<b); return False

        # addq.w #n,(xxx).l
        if (op & 0xF1FF) == 0x5079:
            n=(op>>9)&7 or 8
            addr=((self.fetch()<<16)|self.fetch())&0xFFFFFF
            v=(self.rw(addr)+n)&0xFFFF
            self.wb(addr,v>>8); self.wb(addr+1,v&0xFF)
            self.Z=(v==0); return False

        # addq.b / subq.b #n,(xxx).l
        if (op & 0xF1FF) in (0x5039, 0x5139):
            n=(op>>9)&7 or 8
            addr=((self.fetch()<<16)|self.fetch())&0xFFFFFF
            v=self.rb(addr)
            v=(v-n if op & 0x0100 else v+n)&0xFF
            self.wb(addr,v)
            self.Z=(v==0); return False

        # move.b (xxx).w,Dn
        if (op & 0xF1FF) == 0x1038:
            dn=(op>>9)&7
            addr=self._s16(self.fetch()) & 0xFFFFFF
            self.setd_b(dn, self.rb(addr))
            self.Z=((self.d[dn]&0xFF)==0); return False

        # tst.w (a7)
        if op == 0x4A57:
            self.Z = (self.rw(self.a[7]) == 0)
            return False

        # move.w (xxx).l,(An,Xn.w)
        if (op & 0xF1FF) == 0x31B9:
            an=(op>>9)&7
            src=((self.fetch()<<16)|self.fetch())&0xFFFFFF
            ext=self.fetch()
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            addr=(self.a[an]+idx+disp)&0xFFFFFF
            v=self.rw(src)
            self.wb(addr, v>>8); self.wb(addr+1, v&0xFF)
            return False

        # move.w (An,Xn.w),(xxx).l
        if (op & 0xFFF8) == 0x33F0:
            an=op&7
            ext=self.fetch()
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            src=(self.a[an]+idx+disp)&0xFFFFFF
            dst=((self.fetch()<<16)|self.fetch())&0xFFFFFF
            v=self.rw(src)
            self.wb(dst, v>>8); self.wb(dst+1, v&0xFF)
            return False

        # move.b (An),(Am)+
        if (op & 0xF1F8) == 0x10D0:
            am=(op>>9)&7; an=op&7
            v=self.rb(self.a[an])
            self.wb(self.a[am], v); self.a[am]=(self.a[am]+1)&0xFFFFFFFF
            return False

        # ori.l #imm,Dn
        if (op & 0xFFF8) == 0x0080:
            imm=(self.fetch()<<16)|self.fetch()
            r=op&7
            self.d[r]=(self.d[r]|imm)&0xFFFFFFFF
            self.Z=(self.d[r]==0); return False

        # swap Dn
        if (op & 0xFFF8) == 0x4840:
            r=op&7
            v=self.d[r]
            self.d[r]=((v>>16)|(v<<16))&0xFFFFFFFF
            self.Z=(self.d[r]==0); return False

        # cmp.w (xxx).l,Dn
        if (op & 0xF1FF) == 0xB079:
            dn=(op>>9)&7
            addr=((self.fetch()<<16)|self.fetch())&0xFFFFFF
            a=self.d[dn]&0xFFFF; b=self.rw(addr)
            self.Z=(a==b); self.C=(a<b); return False

        # clr.l Dn
        if (op & 0xFFF8) == 0x4280:
            self.d[op & 7] = 0
            self.Z = True; self.N = False; return False

        # clr.w Dn
        if (op & 0xFFF8) == 0x4240:
            self.setd_w(op & 7, 0)
            self.Z = True; self.N = False; return False

        # ori.w #imm,Dn
        if (op & 0xFFF8) == 0x0040:
            imm=self.fetch(); r=op&7
            v=((self.d[r]&0xFFFF)|imm)&0xFFFF
            self.setd_w(r,v); self.Z=(v==0); return False

        # andi.l #imm,Dn
        if (op & 0xFFF8) == 0x0280:
            imm=(self.fetch()<<16)|self.fetch(); r=op&7
            self.d[r]=(self.d[r]&imm)&0xFFFFFFFF
            self.Z=(self.d[r]==0); return False

        # move.b #imm,(An,Xn.w)
        if (op & 0xF1FF) == 0x11BC:
            an=(op>>9)&7
            imm=self.fetch() & 0xFF          # source ea first
            ext=self.fetch()                 # then the destination index
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            self.wb((self.a[an]+idx+disp)&0xFFFFFF, imm)
            self.Z=(imm==0); return False

        # move.w #imm,(An,Xn.w)
        if (op & 0xF1FF) == 0x31BC:
            an=(op>>9)&7
            imm=self.fetch() & 0xFFFF       # source ea first
            ext=self.fetch()                 # then the destination index
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            a=(self.a[an]+idx+disp)&0xFFFFFF
            self.wb(a,imm>>8); self.wb(a+1,imm)
            self.Z=(imm==0); self.N=bool(imm & 0x8000); self.C=False
            return False

        # addq.b / subq.b #n,(An,Xn.w)
        if (op & 0xF0F8) == 0x5030:
            n=(op>>9)&7 or 8
            sub=bool(op & 0x0100)
            an=op&7
            ext=self.fetch()
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            a=(self.a[an]+idx+disp)&0xFFFFFF
            v=(self.rb(a)-n if sub else self.rb(a)+n)&0xFF
            self.wb(a,v); self.Z=(v==0); return False

        # tst.b (An,Xn.w)
        if (op & 0xFFF8) == 0x4A30:
            an=op&7
            ext=self.fetch()
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            v=self.rb((self.a[an]+idx+disp)&0xFFFFFF)
            self.Z=(v==0); self.N=bool(v&0x80); return False

        # clr.b (An,Xn.w)
        if (op & 0xFFF8) == 0x4230:
            an=op&7
            ext=self.fetch()
            ri=(ext>>12)&7
            idx=(self.a[ri] if ext & 0x8000 else self.d[ri])
            idx=(idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp=ext & 0xFF
            if disp & 0x80: disp -= 0x100
            self.wb((self.a[an]+idx+disp)&0xFFFFFF, 0)
            self.Z=True; return False

        # cmpi.w #imm,(xxx).w   (sign-extended short absolute)
        if op == 0x0C78:
            imm=self.fetch()
            addr=self._s16(self.fetch())&0xFFFFFF
            v=self.rw(addr)
            self.Z=(v==imm); self.C=(v<imm)
            self.N=bool((v-imm)&0x8000); return False

        # cmpi.w #imm,(xxx).l
        if op == 0x0C79:
            imm=self.fetch()
            addr=((self.fetch()<<16)|self.fetch())&0xFFFFFF
            v=self.rw(addr)
            self.Z=(v==imm); self.C=(v<imm)
            self.N=bool((v-imm)&0x8000); return False

        # clr.b (An)+
        if (op & 0xFFF8) == 0x4218:
            an=op&7
            self.wb(self.a[an], 0)
            self.a[an]=(self.a[an]+1)&0xFFFFFFFF
            self.Z=True; return False

        # move.w (An)+,Dn
        if (op & 0xF1F8) == 0x3018:
            dn=(op>>9)&7; an=op&7
            self.setd_w(dn, self.rw(self.a[an]))
            self.a[an]=(self.a[an]+2)&0xFFFFFFFF
            self.Z=((self.d[dn]&0xFFFF)==0); return False

        # lea (xxx).w,An
        if (op & 0xF1FF) == 0x41F8:
            an=(op>>9)&7
            self.a[an]=self._s16(self.fetch()) & 0xFFFFFFFF
            return False

        # move.w (xxx).w,Dn
        if (op & 0xF1FF) == 0x3038:
            dn=(op>>9)&7
            addr=self._s16(self.fetch()) & 0xFFFFFF
            self.setd_w(dn, self.rw(addr))
            self.Z=((self.d[dn]&0xFFFF)==0); return False

        # move.l (An),(Am)+
        if (op & 0xF1F8) == 0x20D0:
            am=(op>>9)&7; an=op&7
            v=self.rl(self.a[an])
            self.wl(self.a[am], v); self.a[am]=(self.a[am]+4)&0xFFFFFFFF
            self.Z=(v==0); return False

        # move.l (d16,An),(Am)+
        if (op & 0xF1F8) == 0x20E8:
            am=(op>>9)&7; an=op&7
            v=self.rl((self.a[an]+self._s16(self.fetch()))&0xFFFFFF)
            self.wl(self.a[am], v); self.a[am]=(self.a[am]+4)&0xFFFFFFFF
            self.Z=(v==0); return False

        # move.w (An),Dn  with postincrement destination: move.w Dn,(Am)+
        if (op & 0xF1F8) == 0x30C0:
            am=(op>>9)&7; dn=op&7
            self.wb(self.a[am], (self.d[dn]>>8)&0xFF)
            self.wb(self.a[am]+1, self.d[dn]&0xFF)
            self.a[am]=(self.a[am]+2)&0xFFFFFFFF
            return False

        # cmp.w (An),Dn
        if (op & 0xF1F8) == 0xB050:
            dn=(op>>9)&7; an=op&7
            a=self.d[dn]&0xFFFF; b=self.rw(self.a[an])
            self.Z=(a==b); self.C=(a<b); self.N=bool((a-b)&0x8000); return False

        # cmp.b (An),Dn
        if (op & 0xF1F8) == 0xB010:
            dn=(op>>9)&7; an=op&7
            a=self.d[dn]&0xFF; b=self.rb(self.a[an])
            self.Z=(a==b); self.C=(a<b); self.N=bool((a-b)&0x80); return False

        # or.w Dm,Dn
        if (op & 0xF1F8) == 0x8040:
            dn=(op>>9)&7; dm=op&7
            v=((self.d[dn]&0xFFFF)|(self.d[dm]&0xFFFF))&0xFFFF
            self.setd_w(dn,v); self.Z=(v==0); return False

        # move.l (An),(d16,Am)
        if (op & 0xF1F8) == 0x2150:
            am=(op>>9)&7; an=op&7
            v=self.rl(self.a[an])
            self.wl((self.a[am]+self._s16(self.fetch()))&0xFFFFFF, v)
            self.Z=(v==0); return False

        # move.l (d16,An),(d16,Am)   -- source extension first, then dest
        if (op & 0xF1F8) == 0x2168:
            am=(op>>9)&7; an=op&7
            src=(self.a[an]+self._s16(self.fetch()))&0xFFFFFF
            dst=(self.a[am]+self._s16(self.fetch()))&0xFFFFFF
            v=self.rl(src); self.wl(dst,v)
            self.Z=(v==0); return False

        # mulu.w #imm,Dn
        if (op & 0xF1FF) == 0xC0FC:
            dn=(op>>9)&7
            imm=self.fetch()
            v=((self.d[dn]&0xFFFF)*imm)&0xFFFFFFFF
            self.d[dn]=v; self.Z=(v==0); return False

        # mulu.w Dm,Dn
        if (op & 0xF1F8) == 0xC0C0:
            dn=(op>>9)&7; dm=op&7
            v=((self.d[dn]&0xFFFF)*(self.d[dm]&0xFFFF))&0xFFFFFFFF
            self.d[dn]=v; self.Z=(v==0); return False

        # move.l (An),Dn
        if (op & 0xF1F8) == 0x2010:
            dn = (op >> 9) & 7; an = op & 7
            self.d[dn] = self.rl(self.a[an])
            self.Z = (self.d[dn] == 0)
            return False

        # move.l (An)+,Dn
        if (op & 0xF1F8) == 0x2018:
            dn = (op >> 9) & 7; an = op & 7
            self.d[dn] = self.rl(self.a[an])
            self.a[an] = (self.a[an] + 4) & 0xFFFFFFFF
            self.Z = (self.d[dn] == 0)
            return False

        # clr.w (xxx).l
        if op == 0x4279:
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            self.wb(addr, 0); self.wb(addr + 1, 0)
            self.Z = True
            return False

        # tst.l (An) / tst.l d16(An)
        if (op & 0xFFF8) == 0x4A90 or (op & 0xFFF8) == 0x4AA8:
            a = self.a[op & 7]
            if (op & 0xFFF8) == 0x4AA8: a = (a + self._s16(self.fetch())) & 0xFFFFFFFF
            v = self.rl(a)
            self.Z = (v == 0); self.N = bool(v & 0x80000000); self.C = False
            return False

        # move.l Dn,(An)+
        if (op & 0xF1F8) == 0x20C0:
            an = (op >> 9) & 7
            v = self.d[op & 7] & 0xFFFFFFFF
            self.wl(self.a[an], v)
            self.a[an] = (self.a[an] + 4) & 0xFFFFFFFF
            self.Z = (v == 0); self.N = bool(v & 0x80000000)
            return False

        # move.b Dn,(An)+
        if (op & 0xF1F8) == 0x10C0:
            an = (op >> 9) & 7
            v = self.d[op & 7] & 0xFF
            self.wb(self.a[an], v)
            self.a[an] = (self.a[an] + 1) & 0xFFFFFFFF
            self.Z = (v == 0); self.N = bool(v & 0x80)
            return False

        # move.b (xxx).l,Dn
        if (op & 0xF1FF) == 0x1039:
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            v = self.rb(addr)
            self.setd_b((op >> 9) & 7, v)
            self.Z = (v == 0); self.N = bool(v & 0x80)
            return False

        # move.b Dn,(An,Xn.w)
        if (op & 0xF1F8) == 0x1180:
            an = (op >> 9) & 7
            ext = self.fetch()
            ri = (ext >> 12) & 7
            idx = (self.a[ri] if ext & 0x8000 else self.d[ri])
            idx = (idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp = ext & 0xFF
            if disp & 0x80: disp -= 0x100
            v = self.d[op & 7] & 0xFF
            self.wb((self.a[an] + idx + disp) & 0xFFFFFF, v)
            self.Z = (v == 0); self.N = bool(v & 0x80)
            return False

        # addq.b #n,(xxx).l
        if (op & 0xF1FF) == 0x5039:
            n = ((op >> 9) & 7) or 8
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            v = (self.rb(addr) + n) & 0xFF
            self.wb(addr, v)
            self.Z = (v == 0); self.N = bool(v & 0x80)
            return False

        # movea.l (xxx).w,An
        if (op & 0xF1FF) == 0x2078:
            addr = self._s16(self.fetch()) & 0xFFFFFF
            self.a[(op >> 9) & 7] = self.rl(addr)
            return False

        # tst.w (xxx).l
        if op == 0x4A79:
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            self.Z = (self.rw(addr) == 0)
            return False

        # --- forms the composed-name path (vwf_menu_strips=0) needed ---
        # clr.l (xxx).l
        if op == 0x42B9:
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            self.wl(addr, 0)
            self.Z = True; self.N = False; self.C = False
            return False

        # move.l An,(xxx).l
        if (op & 0xFFF8) == 0x23C8:
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            v = self.a[op & 7] & 0xFFFFFFFF
            self.wl(addr, v)
            self.Z = (v == 0); self.N = bool(v & 0x80000000)
            return False

        # move.l (xxx).l,Dn
        if (op & 0xF1FF) == 0x2039:
            addr = ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
            v = self.rl(addr)
            self.d[(op >> 9) & 7] = v
            self.Z = (v == 0); self.N = bool(v & 0x80000000)
            return False

        # movea.l Dn,An   (touches no flags)
        if (op & 0xF1F8) == 0x2040:
            self.a[(op >> 9) & 7] = self.d[op & 7] & 0xFFFFFFFF
            return False

        # add.b (An,Xn.w),Dn
        if (op & 0xF1F8) == 0xD030:
            an = op & 7
            ext = self.fetch()
            ri = (ext >> 12) & 7
            idx = (self.a[ri] if ext & 0x8000 else self.d[ri])
            idx = (idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp = ext & 0xFF
            if disp & 0x80: disp -= 0x100
            dn = (op >> 9) & 7
            v = ((self.d[dn] & 0xFF) + self.rb((self.a[an] + idx + disp) & 0xFFFFFF))
            self.C = v > 0xFF
            v &= 0xFF
            self.setd_b(dn, v)
            self.Z = (v == 0); self.N = bool(v & 0x80)
            return False

        # btst/bchg/bclr/bset  #n,<ea>  (0x08xx)  and  Dn,<ea>  (0x01xx..)
        is_static = (op & 0xFF00) == 0x0800
        is_dyn = (op & 0xF100) == 0x0100 and ((op >> 3) & 7) != 1
        if is_static or is_dyn:
            kind = (op >> 6) & 3                       # 0 tst 1 chg 2 clr 3 set
            bit = self.fetch() & 0xFF if is_static else self.d[(op >> 9) & 7]
            mode, reg = (op >> 3) & 7, op & 7
            if mode == 0:                              # Dn: long, bit mod 32
                bit &= 31
                v = self.d[reg]
                self.Z = not (v & (1 << bit))
                if kind == 1: v ^= (1 << bit)
                elif kind == 2: v &= ~(1 << bit)
                elif kind == 3: v |= (1 << bit)
                self.d[reg] = v & 0xFFFFFFFF
                return False
            bit &= 7
            ea = self._ea_mem(mode, reg, 1, pc0)
            v = self.rb(ea)
            self.Z = not (v & (1 << bit))
            if kind == 1: v ^= (1 << bit)
            elif kind == 2: v &= ~(1 << bit)
            elif kind == 3: v |= (1 << bit)
            if kind:
                self.wb(ea, v & 0xFF)
            return False

        # move / movea, any size, any source and destination mode.  The
        # specific handlers above stay; this catches the forms they miss.
        if (op & 0xC000) == 0 and (op & 0x3000):
            size = {0x1000: 1, 0x3000: 2, 0x2000: 4}[op & 0x3000]
            smode, sreg = (op >> 3) & 7, op & 7
            dmode, dreg = (op >> 6) & 7, (op >> 9) & 7
            v = self._ea_read(smode, sreg, size, pc0)
            if dmode == 1:                                  # movea
                if size == 2: v = self._s16(v) & 0xFFFFFFFF
                self.a[dreg] = v
                return False
            self._ea_write(dmode, dreg, size, v, pc0)
            self.Z = (v == 0)
            self.N = bool(v & (1 << (size * 8 - 1)))
            self.C = False
            return False

        # tst / clr, any size, any EA
        if (op & 0xFF00) in (0x4A00, 0x4200) and (op & 0xC0) != 0xC0:
            size = (1, 2, 4)[(op >> 6) & 3]
            mode, reg = (op >> 3) & 7, op & 7
            if op & 0x0800:                                     # tst
                v = self._ea_read(mode, reg, size, pc0)
            else:                                               # clr
                v = 0
                if mode == 0:
                    self._ea_write(0, reg, size, 0, pc0)
                else:
                    self._ea_write(mode, reg, size, 0, pc0)
            self.Z = (v == 0)
            self.N = bool(v & (1 << (size * 8 - 1)))
            self.C = False
            return False

        # addq / subq #n,<ea>  (memory or data register, any size)
        if (op & 0xF000) == 0x5000 and (op & 0xC0) != 0xC0 and ((op >> 3) & 7) != 1:
            size = (1, 2, 4)[(op >> 6) & 3]
            n = (op >> 9) & 7 or 8
            mode, reg = (op >> 3) & 7, op & 7
            mask = (1 << (size * 8)) - 1
            if mode == 0:
                v = self.d[reg] & mask
                ea = None
            else:
                ea = self._ea_mem(mode, reg, size, pc0)
                v = self._mem_read(ea, size)
            r = (v - n) if op & 0x0100 else (v + n)
            self.C = bool(r & ~mask)
            r &= mask
            if ea is None:
                self._ea_write(0, reg, size, r, pc0)
            elif size == 1: self.wb(ea, r)
            elif size == 2: self.ww(ea, r)
            else: self.wl(ea, r)
            self.Z = (r == 0)
            self.N = bool(r & (1 << (size * 8 - 1)))
            return False

        # add / sub / cmp <ea>,Dn   and   adda / suba / cmpa <ea>,An
        if (op & 0xF000) in (0xD000, 0x9000, 0xB000) and (op & 0x0100) == 0 or                 (op & 0xF0C0) in (0xD0C0, 0x90C0, 0xB0C0):
            opm = (op >> 6) & 7
            mode, reg = (op >> 3) & 7, op & 7
            dn = (op >> 9) & 7
            kind = {0xD000: '+', 0x9000: '-', 0xB000: 'c'}[op & 0xF000]
            if opm in (3, 7):                                   # address register form
                size = 2 if opm == 3 else 4
                src = self._ea_read(mode, reg, size, pc0)
                if size == 2: src = self._s16(src) & 0xFFFFFFFF
                if kind == '+': self.a[dn] = (self.a[dn] + src) & 0xFFFFFFFF
                elif kind == '-': self.a[dn] = (self.a[dn] - src) & 0xFFFFFFFF
                else:
                    r = (self.a[dn] - src)
                    self.C = r < 0
                    self.Z = (r & 0xFFFFFFFF) == 0
                    self.N = bool(r & 0x80000000)
                return False
            size = (1, 2, 4)[opm & 3]
            mask = (1 << (size * 8)) - 1
            src = self._ea_read(mode, reg, size, pc0)
            dst = self.d[dn] & mask
            if kind == '+':
                r = dst + src
            else:
                r = dst - src
            self.C = bool(r & ~mask) if kind == '+' else r < 0
            r &= mask
            self.Z = (r == 0)
            self.N = bool(r & (1 << (size * 8 - 1)))
            if kind != 'c':
                self._ea_write(0, dn, size, r, pc0)
            return False

        # ori / andi / subi / addi / eori / cmpi  #imm,<ea>  (any size, any EA)
        if (op & 0xF000) == 0 and (op & 0x0F00) in (0x000, 0x200, 0x400, 0x600, 0xA00, 0xC00)                 and (op & 0xC0) != 0xC0 and (op & 0x100) == 0:
            size = (1, 2, 4)[(op >> 6) & 3]
            mask = (1 << (size * 8)) - 1
            imm = ((self.fetch() << 16) | self.fetch()) if size == 4 else (self.fetch() & mask)
            mode, reg = (op >> 3) & 7, op & 7
            if mode == 0:
                v = self.d[reg] & mask; ea = None
            else:
                ea = self._ea_mem(mode, reg, size, pc0)
                v = self._mem_read(ea, size)
            kind = op & 0x0F00
            if kind == 0x000: r = v | imm; self.C = False
            elif kind == 0x200: r = v & imm; self.C = False
            elif kind == 0xA00: r = v ^ imm; self.C = False
            elif kind == 0x600: r = v + imm; self.C = bool(r & ~mask)
            else: r = v - imm; self.C = r < 0                       # subi / cmpi
            r &= mask
            self.Z = (r == 0)
            self.N = bool(r & (1 << (size * 8 - 1)))
            if kind != 0xC00:
                if ea is None: self._ea_write(0, reg, size, r, pc0)
                elif size == 1: self.wb(ea, r)
                elif size == 2: self.ww(ea, r)
                else: self.wl(ea, r)
            return False

        raise Trap(f'{pc0:06X}: unsupported opcode {op:04X}')

    def _ea_read(self, mode, reg, size, pc0):
        if mode == 0:
            v = self.d[reg]
        elif mode == 1:
            v = self.a[reg]
        elif mode == 7 and reg == 4:                       # #imm
            if size == 4:
                return (self.fetch() << 16) | self.fetch()
            v = self.fetch()
            return v & 0xFF if size == 1 else v
        elif mode == 7 and reg in (2, 3):                  # d16(pc) / d8(pc,Xn)
            base = self.pc
            if reg == 2:
                ea = (base + self._s16(self.fetch())) & 0xFFFFFF
            else:
                ext = self.fetch()
                ri = (ext >> 12) & 7
                idx = self.a[ri] if ext & 0x8000 else self.d[ri]
                idx = (idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
                disp = ext & 0xFF
                if disp & 0x80: disp -= 0x100
                ea = (base + idx + disp) & 0xFFFFFF
            return self._mem_read(ea, size)
        else:
            return self._mem_read(self._ea_mem(mode, reg, size, pc0), size)
        return v & ((1 << (size * 8)) - 1)

    def _ea_write(self, mode, reg, size, v, pc0):
        if mode == 0:
            if size == 1: self.setd_b(reg, v)
            elif size == 2: self.setd_w(reg, v)
            else: self.d[reg] = v & 0xFFFFFFFF
            return
        ea = self._ea_mem(mode, reg, size, pc0)
        if size == 1: self.wb(ea, v)
        elif size == 2: self.ww(ea, v)
        else: self.wl(ea, v)

    def _mem_read(self, ea, size):
        if size == 1: return self.rb(ea)
        if size == 2: return self.rw(ea)
        return self.rl(ea)

    def _ea_mem(self, mode, reg, size, pc0):
        """Address of a memory operand; consumes extension words."""
        if mode == 2:
            return self.a[reg] & 0xFFFFFF
        if mode == 3:
            ea = self.a[reg]
            self.a[reg] = (ea + (2 if (reg == 7 and size == 1) else size)) & 0xFFFFFFFF
            return ea & 0xFFFFFF
        if mode == 4:
            self.a[reg] = (self.a[reg] - (2 if (reg == 7 and size == 1) else size)) & 0xFFFFFFFF
            return self.a[reg] & 0xFFFFFF
        if mode == 5:
            return (self.a[reg] + self._s16(self.fetch())) & 0xFFFFFF
        if mode == 6:
            ext = self.fetch()
            ri = (ext >> 12) & 7
            idx = self.a[ri] if ext & 0x8000 else self.d[ri]
            idx = (idx & 0xFFFFFFFF) if (ext & 0x0800) else self._s16(idx & 0xFFFF)
            disp = ext & 0xFF
            if disp & 0x80: disp -= 0x100
            return (self.a[reg] + idx + disp) & 0xFFFFFF
        if mode == 7 and reg == 0:
            return self._s16(self.fetch()) & 0xFFFFFF
        if mode == 7 and reg == 1:
            return ((self.fetch() << 16) | self.fetch()) & 0xFFFFFF
        raise Trap(f'{pc0:06X}: unsupported addressing mode {mode}/{reg}')
