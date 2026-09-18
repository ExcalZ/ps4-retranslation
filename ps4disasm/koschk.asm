	cpu	68000
	padding	off
	listing	purecode
	page	0
	supmode	on

StartOfRom:
	if (*) <> 0
	fatal	"Start of ROM is at addres $\{*} but should be 0."
	endif

	include "koschk/init.asm"
	include "koschk/globals.asm"
	include "koschk/charmap.asm"
	include "koschk/text.asm"

__main:

	move.w #$8F02, vdp_control     ; Set autoincrement to 2 bytes

; ************************************
; Move palettes to CRAM
; ************************************
	move.l #vdp_write_palettes, vdp_control ; Set up VDP to write to CRAM address $0000

	lea Palettes(pc), a0  ; Load address of Palettes into a0
	move.l #$1F, d0  ; 128 bytes of data (4 palettes, 32 longwords, minus 1 for counter) in palettes

.ColourLoop:
	move.l (a0)+, vdp_data ; Move data to VDP data port, and increment source address
	dbra d0, .ColourLoop

; ************************************
; Load font
; ************************************
	lea		PixelFont, a0       ; Move font address to a0
	move.l	#PixelFontVRAM, d0   ; Move VRAM dest address to d0
	move.l	#PixelFontSizeT, d1  ; Move number of characters (font size in tiles) to d1
	jsr		LoadFont            ; Jump to subroutine

	; wait until the d0 register is uncleared
	; this should be done in the debugger
	clr.b	d0
WaitForStart:
	; comment following line if you want to debug
	moveq	#$1, d0
	tst.b	d0
	beq		WaitForStart

; ************************************
; Draw text
; ************************************

	; a0 is our scratch buffer to load strings
	; a4 is our current control area position
	; control area layout:
	; r bytes: string for header ("01",0 ; "02",0 etc) + 1 byte padding
	; 1 byte: x position
	; 1 byte: y position
	; 4 bytes: pointer to compressed
	; 4 bytes: pointer to uncompressed
	; ends when first byte of entry is $FF
	;
	; a4: current entry
	; d4: x:y
	; d5: counter
	; a3: internal
	; a5: pointer to compressed
	; a6: pointer to uncompressed
	; other registers used by routines
	lea		KosText01(pc), a4
	clr.w	d5
	
Loop:
	move.b	(a4), d0
	cmpi.b	#$FF, d0
	beq		End
	
	move.w	4(a4), d4
	movea.l	8(a4), a5
	movea.l	12(a4), a6
	
	; for now just print the data
	movea.l	a4, a0					; string address
	move.l	#PixelFontTileID, d0	; font
	move.w	d4, d1					; XY
	move.l	#2, d2					; white
	movem.l	d3-d7/a4-a6,-(a7)
	bsr		DrawTextPlaneA
	movem.l	(a7)+,d3-d7/a4-a6
	
	; decompress
	movea.l	a5, a0
	lea		uncompress_area, a1
	movem.l	d3-d7/a4-a6,-(a7)
	bsr		KosDecomp
	movem.l	(a7)+,d3-d7/a4-a6

	; compare
	movea.l	a6, a0
	lea		uncompress_area, a1
	move.l	(a0), d0
	subq.l	#1, d0
	lea		4(a0), a0
CmpLoop:
	move.b	(a0)+, d1
	move.b	(a1)+, d2
	cmp.b	d1, d2
	bne		SetBadText
	dbra	d0, CmpLoop
	bra		SetGoodText

SetBadText:
	lea		BadText, a3
	bra		+

SetGoodText:
	lea		GoodText, a3
+
	lea		4(a3), a0
	move.l	#PixelFontTileID, d0
	move.w	d4, d1
	lsr.w	#8, d1
	addq	#3, d1
	lsl.w	#8, d1
	andi.w	#$FF00, d1
	move.b	d4, d1
	move.l	(a3), d2
	movem.l	d3-d7/a4-a6,-(a7)
	bsr		DrawTextPlaneA
	movem.l	(a7)+,d3-d7/a4-a6
	
	lea		16(a4), a4
	addq	#1, d5
	
	bra		Loop


