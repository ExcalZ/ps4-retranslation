; =====================================================================
; Variable-width font: composer and 1bpp -> 4bpp expander
; =====================================================================
; Ported from the Japanese-ROM prototype, where these were hand-assembled
; from Python. Here they are source, so the assembler places them and
; every reference resolves by label.
;
; The face sits on rows 1-7 of the cell with the baseline on row 7, which
; is where the stock 8x8 font sits, so converted and unconverted text
; share a line. Row 0 is always paper.
;
;   VWF_FontTable    256 entries x 8 bytes: advance width, then rows 1-7
;   VWF_ExpandTable  256 longwords: one 1bpp byte -> eight 4bpp nibbles
;
; Eight bytes per font entry rather than six so a code indexes with a
; shift instead of a multiply; the two spare bytes became rows 6 and 7
; when capitals and lowercase were added.
; ---------------------------------------------------------------------

VWF_INK		= $F
VWF_PAPER	= $E
VWF_ROWS	= 7			; glyph rows, cell rows 1-7
VWF_STRIDE	= 12			; bytes per scratch row: 96px, 12 cells
VWF_BLANKROW	= $EEEEEEEE		; one 4bpp row of paper

; ---------------------------------------------------------------------
; VWF_Compose
;   in    a0  text, terminated by any byte >= $FE (advanced past it)
;         a1  scratch buffer, VWF_ROWS * VWF_STRIDE bytes
;   out   d0  pixel width of the run
;   uses  d1-d7, a2, a3
;
; A glyph row is one byte with the leftmost pixel in bit 7. Placing it at
; an arbitrary x means shifting it into a 16-bit window - byte << 8, then
; lsr by (x & 7) - after which the high byte belongs to scratch[x >> 3]
; and the low byte to the cell after it. Everything else is bookkeeping.
; ---------------------------------------------------------------------
VWF_Compose:
	movea.l	a1, a3
	moveq	#(VWF_ROWS*VWF_STRIDE+3)/4-1, d1
VWF_Compose_Clear:
	clr.l	(a3)+
	dbf	d1, VWF_Compose_Clear

	moveq	#0, d3			; x = 0
VWF_Compose_Next:
	moveq	#0, d2
	move.b	(a0)+, d2
	cmpi.b	#$FE, d2
	bcc.s	VWF_Compose_Done	; >= $FE terminates
	lsl.w	#3, d2			; code * 8
	lea	(VWF_FontTable).l, a2
	adda.w	d2, a2
	moveq	#0, d4
	move.b	(a2)+, d4		; advance width
	beq.s	VWF_Compose_Next	; width 0: undrawable, no advance

	move.w	d3, d6
	andi.w	#7, d6			; x & 7
	move.w	d3, d1
	lsr.w	#3, d1			; x >> 3
	movea.l	a1, a3
	adda.w	d1, a3
	moveq	#VWF_ROWS-1, d7
VWF_Compose_Row:
	moveq	#0, d5
	move.b	(a2)+, d5
	lsl.w	#8, d5			; glyph row into bits 15-8
	lsr.w	d6, d5			; slide to its sub-byte position
	move.w	d5, d0
	lsr.w	#8, d0
	or.b	d0, (a3)		; high byte -> this cell
	or.b	d5, 1(a3)		; low byte  -> the next one
	lea	VWF_STRIDE(a3), a3
	dbf	d7, VWF_Compose_Row

	add.w	d4, d3			; x += width
	addq.w	#1, d3			; x += one pixel of tracking
	bra.w	VWF_Compose_Next

VWF_Compose_Done:
	tst.w	d3
	beq.s	VWF_Compose_Zero	; empty run: do not underflow
	subq.w	#1, d3			; drop the trailing gap
VWF_Compose_Zero:
	move.w	d3, d0
	rts

; ---------------------------------------------------------------------
; VWF_Expand
;   in    d0  cell count
;         a1  destination, d0 * 32 bytes
;   uses  d1, d3, d4, d5, a2, a3, a4
;
; Expansion is a 1 KB lookup rather than a bit loop: eight nibbles from
; one table read is about 12 cycles against roughly 100 for shifting them
; out one at a time.
; ---------------------------------------------------------------------
VWF_Expand:
	tst.w	d0
	beq.s	VWF_Expand_Out
	movea.l	a1, a3
	move.w	d0, d1
	subq.w	#1, d1
	moveq	#0, d4			; cell index
VWF_Expand_Cell:
	move.l	#VWF_BLANKROW, (a3)+	; row 0 is paper; 1-7 carry glyphs
	lea	(VWF_Scratch).l, a2
	adda.w	d4, a2
	moveq	#VWF_ROWS-1, d3
VWF_Expand_Row:
	moveq	#0, d5
	move.b	(a2), d5
	lsl.w	#2, d5
	lea	(VWF_ExpandTable).l, a4
	adda.w	d5, a4
	move.l	(a4), (a3)+		; eight nibbles out
	lea	VWF_STRIDE(a2), a2	; down one scratch row
	dbf	d3, VWF_Expand_Row
	addq.w	#1, d4
	dbf	d1, VWF_Expand_Cell
VWF_Expand_Out:
	rts

; ---------------------------------------------------------------------
	even
VWF_FontTable:		binclude	"vwf/font.bin"
	even
VWF_ExpandTable:	binclude	"vwf/expand.bin"
	even

; ---------------------------------------------------------------------
; VWF_DbgUpdate - measurement only, built out when vwf_measure = 0
;
; LoadWindowTiles draws a whole message in one call, wrapping across lines
; until it hits a terminator, so the cells written by a single call IS the
; box fill. That is the number the pool has to cover, and it is the one
; figure in the layout that was estimated rather than measured.
; ---------------------------------------------------------------------
	if vwf_measure
VWF_DbgUpdate:
	move.w	d0, -(sp)
	addq.w	#1, (VWF_Dbg_Calls).l
	move.w	(VWF_Dbg_Run).l, d0
	cmp.w	(VWF_Dbg_Max).l, d0
	bls.s	VWF_DbgUpdate_Done
	move.w	d0, (VWF_Dbg_Max).l
VWF_DbgUpdate_Done:
	move.w	(sp)+, d0
	rts
	endif
