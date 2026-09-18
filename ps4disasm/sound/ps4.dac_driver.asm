	cpu Z80
	listing off

Z80_DacDriver:	
	di
	di
	ld	sp, Z80_Stack
	ld	c, 0
-
	ld	b, 0
-	djnz	-
	dec	c
	jr	nz, --	; wait a bit (10000h loops)
	jp	zInitDriver
	

; -----------------------
; Z80 Stack Space
;------------------------
	ds	0EFh
Z80_Stack:


zInitDriver:
	ld	hl, 1F00h
	ld	de, 1F01h
	ld	bc, 0FFh
	ld	(hl), 0
	ldir		; clear	1F00..1FFF

zReadyLoop:
	ld	a, (1F00h)
	or	a
	jr	z, zReadyLoop	; wait until a DAC sound is requested
	ld	a, (1F01h)
	or	a
	jr	z, zReadyLoop	; DAC disabled - jump back
	jp	m, zDAC_VolCtrl		; DAC with Volume Control - jump
	ld	a, (1F00h)
	or	a
	jr	z, zReadyLoop
	or	80h
	ld	(1F00h), a		; make the DAC sound 80+
	ld	a, (1F01h)
	or	a
	jp	m, zReadyLoop
	ld	a, 80h
	ld	(1FFDh), a		; set "busy" byte
	ld	hl, 4000h
	ld	(hl), 2Bh
	inc	hl
	ld	a, 80h			; Reg 2B, Data 80 - DAC	Enable
	ld	(hl), a
	inc	hl
	ld	(hl), 0B6h
	inc	hl
	ld	a, (1F04h)		; Reg 1B6 - Stereo bits
	ld	(hl), a
	xor	a
	ld	(1FFDh), a		; clear	"busy" byte
	ld	a, (1F02h)
	sub	81h
	jp	m, zReadyLoop
	call	zSetDACSndBank
	call	zReadDACTbl
	jp	zDoDACSample

zDoSampleDelay:
	push	bc
	ld	hl, zPitchJumpTbl
	ld	a, (1F02h)
	sub	81h
	jp	m, zloc_450	; invalid frequency - cancel playback
	ld	b, 0
	ld	c, a
	add	hl, bc
	add	hl, bc
	ld	a, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, a
	pop	bc
	jp	(hl)		; delay	the driver depending on	the frequency setting


zPitchJumpTbl:
	dw	zloc_1AA
	dw	zloc_1C2
	dw	zloc_1D9
	dw	zloc_1EF
	dw	zloc_204
	dw	zloc_218
	dw	zloc_22A
	dw	zloc_23C
	dw	zloc_24E
	dw	zloc_25F
	dw	zloc_26F
	dw	zloc_27E
	dw	zloc_28C
	dw	zloc_299
	dw	zloc_2A5
	dw	zloc_2B0
	dw	zloc_2BB
	dw	zloc_2C5
	dw	zloc_2CE
	dw	zloc_2D7
	dw	zloc_2DF
	dw	zloc_2E7
	dw	zloc_2EF
	dw	zloc_2F5
	dw	zloc_2FC
	dw	zloc_302
	dw	zloc_307
	dw	zloc_30D
	dw	zloc_312
	
zloc_1AA:
	rept 24
	nop
	endm
	
zloc_1C2:
	rept 23
	nop
	endm
	
zloc_1D9:
	rept 22
	nop
	endm
	
zloc_1EF:
	rept 21
	nop
	endm
	
zloc_204:
	rept 20
	nop
	endm
	
zloc_218:
	rept 18
	nop
	endm
	
zloc_22A:
	rept 18
	nop
	endm
	
zloc_23C:
	rept 18
	nop
	endm
	
zloc_24E:
	rept 17
	nop
	endm
	
zloc_25F:
	rept 16
	nop
	endm
	
zloc_26F:
	rept 15
	nop
	endm
	
zloc_27E:
	rept 14
	nop
	endm
	
zloc_28C:
	rept 13
	nop
	endm
	
zloc_299:
	rept 12
	nop
	endm
	
zloc_2A5:
	rept 11
	nop
	endm
	
zloc_2B0:
	rept 11
	nop
	endm
	
zloc_2BB:
	rept 10
	nop
	endm
	