; -------------------------------------------------------------------------
; Kosinski decompression subroutine
; Inputs:
; a0 = compressed data location
; a1 = destination
; -------------------------------------------------------------------------
KosDecomp:
	subq.l	#2, sp			; make space for two bytes on the stack
	move.b	(a0)+, $1(sp)
	move.b	(a0)+, (sp)
	move.w	(sp), d5		; copy first description field
	moveq	#$F, d4			; 16 bits in a byte

KosDecomp_Loop:
	lsr.w	#1, d5			; bit which is shifted out goes into C flag
	move	sr, d6
	dbf	d4, KosDecomp_ChkBit
	move.b	(a0)+, $1(sp)
	move.b	(a0)+, (sp)
	move.w	(sp), d5		; get next description field if needed
	moveq	#$F, d4			; reset bit counter

KosDecomp_ChkBit:
	move	d6, ccr			; was the bit set?
	bcc.s	KosDecomp_Match	; if not, branch (C flag clear means bit was clear)
	move.b	(a0)+, (a1)+	; otherwise, copy byte as-is
	bra.s	KosDecomp_Loop

KosDecomp_Match:
	moveq	#0, d3
	lsr.w	#1, d5			; get next bit
	move	sr, d6
	dbf	d4, KosDecomp_ChkBit2
	move.b	(a0)+, $1(sp)
	move.b	(a0)+, (sp)
	move.w	(sp), d5
	moveq	#$F, d4

KosDecomp_ChkBit2:
	move	d6, ccr			; was the bit set?
	bcs.s	KosDecomp_FullMatch		; if it was, branch
	lsr.w	#1, d5
	dbf	d4, +
	move.b	(a0)+, $1(sp)
	move.b	(a0)+, (sp)
	move.w	(sp), d5
	moveq	#$F, d4

+
	roxl.w	#1, d3			; get high repeat count bit (shift X flag in)
	lsr.w	#1, d5
	dbf	d4, +
	move.b	(a0)+, $1(sp)
	move.b	(a0)+, (sp)
	move.w	(sp), d5
	moveq	#$F, d4
+
	roxl.w	#1, d3			; get low repeat count bit
	addq.w	#1, d3
	moveq	#-1, d2
	move.b	(a0)+, d2
	bra.s	KosDecomp_MatchLoop

KosDecomp_FullMatch:
	move.b	(a0)+, d0		; get first byte
	move.b	(a0)+, d1		; get second byte
	moveq	#-1, d2
	move.b	d1, d2
	lsl.w	#5, d2
	move.b	d0, d2			; calculate offset
	andi.w	#7, d1			; does a third byte need to be read?
	beq.s	KosDecomp_FullMatch2		; if it does, branch
	move.b	d1, d3			; copy repeat count
	addq.w	#1, d3			; and increment it

KosDecomp_MatchLoop:
	move.b	(a1,d2.w), d0
	move.b	d0, (a1)+		; copy appropriate byte
	dbf	d3, KosDecomp_MatchLoop	; and repeat the copying
	bra.s	KosDecomp_Loop

KosDecomp_FullMatch2:
	move.b	(a0)+, d1
	beq.s	KosDecomp_Done		; 0 indicates end of compressed data
	cmpi.b	#1, d1
	beq.w	KosDecomp_Loop	; 1 indicates a new description needs to be read
	move.b	d1, d3			; otherwise, copy repeat count
	bra.s	KosDecomp_MatchLoop
KosDecomp_Done:
	addq.l	#2, sp			; restore stack pointer to original state
	rts
; -------------------------------------------------------------

	

End:
	stop #$2700 ; Halt CPU

Palettes:
	dc.w $0000 ; Colour 0 - Transparent
	dc.w $000E ; Colour 1 - Red
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000

	dc.w $0000 ; Colour 0 - Transparent
	dc.w $00E0 ; Colour 1 - Green
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000

	dc.w $0000 ; Colour 0 - Transparent
	dc.w $0EEE ; Colour 1 - White
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000
	dc.w $0000

        dc.w $0000 ; Colour 0 - Transparent
        dc.w $0E00 ; Colour 1 - Blue
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000
        dc.w $0000

GoodText:
	dc.l	$1			; green
	dc.b	"GOOD",0
BadText:
	dc.l	$0			; red
	dc.b	"BAD ",0


