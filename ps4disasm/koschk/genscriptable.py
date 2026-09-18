#!/usr/bin/env python3

import sys

if len(sys.argv) != 2:
	print(sys.stderr, "Usage: {} n".format(sys.argv[0]))
	print(sys.stderr, "Where:")
	print(sys.stderr, "\tn: number of script files")
	sys.exit(0)

n = int(sys.argv[1])
ncols = n // 10 + (1 if n % 10 > 0 else 0)
if ncols > 5:
	print(sys.stderr, "Cannot have more than 5 columns")
	sys.exit(0)

jumptable = []
uncompressed = []
compressed = []

for i in range(1,n+1):
	col = i // 10 - (1 if i % 10 == 0 else 0)
	xpos = col * 8 + 1
	ypos = i % 10 + (10 if i % 10 == 0 else 0)
	print("KosText{0:02d}:".format(i))
	print('\tdc.b\t"{0:02d}",0,0'.format(i))
	print("\tdc.b\t{}\t\t\t; x".format(xpos))
	print("\tdc.b\t{}\t\t\t; y".format(ypos))
	print("\tdc.w\t$0000\t\t\t; padding")
	print("\tdc.l\tCText{0:02d}\t\t\t;Compressed address".format(i))
	print("\tdc.l\tUText{0:02d}\t\t\t;Uncompressed address".format(i))
	print()

print("EndOfText:")
print("\tdc.b\t$FF")
print()
print("\talign\t8")
print()

for i in range(1,n+1):
	print("UText{0:02d}:".format(i))
	if(i == n):
		print("\tdc.l\tCText01-UText{0:02d}-4".format(i))
	else:
		print("\tdc.l\tUText{0:02d}-UText{1:02d}-4".format(i+1,i))
	print('\tbinclude\t"script/dialogue {}.bin.unc"'.format(i))
	print()

for i in range(1,n+1):
	print('CText{0:02d}:\tbinclude "script/dialogue {0}.bin"'.format(i))

