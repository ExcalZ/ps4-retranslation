; =====================================================================
; Variable-width renderer for the 8x16 dialogue font.
;
; The dialogue box is a private 128-tile region at VRAM $B000 with a
; full 4096-byte RAM shadow at Text_Buffer.  Offsets inside both are
; identical, so a shadow offset doubles as a VRAM offset:
;
;     offset(line, cell, row) = line*$800 + cell*$40 + row*4
;
; FillTextBackground pre-fills the shadow with paper ($E nibbles) and
; ink is $F, so a glyph composites with a plain OR of $1 into each
; inked nibble: $E|$1 = $F.  No read-modify-write, and drawing the
; same glyph twice is harmless.
;
; A glyph is 8px wide and lands at an arbitrary x, so it straddles at
; most two cells.  VWFDia_NibExp holds, for every (byte, shift) pair,
; the two longs to OR into those cells.  At cell 31 the second long is
; suppressed: "cell 32" of line 1 would be offset $1000, one byte past
; the end of the shadow buffer.
; =====================================================================

VWFDIA_CELLS	= 32
VWFDIA_WIDTH	= VWFDIA_CELLS*8	; 256 px of usable line
VWFDIA_CELL	= $40			; bytes per 8x16 cell
VWFDIA_LINE	= VWFDIA_CELLS*VWFDIA_CELL

; ---------------------------------------------------------------------
; Compose one glyph into the dialogue shadow buffer.
;   a1 = glyph art, as returned by GetFontGraphics
;   d1 = pixel cursor, 0..VWFDIA_WIDTH-1
;   d2 = line (bit 0 only)
; d1 is advanced past the glyph.  All other registers are preserved.
;
; The width comes from the a1 pointer rather than from d0, because
; GetFontGraphics restores d0 -- for the $E0+ substitution codes the
; resolved character survives only in a1.
; ---------------------------------------------------------------------
VWFDia_DrawGlyph:
	movem.l	d0/d3-d4/d6/a1-a4, -(sp)	; d5 is the result, not saved

	move.l	a1, d0
	subi.l	#Art_DiaFont, d0
	lsr.l	#4, d0			; glyph index
	lea	(VWFDia_Widths).l, a4
	moveq	#0, d6
	move.b	(a4,d0.w), d6		; d6 = advance in pixels

	; Art_DiaFont stays exactly as the game shipped it, because the
	; narration engine (RunText2) draws from it at a fixed 8px pitch and
	; would show the slack left by a stripped bearing.  The VWF reads its
	; own left-normalised copy instead.
	lsl.w	#4, d0
	lea	(VWFDia_Font).l, a1
	adda.w	d0, a1

	; The box holds two lines.  An explicit newline ($FC) increments d2
	; with no bounds check -- only the auto-wrap path clamps it -- so a
	; string with three lines runs d2 to 2.  Stock let the write go past
	; the text buffer, where it landed in an off-screen corner of the
	; nametable and was never seen.  Masking d2 instead folds the third
	; line onto the first, which is what made the shop's sell offer
	; overlap.  Drop it: same result on screen, no stray write.
	cmpi.w	#2, d2
	bcc.w	VWFDia_DrawGlyph_Drop

	move.w	d1, d3
	lsr.w	#3, d3			; d3 = starting cell
	move.w	d1, d4
	andi.w	#7, d4
	lsl.w	#3, d4			; d4 = nibble shift * 8

	lea	(Text_Buffer).l, a2
	move.w	d2, d0
	andi.w	#1, d0
	beq.s	VWFDia_DrawGlyph_Line0
	lea	VWFDIA_LINE(a2), a2
VWFDia_DrawGlyph_Line0:
	move.w	d3, d0
	lsl.w	#6, d0
	adda.w	d0, a2			; a2 = first row of the glyph

	moveq	#1, d5			; d5 = may spill into next cell
	cmpi.w	#VWFDIA_CELLS-1, d3
	bne.s	VWFDia_DrawGlyph_Spill
	moveq	#0, d5