KosText01:
	dc.b	"01",0,0
	dc.b	1			; x
	dc.b	1			; y
	dc.w	$0000			; padding
	dc.l	CText01			;Compressed address
	dc.l	UText01			;Uncompressed address

KosText02:
	dc.b	"02",0,0
	dc.b	1			; x
	dc.b	2			; y
	dc.w	$0000			; padding
	dc.l	CText02			;Compressed address
	dc.l	UText02			;Uncompressed address

KosText03:
	dc.b	"03",0,0
	dc.b	1			; x
	dc.b	3			; y
	dc.w	$0000			; padding
	dc.l	CText03			;Compressed address
	dc.l	UText03			;Uncompressed address

KosText04:
	dc.b	"04",0,0
	dc.b	1			; x
	dc.b	4			; y
	dc.w	$0000			; padding
	dc.l	CText04			;Compressed address
	dc.l	UText04			;Uncompressed address

KosText05:
	dc.b	"05",0,0
	dc.b	1			; x
	dc.b	5			; y
	dc.w	$0000			; padding
	dc.l	CText05			;Compressed address
	dc.l	UText05			;Uncompressed address

KosText06:
	dc.b	"06",0,0
	dc.b	1			; x
	dc.b	6			; y
	dc.w	$0000			; padding
	dc.l	CText06			;Compressed address
	dc.l	UText06			;Uncompressed address

KosText07:
	dc.b	"07",0,0
	dc.b	1			; x
	dc.b	7			; y
	dc.w	$0000			; padding
	dc.l	CText07			;Compressed address
	dc.l	UText07			;Uncompressed address

KosText08:
	dc.b	"08",0,0
	dc.b	1			; x
	dc.b	8			; y
	dc.w	$0000			; padding
	dc.l	CText08			;Compressed address
	dc.l	UText08			;Uncompressed address

KosText09:
	dc.b	"09",0,0
	dc.b	1			; x
	dc.b	9			; y
	dc.w	$0000			; padding
	dc.l	CText09			;Compressed address
	dc.l	UText09			;Uncompressed address

KosText10:
	dc.b	"10",0,0
	dc.b	1			; x
	dc.b	10			; y
	dc.w	$0000			; padding
	dc.l	CText10			;Compressed address
	dc.l	UText10			;Uncompressed address

KosText11:
	dc.b	"11",0,0
	dc.b	9			; x
	dc.b	1			; y
	dc.w	$0000			; padding
	dc.l	CText11			;Compressed address
	dc.l	UText11			;Uncompressed address

KosText12:
	dc.b	"12",0,0
	dc.b	9			; x
	dc.b	2			; y
	dc.w	$0000			; padding
	dc.l	CText12			;Compressed address
	dc.l	UText12			;Uncompressed address

KosText13:
	dc.b	"13",0,0
	dc.b	9			; x
	dc.b	3			; y
	dc.w	$0000			; padding
	dc.l	CText13			;Compressed address
	dc.l	UText13			;Uncompressed address

KosText14:
	dc.b	"14",0,0
	dc.b	9			; x
	dc.b	4			; y
	dc.w	$0000			; padding
	dc.l	CText14			;Compressed address
	dc.l	UText14			;Uncompressed address

KosText15:
	dc.b	"15",0,0
	dc.b	9			; x
	dc.b	5			; y
	dc.w	$0000			; padding
	dc.l	CText15			;Compressed address
	dc.l	UText15			;Uncompressed address

KosText16:
	dc.b	"16",0,0
	dc.b	9			; x
	dc.b	6			; y
	dc.w	$0000			; padding
	dc.l	CText16			;Compressed address
	dc.l	UText16			;Uncompressed address

KosText17:
	dc.b	"17",0,0
	dc.b	9			; x
	dc.b	7			; y
	dc.w	$0000			; padding
	dc.l	CText17			;Compressed address
	dc.l	UText17			;Uncompressed address

KosText18:
	dc.b	"18",0,0
	dc.b	9			; x
	dc.b	8			; y
	dc.w	$0000			; padding
	dc.l	CText18			;Compressed address
	dc.l	UText18			;Uncompressed address

KosText19:
	dc.b	"19",0,0
	dc.b	9			; x
	dc.b	9			; y
	dc.w	$0000			; padding
	dc.l	CText19			;Compressed address
	dc.l	UText19			;Uncompressed address