zloc_2C5:
	rept 9
	nop
	endm
	
zloc_2CE:
	rept 9
	nop
	endm
	
zloc_2D7:
	rept 8
	nop
	endm
	
zloc_2DF:
	rept 8
	nop
	endm
	
zloc_2E7:
	rept 8
	nop
	endm
	
zloc_2EF:
	rept 6
	nop
	endm
	
zloc_2F5:
	rept 7
	nop
	endm
	
zloc_2FC:
	rept 6
	nop
	endm
	
zloc_302:
	rept 5
	nop
	endm
	
zloc_307:
	rept 6
	nop
	endm
	
zloc_30D:
	rept 5
	nop
	endm
	
zloc_312:
	rept 2
	nop
	endm


zDoDACSample:
	ld	a, 80h
	ld	(1FFDh), a	; set "busy" byte
	ld	hl, 4000h
	ld	a, (de)		; read Sample
	ld	(hl), 2Ah	; Reg 2A - DAC data
	inc	hl
	ld	(hl), a		; write	sample data
	xor	a
	ld	(1FFDh), a	; clear	"busy" byte
	ld	a, (1F00h)
	or	a
	jp	p, zReadyLoop	; new sound queued - cancel playback

zloc_32C:
	inc	de		; self-modifying code: INC/DEC DE (next	sample)
	dec	bc		; one sample less to play
	ld	a, b
	or	c
	jr	nz, +	; remaining samples not	yet 0 -	jump
	ld	a, (1F05h)	; sound	finished - looping?
	or	a
	jr	z, zloc_358	; not looping -	end playback
	ld	bc, (1F0Ah)
	ld	de, (1F08h)
	jp	zDoSampleDelay	
+
	ld	a, (1F05h)
	or	a
	ld	a, (hl)		; do a few dummy operations to compensate the
	ld	a, (hl)		; cycle	usage of the DAC sample	loop above
	ld	hl, 4000h
	ld	hl, 4000h
	ld	hl, 4000h
	ld	hl, 4000h
	jp	zDoSampleDelay
zloc_358:
	xor	a
	ld	(1F00h), a
	jp	zReadyLoop
	
zDAC_VolCtrl:
	ld	a, (1F00h)
	or	a
	jp	z, zReadyLoop
	or	80h
	ld	(1F00h), a
	ld	a, (1F01h)
	or	a
	jp	p, zReadyLoop
	ld	a, 80h
	ld	(1FFDh), a		; set "busy" byte
	ld	hl, 4000h
	ld	(hl), 2Bh
	inc	hl
	ld	a, 80h			; Reg 2B, Data 80 - DAC	Enable
	ld	(hl), a
	inc	hl
	ld	(hl), 0B6h
	inc	hl
	ld	a, (1F04h)		; Reg 1B6 - Stereo bits
	ld	(hl), a
	xor	a
	ld	(1FFDh), a		; clear	"busy" byte
	call	zSetDACSndBank
	call	zReadDACTbl
	ld	hl, 4000h
zloc_395:
	push	bc
	ld	a, (1F03h)
	ld	c, a
	ld	a, (de)		; read Sample
	or	a
	jp	m, zloc_3AC	; test sign (m/p) of the sample
	ex	af, af'
	ld	a, 2Fh		; self-modifying code: write CPL to 03B9 and 03DB
	ld	(zloc_3B9), a
	ld	(zloc_3DB), a
	ex	af, af'
	jp	zloc_3B9
	
zloc_3AC:
	ex	af, af'
	ld	a, 0		; self-modifying code: write NOP to 03B9 and 03DB
	ld	(zloc_3B9), a
	ld	(zloc_3DB), a
	ex	af, af'
	jp	zloc_3B9
	
zloc_3B9:
	cpl
	and	7Fh			; strip	80h-bit
	ld	b, a		; store	to B
	ld	a, 80h		; the following	code performs a	calculation of A * C
	srl	b
	bit	3, c
	jr	z, +
	add	a, b
+
	srl	b
	bit	2, c
	jr	z, +
	add	a, b
+
	srl	b
	bit	1, c
	jr	z, +
	add	a, b
+
	srl	b
	bit	0, c
	jr	z, zloc_3DB
	add	a, b
	