VWFDia_DrawGlyph_Spill:

	lea	(VWFDia_NibExp).l, a3
	moveq	#16-1, d3
VWFDia_DrawGlyph_Row:
	moveq	#0, d0
	move.b	(a1)+, d0
	beq.s	VWFDia_DrawGlyph_Next	; blank row, nothing to OR
	lsl.w	#6, d0			; byte * 64
	add.w	d4, d0			; + shift * 8
	movea.l	a3, a4
	adda.w	d0, a4
	move.l	(a4)+, d0
	or.l	d0, (a2)
	tst.w	d5
	beq.s	VWFDia_DrawGlyph_Next
	move.l	(a4), d0
	or.l	d0, VWFDIA_CELL(a2)
VWFDia_DrawGlyph_Next:
	addq.l	#4, a2
	dbf	d3, VWFDia_DrawGlyph_Row

	; record the touched span so the typewriter path can flush it
	move.w	d1, d0
	lsr.w	#3, d0
	move.w	d0, (VWFDia_DirtyCell).l
	addq.w	#1, d5
	move.w	d5, (VWFDia_DirtySpan).l
	move.w	d2, d0
	andi.w	#1, d0
	move.w	d0, (VWFDia_DirtyLine).l
	bra.s	VWFDia_DrawGlyph_Advance

VWFDia_DrawGlyph_Drop:
	clr.w	(VWFDia_DirtySpan).l	; nothing composed, nothing to flush

VWFDia_DrawGlyph_Advance:
	add.w	d6, d1			; advance the cursor

	; Wrap here rather than at the call site: the two dialogue loops
	; dispatch control codes through jmp tbl(pc,d5.w), whose 8-bit
	; displacement leaves no room for the loop to grow.  Returning the
	; result in d5 keeps both call sites exactly their stock size.
	moveq	#1, d5			; d5 = room left on this line
	cmpi.w	#VWFDIA_WIDTH, d1
	blo.s	VWFDia_DrawGlyph_Fits
	moveq	#0, d5
	moveq	#0, d1			; line is full; reset the cursor
VWFDia_DrawGlyph_Fits:
	movem.l	(sp)+, d0/d3-d4/d6/a1-a4
	rts

; ---------------------------------------------------------------------
; Queue a DMA for just the cells the last glyph touched.  Used by the
; one-letter-at-a-time path; the print-all-at-once path still calls
; TextToVRAM to move the whole box.
; ---------------------------------------------------------------------
VWFDia_FlushGlyph:
	movem.l	d0-d7/a0-a2, -(sp)
	tst.w	(VWFDia_DirtySpan).l
	beq.s	VWFDia_FlushGlyph_Done	; dropped glyph, nothing to send
	moveq	#0, d2
	move.w	(VWFDia_DirtyCell).l, d2
	lsl.w	#6, d2
	tst.w	(VWFDia_DirtyLine).l
	beq.s	VWFDia_FlushGlyph_Line0
	addi.w	#VWFDIA_LINE, d2
VWFDia_FlushGlyph_Line0:
	andi.l	#$FFFF, d2		; byte offset within the box
	move.l	d2, d1
	addi.l	#$B000, d1		; VRAM destination
	move.l	#Text_Buffer, d0
	add.l	d2, d0
	lsr.l	#1, d0			; DMA source, pre-shifted
	moveq	#0, d2
	move.w	(VWFDia_DirtySpan).l, d2
	lsl.w	#5, d2			; cells -> words ($20 each)
	jsr	(QueueDMACommands).l
VWFDia_FlushGlyph_Done:
	movem.l	(sp)+, d0-d7/a0-a2
	rts

	even
VWFDia_Font:	binclude	"vwf/diafont.bin"
	even
VWFDia_Widths:	binclude	"vwf/diawidth.bin"
	even
VWFDia_NibExp:	binclude	"vwf/nibexp.bin"
	even