KosText20:
	dc.b	"20",0,0
	dc.b	9			; x
	dc.b	10			; y
	dc.w	$0000			; padding
	dc.l	CText20			;Compressed address
	dc.l	UText20			;Uncompressed address

KosText21:
	dc.b	"21",0,0
	dc.b	17			; x
	dc.b	1			; y
	dc.w	$0000			; padding
	dc.l	CText21			;Compressed address
	dc.l	UText21			;Uncompressed address

KosText22:
	dc.b	"22",0,0
	dc.b	17			; x
	dc.b	2			; y
	dc.w	$0000			; padding
	dc.l	CText22			;Compressed address
	dc.l	UText22			;Uncompressed address

KosText23:
	dc.b	"23",0,0
	dc.b	17			; x
	dc.b	3			; y
	dc.w	$0000			; padding
	dc.l	CText23			;Compressed address
	dc.l	UText23			;Uncompressed address

KosText24:
	dc.b	"24",0,0
	dc.b	17			; x
	dc.b	4			; y
	dc.w	$0000			; padding
	dc.l	CText24			;Compressed address
	dc.l	UText24			;Uncompressed address

KosText25:
	dc.b	"25",0,0
	dc.b	17			; x
	dc.b	5			; y
	dc.w	$0000			; padding
	dc.l	CText25			;Compressed address
	dc.l	UText25			;Uncompressed address

KosText26:
	dc.b	"26",0,0
	dc.b	17			; x
	dc.b	6			; y
	dc.w	$0000			; padding
	dc.l	CText26			;Compressed address
	dc.l	UText26			;Uncompressed address

KosText27:
	dc.b	"27",0,0
	dc.b	17			; x
	dc.b	7			; y
	dc.w	$0000			; padding
	dc.l	CText27			;Compressed address
	dc.l	UText27			;Uncompressed address

KosText28:
	dc.b	"28",0,0
	dc.b	17			; x
	dc.b	8			; y
	dc.w	$0000			; padding
	dc.l	CText28			;Compressed address
	dc.l	UText28			;Uncompressed address

KosText29:
	dc.b	"29",0,0
	dc.b	17			; x
	dc.b	9			; y
	dc.w	$0000			; padding
	dc.l	CText29			;Compressed address
	dc.l	UText29			;Uncompressed address

KosText30:
	dc.b	"30",0,0
	dc.b	17			; x
	dc.b	10			; y
	dc.w	$0000			; padding
	dc.l	CText30			;Compressed address
	dc.l	UText30			;Uncompressed address

KosText31:
	dc.b	"31",0,0
	dc.b	25			; x
	dc.b	1			; y
	dc.w	$0000			; padding
	dc.l	CText31			;Compressed address
	dc.l	UText31			;Uncompressed address

KosText32:
	dc.b	"32",0,0
	dc.b	25			; x
	dc.b	2			; y
	dc.w	$0000			; padding
	dc.l	CText32			;Compressed address
	dc.l	UText32			;Uncompressed address

KosText33:
	dc.b	"33",0,0
	dc.b	25			; x
	dc.b	3			; y
	dc.w	$0000			; padding
	dc.l	CText33			;Compressed address
	dc.l	UText33			;Uncompressed address

KosText34:
	dc.b	"34",0,0
	dc.b	25			; x
	dc.b	4			; y
	dc.w	$0000			; padding
	dc.l	CText34			;Compressed address
	dc.l	UText34			;Uncompressed address

KosText35:
	dc.b	"35",0,0
	dc.b	25			; x
	dc.b	5			; y
	dc.w	$0000			; padding
	dc.l	CText35			;Compressed address
	dc.l	UText35			;Uncompressed address

KosText36:
	dc.b	"36",0,0
	dc.b	25			; x
	dc.b	6			; y
	dc.w	$0000			; padding
	dc.l	CText36			;Compressed address
	dc.l	UText36			;Uncompressed address

KosText37:
	dc.b	"37",0,0
	dc.b	25			; x
	dc.b	7			; y
	dc.w	$0000			; padding
	dc.l	CText37			;Compressed address
	dc.l	UText37			;Uncompressed address

