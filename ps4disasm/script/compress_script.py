#!/usr/bin/env python3

import os
import sys
import re
import pathlib
import subprocess
import io

# change this if the start address is changed in ps4constants.asm
Dialogue_Trees_ADDRESS = 0xFF3000
MAX_TEXT_ADDRESS = 0xFF4ECF
MAX_TEXT_SIZE = MAX_TEXT_ADDRESS - Dialogue_Trees_ADDRESS

# alternatively, if you're not 100% sure, max length in US script is 7220 bytes
#MAX_TEXT_SIZE = 7220

def decodenum(s):
	if s[0] == '$':
		return int(s[1:], 16)
	else:
		return int(s)

class IgnoreDcProcessor:
	def __init__(self, fname):
		self.fname = fname
		
	def matches(self, line):
		return line

	def process(self, m, linenum):
		pass

DC_W_DIRECTIVE = re.compile(r"^\s+dc\.w\s+((\$[A-Fa-f0-9]{4})|(\d+))\s*(;.*)?$")
class DcWProcessor(IgnoreDcProcessor):

	def __init__(self, fname, out):
		super().__init__(fname)
		self.out = out
		
	def matches(self, line):
		self.m = DC_W_DIRECTIVE.match(line)
		return self.m
		
	def process(self, m, linenum):
		s = m.group(1)
		decoded = decodenum(s)
		out.write(bytes([(decoded&0xFF00)>>8, decoded&0xFF]))
		
DC_DIRECTIVE = re.compile(r"^\s+dc\.b\s+(.*)$")
hexdigits = set("ABCDEFabcdef0123456789")
class DcBProcessor(IgnoreDcProcessor):
	
	def __init__(self, fname, out, charset, symbols):
		super().__init__(fname)
		self.out = out
		self.charset = charset
		self.buf = []
		self.state = self.scanning
		
	def matches(self, line):
		self.m = DC_DIRECTIVE.match(line)
		return self.m
	
	def process(self, m, linenum):
		self.state = self.scanning
		self.buf.clear()
		for ch in m.group(1):
			self.state = self.state(ch, linenum)
		self.state(None, linenum)

	def syntax_error(self, ch, linenum):
		print("Syntax error: illegal character", ch, "file:", self.fname, "@", linenum)
		sys.exit(-1)
		
	def comment(self, ch, linenum):
		return self.comment

	def hex_digit(self, ch, linenum):
		if ch is not None and ch in hexdigits:
			self.buf.append(ch)
			return self.hex_digit
		else:
			translated = decodenum(''.join(self.buf))
			out.write(bytes([translated]))
			self.buf.clear()
			return self.scanning(ch, linenum)
		
	def in_quote(self, ch, linenum):
		if ch is None:
			self.syntax_error("newline", linenum)
		if ch == '"':
			return self.maybe_quote_char
		self.buf.append(ch)
		return self.in_quote

	def maybe_quote_char(self, ch, linenum):
		if ch is not None and ch == '"':
			self.buf.append('"')
			return self.in_quote
		else:
			# translate unknown chars to space
			self.out.write(bytes([self.charset.get(ch, self.charset.get(' ', 0)) for ch in self.buf]))
			self.buf.clear()
			return self.scanning(ch, linenum)

	def dec_digit(self, ch, linenum):
		if ch is not None and ch.isdigit():
			self.buf.append(ch)
			return self.dec_digit
		else:
			translated = decodenum(''.join(self.buf))
			self.out.write(bytes([translated]))
			self.buf.clear()
			return self.scanning(ch, buf, linenum, out)
			
	def identifier(self, ch, linenum):
		if ch is None or ch == ',' or ch.isspace():
			sym = ''.join(self.buf)
			val = self.symbols[sym]
			# split in bytes
			if val < 0xFF:
				self.syntax_error(sym, linenum)
				
			self.out.write(bytes([val]))
			return self.scanning
		elif ch.isalnum():
			self.buf.append(ch)
			return self.identifier
		else:
			self.syntax_error(ch, linenum)

	def scanning(self, ch, linenum):
		if ch is None:
			return
		if ch == '$':
			self.buf.append('$')
			return self.hex_digit
		if ch == ',':
			return self.scanning
		if ch == '"':
			return self.in_quote
		if ch == ';':
			return self.comment
		if ch.isdigit():
			self.buf.append(ch)
			return self.dec_digit
		if ch.isidentifier():
			self.buf.append(ch)
			return self.identifier
		if ch.isspace():
			return self.scanning
		self.syntax_error(ch, linenum)
		