; ---------------------------------------------------------------------
; Narration variant (RunText2).
;
; Same cell geometry as the dialogue box, but the buffer is RAM_Start,
; there is only one line, and paper is 0 rather than $E -- the narration
; overlays scenery, so its background must stay transparent.  loc_6AA86
; pre-clears the buffer to zero, so an OR still composites; the mask has
; to carry $F per pixel instead of $1.  Each nibble of VWFDia_NibExp
; holds $1, and shifting a nibble left by 1 then by 2 cannot carry into
; its neighbour, so v |= v<<1; v |= v<<2 widens $1 to $F in place.
;
;   a1 = glyph art, as returned by GetFontGraphics
;   d1 = pixel cursor
; d1 is advanced; d5 returns non-zero while the line still has room.
;
; ($FFFFED5A).w is left holding the number of cells *covered*, which is
; what loc_6AC98 multiplies by $20 for its DMA length.  Under fixed
; width that equalled the character count; under a VWF it does not, so
; it is recomputed from the cursor here.  Its other role -- a cell index
; in the d4==2 path -- is unreachable: all sixteen RunText2 call sites
; pass d4=1, and d4 is never modified in between.
; ---------------------------------------------------------------------
VWFNar_DrawGlyph:
	movem.l	d0/d2-d4/d6/a1-a4, -(sp)	; d3 is the caller's tile base

	move.l	a1, d0
	subi.l	#Art_DiaFont, d0
	lsr.l	#4, d0			; glyph index
	lea	(VWFDia_Widths).l, a4
	moveq	#0, d6
	move.b	(a4,d0.w), d6		; d6 = advance in pixels
	lsl.w	#4, d0
	lea	(VWFDia_Font).l, a1
	adda.w	d0, a1

	move.w	d1, d3
	lsr.w	#3, d3			; starting cell
	move.w	d1, d4
	andi.w	#7, d4
	lsl.w	#3, d4			; nibble shift * 8

	lea	(RAM_Start).l, a2
	move.w	d3, d0
	lsl.w	#6, d0
	adda.w	d0, a2

	moveq	#1, d5
	cmpi.w	#VWFDIA_CELLS-1, d3
	bne.s	VWFNar_DrawGlyph_Spill
	moveq	#0, d5			; last cell: suppress the spill write
VWFNar_DrawGlyph_Spill:

	lea	(VWFDia_NibExp).l, a3
	moveq	#16-1, d3
VWFNar_DrawGlyph_Row:
	moveq	#0, d0
	move.b	(a1)+, d0
	beq.s	VWFNar_DrawGlyph_Next
	lsl.w	#6, d0
	add.w	d4, d0
	movea.l	a3, a4
	adda.w	d0, a4
	move.l	(a4)+, d0
	move.l	d0, d2
	lsl.l	#1, d2
	or.l	d2, d0
	move.l	d0, d2
	lsl.l	#2, d2
	or.l	d2, d0			; $1 nibbles widened to $F
	or.l	d0, (a2)
	tst.w	d5
	beq.s	VWFNar_DrawGlyph_Next
	move.l	(a4), d0
	move.l	d0, d2
	lsl.l	#1, d2
	or.l	d2, d0
	move.l	d0, d2
	lsl.l	#2, d2
	or.l	d2, d0
	or.l	d0, VWFDIA_CELL(a2)
VWFNar_DrawGlyph_Next:
	addq.l	#4, a2
	dbf	d3, VWFNar_DrawGlyph_Row

	add.w	d6, d1			; advance the cursor

	move.w	d1, d0			; cells covered = ceil(cursor / 8)
	addq.w	#7, d0
	lsr.w	#3, d0
	cmpi.w	#VWFDIA_CELLS, d0
	bcs.s	VWFNar_DrawGlyph_Cells
	moveq	#VWFDIA_CELLS, d0	; never let the DMA run past the buffer
VWFNar_DrawGlyph_Cells:
	move.b	d0, ($FFFFED5A).w

	moveq	#1, d5
	cmpi.w	#VWFDIA_WIDTH, d1
	blo.s	VWFNar_DrawGlyph_Fits
	moveq	#0, d5
	moveq	#0, d1
VWFNar_DrawGlyph_Fits:
	movem.l	(sp)+, d0/d2-d4/d6/a1-a4
	rts