KosText38:
	dc.b	"38",0,0
	dc.b	25			; x
	dc.b	8			; y
	dc.w	$0000			; padding
	dc.l	CText38			;Compressed address
	dc.l	UText38			;Uncompressed address

KosText39:
	dc.b	"39",0,0
	dc.b	25			; x
	dc.b	9			; y
	dc.w	$0000			; padding
	dc.l	CText39			;Compressed address
	dc.l	UText39			;Uncompressed address

KosText40:
	dc.b	"40",0,0
	dc.b	25			; x
	dc.b	10			; y
	dc.w	$0000			; padding
	dc.l	CText40			;Compressed address
	dc.l	UText40			;Uncompressed address

KosText41:
	dc.b	"41",0,0
	dc.b	33			; x
	dc.b	1			; y
	dc.w	$0000			; padding
	dc.l	CText41			;Compressed address
	dc.l	UText41			;Uncompressed address

KosText42:
	dc.b	"42",0,0
	dc.b	33			; x
	dc.b	2			; y
	dc.w	$0000			; padding
	dc.l	CText42			;Compressed address
	dc.l	UText42			;Uncompressed address

KosText43:
	dc.b	"43",0,0
	dc.b	33			; x
	dc.b	3			; y
	dc.w	$0000			; padding
	dc.l	CText43			;Compressed address
	dc.l	UText43			;Uncompressed address

EndOfText:
	dc.b	$FF

	align	8

UText01:
	dc.l	UText02-UText01-4
	binclude	"script/dialogue 1.bin.unc"

UText02:
	dc.l	UText03-UText02-4
	binclude	"script/dialogue 2.bin.unc"

UText03:
	dc.l	UText04-UText03-4
	binclude	"script/dialogue 3.bin.unc"

UText04:
	dc.l	UText05-UText04-4
	binclude	"script/dialogue 4.bin.unc"

UText05:
	dc.l	UText06-UText05-4
	binclude	"script/dialogue 5.bin.unc"

UText06:
	dc.l	UText07-UText06-4
	binclude	"script/dialogue 6.bin.unc"

UText07:
	dc.l	UText08-UText07-4
	binclude	"script/dialogue 7.bin.unc"

UText08:
	dc.l	UText09-UText08-4
	binclude	"script/dialogue 8.bin.unc"

UText09:
	dc.l	UText10-UText09-4
	binclude	"script/dialogue 9.bin.unc"

UText10:
	dc.l	UText11-UText10-4
	binclude	"script/dialogue 10.bin.unc"

UText11:
	dc.l	UText12-UText11-4
	binclude	"script/dialogue 11.bin.unc"

UText12:
	dc.l	UText13-UText12-4
	binclude	"script/dialogue 12.bin.unc"

UText13:
	dc.l	UText14-UText13-4
	binclude	"script/dialogue 13.bin.unc"

UText14:
	dc.l	UText15-UText14-4
	binclude	"script/dialogue 14.bin.unc"

UText15:
	dc.l	UText16-UText15-4
	binclude	"script/dialogue 15.bin.unc"

UText16:
	dc.l	UText17-UText16-4
	binclude	"script/dialogue 16.bin.unc"

UText17:
	dc.l	UText18-UText17-4
	binclude	"script/dialogue 17.bin.unc"

UText18:
	dc.l	UText19-UText18-4
	binclude	"script/dialogue 18.bin.unc"

UText19:
	dc.l	UText20-UText19-4
	binclude	"script/dialogue 19.bin.unc"

UText20:
	dc.l	UText21-UText20-4
	binclude	"script/dialogue 20.bin.unc"

UText21:
	dc.l	UText22-UText21-4
	binclude	"script/dialogue 21.bin.unc"

UText22:
	dc.l	UText23-UText22-4
	binclude	"script/dialogue 22.bin.unc"

UText23:
	dc.l	UText24-UText23-4
	binclude	"script/dialogue 23.bin.unc"

UText24:
	dc.l	UText25-UText24-4
	binclude	"script/dialogue 24.bin.unc"

UText25:
	dc.l	UText26-UText25-4
	binclude	"script/dialogue 25.bin.unc"

UText26:
	dc.l	UText27-UText26-4
	binclude	"script/dialogue 26.bin.unc"

UText27:
	dc.l	UText28-UText27-4
	binclude	"script/dialogue 27.bin.unc"