class CompositeDcProcessor:
	def __init__(self, fname, out, charset, symbols):
		self.delegate = [DcWProcessor(fname, out),
				 DcBProcessor(fname, out, charset, symbols),
				 IgnoreDcProcessor(fname)]
		self.current = None
	
	def matches(self, line):
		self.current = None
		for d in self.delegate:
			m = d.matches(line)
			if m:
				self.current = d
				return m
	
	def process(self, m, linenum):
		self.current.process(m, linenum)
		self.current = None


CHARSET_RANGE = re.compile(r"^\s+charset\s+'(.)'\s*,\s*'(.)'\s*,\s*((\$[A-Fa-f0-9][A-Fa-f0-9])|(\d+))\s*(;.*)?$")
CHARSET_SINGLE = re.compile(r"^\s+charset\s+'(.)'\s*,\s*((\$[A-Fa-f0-9][A-Fa-f0-9])|(\d+))\s*(;.*)?$")
CHARSET_SINGLE_NUM = re.compile(r"^\s+charset\s+(\$[A-Fa-f0-9][A-Fa-f0-9])\s*,\s*((\$[A-Za-z0-9][A-Za-z0-9])|(\d+))\s*(;.*)?$")
class CharsetProcessor:
	
	def __init__(self, fname, charset, rcharset):
		self.fname = fname
		self.charset = charset
		self.rcharset = rcharset
		self.linenum = 0
	
	def process(self, line):
		self.linenum += 1
		r = CHARSET_RANGE.match(line)
		if r:
			base = decodenum(r.group(3))
			for count, ch in enumerate(range(ord(r.group(1)), ord(r.group(2)) + 1)):
				self.charset[chr(ch)] = base + count
				self.rcharset[base+count] = chr(ch)
			return
			
		single = CHARSET_SINGLE.match(line)
		if single:
			self.charset[single.group(1)] = decodenum(single.group(2))
			self.rcharset[decodenum(single.group(2))] = single.group(1)
			return
			
		single_num = CHARSET_SINGLE_NUM.match(line)
		if single_num:
			self.charset[chr(decodenum(single_num.group(1)))] = decodenum(single_num.group(2))
			self.rcharset[decodenum(single_num.group(2))] = chr(decodenum(single_num.group(1)))
			return
			
		print("Invalid charset line; file:", self.fname, "@", self.linenum, "- ignoring")


ASSIGN_DIRECTIVE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*((\$[A-Fa-f0-9]+)|(\d+))\s*(;.*)?$")
IF_DIRECTIVE = re.compile(r"^\s+if\s+([A-Za-z0-9_]+)\s*=\s*([0-9]+)\s*$")
ELSE_DIRECTIVE = re.compile(r"^\s+else\s*$")
ENDIF_DIRECTIVE = re.compile(r"^\s+endif\s*$")
class Processor:
	def __init__(self, filename, symbols, dc_processor):
		self.filename = filename
		self.linenum = 1
		self.state = self.normal
		self.symbols = symbols
		self.dc_processor = dc_processor
		
	def process(self, line):
		if self.state is None:
			return
		self.state = self.state(line)
		self.linenum += 1
		
	def check(self):
		if self.state != self.normal:
			abort("unterminated if", self.filename)
	
	def normal(self, line):
		m = IF_DIRECTIVE.match(line)
		if m:
			var, val = m.group(1), m.group(2)
			if val == self.symbols.get(var, None):
				return self.look_for_else
			else:
				return self.look_for_else_skip
		self.process_non_controlflow(line)
		return self.normal
		
	def look_for_else_skip(self, line):
		m = ELSE_DIRECTIVE.match(line)
		if m:
			return self.look_for_endif
		m = ENDIF_DIRECTIVE.match(line)
		if m:
			return self.normal
		return self.look_for_else_skip
		
	def look_for_else(self, line):
		m = ELSE_DIRECTIVE.match(line)
		if m:
			return self.look_for_endif_skip
		m = ENDIF_DIRECTIVE.match(line)
		if m:
			return self.normal
		self.process_non_controlflow(line)
		return self.look_for_else
			
	def look_for_endif_skip(self, line):
		m = ENDIF_DIRECTIVE.match(line)
		if m:
			return self.normal
		return self.look_for_endif_skip

	def look_for_endif(self, line):
		m = ENDIF_DIRECTIVE.match(line)
		if m:
			return self.normal
		self.process_non_controlflow(line)
		return self.look_for_endif
			
	def process_non_controlflow(self, line):
		m = ASSIGN_DIRECTIVE.match(line)
		if m:
			self.symbols[m.group(1)] = decodenum(m.group(2))
			return
		
		m = self.dc_processor.matches(line)
		if m:
			self.dc_processor.process(m, self.linenum)
			
	def abort(self, s, filename):
		print(s, "file:", self.fname, "@", self.linenum)
		sys.exit(-1)

