#!/usr/bin/env python3

import sys
import re

LINE = re.compile(r"^\s*dc\.b\s+((\$[A-F0-9][A-F0-9](,\s+)?)+)(\s*;.*)?$")

with open(sys.argv[1], 'rt') as ifile:
    with open(sys.argv[2], 'wb') as ofile:
        for line in ifile:
            m = LINE.sub(r"\1", line)
            line = ''.join([c for c in m if c not in ', $\r\n'])
            print(line)
            for byt in map(''.join, zip(*[iter(line)]*2)):
                bin_byte = bytes.fromhex(byt)
                ofile.write(bin_byte)