UText28:
	dc.l	UText29-UText28-4
	binclude	"script/dialogue 28.bin.unc"

UText29:
	dc.l	UText30-UText29-4
	binclude	"script/dialogue 29.bin.unc"

UText30:
	dc.l	UText31-UText30-4
	binclude	"script/dialogue 30.bin.unc"

UText31:
	dc.l	UText32-UText31-4
	binclude	"script/dialogue 31.bin.unc"

UText32:
	dc.l	UText33-UText32-4
	binclude	"script/dialogue 32.bin.unc"

UText33:
	dc.l	UText34-UText33-4
	binclude	"script/dialogue 33.bin.unc"

UText34:
	dc.l	UText35-UText34-4
	binclude	"script/dialogue 34.bin.unc"

UText35:
	dc.l	UText36-UText35-4
	binclude	"script/dialogue 35.bin.unc"

UText36:
	dc.l	UText37-UText36-4
	binclude	"script/dialogue 36.bin.unc"

UText37:
	dc.l	UText38-UText37-4
	binclude	"script/dialogue 37.bin.unc"

UText38:
	dc.l	UText39-UText38-4
	binclude	"script/dialogue 38.bin.unc"

UText39:
	dc.l	UText40-UText39-4
	binclude	"script/dialogue 39.bin.unc"

UText40:
	dc.l	UText41-UText40-4
	binclude	"script/dialogue 40.bin.unc"

UText41:
	dc.l	UText42-UText41-4
	binclude	"script/dialogue 41.bin.unc"

UText42:
	dc.l	UText43-UText42-4
	binclude	"script/dialogue 42.bin.unc"

UText43:
	dc.l	CText01-UText43-4
	binclude	"script/dialogue 43.bin.unc"

CText01:	binclude "script/dialogue 1.bin"
CText02:	binclude "script/dialogue 2.bin"
CText03:	binclude "script/dialogue 3.bin"
CText04:	binclude "script/dialogue 4.bin"
CText05:	binclude "script/dialogue 5.bin"
CText06:	binclude "script/dialogue 6.bin"
CText07:	binclude "script/dialogue 7.bin"
CText08:	binclude "script/dialogue 8.bin"
CText09:	binclude "script/dialogue 9.bin"
CText10:	binclude "script/dialogue 10.bin"
CText11:	binclude "script/dialogue 11.bin"
CText12:	binclude "script/dialogue 12.bin"
CText13:	binclude "script/dialogue 13.bin"
CText14:	binclude "script/dialogue 14.bin"
CText15:	binclude "script/dialogue 15.bin"
CText16:	binclude "script/dialogue 16.bin"
CText17:	binclude "script/dialogue 17.bin"
CText18:	binclude "script/dialogue 18.bin"
CText19:	binclude "script/dialogue 19.bin"
CText20:	binclude "script/dialogue 20.bin"
CText21:	binclude "script/dialogue 21.bin"
CText22:	binclude "script/dialogue 22.bin"
CText23:	binclude "script/dialogue 23.bin"
CText24:	binclude "script/dialogue 24.bin"
CText25:	binclude "script/dialogue 25.bin"
CText26:	binclude "script/dialogue 26.bin"
CText27:	binclude "script/dialogue 27.bin"
CText28:	binclude "script/dialogue 28.bin"
CText29:	binclude "script/dialogue 29.bin"
CText30:	binclude "script/dialogue 30.bin"
CText31:	binclude "script/dialogue 31.bin"
CText32:	binclude "script/dialogue 32.bin"
CText33:	binclude "script/dialogue 33.bin"
CText34:	binclude "script/dialogue 34.bin"
CText35:	binclude "script/dialogue 35.bin"
CText36:	binclude "script/dialogue 36.bin"
CText37:	binclude "script/dialogue 37.bin"
CText38:	binclude "script/dialogue 38.bin"
CText39:	binclude "script/dialogue 39.bin"
CText40:	binclude "script/dialogue 40.bin"
CText41:	binclude "script/dialogue 41.bin"
CText42:	binclude "script/dialogue 42.bin"
CText43:	binclude "script/dialogue 43.bin"

	; Include art assets
	include "koschk/fonts/pixelfont.asm"
	

__end    ; Very last line, end of ROM address