basedir = pathlib.Path(sys.argv[0]).resolve().parent
print("Working directory:", basedir)


cmd_symbols = [a for a in sys.argv[1:] if '=' in a]
cmd_symbols = {arg: val for arg, val in map(lambda s: s.split('='), cmd_symbols)}
remainder = set([a for a in sys.argv[1:] if '=' not in a])
debug = False
no_compress = False
if '--debug' in remainder:
	debug = True
	remainder.remove('--debug')
	
if "--no-compress" in remainder:
	no_compress = True
	remainder.remove("--no-compress")
	
remainder = [pathlib.Path(f) for f in remainder]

symbols = {}

# load symbols from ps4.options.asm in directory one above
fname = basedir.parent / "ps4.options.asm"
if fname.exists():
	with open(fname, "rt", encoding="iso-8859-1") as f:
		processor = Processor(fname, symbols, IgnoreDcProcessor(fname))
		for line in f:
			line = line.rstrip()
			processor.process(line)

# override with command line settings
symbols.update(cmd_symbols)

print("Processing using symbols:", symbols)

charset = {}
rcharset = {0xff: '\n-----\n', 0xfc: '\n', 0xfd: '\nVV\n'}

fname = basedir / "charset.asm"
with open(fname, "rt", encoding="iso-8859-1") as f:
	charset_processor = CharsetProcessor(fname, charset, rcharset)
	for line in f:
		line = line.rstrip()
		charset_processor.process(line)
		
print("Using charset table:")
for char, value in charset.items():
	if char.isprintable():
		print('\t"{0}": {1:02X}'.format(char, value))
	else:
		print('\t${0:02X}: {1:02X}'.format(ord(char[0]), value))

	
def dump(f):
	print(f)
	print('==================')
	with open(f, "rb") as debugf:
		while True:
			chunk = debugf.read(8192)
			if not chunk:
				break
			changed = [rcharset.get(b, '${0:02X}\n'.format(b)) for b in chunk]
			print(''.join(changed), sep='', end='')

if len(remainder) == 0:
	remainder = basedir.glob('dialogue *.asm')

for fname in remainder:
	print("processing", fname)
	dest = fname.with_suffix('.bin.unc')
	dest2 = dest
	idx = 0
	while dest2.exists():
		dest2 = dest.with_suffix('.unc.{}'.format(idx))
		idx += 1
	if idx != 0:
		print("backing up", dest, "to", dest2)
		dest.rename(dest2)
	with open(fname, "rt", encoding="iso-8859-1") as f, open(dest, "wb") as out:
		processor = Processor(fname, symbols, CompositeDcProcessor(fname, out, charset, symbols))
		for line in f:
			line = line.rstrip()
			processor.process(line)
			if debug:
				print(out.tell(), ':', line)
		processor.check()
		# todo: make that part of the processor somehow
		if out.tell() % 2 != 0:
			out.write(bytes([0]))
		print("done processing", fname, "to", dest)
		if out.tell() > MAX_TEXT_SIZE:
			print("WARNING! script file ", fname, "is too large (", out.tell(), " bytes)", file=sys.stderr, sep='')
			print("You may need to relocate the decompression buffer.", file=sys.stderr, sep='')
			print("Press enter to continue.", file=sys.stderr, sep='')
			input()

	if debug:
		dump(dest)
		if dest2.exists():
			dump(dest2)
	# compress
	if not(no_compress):
		bindest = fname.with_suffix('.bin')
		bindest2 = bindest
		idx = 0
		while bindest2.exists():
			bindest2 = bindest.with_suffix('.bin.{}'.format(idx))
			idx += 1
		if idx != 0:
			print("backing up", bindest, "to", bindest2)
			bindest.rename(bindest2)
		# koscmp has no extension on Linux and is koscmp.exe on Windows; the
		# bare name resolves to the ELF binary there and CreateProcess rejects
		# it with WinError 193. Resolve against basedir so cwd does not matter.
		kos = basedir.parent / 'compressors' / 'koscmp'
		if not kos.exists() or os.name == 'nt':
			kos = kos.with_suffix('.exe')
		subprocess.run([str(kos), str(dest.resolve(strict=True)), str(bindest.resolve())])
		# pad to 16 bytes
		with open(bindest, "r+b") as f:
			f.seek(0, io.SEEK_END)
			sz = f.tell()
			if sz % 16 != 0:
				f.write(bytes(16 - sz%16))