zloc_3DB:
	cpl		; invert (CPL) or leave	(NOP)
	bit	4, c	; Volume >= 10h
	jr	z, +
	ld	a, (de)	; yes -	use original value
+
	ld	hl, 4000h
	ex	af, af'
	ld	a, 80h
	ld	(1FFDh), a	; set "busy" byte
	ex	af, af'
	ld	(hl), 2Ah
	inc	hl
	ld	(hl), a		; write	new sample value
	pop	bc
	xor	a
	ld	(1FFDh), a	; clear	"busy" byte
	ld	a, (1F00h)
	or	a
	jp	p, zReadyLoop
	
zloc_3FB:
	inc	de			; self-modifying code: INC/DEC DE
	dec	bc
	ld	a, b
	or	c
	jr	nz, +		; not yet finished - jump
	ld	a, (1F05h)
	or	a
	jp	z, zloc_358
	ld	bc, (1F0Ah)
	ld	de, (1F08h)
	jp	zloc_395
+
	nop
	nop
	nop
	ld	hl, 4000h
	ld	hl, 4000h
	ld	hl, 4000h
	ld	hl, 4000h
	jp	zloc_395
	
zSetDACSndBank:
	ld	a, 80h
	ld	(1FFDh), a
	ld	de, zBankTbl
	ld	a, (1F00h)
	sub	81h			; DAC sound -> index
	jp	m, zloc_450	; invalid index	-> cancel
	add	a, a		; 2 bytes per entry (Bank, Sound in bank)
	ld	e, a
	ld	a, (de)		; read Bank value (last	2 bits)
	ld	hl, 6000h	; switch to Bank 0Ex000/0Fx000
	ld	(hl), a		; Bank bits written: 01Ch..01Fh
	srl	a
	ld	(hl), a
	xor	a
	ld	b, 1
	ld	(hl), b
	ld	(hl), b
	ld	(hl), b
	ld	(hl), a
	ld	(hl), a
	ld	(hl), a
	ld	(hl), a
	xor	a
	ld	(1FFDh), a	; clear	"busy" byte
	inc	de
	ld	a, (de)		; read Sound ID	(in bank)
	ret

	
zloc_450:
	pop	hl		; remove return	address	from stack
	jp	zReadyLoop

	
zReadDACTbl:
	ld	hl, 8000h
	add	a, a
	add	a, a
	add	a, a		; A = A	* 8
	add	a, l
	ld	l, a		; HL +=	A*8 (8 bytes per entry)
	ld	e, (hl)
	inc	hl
	ld	d, (hl)		; DE = Sample Start
	inc	hl
	ld	c, (hl)
	inc	hl
	ld	b, (hl)		; BC = Sample Length
	inc	hl
	ld	a, (hl)
	ld	(1F08h), a
	inc	hl
	ld	a, (hl)
	ld	(1F09h), a
	inc	hl
	ld	a, (hl)
	ld	(1F0Ah), a
	inc	hl
	ld	a, (hl)
	ld	(1F0Bh), a
	ld	a, (1F06h)
	or	a
	jp	z, zloc_485
	ex	de, hl
	add	hl, bc
	dec	hl
	ld	(1F08h), hl
	ex	de, hl		; DE = SmplStart + SmplLen - 1
	
zloc_485:
	jp	nz, zloc_48D
	ld	a, 13h		; write	INC de
	jp	zloc_48F
	
zloc_48D:
	ld	a, 1Bh		 ; write	DEC de (for reversed sample play)
	
zloc_48F:
	ld	hl, zloc_32C
	ld	(hl), a		; write	INC/DEC	to 032Ch
	ld	hl, zloc_3FB
	ld	(hl), a		; write	INC/DEC	to 03FBh
	ret
	
	
	ds	68h
	
	
zBankTbl:
	db	00h, 00h
	db	00h, 01h
	db	00h, 02h
	db	00h, 03h
	db	00h, 04h
	db	00h, 05h
	db	01h, 00h
	db	00h, 07h
	db	02h, 00h
	db	01h, 01h
	db	00h, 08h
	db	02h, 01h
	db	00h, 09h
	db	02h, 02h
	db	00h, 06h
	db	03h, 00h
	db	02h, 03h
	
Z80_DacDriver_End:
