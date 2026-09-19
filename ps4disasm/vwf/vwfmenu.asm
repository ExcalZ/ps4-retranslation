
; =====================================================================
; Menu VWF tile pool.
;
; The window bank at $680-$6FF is 128 tiles.  $680 is the blank used for
; the space; $681-$6A4 keep the fixed font for the glyphs that labels and
; numbers need (uppercase and digits, which already live at those codes,
; so nothing has to move).  The pool takes what is left.
;
; Allocation is by **content**, not by destination.  A composed tile that
; is already resident is reused, which is what makes the budget work: the
; camp technique window costs zero tiles because all of its names also
; appear in the battle list, and names sharing a prefix at the same pixel
; phase share their leading tiles.  Fields are cell-aligned, so every
; name starts at phase 0 and identical text always composes identically.
;
; Invalidation mirrors the engine's own window stack.  Window_Create
; pushes a saved plane map and Window_Destroy pops it, restoring the
; nametable underneath; so the pool records its high-water mark on create
; and rolls back to it on destroy.  A restored nametable can never point
; at a freed tile, because everything that window drew lies above the
; mark and everything beneath it is still resident.
; =====================================================================

; ---------------------------------------------------------------------
; Find or allocate a pool slot for one composed tile.
;   a0 = the tile's 8 bytes of 1bpp source
; Returns d0 = slot index, or -1 if the pool is exhausted.  The caller
; must test for -1: overflowing would hand back a tile belonging to
; another string, which is far harder to diagnose than a missing glyph.
; ---------------------------------------------------------------------
VWFMenu_Alloc:
	; d0 = slot (or -1); d1 != 0 if the caller must upload the tile.
	; d1 is a result and is deliberately not saved.
	movem.l	d2-d6/a1-a2, -(sp)
	move.l	(a0), d2		; the key, compared as two longs
	move.l	4(a0), d3
	if vwf_menu_strips=1
	lea	(VWFMenu_StripOf).l, a2
	else
	moveq	#0, d4			; set once this call has swept
	endif
	moveq	#0, d0
	if vwf_menu_hash=1
	; The linear scan cost about 50 cycles per slot per cell, and every
	; cell of every string paid it - 290 lookups on a Status back-out.
	; Walk the key's bucket instead: the chain holds only slots whose
	; key hashes the same, so a lookup is a few compares.  The bound in
	; d1 is the same as the scan's - PoolTop in battle, the whole pool in
	; the field - because a slot above the frontier in battle is about to
	; be overrun by the plain bump.
	move.w	(VWFMenu_PoolTop).l, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	beq.s	VWFMenu_Alloc_HashField
	cmpi.w	#VWFMENU_BATTLE_SLOTS, d1
	bls.s	VWFMenu_Alloc_HashWalk
	move.w	#VWFMENU_BATTLE_SLOTS, d1
	bra.s	VWFMenu_Alloc_HashWalk
VWFMenu_Alloc_HashField:
	move.w	#VWFMENU_ACTIVE_SLOTS, d1
VWFMenu_Alloc_HashWalk:
	bsr.w	VWFMenu_KeyHash		; d5 = bucket of the key at (a0)
	lea	(VWFMenu_Bucket).l, a2
	move.b	(a2,d5.w), d0		; head, as slot+1; 0 ends a chain
	move.w	#VWFMENU_SLOTS, d6	; a chain can never be longer than the pool:
					; (move.w, not moveq: 146 does not fit a moveq)
VWFMenu_Alloc_Chain:			; a longer walk means a stale index (an old
	subq.w	#1, d0			; savestate), and ends as a miss
	bmi.s	VWFMenu_Alloc_Retry	; end of chain: not resident
	cmpi.w	#VWFMENU_SLOTS, d0
	bcc.s	VWFMenu_Alloc_Retry	; not a slot: stale index, treat as a miss
	subq.w	#1, d6
	bmi.s	VWFMenu_Alloc_Retry
	cmp.w	d1, d0
	bcc.s	VWFMenu_Alloc_ChainNext	; above the bound: skip, keep walking
	bsr.w	VWFMenu_KeyAddr
	cmp.l	(a1), d2
	bne.s	VWFMenu_Alloc_ChainNext
	cmp.l	4(a1), d3
	beq.w	VWFMenu_Alloc_Hit
VWFMenu_Alloc_ChainNext:
	bsr.w	VWFMenu_NextAddr
	moveq	#0, d0
	move.b	(a1), d0		; high byte stays clear: d0 < 256 throughout
	bra.s	VWFMenu_Alloc_Chain
	else
	if vwf_menu_strips=0
	; Scan the WHOLE table, not just below PoolTop.  A key above the
	; frontier still has its tile in VRAM - only Take rewrites either, and
	; Reset clears both - and after Release rolls the frontier back, the
	; cells an outer window shares with the released one still point up
	; there.  Re-finding those keys is what keeps such cells valid when the
	; inner window is rebuilt in another order.  Field only: battle never
	; sweeps, so there a revived key above the frontier would be overrun by
	; the plain bump below.
	move.w	(VWFMenu_PoolTop).l, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	bne.s	VWFMenu_Alloc_Test
	move.w	#VWFMENU_ACTIVE_SLOTS, d1
	else
	move.w	(VWFMenu_PoolTop).l, d1
	endif
	bra.s	VWFMenu_Alloc_Test

VWFMenu_Alloc_Scan:
	if vwf_menu_strips=1
	move.w	d0, d4			; strip slots do not own valid keys
	add.w	d4, d4
	move.w	(a2,d4.w), d4
	cmpi.w	#$FFFE, d4
	bne.s	VWFMenu_Alloc_Next
	endif
	cmp.l	(a1), d2		; first long rejects almost every miss
	bne.s	VWFMenu_Alloc_Next
	cmp.l	4(a1), d3
	beq.w	VWFMenu_Alloc_Hit	; resident: take another reference
VWFMenu_Alloc_Next:
	lea	8(a1), a1
	addq.w	#1, d0
VWFMenu_Alloc_Test:
	cmp.w	d1, d0
	blo.s	VWFMenu_Alloc_Scan
	endif	; vwf_menu_hash

	; Not resident.  Prefer a slot this window has finished with - one
	; whose last referring cell was overwritten - before growing the
	; pool.  Slots below the window's mark belong to windows further out
	; and are never taken.
	; Scan the whole pool, not from the window's mark.  The mark was a
	; guard against an inner window evicting an outer one's tiles, but
	; the sweep already guarantees that: anything the plane still refers
	; to is marked live.  Worse, the mark saturates - once the pool fills
	; once, every later window records a mark of VWFMENU_SLOTS and the
	; free-slot scan covers an empty range forever, so the sweep's work
	; was thrown away and it re-ran on every string.
VWFMenu_Alloc_Retry:
	moveq	#0, d0
	if vwf_menu_strips=0
	move.w	(VWFMenu_PoolTop).l, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	beq.s	VWFMenu_Alloc_FreeTest
	cmpi.w	#VWFMENU_BATTLE_SLOTS, d1
	bls.s	VWFMenu_Alloc_FreeTest
	move.w	#VWFMENU_BATTLE_SLOTS, d1
	endif
	bra.s	VWFMenu_Alloc_FreeTest
VWFMenu_Alloc_FreeScan:
	bsr.w	VWFMenu_RefAddr
	tst.b	(a1)
	beq.s	VWFMenu_Alloc_Take
	addq.w	#1, d0
VWFMenu_Alloc_FreeTest:
	cmp.w	d1, d0
	blo.s	VWFMenu_Alloc_FreeScan

VWFMenu_Alloc_Grow:
	move.w	#VWFMENU_ACTIVE_SLOTS, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	beq.s	VWFMenu_Alloc_GrowCap
	move.w	#VWFMENU_BATTLE_SLOTS, d1 ; the appended alphabet bank is field-only
VWFMenu_Alloc_GrowCap:
	cmp.w	d1, d0			; nothing free: grow if there is room
	bcc.w	VWFMenu_Alloc_Full
	addq.w	#1, (VWFMenu_PoolTop).l
	move.w	(VWFMenu_PoolTop).l, d1
	cmp.w	(VWFMenu_Peak).l, d1
	bls.s	VWFMenu_Alloc_GrowLive
	move.w	d1, (VWFMenu_Peak).l
VWFMenu_Alloc_GrowLive:
	if vwf_menu_strips=0
	; A slot above the old frontier can still be live: the sweep that
	; follows every field Window_Destroy marks whatever the plane still
	; shows, including an outer window's cells that shared slots with the
	; window just released.  Taking it would overwrite a tile that is on
	; screen; step past it instead.  Battle never sweeps and its counts
	; are never cleared, so there this stays the plain bump it always was.
	cmpi.w	#$C, (Game_Mode_Index).w
	bne.s	VWFMenu_Alloc_Take
	bsr.w	VWFMenu_RefAddr
	tst.b	(a1)
	beq.s	VWFMenu_Alloc_Take
	move.w	d1, d0
	bra.s	VWFMenu_Alloc_Grow
	endif

VWFMenu_Alloc_Take:
	bsr.w	VWFMenu_KeyAddr	; claim the slot for this key
	if vwf_menu_hash=1
	bsr.w	VWFMenu_KeyUnlink	; the old key at (a1) leaves its bucket
	endif
	move.l	d2, (a1)
	move.l	d3, 4(a1)
	if vwf_menu_hash=1
	bsr.w	VWFMenu_KeyLink		; the new key at (a1) joins its bucket
	endif
	bsr.w	VWFMenu_RefAddr
	move.b	#1, (a1)
	addq.w	#1, (VWFMenu_TakeGen).l	; a slot changed hands: HUD cache stale
	if vwf_menu_strips=1
	lea	(VWFMenu_StripOf).l, a1	; mark this slot as composer-owned
	move.w	d0, d1
	add.w	d1, d1
	move.w	#$FFFE, (a1,d1.w)
	endif
	moveq	#1, d1			; d1 != 0 tells the caller to upload
	bra.s	VWFMenu_Alloc_Done

VWFMenu_Alloc_Hit:
	bsr.w	VWFMenu_RefAddr
	; Saturate.  The count is a byte and battle never decrements it, so a
	; cell hit every frame - the party HUD's, before it was cached - wrapped
	; to zero every 256 frames and the free scan handed the slot to the
	; next list drawn on that frame.  Only zero means free; 255 is plenty.
	cmpi.b	#$FF, (a1)
	beq.s	VWFMenu_Alloc_HitCounted
	addq.b	#1, (a1)
VWFMenu_Alloc_HitCounted:
	moveq	#0, d1			; already in VRAM
VWFMenu_Alloc_Done:
	movem.l	(sp)+, d2-d6/a1-a2
	rts

	if vwf_menu_hash=1
; ---------------------------------------------------------------------
; Bucket of the 8-byte key at (a0): the eight rows folded together with
; XOR down to one byte, masked to VWFMENU_BUCKETS.  Returns d5.w; d6 is
; scratch.  Cheap on purpose - it runs once per lookup and twice per
; take - and good enough: 88 slots over 128 buckets keeps chains short.
; ---------------------------------------------------------------------
VWFMenu_KeyHash:
	move.l	(a0), d5
	move.l	4(a0), d6
	eor.l	d6, d5
	move.w	d5, d6
	swap	d5
	eor.w	d6, d5
	move.b	d5, d6
	lsr.w	#8, d5
	eor.b	d6, d5
	andi.w	#VWFMENU_BUCKETS-1, d5
	rts

; Rebuild the whole index from the key table: every chain emptied, then
; every slot linked.  About 5000 cycles, so it is affordable wherever a
; window opens, and it is what makes the index safe against RAM it did
; not write - a savestate from a build without it, whose StripOf/StripNext
; bytes are whatever that build left.  Keys of all-ones (Reset) are never
; linked: no cell composes to them.
VWFMenu_IndexRebuild:
	movem.l	d0-d1/d5-d6/a0-a3, -(sp)
	lea	(VWFMenu_Bucket).l, a2
	move.w	#VWFMENU_BUCKETS/4-1, d0
VWFMenu_IndexRebuild_Clear:
	clr.l	(a2)+
	dbf	d0, VWFMenu_IndexRebuild_Clear
	moveq	#0, d0
	move.w	#VWFMENU_BATTLE_SLOTS, d6
	cmpi.w	#$C, (Game_Mode_Index).w
	bne.s	VWFMenu_IndexRebuild_Limit
	move.w	#VWFMENU_ACTIVE_SLOTS, d6
VWFMenu_IndexRebuild_Limit:
VWFMenu_IndexRebuild_Slot:
	bsr.w	VWFMenu_KeyAddr
	moveq	#-1, d1
	cmp.l	(a1), d1
	bne.s	VWFMenu_IndexRebuild_Link
	cmp.l	4(a1), d1
	beq.s	VWFMenu_IndexRebuild_Next	; never composed: leave unlinked
VWFMenu_IndexRebuild_Link:
	bsr.s	VWFMenu_KeyLink
VWFMenu_IndexRebuild_Next:
	addq.w	#1, d0
	cmp.w	d6, d0
	blo.s	VWFMenu_IndexRebuild_Slot
	movem.l	(sp)+, d0-d1/d5-d6/a0-a3
	rts

; Link slot d0, whose key is at (a1), at the head of its bucket.  Heads
; and links hold slot+1 so that zero - fresh RAM, and what Reset writes -
; is an empty chain.
VWFMenu_KeyLink:
	movem.l	d5-d6/a0/a2, -(sp)
	movea.l	a1, a0
	bsr.w	VWFMenu_KeyHash
	lea	(VWFMenu_Bucket).l, a2
	move.b	(a2,d5.w), d6
	bsr.w	VWFMenu_NextAddr
	move.b	d6, (a1)		; Next[slot] = head
	move.w	d0, d6
	addq.w	#1, d6
	move.b	d6, (a2,d5.w)		; head = slot+1
	movem.l	(sp)+, d5-d6/a0/a2
	rts

; Unlink slot d0, whose (old) key is at (a1), from its bucket.  A key
; that was never linked - Reset's all-ones, fresh RAM's zeroes - is not
; found and nothing changes; so is a chain from an old savestate, whose
; links are bounded and validated the same way the lookup's are.
VWFMenu_KeyUnlink:
	movem.l	d3-d7/a0-a2, -(sp)
	move.w	d0, d4		; target slot: helpers use d0 as their input
	movea.l	a1, a0
	bsr.w	VWFMenu_KeyHash
	move.w	d5, d3		; bucket survives while d5 becomes the walk bound
	lea	(VWFMenu_Bucket).l, a2
	move.w	#VWFMENU_SLOTS, d5	; bound: a stale index may hold a cycle
					; (move.w: 146 does not fit a moveq)
	moveq	#0, d6
	move.b	(a2,d3.w), d6		; head, slot+1
	subq.w	#1, d6
	bmi.s	VWFMenu_KeyUnlink_Done	; empty chain
	cmpi.w	#VWFMENU_SLOTS, d6
	bcc.s	VWFMenu_KeyUnlink_Done	; stale
	cmp.w	d4, d6
	bne.s	VWFMenu_KeyUnlink_Walk
	move.w	d4, d0
	bsr.w	VWFMenu_NextAddr
	move.b	(a1), (a2,d3.w)	; head = Next[slot]
	bra.s	VWFMenu_KeyUnlink_Done
VWFMenu_KeyUnlink_Walk:
	subq.w	#1, d5
	bmi.s	VWFMenu_KeyUnlink_Done	; walked the whole pool: stale
	moveq	#0, d7
	move.w	d6, d0
	bsr.w	VWFMenu_NextAddr
	move.b	(a1), d7		; d7 = Next[d6], slot+1
	subq.w	#1, d7
	bmi.s	VWFMenu_KeyUnlink_Done	; not in this chain
	cmpi.w	#VWFMENU_SLOTS, d7
	bcc.s	VWFMenu_KeyUnlink_Done	; stale
	cmp.w	d4, d7
	beq.s	VWFMenu_KeyUnlink_Found
	move.w	d7, d6
	bra.s	VWFMenu_KeyUnlink_Walk
VWFMenu_KeyUnlink_Found:
	move.w	d4, d0
	bsr.w	VWFMenu_NextAddr
	move.b	(a1), d7
	move.w	d6, d0
	bsr.w	VWFMenu_NextAddr
	move.b	d7, (a1)		; Next[pred] = Next[slot]
VWFMenu_KeyUnlink_Done:
	; The walk feeds NextAddr through d0, so d0 is the last chain node
	; here, not the target.  Alloc_Take goes on to link, count and return
	; d0 as the slot it claimed: without this it handed back the bucket
	; head's slot whenever the stale key shared a bucket with a live one
	; (every fresh slot's all-ones key hashes to bucket 0, so with 32
	; buckets that is one glyph in 32).
	move.w	d4, d0
	movem.l	(sp)+, d3-d7/a0-a2
	rts
	endif
VWFMenu_Alloc_Full:
	if vwf_menu_strips=0
	; Hits revive slots above PoolTop, so PoolTop no longer says how full
	; the pool is and the composer's pressure sweep (PoolTop + cells > cap)
	; can stay silent while every slot is live-or-dead-unswept.  Rudy's
	; equip screen drew PlasmaDagger with two blank cells that way, thirty
	; dead cells waiting for a sweep nobody ran.  Sweep once here, in the
	; field, and look again before giving up.
	tst.w	d4
	bne.s	VWFMenu_Alloc_FullReally
	bsr.w	VWFMenu_FieldReclaimAllowed
	beq.s	VWFMenu_Alloc_FullReally
	moveq	#1, d4
	jsr	(VWFMenu_Sweep).l
	bra.w	VWFMenu_Alloc_Retry
VWFMenu_Alloc_FullReally:
	endif
	moveq	#-1, d0
	movem.l	(sp)+, d2-d6/a1-a2
	rts

; ---------------------------------------------------------------------
; Battle Item window, open: rewind the pool to the command menu's level
; and draw the pre-rendered page buffers without composing any name.
; Battle_ItemPageRender rebuilds every page on its way in - including the
; first, from VWFMenu_BattleItemPageOpen - so composing all four here only
; ran the pool dry (150 cells refused per open) and cost a dozen frames.
; Both are called through six-byte jsrs padded to the size of the code
; they replaced, so ps4.asm's addresses - and the player's savestates -
; do not move.
; ---------------------------------------------------------------------
VWFMenu_BattleOpenItems:
	move.w	(VWFMenu_BattleBase).l, (VWFMenu_PoolTop).l
	st	(VWFMenu_SkipNames).l
	rts

VWFMenu_BattleItemPageOpen:
	clr.w	($FFFF418C).l		; as the stock code did before the render
	clr.b	(VWFMenu_SkipNames).l
	jmp	(Battle_ItemPageRender).l	; only the visible page owns tiles

; ---------------------------------------------------------------------
; d0 = slots with a zero count, anywhere in the pool: what Alloc can hand
; out without a sweep.
; ---------------------------------------------------------------------
VWFMenu_FreeSlots:
	movem.l	d1-d2/a0-a1, -(sp)
	moveq	#0, d0
	moveq	#0, d2
	move.w	#VWFMENU_ACTIVE_SLOTS-1, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	beq.s	VWFMenu_FreeSlots_Next
	move.w	#VWFMENU_BATTLE_SLOTS-1, d1
VWFMenu_FreeSlots_Next:
	move.w	d0, -(sp)
	move.w	d2, d0
	bsr.w	VWFMenu_RefAddr
	move.w	(sp)+, d0
	tst.b	(a1)
	bne.s	VWFMenu_FreeSlots_Used
	addq.w	#1, d0
VWFMenu_FreeSlots_Used:
	addq.w	#1, d2
	dbf	d1, VWFMenu_FreeSlots_Next
	movem.l	(sp)+, d1-d2/a0-a1
	rts

; ---------------------------------------------------------------------
; Drop a reference held by a nametable cell that is being overwritten.
; This is what bounds the pool: without it a scrolling list allocates a
; fresh tile for every name it reveals and frees nothing, because no
; window is destroyed while scrolling.
;   d0 = the nametable entry being replaced
; ---------------------------------------------------------------------
VWFMenu_Deref:
	movem.l	d0-d1/a0-a1, -(sp)
	andi.w	#$7FF, d0
	subi.w	#$680, d0
	bcs.s	VWFMenu_Deref_Done	; below the pool
	cmpi.w	#VWFMENU_TILESPAN, d0
	bcc.s	VWFMenu_Deref_Done	; beyond the reverse map
	lea	(VWFMenu_TileSlot).l, a0
	move.b	(a0,d0.w), d0		; physical tile -> non-contiguous slot
	cmpi.b	#$FF, d0
	beq.s	VWFMenu_Deref_Done	; not one of ours
	andi.w	#$FF, d0
	bsr.w	VWFMenu_SlotCap
	bcc.s	VWFMenu_Deref_Done
	bsr.w	VWFMenu_RefAddr
	tst.b	(a1)
	beq.s	VWFMenu_Deref_Done	; already free
	subq.b	#1, (a1)
VWFMenu_Deref_Done:
	movem.l	(sp)+, d0-d1/a0-a1
	rts

; ---------------------------------------------------------------------
; Field chrome has 32 more slots than fit in VWF_RAM_Base.  The first 114
; keep their VWF4 addresses; only indices 114..145 use the battle-setup RAM
; tails.  Each helper preserves d0 (the logical slot/record) and returns the
; requested physical address in a1.  Battle allocation is capped at 88, so it
; never reaches these tails after battle data has claimed that RAM.
; ---------------------------------------------------------------------
VWFMenu_KeyAddr:
	move.w	d0, -(sp)
	cmpi.w	#VWFMENU_BASE_SLOTS, d0
	bcs.s	VWFMenu_KeyAddr_Base
	subi.w	#VWFMENU_BASE_SLOTS, d0
	lsl.w	#3, d0
	lea	(VWFMenu_KeysX).l, a1
	bra.s	VWFMenu_KeyAddr_Done
VWFMenu_KeyAddr_Base:
	lsl.w	#3, d0
	lea	(VWFMenu_Keys).l, a1
VWFMenu_KeyAddr_Done:
	adda.w	d0, a1
	move.w	(sp)+, d0
	rts

VWFMenu_RefAddr:
	move.w	d0, -(sp)
	cmpi.w	#VWFMENU_BASE_SLOTS, d0
	bcs.s	VWFMenu_RefAddr_Base
	subi.w	#VWFMENU_BASE_SLOTS, d0
	lea	(VWFMenu_RefsX).l, a1
	bra.s	VWFMenu_RefAddr_Done
VWFMenu_RefAddr_Base:
	lea	(VWFMenu_Refs).l, a1
VWFMenu_RefAddr_Done:
	adda.w	d0, a1
	move.w	(sp)+, d0
	rts

VWFMenu_NextAddr:
	move.w	d0, -(sp)
	cmpi.w	#VWFMENU_BASE_SLOTS, d0
	bcs.s	VWFMenu_NextAddr_Base
	subi.w	#VWFMENU_BASE_SLOTS, d0
	lea	(VWFMenu_NextX).l, a1
	bra.s	VWFMenu_NextAddr_Done
VWFMenu_NextAddr_Base:
	lea	(VWFMenu_Next).l, a1
VWFMenu_NextAddr_Done:
	adda.w	d0, a1
	move.w	(sp)+, d0
	rts

VWFMenu_SaveAddr:
	move.w	d0, -(sp)
	cmpi.w	#VWFMENU_BASE_SLOTS, d0
	bcs.s	VWFMenu_SaveAddr_Base
	subi.w	#VWFMENU_BASE_SLOTS, d0
	lsl.w	#3, d0
	lea	(VWFMenu_SaveStackX).l, a1
	bra.s	VWFMenu_SaveAddr_Done
VWFMenu_SaveAddr_Base:
	lsl.w	#3, d0
	lea	(VWFMenu_SaveStack).l, a1
VWFMenu_SaveAddr_Done:
	adda.w	d0, a1
	move.w	(sp)+, d0
	rts

; d0 = slot.  Compare it against the pool this game mode may touch:
; VWFMENU_ACTIVE_SLOTS in the field, VWFMENU_BATTLE_SLOTS anywhere else.
; Returns the flags of that cmpi (rts leaves CCR alone): bcc = out of range.
; A slot number derived from a plane cell - Deref, Sweep, SaveRegion, the
; glue - can name a tail slot in battle if a lowercase or Japanese tile is
; on the plane there, and the tails are Enemy_Stats by then; a fixed 146
; compare would let such a cell read or count into enemy data.
VWFMenu_SlotCap:
	cmpi.w	#$C, (Game_Mode_Index).w
	beq.s	VWFMenu_SlotCap_Field
	cmpi.w	#VWFMENU_BATTLE_SLOTS, d0
	rts
VWFMenu_SlotCap_Field:
	cmpi.w	#VWFMENU_ACTIVE_SLOTS, d0
	rts

; KeyAddr/RefAddr answering in a2 with a1 preserved, for the composer paths
; where a1 is the plane cursor.
VWFMenu_KeyAddr2:
	move.l	a1, -(sp)
	bsr.w	VWFMenu_KeyAddr
	movea.l	a1, a2
	movea.l	(sp)+, a1
	rts

VWFMenu_RefAddr2:
	move.l	a1, -(sp)
	bsr.w	VWFMenu_RefAddr
	movea.l	a1, a2
	movea.l	(sp)+, a1
	rts

; ---------------------------------------------------------------------
; The composed build changed saved-region records from (tile,key) to the
; key alone.  Besides buying eight more records in the same RAM, this keeps
; old in-progress savestates usable: convert their ten-byte records in place
; on the first window operation.  Destination always trails source, so the
; forward copy cannot overwrite an unread record.
; ---------------------------------------------------------------------
VWFMenu_EnsureLayout:
	if vwf_menu_strips=0
	cmpi.l	#$56574635, (VWFMenu_LayoutMagic).l ; "VWF5"
	beq.w	VWFMenu_EnsureLayout_Done
	movem.l	d0-d6/a0-a2, -(sp)
	move.l	(VWFMenu_LayoutMagic).l, d3
	cmpi.l	#$56574634, d3		; VWF4 has the complete 114-slot base
	beq.w	VWFMenu_EnsureLayout_V4
	cmpi.l	#$56574633, d3		; VWF3 already has the 114-slot arrays
	beq.w	VWFMenu_EnsureLayout_V3
	moveq	#88, d2			; legacy chrome pool size
	cmpi.l	#$56574632, d3		; VWF2 already had 96 compact slots
	bne.s	VWFMenu_EnsureLayout_Count
	moveq	#96, d2
VWFMenu_EnsureLayout_Count:
	; Move arrays that the enlarged key table now occupies before filling its
	; new tail.  The first 88/96 slot indices and their VRAM tiles stay exact.
	move.w	d2, d0
	subq.w	#1, d0
	lea	(VWF_RAM_Base+$4A0).l, a0
	lea	(VWFMenu_StripNext).l, a1
VWFMenu_EnsureLayout_Next:
	move.b	(a0)+, (a1)+
	dbf	d0, VWFMenu_EnsureLayout_Next
	move.w	d2, d0
	subq.w	#1, d0
	lea	(VWF_RAM_Base+$440).l, a0
	lea	(VWFMenu_Refs).l, a1
VWFMenu_EnsureLayout_Refs:
	move.b	(a0)+, (a1)+
	dbf	d0, VWFMenu_EnsureLayout_Refs
	lea	(VWFMenu_Bucket).l, a1
	moveq	#VWFMENU_BUCKETS/4-1, d0
VWFMenu_EnsureLayout_Buckets:
	clr.l	(a1)+			; Mark/Release rebuilds the index immediately
	dbf	d0, VWFMenu_EnsureLayout_Buckets
	; Slots newly introduced by this layout own no key or reference.
	move.w	d2, d0
	lsl.w	#3, d0
	lea	(VWFMenu_Keys).l, a0
	adda.w	d0, a0
	move.w	#VWFMENU_BASE_SLOTS, d0
	sub.w	d2, d0
	add.w	d0, d0			; two longwords per key
	subq.w	#1, d0
	moveq	#-1, d1
VWFMenu_EnsureLayout_Keys:
	move.l	d1, (a0)+
	dbf	d0, VWFMenu_EnsureLayout_Keys
	lea	(VWFMenu_Refs).l, a0
	adda.w	d2, a0
	lea	(VWFMenu_StripNext).l, a1
	adda.w	d2, a1
	move.w	#VWFMENU_BASE_SLOTS, d0
	sub.w	d2, d0
	subq.w	#1, d0
VWFMenu_EnsureLayout_ClearTail:
	clr.b	(a0)+
	clr.b	(a1)+
	dbf	d0, VWFMenu_EnsureLayout_ClearTail
	cmpi.l	#$56574632, d3
	beq.w	VWFMenu_EnsureLayout_Stamp ; VWF2 records are already compact
	move.w	(VWFMenu_SaveTop).l, d0
	lea	(VWFMenu_SaveMark).l, a0
	moveq	#VWFMENU_DEPTH-1, d1
VWFMenu_EnsureLayout_Mark:
	move.w	(a0)+, d2
	cmp.w	d2, d0
	bcc.s	VWFMenu_EnsureLayout_MarkNext
	move.w	d2, d0
VWFMenu_EnsureLayout_MarkNext:
	dbf	d1, VWFMenu_EnsureLayout_Mark
	cmpi.w	#88+8, d0		; the old layout held at most 96 records
	bls.s	VWFMenu_EnsureLayout_CountOK
	move.w	#88+8, d0
VWFMenu_EnsureLayout_CountOK:
	tst.w	d0
	beq.s	VWFMenu_EnsureLayout_Stamp
	subq.w	#1, d0
	lea	(VWFMenu_SaveStack+2).l, a0
	lea	(VWFMenu_SaveStack).l, a1
VWFMenu_EnsureLayout_Record:
	move.l	(a0), (a1)
	move.l	4(a0), 4(a1)
	lea	10(a0), a0
	lea	VWFMENU_SAVERECSZ(a1), a1
	dbf	d0, VWFMenu_EnsureLayout_Record
	bra.s	VWFMenu_EnsureLayout_Stamp
VWFMenu_EnsureLayout_V3:
	; VWF3's keys, refs, links and compact records are already in their final
	; locations.  Only its 128 heads at +$900 conflict with the enlarged
	; ledger, so discard that derived index and let Mark/Release rebuild it.
	lea	(VWFMenu_Bucket).l, a1
	moveq	#VWFMENU_BUCKETS/4-1, d0
VWFMenu_EnsureLayout_V3Buckets:
	clr.l	(a1)+
	dbf	d0, VWFMenu_EnsureLayout_V3Buckets
VWFMenu_EnsureLayout_Stamp:
	move.l	#$56574634, (VWFMenu_LayoutMagic).l
VWFMenu_EnsureLayout_V4:
	; The VWF5 tail is not present in an old savestate.  Leave the existing
	; first 114 keys/refs/records untouched and initialise only 114..145.
	lea	(VWFMenu_KeysX).l, a0
	moveq	#-1, d1
	move.w	#32*2-1, d0
VWFMenu_EnsureLayout_KeysX:
	move.l	d1, (a0)+
	dbf	d0, VWFMenu_EnsureLayout_KeysX
	lea	(VWFMenu_RefsX).l, a0
	lea	(VWFMenu_NextX).l, a1
	move.w	#32-1, d0
VWFMenu_EnsureLayout_TailBytes:
	clr.b	(a0)+
	clr.b	(a1)+
	dbf	d0, VWFMenu_EnsureLayout_TailBytes
	lea	(VWFMenu_SaveStackX).l, a0
	move.w	#32*2-1, d0
VWFMenu_EnsureLayout_SaveX:
	clr.l	(a0)+
	dbf	d0, VWFMenu_EnsureLayout_SaveX
	move.l	#$56574635, (VWFMenu_LayoutMagic).l
	movem.l	(sp)+, d0-d6/a0-a2
VWFMenu_EnsureLayout_Done:
	endif
	rts

; ---------------------------------------------------------------------
; Record the pool mark for the window about to be created.  Called from
; Window_Create before Windows_Opened_Num is incremented, so the depth
; read here is the one this window will occupy.
; ---------------------------------------------------------------------
VWFMenu_Mark:
	movem.l	d0/a0, -(sp)
	bsr.w	VWFMenu_EnsureLayout
	if vwf_menu_chrome=1
	clr.b	(VWFMenu_GluePhase).l	; joins never cross a window lifetime
	endif
	if vwf_menu_hash=1
	bsr.w	VWFMenu_IndexRebuild	; a window is opening: cheap, and heals a
	endif				; savestate whose index is another build's
	moveq	#0, d0
	move.b	(Windows_Opened_Num).w, d0
	cmpi.w	#VWFMENU_DEPTH, d0
	bcc.s	VWFMenu_Mark_Untracked
	add.w	d0, d0
	lea	(VWFMenu_Marks).l, a0
	move.w	(VWFMenu_PoolTop).l, (a0,d0.w)
	move.w	(VWFMenu_PoolTop).l, (VWFMenu_Mark_Cur).l
	; SaveMarkPush and SaveRegion have both succeeded for this depth.  The
	; window is now safe to reclaim from when a later strip allocation needs
	; pressure relief; Window_Draw has not run yet.
	addq.b	#1, (VWFMenu_FieldReuseDepth).l
	bra.s	VWFMenu_Mark_Done
VWFMenu_Mark_Untracked:
	; Do not infer safety above the mark/save-stack depth.  An outer tracked
	; window remains open, but this untracked child makes reclamation fail
	; closed until its matching SaveMarkPop.
	addq.b	#1, (VWFMenu_FieldReuseBlocked).l
VWFMenu_Mark_Done:
	movem.l	(sp)+, d0/a0
	rts

; ---------------------------------------------------------------------
; Roll the pool back to the destroyed window's mark.  Called from
; Window_Destroy *after* Windows_Opened_Num is decremented, so the depth
; read here is again the one that window occupied.
; ---------------------------------------------------------------------
VWFMenu_Release:
	movem.l	d0-d1/a0-a1, -(sp)
	bsr.w	VWFMenu_EnsureLayout
	if vwf_menu_chrome=1
	clr.b	(VWFMenu_GluePhase).l	; restored plane cells are a new lifetime
	endif
	if vwf_menu_hash=1
	bsr.w	VWFMenu_IndexRebuild	; a window is closing: the remap that
	endif				; follows looks every restored cell up
	moveq	#0, d0
	move.b	(Windows_Opened_Num).w, d0
	cmpi.w	#VWFMENU_DEPTH, d0
	bcc.s	VWFMenu_Release_Done
	add.w	d0, d0
	lea	(VWFMenu_Marks).l, a0
	move.w	(a0,d0.w), d1		; this window's mark
	move.w	(VWFMenu_PoolTop).l, d0
	move.w	d1, (VWFMenu_PoolTop).l
	move.w	d1, (VWFMenu_Mark_Cur).l
	if vwf_menu_strips=0
	; Do NOT clear the refcounts above the mark.  Window_Destroy sweeps the
	; plane right after the restore, which frees this window's cells and
	; keeps any slot an outer window still shows; clearing here would let
	; the reveal-time allocations between now and that sweep take a slot
	; that is still on screen.  Alloc's growth honours the counts.
	else
	; the slots this window owned go back to unreferenced
	lea	(VWFMenu_Refs).l, a0
	bra.s	VWFMenu_Release_Test
VWFMenu_Release_Clear:
	clr.b	(a0,d1.w)
	addq.w	#1, d1
VWFMenu_Release_Test:
	cmp.w	d0, d1
	blo.s	VWFMenu_Release_Clear
	endif
VWFMenu_Release_Done:
	movem.l	(sp)+, d0-d1/a0-a1
	rts

; ---------------------------------------------------------------------
; Forget residency after a mode transition rebuilds VRAM.  Battle setup
; clears VRAM outright, and map loading may replace reclaimed frame tiles;
; retaining StripOf/Keys across either transition made later menus trust
; tiles whose pixels no longer existed.
; ---------------------------------------------------------------------
VWFMenu_Reset:
	clr.w	(VWFMenu_PoolTop).l
	bsr.w	VWFMenu_BankRestore	; stock A-Z back under the field pool's $7C0 slots
	if vwf_menu_strips=0
	; Alloc searches every key, so a key must never outlive its tile: VRAM
	; is rebuilt across these transitions, so forget all of them.  Forget
	; them as all-ones, which no glyph cell composes to; all-zeroes is a
	; real key (a blank cell) and would match a slot that was never
	; uploaded.
	movem.l	d0-d1/a0-a1, -(sp)
	moveq	#-1, d1
	lea	(VWFMenu_Keys).l, a0
	move.w	#(VWFMENU_BASE_SLOTS*8)/4-1, d0
VWFMenu_Reset_Keys:
	move.l	d1, (a0)+
	dbf	d0, VWFMenu_Reset_Keys
	lea	(VWFMenu_Refs).l, a0
	move.w	#VWFMENU_BASE_SLOTS-1, d0
VWFMenu_Reset_Refs:
	clr.b	(a0)+
	dbf	d0, VWFMenu_Reset_Refs
	lea	(VWFMenu_KeysX).l, a0
	move.w	#32*2-1, d0
VWFMenu_Reset_KeysX:
	move.l	d1, (a0)+
	dbf	d0, VWFMenu_Reset_KeysX
	lea	(VWFMenu_RefsX).l, a0
	lea	(VWFMenu_NextX).l, a1
	move.w	#32-1, d0
VWFMenu_Reset_TailBytes:
	clr.b	(a0)+
	clr.b	(a1)+
	dbf	d0, VWFMenu_Reset_TailBytes
	lea	(VWFMenu_SaveStackX).l, a0
	move.w	#32*2-1, d0
VWFMenu_Reset_SaveX:
	clr.l	(a0)+
	dbf	d0, VWFMenu_Reset_SaveX
	if vwf_menu_hash=1
	lea	(VWFMenu_Bucket).l, a0	; no key is linked: every chain empty
	move.w	#VWFMENU_BUCKETS/4-1, d0
VWFMenu_Reset_Buckets:
	clr.l	(a0)+
	dbf	d0, VWFMenu_Reset_Buckets
	endif
	movem.l	(sp)+, d0-d1/a0-a1
	endif
	clr.w	(VWFMenu_SaveTop).l
	if vwf_menu_strips=0
	move.l	#$56574635, (VWFMenu_LayoutMagic).l ; fresh state already uses current layout
	endif
	clr.w	(VWFMenu_BattleBase).l
	clr.w	(VWFMenu_BattleActionMark).l
	clr.w	(VWFMenu_BattleEnemyMark).l
	clr.w	(VWFMenu_BattleResultMark).l
	clr.w	(VWFMenu_BattleEffectMark).l
	clr.w	(VWFMenu_BattleMacroMark).l
	clr.w	(VWFMenu_BattleOptionsMark).l
	clr.b	(VWFMenu_DeferN).l
	clr.b	(VWFMenu_BattleResultActive).l
	clr.w	(VWFMenu_Mark_Cur).l
	clr.b	(VWFMenu_WrapFlag).l
	clr.b	(VWFMenu_StripReuseOK).l
	clr.b	(VWFMenu_ForceCompose).l
	clr.b	(VWFMenu_NoPad).l
	clr.b	(VWFMenu_FieldReuseDepth).l
	clr.b	(VWFMenu_FieldReuseBlocked).l
	clr.b	(VWFMenu_ReclaimInhibit).l
	clr.b	(VWFMenu_SkipNames).l
	clr.l	(VWFMenu_PartyEntry).l
	if vwf_menu_chrome=1
	clr.b	(VWFMenu_GluePhase).l
	clr.b	(VWFMenu_GlueCandidate).l
	clr.b	(VWFMenu_GlueActive).l
	clr.b	(VWFMenu_GlueDeref).l
	clr.b	(VWFMenu_GlueFailed).l
	clr.b	(VWFMenu_GlueOwned).l
	endif
	clr.w	(VWFMenu_TakeGen).l
	movem.l	d0/a0, -(sp)
	lea	(VWFMenu_PartyCache).l, a0
	moveq	#VWFMENU_PARTY_N-1, d0
VWFMenu_Reset_Party:
	move.w	#$FFFF, (a0)		; no generation matches
	lea	16(a0), a0
	dbf	d0, VWFMenu_Reset_Party
	movem.l	(sp)+, d0/a0
	rts

; Copy a party member's name into a RAM message, from the translated table.
;   a0 = the character's Character_Stats record
;   a1 = destination; advanced past the name, no terminator written
; The record's own name field is six bytes with the terminator, which a
; six-letter name overruns; CharNameData is $FF-terminated and complete.
VWFMenu_CopyCharName:
	movem.l	d0/a0, -(sp)
	move.l	a0, d0
	subi.l	#Character_Stats, d0
	lsr.w	#7, d0
	lea	(CharNameData).l, a0
	jsr	(GetOffsetByID).l
VWFMenu_CopyCharName_Loop:
	move.b	(a0)+, d0
	cmpi.b	#$FE, d0
	bcc.s	VWFMenu_CopyCharName_Done
	move.b	d0, (a1)+
	bra.s	VWFMenu_CopyCharName_Loop
VWFMenu_CopyCharName_Done:
	movem.l	(sp)+, d0/a0
	rts

; Render a field message assembled in RAM with the proportional menu face.
; The flag remains set across control-code-separated runs and is cleared only
; after LoadWindowTiles returns, so compound item notices stay consistent.
VWFField_LoadWindowTiles:
	move.b	#1, (VWFMenu_ForceCompose).l
	jsr	(LoadWindowTiles).l
	clr.b	(VWFMenu_ForceCompose).l
	rts

; LoadWindowTiles enters here after fetching one ordinary character.  Its
; immediate mode still composes an entire VWF run; its slow mode writes one
; fixed-width tile and returns so the stock per-character delay remains intact.
VWFMenu_DrawWindowRun:
	tst.w	d4
	bne.s	.immediate
	; Slow mode types one character per Message_Speed tick, which the composer
	; cannot do: it consumes a whole run at once.  Where the caller has asked
	; for the proportional face anyway - the item description and the item
	; notices - compose the run and let LoadWindowTiles pay its delay once
	; afterwards, so a line appears whole and then pauses.  Everything else
	; keeps the untouched fixed-width path below.
	;
	; The cell loop paid the delay per cell at first, and that crashed Item >
	; LOOK.  A delay means DMAPlane_A_VInt, which waits for the VInt, and the
	; window-open animation runs on the far side of it: Window_Create records
	; a pool mark and Window_Destroy calls VWFMenu_Release, which rolls the
	; pool back.  Yielding from inside a run therefore let a window free the
	; very tiles the run had just allocated - an empty description and a
	; status panel drawing other strings' tiles.  The composer has to be
	; atomic with respect to the window stack, so it must not yield at all.
	if vwf_menu_chrome=1
	bra.s	.immediate		; no alphabet remains on the fixed slow path
	else
	tst.b	(VWFMenu_ForceCompose).l
	bne.s	.immediate
	endif
	tst.w	d1
	beq.s	.fixed		; space uses the blank at $680
	cmpi.w	#65, d1
	bcc.s	.fixed		; codes 65+ live at $680+code
	addi.w	#$13F, d1	; codes 1-64 use the copy at $7C0
.fixed:
	add.w	d2, d1
	move.w	d1, (a1)+
	rts
.immediate:
	subq.l	#1, a0		; the composer consumes the whole run
	move.b	#1, (VWFMenu_WrapFlag).l
	jmp	(VWFMenu_DrawString).l

	even
; Stock artwork for the labels that stay fixed-width, packed into
; VWFMENU_FIXEDN slots at VWFMENU_FIXED0.  Keeping the shipped glyphs
; means chrome renders exactly as it always did.
VWFMenu_FixedArt:	binclude	"vwf/menufixed.bin"
	even
; The stock A-Z of the $7C0 font copy.  The field pool owns $7C0-$7D9
; (slots 88..113) and the bank is loaded once, at the title screen, so a
; battle - which never allocates past 88 but does read letters straight
; from that bank (Battle_OpenMacroLetters' A-H, the vehicle HUD label at
; loc_75BC) - would otherwise show whatever the field composed there last.
VWFMenu_AlphaArt:	binclude	"vwf/menualpha.bin"
	even

; Put the 26 stock letters back at $7C0.  Called from VWFMenu_Reset, which
; GameMode_LoadBattle runs before its VRAM fills (they clear $0000 and $2000
; only) and GameMode_LoadFieldMap runs first thing; in the field the pool
; re-composes over them as it needs to, so restoring there too is harmless.
VWFMenu_BankRestore:
	movem.l	d0-d1/a0/a6, -(sp)
	lea	(VDP_Control_Port).l, a6
	move.w	#$8F02, (a6)
	move.w	#$7C0, d0
	jsr	(LoadVRAMAddressFromTileNumber).l
	lea	(VDP_Data_Port).l, a6
	lea	(VWFMenu_AlphaArt).l, a0
	move.w	#26*32/4-1, d0
VWFMenu_BankRestore_Copy:
	move.l	(a0)+, (a6)
	dbf	d0, VWFMenu_BankRestore_Copy
	movem.l	(sp)+, d0-d1/a0/a6
	rts

	if vwf_menu_chrome=1
; Chrome that composes: (first address, address past the end, kind).
; Kind 0 composes plainly; kind 1 is the PAD rule (see VWFMenu_DrawString
; _Pad).  Bounds are symbols, so the table follows the text when it moves.
; tools/test_paths.py walks every entry.
VWFMenu_ChromeTable:
	dc.l	WinTiles_StartString, loc_2A9F04
	dc.w	0				; title menu: START / CONTINUE / ERASE DATA
	dc.l	loc_2A9F04, loc_2A9F1A
	dc.w	0				; title save-slot summaries
	dc.l	loc_2A9F1A, IppoString
	dc.w	0				; erase prompt, sound test legend
	dc.l	IppoString, WinTiles_MainOptions
	dc.w	0				; sound-test IPPO / GAKI CHAN tag
	dc.l	WinTiles_MainOptions, WinTiles_Meseta
	dc.w	0				; the field menu, both tables
	dc.l	WinTiles_Meseta, DyingString
	dc.w	1				; Meseta; Level on the party bar
	dc.l	DyingString, loc_2AA02E
	dc.w	0				; DYING / PARA / POIS party-status labels
	dc.l	loc_2AA02E, loc_2AA034
	dc.w	0				; WHO?
	dc.l	loc_2AA034, WinTiles_2HandString
	dc.w	1				; equip comparison labels
	dc.l	VWFMenu_2HandedStr, VWFMenu_2HandedStr_End
	dc.w	0				; proportional /2-Handed equipment label
	dc.l	loc_2AA084, loc_2AA0B8
	dc.w	0				; equip notices, EQUIP caption
	dc.l	WinTiles_TalkString, loc_2AA0C6
	dc.w	0				; TALK / MUMBLE caption
	dc.l	WinTiles_ItemString, loc_2AA0E6
	dc.w	0				; ITEM caption, USE / LOOK / DISCARD
	dc.l	loc_2AA0E6, loc_2AA0FC
	dc.w	0				; "You have no items!"
	dc.l	loc_2AA126, loc_2AA132
	dc.w	0				; YES / NO
	dc.l	WinTiles_MACROString, loc_2AA2E4
	dc.w	0				; MACRO caption
	dc.l	loc_2AA32A, loc_2AA3B4
	dc.w	0				; macro slot digits, alone / perished notices
	dc.l	loc_2AA3B4, loc_2AA3C6
	dc.w	0				; STATUS / ORDER
	dc.l	loc_2AA3C6, loc_2AA422
	dc.w	1				; Level / Age / HP / TP, the attributes
	dc.l	loc_2AA422, loc_2AA42C
	dc.w	0				; Exp / Next
	dc.l	loc_2AA42E, loc_2AA4B6
	dc.w	0				; WHOSE?, ORDER, COMBAT / FIELD, only-one-of-you, SYS menu, SYS
	dc.l	loc_2AA4B6, loc_2AA4C4
	dc.w	1				; save slots "1  o" / "2  o"
	dc.l	loc_2AA4C4, loc_2AA53E
	dc.w	0				; LV, save prompts, YES / NO, cannot save
	dc.l	loc_2AA53E, loc_2AA55E
	dc.w	1				; the speed selector
	dc.l	loc_2AA55E, loc_2AA58A
	dc.w	0				; speed prompts
	dc.l	loc_2AA58A, loc_2AA618
	dc.w	1				; button assignments
	dc.l	loc_2AA618, loc_2AA65C
	dc.w	0				; BUTTONS, button prompts
	dc.l	loc_2AA65C, loc_2AA70A
	dc.w	0				; debug check window / map overlay
	dc.l	loc_2AA81E, loc_2AA892
	dc.w	0				; DISCARD / USE, RETURN / USE, WHO?, TECH, TO?
	dc.l	loc_2AA892, loc_2AAA44
	dc.w	0				; TO?, HP fully recovered, WHO?, SKILL, TO?
	dc.l	loc_2AE1AE, InventoryDescriptions2
	dc.w	0				; shop: buy / sell, equip, Are you sure?
	dc.l	InventoryDescriptions2, loc_2AFA28
	dc.w	0				; LOOK item descriptions
	dc.l	loc_27E5B0, loc_27E5D2
	dc.w	0				; Victory!, Each got, EXP, meseta!
	dc.l	loc_27E7E6, loc_27E7EE
	dc.w	0				; battle item: Use / Discard
	dc.l	loc_27E7EE, loc_27E862
	dc.w	1				; level up: name's Level, <attribute> increased by <n>!
	dc.l	loc_27E862, BattleLevelUpText_End
	dc.w	0				; Technique / Skill ... has been mastered!
	dc.l	VWFMenu_AllAlliesRecoveredStr, VWFMenu_AllAlliesRecoveredStr_End
	dc.w	0				; field/battle Miracle result
	dc.l	VWFMenu_ParalyzedStr, VWFMenu_PoisonedStr_End
	dc.w	0				; PARALYZED / POISONED party-status labels
	dc.l	0, 0
	dc.w	0

; The stock field-message text omits the possessive ("Everybody HP").  Keep
; the corrected chrome string in the extension so the fixed build and every
; address in the original ROM stay put.
VWFMenu_AllAlliesRecoveredStr:
	dc.b	$FC
	; Extension source is outside ps4.asm's game-character mapping, so keep
	; these bytes explicit (E v e r y b o d y ' s, space; HP graphic; tail).
	dc.b	$05, $4E, $3D, $4A, $51, $3A, $47, $3C, $51, $54, $4B, $00
	dc.b	$78, $79
	dc.b	$00, $4A, $3D, $3B, $47, $4E, $3D, $4A, $3D, $3C, $32
	dc.b	$FE
VWFMenu_AllAlliesRecoveredStr_End:
	even

VWFMenu_2HandedStr:
	; /, 2, -, H a n d e d in the normal window charset.
	dc.b	$77,$1D,$31,$08,$39,$46,$3C,$3D,$3C,$FE
VWFMenu_2HandedStr_End:
	even

; Status professions are copied to RAM before the forced VWF renderer sees
; them.  Keep the expanded Berserker spelling here in extension ROM so the
; original fixed-width table and every address below it remain unchanged.
VWFMenu_ProfessionNameData:
	dc.b	$08,$4D,$46,$4C,$3D,$4A,$FF                         ; Hunter
	dc.b	$13,$3B,$40,$47,$44,$39,$4A,$FF                     ; Scholar
	dc.b	$17,$41,$52,$39,$4A,$3C,$FF                         ; Wizard
	dc.b	$02,$3D,$4A,$4B,$3D,$4A,$43,$3D,$4A,$FF             ; Berserker
	dc.b	$0E,$3D,$4F,$45,$39,$46,$FF                         ; Newman (PSO/PSU spelling)
	dc.b	$01,$46,$3C,$4A,$47,$41,$3C,$FF                     ; Android
	dc.b	$10,$4A,$41,$3D,$4B,$4C,$FF                         ; Priest
	dc.b	$05,$4B,$48,$3D,$4A,$FF                             ; Esper
VWFMenu_ProfessionNameData_End:
	even
	endif
; charset code -> fixed slot, $FF when the code is not drawn fixed-width
VWFMenu_FixedMap:	binclude	"vwf/menufixmap.bin"
	even
; the proportional face, and its advances, for everything else
VWFMenu_Font:	binclude	"vwf/menufont.bin"
	even
VWFMenu_Widths:	binclude	"vwf/menuwidth.bin"
	even
; Full translated names for messages assembled in RAM.  Menu lists retain
; their independent prerendered-strip source and ordinal mapping.
VWFField_ItemNames:	binclude	"vwf/fielditemnames.bin"
	even
VWFField_TechNames:	binclude	"vwf/fieldtechnames.bin"
	even
VWFField_SkillNames:	binclude	"vwf/fieldskillnames.bin"
	even
VWFDialogue_ItemNames:	binclude	"vwf/dialogueitemnames.bin"
	even
VWFMenu_SlotTile:	binclude	"vwf/poolslot.bin"
	even
VWFMenu_TileSlot:	binclude	"vwf/pooltile.bin"
	even

; ---------------------------------------------------------------------
; Draw one proportional string into the window plane buffer.
;   a0 = text, charset codes, ending at the first code >= $F0
;   a1 = nametable write pointer inside the plane buffer
;   d2 = tile attribute base, as LoadWindowTiles holds it
; a0 is left on the terminator; a1 is advanced past the cells written.
;
; Composition is 1bpp into VWFMenu_Scratch, then one cell at a time:
; allocate by content, and upload only if the slot is newly taken.  The
; tile goes straight to VRAM through the data port rather than through
; the DMA queue, so no staging buffer can be overwritten before a queued
; transfer reads it - the aliasing that broke the Japanese attempt cannot
; arise here.
; ---------------------------------------------------------------------
; ---------------------------------------------------------------------
; Fold the write pointer the way LoadWindowTiles' own loop does.
;
; A plane row is $80 bytes - 64 cells - and wraps onto ITSELF: passing
; column 63 returns to column 0 of the same row, not the start of the next
; one.  The stock loop enforces that after every character.  DrawString
; writes a whole run at once, so it has to enforce it after every cell or
; the tail of a string lands one row down, which is exactly the split seen
; at a fixed screen X across every menu.
;
; Only for LoadWindowTiles: loc_27DB9C's own loop has no such fold, and
; adding one there would break geometry that is currently correct.
; ---------------------------------------------------------------------
VWFMenu_RowWrap:
	move.l	d0, -(sp)
	tst.b	(VWFMenu_WrapFlag).l
	beq.s	VWFMenu_RowWrap_Done
	move.w	a1, d0
	andi.w	#$7F, d0
	bne.s	VWFMenu_RowWrap_Done
	lea	-$80(a1), a1
VWFMenu_RowWrap_Done:
	move.l	(sp)+, d0
	rts

VWFMenu_DrawString:
	; a0 and a1 are results and must NOT be restored: a0 is left on the
	; terminator, a1 past the cells written.  a6 is saved because it is
	; the VDP port and belongs to a caller further out - LoadWindowTiles
	; does not save it either.
	movem.l	d0-d7/a2-a6, -(sp)
	if vwf_menu_chrome=1
	clr.b	(VWFMenu_PadMode).l	; set again only by a PAD-range match
	clr.b	(VWFMenu_PadRun).l
	clr.b	(VWFMenu_GlueCandidate).l
	clr.b	(VWFMenu_GlueActive).l
	clr.b	(VWFMenu_GlueDeref).l
	clr.b	(VWFMenu_GlueFailed).l
	endif

	moveq	#0, d0
	move.b	(a0), d0
	cmpi.b	#$F0, d0
	bcc.w	VWFMenu_DrawString_Exit	; control code: the caller handles it
	cmpi.b	#$80, d0
	bcc.w	VWFMenu_DrawString_Graphic
	tst.b	(VWFMenu_ForceCompose).l
	bne.w	VWFMenu_DrawString_Compose

	if vwf_menu_fixedlabels=1
	; A short all-caps run is a label, not content.  Charset codes 1-64
	; have a second, permanent copy of the font at $7C0 - the one the
	; numeric fields already draw from, verified byte-identical against
	; Font.bin in the stock ROM and in every VWF savestate - so drawing
	; these fixed costs nothing in the $680 bank and hands 16 tiles back
	; to the pool.  One cell per character is stock's own layout, so the
	; columns cannot shift.
	;
	; The test is on length, not on case.  "All caps" alone would also
	; select HUNT-KNIFE and LTHR-HELM and re-truncate the very names this
	; is for; at three non-space characters it selects HP, TP, EX, NX, LV,
	; MST and AGE and can select nothing else.  Lowercase is not resident
	; past code 64 (a-h only), so mixed-case labels never qualify.
	; The pool exists for the three name tables that overflow their cell
	; budgets - item, technique and skill names - and they are contiguous
	; in ROM, so one range test separates content from chrome.  Names are
	; drawn straight out of the table (loc_193C does `lea
	; (TechniqueNames).l, a0` and walks forward past $FE terminators), never
	; copied to RAM first, so a0 really is the table address at draw time.
	; Everything else - panel labels, base-menu options, attributes, class
	; and location names - is chrome and goes back to fixed width.
	; Party names are the first field of each $80-byte Character_Stats
	; record.  Resolve them through the translated ROM table even when an old
	; save state still contains a US name, then compose it with the regular
	; menu VWF.  This uses only the cells carrying ink (2-4 for these names),
	; unlike a fixed four-cell strip.
	cmpa.l	#Character_Stats, a0
	bcs.w	VWFMenu_DrawString_NotParty
	cmpa.l	#Character_Stats+($80*11), a0
	bcc.w	VWFMenu_DrawString_NotParty
	move.l	a0, d0
	subi.l	#Character_Stats, d0
	move.w	d0, d1
	andi.w	#$7F, d1
	if vwf_menu_chrome=1
	bne.w	VWFMenu_DrawString_NotParty
	else
	bne.s	VWFMenu_DrawString_NotParty
	endif
	lsr.w	#7, d0
	move.w	d0, d3			; record index; GetOffsetByID counts d0 down
	lea	(CharNameData).l, a0
	jsr	(GetOffsetByID).l
	cmpi.w	#$14, (Game_Mode_Index).w
	bne.w	VWFMenu_DrawString_Compose	; field menus: no cache, sweeps move slots
	; Battle: the HUD asks for these five names every frame.  Their slots
	; sit below BattleBase and, with the count saturating, are never
	; reclaimed, so the cells composed last time are still right unless
	; some Take has happened since (TakeGen moved).  Replay them.
	lsl.w	#4, d3			; record index * 16
	lea	(VWFMenu_PartyCache).l, a2
	adda.w	d3, a2
	move.l	a2, (VWFMenu_PartyEntry).l	; the compose path fills this entry
	move.w	(VWFMenu_TakeGen).l, d0
	cmp.w	(a2), d0
	bne.w	VWFMenu_DrawString_Compose	; stale or never composed: compose and record
	moveq	#0, d4
	move.b	2(a2), d4		; cells; zero is "never composed" (a state
	beq.w	VWFMenu_DrawString_Compose	; saved before this cache existed)
	addq.l	#4, a2
	subq.w	#1, d4
VWFMenu_DrawString_PartyCell:
	move.w	(a2)+, d1
	add.w	d2, d1			; tile offset + $680 + attribute, as Resident writes
	move.w	d1, (a1)+
	bsr.w	VWFMenu_RowWrap
	dbf	d4, VWFMenu_DrawString_PartyCell
VWFMenu_DrawString_PartyEnd:
	; leave a0 where the compose loop would: on the first code it stops at
	lea	(VWFMenu_Widths).l, a2
	if vwf_menu_chrome=1
	moveq	#0, d3			; replay still has to report the name's pixel phase
	endif
VWFMenu_DrawString_PartySkip:
	moveq	#0, d0
	move.b	(a0), d0
	cmpi.b	#$80, d0
	bcc.s	VWFMenu_DrawString_PartyDone
	if vwf_menu_chrome=1
	moveq	#0, d1
	move.b	(a2,d0.w), d1
	tst.b	d1
	beq.s	VWFMenu_DrawString_PartyDone
	add.w	d1, d3
	else
	tst.b	(a2,d0.w)
	beq.s	VWFMenu_DrawString_PartyDone
	endif
	addq.l	#1, a0
	bra.s	VWFMenu_DrawString_PartySkip
VWFMenu_DrawString_PartyDone:
	if vwf_menu_chrome=1
	moveq	#1, d5			; the replay wrote at least one cached cell
	bsr.w	VWFMenu_GlueRememberCached
	endif
	clr.l	(VWFMenu_PartyEntry).l
	bra.w	VWFMenu_DrawString_Exit
VWFMenu_DrawString_NotParty:
	; An enemy's battle record, for the $F2-prefixed status messages ("Fly
	; Screamer is poisoned!").  The record holds a blind 14-byte copy of the
	; name with no terminator for the long ones; its id at $68 reaches the
	; translated EnemyNames entry, which composes.
	cmpa.l	#Enemy_Stats, a0
	bcs.s	VWFMenu_DrawString_NotEnemyRec
	cmpa.l	#Enemy_Stats+($80*4), a0
	bcc.s	VWFMenu_DrawString_NotEnemyRec
	move.l	a0, d0
	andi.w	#$7F, d0
	bne.s	VWFMenu_DrawString_NotEnemyRec
	move.w	$68(a0), d0
	lea	(EnemyNames).l, a0
	jsr	(Battle_GetOffsetByID_FE_Delim).l
	bra.w	VWFMenu_DrawString_Compose
VWFMenu_DrawString_NotEnemyRec:
	cmpa.l	#VWFMENU_NAMES_LO, a0
	bcs.s	VWFMenu_DrawString_NotName
	cmpa.l	#VWFMENU_NAMES_HI, a0
	bcc.s	VWFMenu_DrawString_NotName
	tst.b	(VWFMenu_SkipNames).l
	bne.s	VWFMenu_DrawString_SkipName
	if vwf_menu_strips=1
	bra.w	VWFMenu_DrawStrip	; a name: it has a prerendered strip
	else
	bra.w	VWFMenu_DrawName	; a name: compose its translation
	endif
VWFMenu_DrawString_SkipName:
	; A page nobody will see before it is rebuilt: stock-length blanks, a0
	; on the terminator, nothing allocated.
	cmpi.b	#$FE, (a0)
	bcc.w	VWFMenu_DrawString_Exit
	addq.l	#1, a0
	move.w	d2, (a1)+
	bsr.w	VWFMenu_RowWrap
	bra.s	VWFMenu_DrawString_SkipName
VWFMenu_DrawString_NotName:
	cmpa.l	#VWFMENU_ENEMY_LO, a0
	bcs.s	VWFMenu_DrawString_NotEnemy
	cmpa.l	#VWFMENU_ENEMY_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; an enemy or enemy-skill name
VWFMenu_DrawString_NotEnemy:
	cmpa.l	#VWFMENU_COMBO_LO, a0
	bcs.s	VWFMenu_DrawString_NotCombo
	cmpa.l	#VWFMENU_COMBO_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; a combination or vehicle attack
VWFMenu_DrawString_NotCombo:
	cmpa.l	#VWFMENU_GUILD_LO, a0
	bcs.s	VWFMenu_DrawString_NotGuild
	cmpa.l	#VWFMENU_GUILD_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; a Hunters Guild job title
VWFMenu_DrawString_NotGuild:
	cmpa.l	#VWFMENU_SPACE_LO, a0
	bcs.s	VWFMenu_DrawString_NotSpace	; ranges are not ordered: test each on its own
	cmpa.l	#VWFMENU_SPACE_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; the spaceship's destination prompt and list
VWFMenu_DrawString_NotSpace:
	if vwf_menu_chrome=1
	; Chrome ranges live in a table (VWFMenu_ChromeTable, below): pairs of
	; bounds and a kind, 0 to compose plainly, 1 for the PAD rule.  A
	; string outside every entry is what it always was: fixed width.
	lea	(VWFMenu_ChromeTable).l, a2
VWFMenu_DrawString_ChromeNext:
	move.l	(a2)+, d0
	beq.s	VWFMenu_DrawString_NotChrome	; end of table: on to the ordered ranges
	cmpa.l	d0, a0
	bcs.s	VWFMenu_DrawString_ChromeSkip
	cmpa.l	(a2), a0
	bcs.s	VWFMenu_DrawString_ChromeHit
VWFMenu_DrawString_ChromeSkip:
	addq.l	#6, a2
	bra.s	VWFMenu_DrawString_ChromeNext
VWFMenu_DrawString_ChromeHit:
	tst.w	4(a2)
	beq.w	VWFMenu_DrawString_Compose
	bra.w	VWFMenu_DrawString_Pad
VWFMenu_DrawString_NotChrome:
	endif
	cmpa.l	#VWFMENU_EFFECT_LO, a0
	bcs.w	VWFMenu_DrawString_LabelTry
	cmpa.l	#VWFMENU_EFFECT_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; a battle status-effect message
	; The flow range lies between EFFECT_HI and RESULT_LO, so it is
	; tested here, in address order.
	cmpa.l	#VWFMENU_FLOW_LO, a0
	bcs.w	VWFMenu_DrawString_LabelTry
	cmpa.l	#VWFMENU_FLOW_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; battle menus and flow messages
	cmpa.l	#VWFMENU_RESULT_LO, a0
	bcs.s	VWFMenu_DrawString_NotResult
	cmpa.l	#VWFMENU_RESULT_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; a battle result tail after an item name
VWFMenu_DrawString_NotResult:
	cmpa.l	#VWFMENU_RESULT2_LO, a0
	bcs.w	VWFMenu_DrawString_LabelTry
	cmpa.l	#VWFMENU_RESULT2_HI, a0
	bcs.w	VWFMenu_DrawString_Compose	; likewise
	bra.w	VWFMenu_DrawString_LabelTry
VWFMenu_DrawString_Pad:
	; A label that positions itself with spaces: compose it, with the
	; pad rule on.  A colon at the head of the run is the stock tile in
	; one cell - the composer flushes a run when it meets one, and the
	; caller re-enters here on it.  The tile is the colon of the font
	; copy at $7C0, the one the label path and the numeric fields use;
	; $681 (VWFMENU_FIXED0) is a pool slot now, see tools/menupool.py.
	move.b	#1, (VWFMenu_PadMode).l
	cmpi.b	#$34, (a0)
	bne.w	VWFMenu_DrawString_Compose
	addq.l	#1, a0
	move.w	d2, d0
	addi.w	#$7C0+$34-1-$680, d0	; d2 carries $680 plus the attribute
	move.w	d0, (a1)+
	bsr.w	VWFMenu_RowWrap
	bra.w	VWFMenu_DrawString_Exit
VWFMenu_DrawString_LabelTry:
	; An unclassified run assembled in RAM used to fall back to fixed width.
	; That missed messages such as the save confirmation and money-chest
	; notice: their English tail is copied out of a classified ROM range before
	; LoadWindowTiles sees it.  Detect alphabetic wincharset codes in the run
	; itself and compose the whole run from its beginning.  Besides covering
	; every dynamic sentence, this makes A-Z/a-z unreachable on the fixed path,
	; so their stock tiles can safely join the pool.  Pure blank/numeric/graphic
	; runs still take the fixed path below; in particular loc_2AA43C's clearing
	; spaces must continue to emit physical blank cells.
	movea.l	a0, a2
VWFMenu_DrawString_LabelScan:
	moveq	#0, d0
	move.b	(a2)+, d0
	cmpi.b	#$80, d0
	bcc.s	VWFMenu_DrawString_Label
	cmpi.b	#1, d0
	bcs.s	VWFMenu_DrawString_LabelScan	; space
	cmpi.b	#26, d0
	bls.w	VWFMenu_DrawString_Compose	; A-Z
	cmpi.b	#57, d0
	bcs.s	VWFMenu_DrawString_LabelScan
	cmpi.b	#82, d0
	bls.w	VWFMenu_DrawString_Compose	; a-z
	bra.s	VWFMenu_DrawString_LabelScan

	; Fixed punctuation/numbers use two sources because the pool sits
	; on top of the $680 bank:
	;   codes 1-64    the permanent second font copy at $7C0
	;   codes 65-127  $680+code, which is why tools/menupool.py holds those
	;                 tiles out of the pool
	; Codes $80 and up end the run and the caller's graphic path takes them
	; to $740+code, reaching the same $7C0 bank from the far side.
	;
VWFMenu_DrawString_Label:
	moveq	#0, d1
	move.b	(a0), d1
	bmi.s	VWFMenu_DrawString_LabelDone
	addq.l	#1, a0
	tst.w	d1
	beq.s	VWFMenu_DrawString_LabelCell	; space -> the blank at $680
	cmpi.w	#65, d1
	bcc.s	VWFMenu_DrawString_LabelCell	; 65-127 already sit at $680+code
	addi.w	#$13F, d1		; $7C0 + code - 1, less the $680 in d2
VWFMenu_DrawString_LabelCell:
	add.w	d2, d1			; d2 carries $680 plus the attribute
	move.w	d1, (a1)+
	bsr.w	VWFMenu_RowWrap
	bra.s	VWFMenu_DrawString_Label
VWFMenu_DrawString_LabelDone:
	bra.w	VWFMenu_DrawString_Exit
	endif

VWFMenu_DrawString_Compose:
	if vwf_menu_strips=0
	clr.l	(VWFMenu_NameSrc).l	; not a name: nothing to pad or restore
VWFMenu_DrawString_ComposeName:
	endif
	; Codes $58-$7F are window-bank graphics, not glyphs: menuwidth gives
	; them width 0 and menufont gives them no art, so composing one deletes
	; it.  The healing notices are built out of them - "$78$79 has
	; increased!", where the pair is the HP/TP label the status window also
	; draws - and they would have read " has increased!".  Width 0 is the
	; test rather than a code range because it is the same table the
	; composer measures with, so the two can never disagree; the space at
	; code 0 has a real 8px advance and is unaffected.
	moveq	#0, d0
	move.b	(a0), d0
	lea	(VWFMenu_Widths).l, a2
	tst.b	(a2,d0.w)
	beq.w	VWFMenu_DrawString_Fixed
	lea	(VWFMenu_Scratch).l, a3
	moveq	#(8*32)/4-1, d0
VWFMenu_DrawString_Clear:
	clr.l	(a3)+
	dbf	d0, VWFMenu_DrawString_Clear

	moveq	#0, d3			; pixel cursor
	cmpa.l	#loc_27E6E8+1, a0	; COMMAND follows its cursor with no space
	bne.s	VWFMenu_DrawString_NoCommandLead
	moveq	#2, d3			; centre its 38 pixels in the five-cell field
VWFMenu_DrawString_NoCommandLead:
	if vwf_menu_chrome=1
	bsr.w	VWFMenu_GlueBegin	; may seed cell 0 and return its used pixels in d3
	endif
VWFMenu_DrawString_Next:
	moveq	#0, d0
	move.b	(a0), d0
	cmpi.b	#$80, d0
	bcc.w	VWFMenu_DrawString_Composed
	if vwf_menu_chrome=1
	tst.b	(VWFMenu_PadMode).l
	beq.s	VWFMenu_DrawString_NextWidth
	cmpi.b	#$34, d0
	beq.w	VWFMenu_DrawString_Composed	; the colon is a fixed cell: flush here
	tst.w	d0
	bne.s	VWFMenu_DrawString_NextWidth
	; A space pads - advances to the next cell boundary - when it starts
	; the run, sits in a run of spaces, or is followed by something that
	; is not a glyph (a colon, a graphic, a control).  A lone space between
	; two glyphs is an ordinary word space, so "Strength increased by"
	; composes as prose and only the spaces that hold the value pad.
	tst.w	d3
	beq.s	VWFMenu_DrawString_PadSpace
	move.b	1(a0), d0
	beq.s	VWFMenu_DrawString_PadSpace	; another space follows
	cmpi.b	#$34, d0
	beq.s	VWFMenu_DrawString_PadSpace	; the colon follows
	tst.b	d0
	bmi.s	VWFMenu_DrawString_PadSpace	; a graphic or a control follows
	lea	(VWFMenu_Widths).l, a2
	tst.b	(a2,d0.w)
	beq.s	VWFMenu_DrawString_PadSpace	; a width-0 code follows
	tst.b	(VWFMenu_PadRun).l
	bne.s	VWFMenu_DrawString_PadSpace	; inside a run of spaces
	moveq	#0, d0			; a word space: fall through to the width table
	bra.s	VWFMenu_DrawString_NextWidth
VWFMenu_DrawString_PadSpace:
	move.b	#1, (VWFMenu_PadRun).l
	moveq	#8, d4			; a pad space: on to the next cell boundary
	move.w	d3, d0
	andi.w	#7, d0
	sub.w	d0, d4
	addq.l	#1, a0
	add.w	d4, d3
	cmpi.w	#31*8, d3
	bcs.s	VWFMenu_DrawString_Next
	bra.w	VWFMenu_DrawString_Composed
VWFMenu_DrawString_NextWidth:
	clr.b	(VWFMenu_PadRun).l
	endif
	lea	(VWFMenu_Widths).l, a2
	moveq	#0, d4
	move.b	(a2,d0.w), d4
	beq.s	VWFMenu_DrawString_Composed	; a graphic: flush and let it through
	addq.l	#1, a0

	lea	(VWFMenu_Font).l, a2
	lsl.w	#3, d0
	adda.w	d0, a2

	move.w	d3, d5
	lsr.w	#3, d5
	move.w	d3, d6
	andi.w	#7, d6
	lea	(VWFMenu_Scratch).l, a3
	adda.w	d5, a3
	moveq	#8-1, d7
VWFMenu_DrawString_Row:
	moveq	#0, d0
	move.b	(a2)+, d0
	beq.s	VWFMenu_DrawString_RowDone
	lsl.w	#8, d0
	lsr.w	d6, d0
	move.w	d0, d1
	lsr.w	#8, d1
	or.b	d1, (a3)
	or.b	d0, 1(a3)
VWFMenu_DrawString_RowDone:
	lea	32(a3), a3
	dbf	d7, VWFMenu_DrawString_Row

	add.w	d4, d3
	cmpi.w	#31*8, d3
	bcs.w	VWFMenu_DrawString_Next

VWFMenu_DrawString_Composed:
	move.l	a0, -(sp)		; keep the terminator; a0 is needed for keys
	move.w	d3, d4
	addq.w	#7, d4
	lsr.w	#3, d4
	if vwf_menu_strips=0
	bne.s	VWFMenu_DrawString_HasCells
	moveq	#0, d5			; nothing written: the pad below counts from d5
	bra.w	VWFMenu_DrawString_Done
VWFMenu_DrawString_HasCells:
	else
	beq.w	VWFMenu_DrawString_Done
	endif

	; Sweep only when this actual run would cross the cap and the current
	; window has a complete SaveRegion/Mark lifetime.  Game mode by itself is
	; not proof of safety: nested windows beyond the tracked stack and the
	; no-sweep animation remap both carry raw, not-yet-repointed cells.
	move.w	(VWFMenu_PoolTop).l, d0
	add.w	d4, d0
	move.w	#VWFMENU_ACTIVE_SLOTS, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	beq.s	VWFMenu_DrawString_CapReady
	move.w	#VWFMENU_BATTLE_SLOTS, d1
VWFMenu_DrawString_CapReady:
	cmp.w	d1, d0
	bls.s	VWFMenu_DrawString_NoSweep	; fits above the frontier as it is
	; Past the frontier.  A sweep does not move PoolTop, it only clears
	; counts, so once the pool had touched the cap this swept on EVERY
	; string: eight full-plane walks per Item page flip, a frame each.
	; Sweep only when the zero-count slots the last sweep (and Release)
	; left - below the frontier, which the free scan takes, or above it,
	; which growth steps onto - cannot cover this run plus a reserve.  The
	; run itself never fails for want of a sweep, as before; the reserve is
	; for the window-close animation, whose remap may not sweep and blanked
	; 22 cells on an Item-menu close when the flips before it had left the
	; pool with nothing free.
	bsr.w	VWFMenu_FreeSlots	; d0 = zero-count slots
	move.w	d4, d1
	add.w	#VWFMENU_SWEEP_RESERVE, d1	; (never subtract from d0: it can be 0)
	cmp.w	d1, d0
	bcc.s	VWFMenu_DrawString_NoSweep
	bsr.w	VWFMenu_FieldReclaimAllowed
	beq.s	VWFMenu_DrawString_NoSweep
	jsr	(VWFMenu_Sweep).l
VWFMenu_DrawString_NoSweep:
	subq.w	#1, d4
	moveq	#0, d5

VWFMenu_DrawString_Cell:
	lea	(VWFMenu_Scratch).l, a3
	adda.w	d5, a3
	lea	(VWFMenu_Scratch+8*32).l, a4
	moveq	#8-1, d7
VWFMenu_DrawString_Gather:
	move.b	(a3), (a4)+
	lea	32(a3), a3
	dbf	d7, VWFMenu_DrawString_Gather

	if vwf_menu_strips=0
	; An ink-less cell - the 1px gap after the last glyph spilling over a
	; cell boundary, which Resta, Ceramic Shield and a third of the names
	; do - gets the blank tile, not a pool slot.  It still counts toward
	; the cells written, so a1 advances exactly as the strip would have.
	; Allocating it was worse than wasteful: its all-zero key matched the
	; all-zero key of a slot that had never been uploaded, and the cell
	; showed whatever VRAM held there.
	lea	(VWFMenu_Scratch+8*32).l, a0
	tst.l	(a0)
	bne.s	VWFMenu_DrawString_Ink
	tst.l	4(a0)
	bne.s	VWFMenu_DrawString_Ink
	bra.w	VWFMenu_DrawString_Full	; writes the blank and moves on
VWFMenu_DrawString_Ink:
	endif
	lea	(VWFMenu_Scratch+8*32).l, a0
	if vwf_menu_chrome=1
	; The first merged output replaces the old final cell.  Release that
	; cell's reference before Alloc so its own slot is available when it was
	; the sole reference.  Alloc's ordinary Take path unlinks the old key and
	; links the merged one, keeping the hash exact.
	tst.w	d5
	bne.s	VWFMenu_DrawString_GlueDerefDone
	tst.b	(VWFMenu_GlueActive).l
	beq.s	VWFMenu_DrawString_GlueDerefDone
	tst.b	(VWFMenu_GlueOwned).l	; a cache replay did not acquire another ref
	beq.s	VWFMenu_DrawString_GlueDerefDone
	moveq	#0, d0
	move.b	(VWFMenu_GlueSlot).l, d0
	bsr.w	VWFMenu_RefAddr2	; a2 = its count; a1 stays the cursor
	tst.b	(a2)
	beq.s	VWFMenu_DrawString_GlueDerefDone
	subq.b	#1, (a2)
	move.b	#1, (VWFMenu_GlueDeref).l
VWFMenu_DrawString_GlueDerefDone:
	endif
	jsr	(VWFMenu_Alloc).l
	tst.w	d0
	bmi.w	VWFMenu_DrawString_NoSlot
	tst.w	d1			; 0 when the tile is already resident
	beq.s	VWFMenu_DrawString_Resident

	movem.l	d0/d4-d5, -(sp)
	lea	(VWFMenu_SlotTile).l, a2	; the pool is not contiguous
	moveq	#0, d1
	move.w	d0, d1
	add.w	d1, d1		; VWFMenu_SlotTile holds word offsets
	move.w	(a2,d1.w), d1
	addi.w	#$680, d1
	move.w	d1, d0
	lea	(VDP_Control_Port).l, a6
	jsr	(LoadVRAMAddressFromTileNumber).l
	lea	(VDP_Data_Port).l, a6
	lea	(VWFMenu_Scratch+8*32).l, a4
	lea	(VWFDia_NibExp).l, a3
	moveq	#8-1, d7
VWFMenu_DrawString_Emit:
	moveq	#0, d0
	move.b	(a4)+, d0
	lsl.w	#6, d0
	movea.l	a3, a2
	adda.w	d0, a2
	move.l	(a2), d1
	ori.l	#VWFMENU_PAPER, d1
	swap	d1
	move.w	d1, (a6)
	swap	d1
	move.w	d1, (a6)
	dbf	d7, VWFMenu_DrawString_Emit
	movem.l	(sp)+, d0/d4-d5

VWFMenu_DrawString_Resident:
	lea	(VWFMenu_SlotTile).l, a2
	moveq	#0, d1
	move.w	d0, d1
	add.w	d1, d1		; VWFMenu_SlotTile holds word offsets
	move.w	(a2,d1.w), d1		; slot -> tile offset from $680
	bsr.w	VWFMenu_DrawString_PartyRecord
	add.w	d2, d1			; d2 already carries $680 + attribute
	move.w	d1, (a1)+
	if vwf_menu_chrome=1
	clr.b	(VWFMenu_GlueActive).l	; replacement committed; never restore old ref
	clr.b	(VWFMenu_GlueDeref).l
	endif
	bsr.w	VWFMenu_RowWrap
	addq.w	#1, d5
	dbf	d4, VWFMenu_DrawString_Cell
	if vwf_menu_chrome=1
	bra.w	VWFMenu_DrawString_Done
	else
	bra.s	VWFMenu_DrawString_Done
	endif

VWFMenu_DrawString_NoSlot:
	clr.l	(VWFMenu_PartyEntry).l	; incomplete: never replay this
	if vwf_menu_chrome=1
	move.b	#1, (VWFMenu_GlueFailed).l
	tst.w	d5
	bne.s	VWFMenu_DrawString_NoSlotNormal
	tst.b	(VWFMenu_GlueActive).l
	beq.s	VWFMenu_DrawString_NoSlotNormal
	; Alloc could not replace the joined cell.  Preserve the name/subject
	; already on the plane and restore the reference dropped above.  The
	; tail's first partial cell is omitted under exhaustion, but the old run
	; is never erased or pointed at an unrelated slot.
	tst.b	(VWFMenu_GlueDeref).l
	beq.s	VWFMenu_DrawString_NoSlotGlueKept
	moveq	#0, d0
	move.b	(VWFMenu_GlueSlot).l, d0
	bsr.w	VWFMenu_RefAddr2	; a2 = its count; a1 stays the cursor
	cmpi.b	#$FF, (a2)
	beq.s	VWFMenu_DrawString_NoSlotGlueKept
	addq.b	#1, (a2)
VWFMenu_DrawString_NoSlotGlueKept:
	clr.b	(VWFMenu_GlueActive).l
	clr.b	(VWFMenu_GlueDeref).l
	addq.l	#2, a1			; GlueBegin moved back onto the old cell
	addq.w	#1, d5			; skip scratch cell 0; later cells may still draw
	dbf	d4, VWFMenu_DrawString_Cell
	bra.w	VWFMenu_DrawString_Done
VWFMenu_DrawString_NoSlotNormal:
	endif
VWFMenu_DrawString_Full:
	; pool exhausted: leave the cell blank.  A gap points at the pool; a
	; tile belonging to another string would point anywhere.
	moveq	#0, d1
	bsr.w	VWFMenu_DrawString_PartyRecord	; an ink-less cell IS the blank
	move.w	d2, (a1)+
	bsr.w	VWFMenu_RowWrap
	addq.w	#1, d5
	dbf	d4, VWFMenu_DrawString_Cell
	bra.s	VWFMenu_DrawString_Done

; Cell d5 of a party name composed to tile offset d1: remember it, and once
; the last cell is in, stamp the entry with the generation it was composed
; under.  Nothing to do when this string is not a party name in battle.
VWFMenu_DrawString_PartyRecord:
	movem.l	d0/a2, -(sp)
	move.l	(VWFMenu_PartyEntry).l, d0
	beq.s	VWFMenu_DrawString_PartyRecDone
	movea.l	d0, a2
	cmpi.w	#VWFMENU_PARTY_CELLS, d5
	bcc.s	VWFMenu_DrawString_PartyTooLong
	move.w	d5, d0
	add.w	d0, d0
	move.w	d1, 4(a2,d0.w)
	move.w	d5, d0
	addq.w	#1, d0
	move.b	d0, 2(a2)		; cells so far
	tst.w	d4
	bne.s	VWFMenu_DrawString_PartyRecDone	; more cells to come
	move.w	(VWFMenu_TakeGen).l, (a2)	; complete: valid from now
	bra.s	VWFMenu_DrawString_PartyRecDone
VWFMenu_DrawString_PartyTooLong:
	clr.l	(VWFMenu_PartyEntry).l
VWFMenu_DrawString_PartyRecDone:
	movem.l	(sp)+, d0/a2
	rts

VWFMenu_DrawString_Done:
	movea.l	(sp)+, a0		; back to the terminator
	if vwf_menu_chrome=1
	bsr.w	VWFMenu_GlueRemember
	endif
	if vwf_menu_strips=0
	; A name composed from the translated table: a0 is on THAT text's
	; terminator, but the caller walks the stock table, so put a0 back on the
	; stock entry's terminator.  Then pad with blanks out to the stock
	; character count, exactly as DrawStrip does, so a1 lands where the
	; fixed-width draw left it and the relative-positioned control codes
	; (`move.w d2, -$80(a1)` and friends) keep landing where they did.
	move.l	(VWFMenu_NameSrc).l, d0
	beq.s	VWFMenu_DrawName_NoPad
	movea.l	d0, a0
	moveq	#0, d7
VWFMenu_DrawName_Len:
	cmpi.b	#$FE, (a0)
	bcc.s	VWFMenu_DrawName_LenDone
	addq.w	#1, d7
	addq.l	#1, a0
	bra.s	VWFMenu_DrawName_Len
VWFMenu_DrawName_LenDone:		; a0 ON the terminator, as the compose path leaves it
	tst.b	(VWFMenu_NoPad).l	; the location banner: no stock length to keep
	bne.s	VWFMenu_DrawName_NoPad
	sub.w	d5, d7			; d5 = cells written, blanks included
	bls.s	VWFMenu_DrawName_NoPad
	subq.w	#1, d7
VWFMenu_DrawName_Pad:
	move.w	d2, (a1)+
	bsr.w	VWFMenu_RowWrap
	dbf	d7, VWFMenu_DrawName_Pad
VWFMenu_DrawName_NoPad:
	endif
	bra.w	VWFMenu_DrawString_Exit

VWFMenu_DrawString_Fixed:
	; One window-bank graphic, in one cell, from the tile the fixed-width
	; path would have used: $680+code, which d2 already carries the $680 of.
	; The caller resumes the proportional run on the next character.
	addq.l	#1, a0
	add.w	d2, d0
	move.w	d0, (a1)+
	bsr.w	VWFMenu_RowWrap
	bra.w	VWFMenu_DrawString_Exit

VWFMenu_DrawString_Graphic:
	; window furniture, drawn fixed-width exactly as it always was
	addq.l	#1, a0
	addi.w	#$C0, d0
	add.w	d2, d0
	move.w	d0, (a1)+
	bsr.w	VWFMenu_RowWrap

VWFMenu_DrawString_Exit:
	clr.l	(VWFMenu_PartyEntry).l	; whichever way this string ended
	movem.l	(sp)+, d0-d7/a2-a6
	; Hand the LAST fold back to the caller.  LoadWindowTiles applies its
	; own fold at loc_69ACA the moment this returns, and a fold leaves a1
	; at column 0 - which is exactly the condition that fold tests for.  A
	; run whose last cell sits in column 63 therefore folded twice and
	; every cell after it drew one row too high: 500 Meseta on the party
	; screen rendered its "00" on the line above.  Undo our fold here and
	; let the caller's single fold stand.  A zero-length run starting at
	; column 0 is unaffected: +$80 here and -$80 there cancel.
	tst.b	(VWFMenu_WrapFlag).l
	beq.s	VWFMenu_DrawString_Exit_Done
	move.l	d0, -(sp)
	move.w	a1, d0
	andi.w	#$7F, d0
	bne.s	VWFMenu_DrawString_Exit_Keep
	lea	$80(a1), a1
VWFMenu_DrawString_Exit_Keep:
	move.l	(sp)+, d0
VWFMenu_DrawString_Exit_Done:
	if vwf_menu_chrome=1
	; End must reflect the final pointer after the LoadWindowTiles boundary
	; handoff above.  A fixed/empty/refused call leaves no candidate and
	; invalidates any older join, preventing a stale address match later.
	tst.b	(VWFMenu_GlueCandidate).l
	beq.s	VWFMenu_DrawString_Exit_NoGlue
	move.l	a1, (VWFMenu_GlueEnd).l
	bra.s	VWFMenu_DrawString_Exit_GlueDone
VWFMenu_DrawString_Exit_NoGlue:
	clr.b	(VWFMenu_GluePhase).l
VWFMenu_DrawString_Exit_GlueDone:
	clr.b	(VWFMenu_GlueCandidate).l
	clr.b	(VWFMenu_GlueActive).l
	clr.b	(VWFMenu_GlueDeref).l
	endif
	rts

	if vwf_menu_chrome=1
; ---------------------------------------------------------------------
; Reopen the preceding composed cell when a second DrawString invocation
; starts exactly where it ended and begins with punctuation that belongs to
; that run: an apostrophe or a leading word space.  The plane entry, reverse
; tile map, slot and saved key all have to agree, so a reassigned slot or an
; unrelated later draw fails closed.  The scratch was cleared by the caller.
; Returns d3 = old pixel phase and a1 = old final-cell address on success;
; otherwise d3/a1 stay at their ordinary new-run values.
; ---------------------------------------------------------------------
VWFMenu_GlueBegin:
	movem.l	d0-d2/d4-d7/a0/a2-a4, -(sp)
	tst.b	(VWFMenu_GluePhase).l
	beq.w	VWFMenu_GlueBegin_Fail
	cmpa.l	(VWFMenu_GlueEnd).l, a1
	bne.w	VWFMenu_GlueBegin_Fail
	moveq	#0, d0
	move.b	(a0), d0
	beq.s	VWFMenu_GlueBegin_Eligible
	cmpi.b	#$54, d0		; apostrophe in wincharset
	bne.w	VWFMenu_GlueBegin_Fail
VWFMenu_GlueBegin_Eligible:
	move.w	-2(a1), d0
	andi.w	#$7FF, d0
	subi.w	#$680, d0
	bcs.w	VWFMenu_GlueBegin_Fail
	cmpi.w	#VWFMENU_TILESPAN, d0
	bcc.w	VWFMenu_GlueBegin_Fail
	lea	(VWFMenu_TileSlot).l, a2
	move.b	(a2,d0.w), d0
	cmpi.b	#$FF, d0
	beq.w	VWFMenu_GlueBegin_Fail
	cmp.b	(VWFMenu_GlueSlot).l, d0
	bne.w	VWFMenu_GlueBegin_Fail
	andi.w	#$FF, d0
	bsr.w	VWFMenu_SlotCap
	bcc.w	VWFMenu_GlueBegin_Fail
	bsr.w	VWFMenu_RefAddr2	; a2 = the slot's count
	tst.b	(a2)
	beq.w	VWFMenu_GlueBegin_Fail
	bsr.w	VWFMenu_KeyAddr2	; a2 = the slot's key
	lea	(VWFMenu_GlueKey).l, a3
	move.l	(a2), d0
	cmp.l	(a3), d0
	bne.w	VWFMenu_GlueBegin_Fail
	move.l	4(a2), d0
	cmp.l	4(a3), d0
	bne.w	VWFMenu_GlueBegin_Fail
	; Key bytes are rows; scratch bytes for one cell are 32 bytes apart.
	lea	(VWFMenu_Scratch).l, a3
	moveq	#8-1, d7
VWFMenu_GlueBegin_Copy:
	move.b	(a2)+, (a3)
	lea	32(a3), a3
	dbf	d7, VWFMenu_GlueBegin_Copy
	moveq	#0, d3
	move.b	(VWFMenu_GluePhase).l, d3
	subq.l	#2, a1
	move.b	#1, (VWFMenu_GlueActive).l
	bra.s	VWFMenu_GlueBegin_Done
VWFMenu_GlueBegin_Fail:
	clr.b	(VWFMenu_GluePhase).l
VWFMenu_GlueBegin_Done:
	movem.l	(sp)+, d0-d2/d4-d7/a0/a2-a4
	rts

; Remember the final resident cell from the current call.  d3 is the total
; pixel cursor, d5 the number of emitted scratch cells, and a1 follows the
; final cell.  GlueEnd itself is committed at DrawString_Exit after row-wrap
; handoff has finished.  A freshly composed cell owns the reference Alloc
; acquired; a party-cache replay does not, so it must never release/recycle
; a slot that may still be visible in another cached plane cell.
VWFMenu_GlueRemember:
	movem.l	d0-d2/d4-d7/a0/a2-a4, -(sp)
	move.b	#1, (VWFMenu_GlueOwned).l
	bra.s	VWFMenu_GlueRemember_Check
VWFMenu_GlueRememberCached:
	movem.l	d0-d2/d4-d7/a0/a2-a4, -(sp)
	clr.b	(VWFMenu_GlueOwned).l
VWFMenu_GlueRemember_Check:
	clr.b	(VWFMenu_GlueCandidate).l
	tst.b	(VWFMenu_GlueFailed).l
	bne.w	VWFMenu_GlueRemember_Done
	tst.w	d5
	beq.w	VWFMenu_GlueRemember_Done
	move.w	d3, d0
	andi.w	#7, d0
	beq.w	VWFMenu_GlueRemember_Done
	move.w	-2(a1), d1
	andi.w	#$7FF, d1
	subi.w	#$680, d1
	bcs.w	VWFMenu_GlueRemember_Done
	cmpi.w	#VWFMENU_TILESPAN, d1
	bcc.w	VWFMenu_GlueRemember_Done
	lea	(VWFMenu_TileSlot).l, a2
	move.b	(a2,d1.w), d1
	cmpi.b	#$FF, d1
	beq.w	VWFMenu_GlueRemember_Done
	andi.w	#$FF, d1
	move.w	d0, d4			; the phase; the helpers take the slot in d0
	move.w	d1, d0
	bsr.w	VWFMenu_SlotCap
	bcc.w	VWFMenu_GlueRemember_Done
	bsr.w	VWFMenu_RefAddr2	; a2 = the slot's count
	tst.b	(a2)
	beq.w	VWFMenu_GlueRemember_Done
	lea	(VWFMenu_GlueKey).l, a3
	move.b	d0, VWFMenu_GlueSlot-VWFMenu_GlueKey(a3)
	bsr.w	VWFMenu_KeyAddr2	; a2 = the slot's key
	move.l	(a2), d2
	move.l	d2, (a3)
	move.l	4(a2), d2
	move.l	d2, 4(a3)
	move.b	d4, VWFMenu_GluePhase-VWFMenu_GlueKey(a3)
	move.b	#1, (VWFMenu_GlueCandidate).l
VWFMenu_GlueRemember_Done:
	movem.l	(sp)+, d0-d2/d4-d7/a0/a2-a4
	rts
	endif

	if vwf_menu_strips=1
; ---------------------------------------------------------------------
; Validate one strip's circular slot chain without borrowing VWFMenu_Scratch:
; Sweep can run while that buffer still holds a composed string.
;   d0 = strip index, d4 = head slot, d5 = cell count
; Returns Z clear only when exactly d5 in-range members lead back to the head.
; The head owns the index and every later member must be a continuation.
; ---------------------------------------------------------------------
VWFMenu_StripValidate:
	movem.l	d1/d3/d6-d7/a0-a1, -(sp)
	moveq	#0, d2			; fail closed
	tst.w	d5
	beq.s	VWFMenu_StripValidate_Done
	cmpi.w	#VWFMENU_SLOTS, d5
	bhi.s	VWFMenu_StripValidate_Done
	move.w	(VWFMenu_PoolTop).l, d6
	cmpi.w	#VWFMENU_SLOTS, d6
	bls.s	VWFMenu_StripValidate_Top
	move.w	#VWFMENU_SLOTS, d6
VWFMenu_StripValidate_Top:
	cmp.w	d6, d4
	bcc.s	VWFMenu_StripValidate_Done
	lea	(VWFMenu_StripOf).l, a0
	lea	(VWFMenu_StripNext).l, a1
	move.w	d4, d7
	move.w	d7, d1
	add.w	d1, d1
	move.w	(a0,d1.w), d3
	cmp.w	d3, d0
	bne.s	VWFMenu_StripValidate_Done
	move.w	d5, d3
	subq.w	#1, d3			; continuation members after the head
VWFMenu_StripValidate_Next:
	moveq	#0, d1
	move.b	(a1,d7.w), d1
	cmp.w	d6, d1
	bcc.s	VWFMenu_StripValidate_Done
	tst.w	d3
	beq.s	VWFMenu_StripValidate_Close
	move.w	d1, d7
	move.w	d7, d1
	add.w	d1, d1
	move.w	(a0,d1.w), d1
	cmpi.w	#$FFFF, d1
	bne.s	VWFMenu_StripValidate_Done
	subq.w	#1, d3
	bra.s	VWFMenu_StripValidate_Next
VWFMenu_StripValidate_Close:
	cmp.w	d4, d1
	bne.s	VWFMenu_StripValidate_Done
	moveq	#1, d2
VWFMenu_StripValidate_Done:
	movem.l	(sp)+, d1/d3/d6-d7/a0-a1
	tst.w	d2
	rts
	endif

; ---------------------------------------------------------------------
; Recompute which pool tiles are actually in use, by reading the plane.
;
; Reference counting was tried first and does not work here: the engine
; writes plane entries from places that cannot all be hooked - the window
; frame painter, the backup and restore of covered regions - so
; decrements go missing and the counts only ever climb.  Measuring the
; plane instead is immune to that, because it asks what is on screen
; rather than trying to track every write.
;
; Runs only when the pool is full, so the cost is paid rarely.
; ---------------------------------------------------------------------
VWFMenu_Sweep:
	movem.l	d0-d7/a0-a2, -(sp)

	lea	(VWFMenu_Refs).l, a1	; nothing is live until the plane says so
	move.w	#VWFMENU_BATTLE_SLOTS-1, d1
	cmpi.w	#$C, (Game_Mode_Index).w
	bne.s	VWFMenu_Sweep_Clear
	move.w	#VWFMENU_BASE_SLOTS-1, d1
VWFMenu_Sweep_Clear:
	clr.b	(a1)+
	dbf	d1, VWFMenu_Sweep_Clear
	cmpi.w	#$C, (Game_Mode_Index).w
	bne.s	VWFMenu_Sweep_ClearDone
	lea	(VWFMenu_RefsX).l, a1
	move.w	#32-1, d1
VWFMenu_Sweep_ClearX:
	clr.b	(a1)+
	dbf	d1, VWFMenu_Sweep_ClearX
VWFMenu_Sweep_ClearDone:

	lea	(Plane_A_Buffer).w, a0
	move.w	#64*32-1, d1
	bsr.w	VWFMenu_Sweep_Range

	if vwf_menu_strips=1
	; Strip ownership is indivisible.  A partly covered or overwritten name
	; can leave only one of its cells on the plane; if that one live slot did
	; not pin the whole validated run, a later allocation could replace an
	; interior cell while StripEnsure still trusted the surviving head.
	lea	(VWFMenu_StripOf).l, a0
	move.w	(VWFMenu_PoolTop).l, d3
	cmpi.w	#VWFMENU_SLOTS, d3
	bls.s	VWFMenu_Sweep_StripsTop
	move.w	#VWFMENU_SLOTS, d3
VWFMenu_Sweep_StripsTop:
	; Valid chains may be scattered in slot-index space.
	moveq	#0, d4			; candidate head slot
VWFMenu_Sweep_StripsNext:
	cmp.w	d3, d4
	bcc.s	VWFMenu_Sweep_StripsDone
	move.w	d4, d1
	add.w	d1, d1
	move.w	(a0,d1.w), d0
	cmpi.w	#$FFFE, d0
	bcc.s	VWFMenu_Sweep_StripsAdvance	; continuation or composer

	move.w	d0, d1
	lsl.w	#2, d1
	lea	(VWFMenu_StripIdx).l, a1
	adda.w	d1, a1
	moveq	#0, d5
	addq.l	#2, a1
	move.b	(a1), d5		; cells in this recorded strip
	bsr.w	VWFMenu_StripValidate
	beq.s	VWFMenu_Sweep_StripsAdvance

	bsr.w	VWFMenu_RefAddr
	lea	(VWFMenu_StripNext).l, a2
	move.w	d5, d7
	subq.w	#1, d7
	move.w	d4, d6
VWFMenu_Sweep_StripsFindLive:
	tst.b	(a1,d6.w)
	bne.s	VWFMenu_Sweep_StripsMark
	moveq	#0, d1
	move.b	(a2,d6.w), d1
	move.w	d1, d6
	dbf	d7, VWFMenu_Sweep_StripsFindLive
	bra.s	VWFMenu_Sweep_StripsAdvance

VWFMenu_Sweep_StripsMark:
	move.w	d5, d7
	subq.w	#1, d7
	move.w	d4, d6
VWFMenu_Sweep_StripsMarkLoop:
	move.b	#1, (a1,d6.w)
	moveq	#0, d1
	move.b	(a2,d6.w), d1
	move.w	d1, d6
	dbf	d7, VWFMenu_Sweep_StripsMarkLoop

VWFMenu_Sweep_StripsAdvance:
	addq.w	#1, d4
	bra.s	VWFMenu_Sweep_StripsNext
VWFMenu_Sweep_StripsDone:
	endif

	; Saved regions are deliberately NOT swept any more.  They used to be,
	; so that a covered window's tiles survived until it was revealed -
	; but that pinned more than half the pool on a nested screen.  Their
	; keys are recorded by VWFMenu_SaveRegion instead, and the tiles are
	; re-allocated on reveal, so holding them here is no longer needed.
VWFMenu_Sweep_Done:
	movem.l	(sp)+, d0-d7/a0-a2
	rts

VWFMenu_Sweep_Range:
VWFMenu_Sweep_Cell:
	move.w	(a0)+, d0
	andi.w	#$7FF, d0
	subi.w	#$680, d0
	bcs.s	VWFMenu_Sweep_Next
	cmpi.w	#VWFMENU_TILESPAN, d0
	bcc.s	VWFMenu_Sweep_Next
	lea	(VWFMenu_TileSlot).l, a1
	move.b	(a1,d0.w), d0		; tile -> slot, $FF when not ours
	cmpi.b	#$FF, d0
	beq.s	VWFMenu_Sweep_Next
	andi.w	#$FF, d0
	bsr.w	VWFMenu_SlotCap		; battle: never past 88, the tails are
	bcc.s	VWFMenu_Sweep_Next	; enemy data by the time results draw
	bsr.w	VWFMenu_RefAddr		; a1 = the slot's count, base or tail
	if vwf_menu_chrome=1
	; More than one visible cell can share a content-keyed slot.  A sweep used
	; to flatten that multiplicity to 1; overwriting either cell then dropped
	; the slot to zero and let Alloc recycle the tile under the other one.  The
	; saturated count is the invariant VWFMenu_Deref already expects.
	cmpi.b	#$FF, (a1)
	beq.s	VWFMenu_Sweep_Next
	addq.b	#1, (a1)
	else
	move.b	#1, (a1)		; legacy fixed-chrome build
	endif
VWFMenu_Sweep_Next:
	dbf	d1, VWFMenu_Sweep_Cell
	rts

; ---------------------------------------------------------------------
; Upload the tile for a pool slot from its recorded key.
;   d0 = slot
; Shared by the composer and the reveal path so both expand identically.
; ---------------------------------------------------------------------
VWFMenu_UploadKey:
	movem.l	d0-d2/a2-a4/a6, -(sp)
	bsr.w	VWFMenu_KeyAddr	; the slot's 1bpp source
	movea.l	a1, a4
	lea	(VWFMenu_SlotTile).l, a2
	moveq	#0, d1
	move.w	d0, d1
	add.w	d1, d1		; VWFMenu_SlotTile holds word offsets
	move.w	(a2,d1.w), d1
	addi.w	#$680, d1
	move.w	d1, d0
	lea	(VDP_Control_Port).l, a6
	jsr	(LoadVRAMAddressFromTileNumber).l
	lea	(VDP_Data_Port).l, a6
	lea	(VWFDia_NibExp).l, a3
	moveq	#8-1, d2
VWFMenu_UploadKey_Row:
	moveq	#0, d0
	move.b	(a4)+, d0
	lsl.w	#6, d0
	movea.l	a3, a2
	adda.w	d0, a2
	move.l	(a2), d1
	ori.l	#VWFMENU_PAPER, d1
	swap	d1
	move.w	d1, (a6)
	swap	d1
	move.w	d1, (a6)
	dbf	d2, VWFMenu_UploadKey_Row
	movem.l	(sp)+, d0-d2/a2-a4/a6
	rts

; ---------------------------------------------------------------------
; Record the composition keys of any pool tiles inside a region that is
; about to be covered, so the tiles no longer have to stay resident.
;   a0 = start of the saved block, d1 = cells in it
; Called from Window_Create after Window_BackupTiles.
; ---------------------------------------------------------------------
VWFMenu_SaveRegion:
	; Records each covered tile's key, and rewrites the cell to carry the
	; record *index* rather than the tile number.  Keying by tile fails
	; once windows nest: an inner window's reveal repoints cells, so an
	; outer window's recorded tile no longer matches what the cell holds
	; and its lookup silently misses.  An index is positional and cannot
	; be invalidated that way.  $700-$791 is safe to borrow as the marker:
	; $700-$77F addresses Plane B's nametable and $780-$793 the sprite
	; table, and no Plane A cell names either.  Real tiles resume at $7C0,
	; so VWFMENU_SAVEN must stay below 192.
	movem.l	d0-d6/a0-a3, -(sp)
	bsr.w	VWFMenu_EnsureLayout
	; Refcounts are a cache of Plane A, not an authoritative ownership log:
	; fixed draws, restores and older nested windows can leave their
	; multiplicity stale.  SaveRegion is about to remove one reference for
	; every markerized backup cell.  Rebuild the counts first so a covered
	; copy of a shared key cannot free the same slot out from under an outer,
	; still-visible cell (Status -> Tech -> Skills exposed this in the
	; equipped-item panel).  Battle does not use field reclamation and keeps
	; its original lifetime rules.
	cmpi.w	#$C, (Game_Mode_Index).w
	bne.s	VWFMenu_SaveRegion_RefsReady
	jsr	(VWFMenu_Sweep).l
VWFMenu_SaveRegion_RefsReady:
	; Strip records are deduplicated by physical tile within this pass.  In
	; the composed build the physical tile is recyclable, so deduplicate all
	; active records by the immutable 8-byte composition key instead.  That
	; both avoids the old cross-pass tile-alias bug and prevents deeply nested
	; Status subpages from filling the record stack with duplicate keys.
	move.w	(VWFMenu_SaveTop).l, (VWFMenu_SavePassBase).l
	subq.w	#1, d1
	bcs.w	VWFMenu_SaveRegion_Done
VWFMenu_SaveRegion_Cell:
	move.w	(a0), d4		; the entry, attributes included
	move.w	d4, d0
	andi.w	#$7FF, d0
	move.w	d0, d5			; the tile
	subi.w	#$680, d0
	bcs.w	VWFMenu_SaveRegion_Next
	cmpi.w	#VWFMENU_TILESPAN, d0
	bcc.w	VWFMenu_SaveRegion_Next
	lea	(VWFMenu_TileSlot).l, a1
	move.b	(a1,d0.w), d0
	cmpi.b	#$FF, d0
	beq.w	VWFMenu_SaveRegion_Next	; not one of ours
	andi.w	#$FF, d0		; d0 = slot
	bsr.w	VWFMenu_SlotCap
	bcc.w	VWFMenu_SaveRegion_Next

	if vwf_menu_strips=1
	; A strip slot has no entry in VWFMenu_Keys - only the composer writes
	; those - so recording one would hand Alloc eight bytes of nothing when
	; the window closes, and the revealed cell would draw whatever that
	; allocated.  Follow the circular slot chain to its head instead and record
	; the strip index plus this cell's offset within it, flagged by bit 15
	; of the record's tile word.  $FFFF is a continuation, $FFFE marks a
	; slot the composer owns.
	move.w	d1, -(sp)		; preserve the region loop counter
	move.w	d0, d2
	lea	(VWFMenu_StripOf).l, a1
	lea	(VWFMenu_StripNext).l, a3
	move.w	(VWFMenu_PoolTop).l, d6
	cmpi.w	#VWFMENU_SLOTS, d6
	bls.s	VWFMenu_SaveRegion_StripTop
	move.w	#VWFMENU_SLOTS, d6
VWFMenu_SaveRegion_StripTop:
	move.w	#VWFMENU_SLOTS-1, d3
VWFMenu_SaveRegion_StripFollow:
	cmp.w	d6, d2
	bcc.s	VWFMenu_SaveRegion_NotStrip
	move.w	d2, d1
	add.w	d1, d1
	move.w	(a1,d1.w), d1
	cmpi.w	#$FFFF, d1
	bne.s	VWFMenu_SaveRegion_StripTest
	moveq	#0, d1
	move.b	(a3,d2.w), d1
	move.w	d1, d2
	dbf	d3, VWFMenu_SaveRegion_StripFollow
	bra.s	VWFMenu_SaveRegion_NotStrip
VWFMenu_SaveRegion_StripTest:
	cmpi.w	#$FFFE, d1
	beq.s	VWFMenu_SaveRegion_NotStrip
	lea	(VWFMenu_StripIdx).l, a2
	move.w	d1, d6
	lsl.w	#2, d6
	adda.w	d6, a2
	moveq	#0, d6
	addq.l	#2, a2
	move.b	(a2), d6
	movem.l	d0/d2/d4-d5, -(sp)
	move.w	d1, d0
	move.w	d2, d4
	move.w	d6, d5
	bsr.w	VWFMenu_StripValidate
	movem.l	(sp)+, d0/d2/d4-d5
	beq.s	VWFMenu_SaveRegion_NotStrip
	move.w	d1, (VWFMenu_SaveStripIdx).l
	moveq	#0, d3
	move.w	d2, d6
VWFMenu_SaveRegion_StripOffset:
	cmp.w	d0, d6
	beq.s	VWFMenu_SaveRegion_StripOffsetFound
	moveq	#0, d2
	move.b	(a3,d6.w), d2
	move.w	d2, d6
	addq.w	#1, d3
	bra.s	VWFMenu_SaveRegion_StripOffset
VWFMenu_SaveRegion_StripOffsetFound:
	move.w	d3, (VWFMenu_SaveStripOff).l
	ori.w	#$8000, d5		; this record describes a strip
VWFMenu_SaveRegion_NotStrip:
	move.w	(sp)+, d1
	endif

	if vwf_menu_strips=1
	lea	(VWFMenu_SaveStack).l, a2
	move.w	(VWFMenu_SaveTop).l, d2
	move.w	(VWFMenu_SavePassBase).l, d3	; this pass's records only
	else
	bsr.w	VWFMenu_KeyAddr
	movea.l	a1, a3			; key of the covered composer slot
	move.w	d0, d5			; keep its slot while d0 walks save records
	move.w	(VWFMenu_SaveTop).l, d2
	moveq	#0, d3			; all active records; compare immutable keys
	moveq	#0, d0
	bsr.w	VWFMenu_SaveAddr
	movea.l	a1, a2			; record zero (or first free record)
	endif
	if vwf_menu_strips=1
	move.w	d3, d6
	mulu.w	#VWFMENU_SAVERECSZ, d6
	adda.w	d6, a2
	endif
	bra.s	VWFMenu_SaveRegion_SeekTest
VWFMenu_SaveRegion_Seek:
	if vwf_menu_strips=1
	cmp.w	(a2), d5
	beq.s	VWFMenu_SaveRegion_Found
	else
	move.l	(a3), d6
	cmp.l	(a2), d6
	bne.s	VWFMenu_SaveRegion_SeekNext
	move.l	4(a3), d6
	cmp.l	4(a2), d6
	beq.s	VWFMenu_SaveRegion_Found
VWFMenu_SaveRegion_SeekNext:
	endif
	if vwf_menu_strips=1
	lea	VWFMENU_SAVERECSZ(a2), a2
	endif
	addq.w	#1, d3
	if vwf_menu_strips=0
	move.w	d3, d0
	bsr.w	VWFMenu_SaveAddr
	movea.l	a1, a2
	endif
VWFMenu_SaveRegion_SeekTest:
	cmp.w	d2, d3
	blo.s	VWFMenu_SaveRegion_Seek

	cmpi.w	#VWFMENU_SAVEN, d2
	bcc.w	VWFMenu_SaveRegion_Overflow
	if vwf_menu_strips=1
	move.w	d5, (a2)		; tile, for dedup within this pass
	tst.w	d5
	bmi.s	VWFMenu_SaveRegion_StripRec
	lea	(VWFMenu_Keys).l, a3
	move.w	d0, d6
	lsl.w	#3, d6
	adda.w	d6, a3
	move.l	(a3), 2(a2)		; its key
	move.l	4(a3), 6(a2)
	bra.s	VWFMenu_SaveRegion_Appended
VWFMenu_SaveRegion_StripRec:
	move.w	(VWFMenu_SaveStripIdx).l, 2(a2)
	move.w	(VWFMenu_SaveStripOff).l, 4(a2)
VWFMenu_SaveRegion_Appended:
	else
	move.l	(a3), (a2)		; the immutable composition key
	move.l	4(a3), 4(a2)
	endif
	addq.w	#1, (VWFMenu_SaveTop).l

VWFMenu_SaveRegion_Found:
	; The marker now owns the saved key; the physical pool tile is no longer
	; present in this backup cell.  Release exactly this reference immediately.
	; This is essential when a later cell overflows the ledger and blocks
	; sweeping: only the raw overflow cells must remain pinned, not every cell
	; already converted to a marker.
	move.w	d4, d0
	bsr.w	VWFMenu_Deref
	andi.w	#$F800, d4		; keep priority, palette and flips
	ori.w	#$700, d4		; marker
	or.w	d3, d4			; record index
	move.w	d4, (a0)
	bra.s	VWFMenu_SaveRegion_Next

VWFMenu_SaveRegion_Overflow:
	; Active save records can outnumber resident slots: outer windows retain
	; historical keys while a deep child covers a new set.  If the ledger is
	; full, leave this backup cell as its raw tile number and pin that slot
	; until the matching window closes.  Reclamation is blocked for the same
	; lifetime, so neither an ordinary free-slot scan nor a pressure sweep can
	; repurpose the tile that the raw backup will reveal.
	move.w	d5, d0
	bsr.w	VWFMenu_RefAddr
	move.b	#$FF, (a1)
	moveq	#0, d3
	move.b	(Windows_Opened_Num).w, d3
	cmpi.w	#VWFMENU_DEPTH, d3
	bcc.s	VWFMenu_SaveRegion_Next	; VWFMenu_Mark handles untracked depth
	add.w	d3, d3
	lea	(VWFMenu_SaveMark).l, a2
	move.w	(a2,d3.w), d6
	tst.w	d6
	bmi.s	VWFMenu_SaveRegion_Next	; this window already owns the block
	ori.w	#$8000, d6		; high bit records the overflow lifetime
	move.w	d6, (a2,d3.w)
	addq.b	#1, (VWFMenu_FieldReuseBlocked).l
VWFMenu_SaveRegion_Next:
	addq.l	#2, a0
	dbf	d1, VWFMenu_SaveRegion_Cell
VWFMenu_SaveRegion_Done:
	movem.l	(sp)+, d0-d6/a0-a3
	rts

; ---------------------------------------------------------------------
; Repoint a revealed region at wherever its tiles now live.
;   d0 = window index of the window that just closed
;
; Runs AFTER loc_6881E has restored the plane, not before.  Before, the
; closing window's own text is still on screen, so the sweep correctly
; marks its tiles live and there is nothing to reclaim - every revealed
; cell then comes back blank.  Afterwards those tiles are unreferenced
; and can be recycled into the region being revealed.
;
; That means walking the plane rather than the saved block, so this
; repeats the row-wrap arithmetic Window_BackupTiles uses: a row is $80
; bytes, a cell crossing the row end wraps back $80, and a row past the
; end of the plane wraps back $1000.
; ---------------------------------------------------------------------
VWFMenu_RemapRegion:
	move.w	#0, -(sp)		; normal entry: do not unwind an outer NoSweep
	movem.l	d0-d7/a0-a4, -(sp)

	; This entry is reached only from VWFMenu_FlushReveal after the restored
	; plane has replaced the closing windows.  Refresh liveness for THIS
	; region unless what is already free could cover every cell in it: the
	; previous region's remap overwrote its restored cells, and the stale
	; slots those pointed at are only reclaimable once a sweep has seen them
	; gone, so one sweep for the whole queue is not enough (it refused 22
	; cells on an Item-menu close) - but a sweep per region, a frame each,
	; was most of a 36-frame hitch closing the Status screen.  A run that
	; still comes up short sweeps once more inside Alloc_Full, which this
	; entry permits.  Allow saved strips to claim a complete dead run even
	; when PoolTop is saturated.
	movea.l	(Win_Group_Start_Addr).w, a1
	move.w	d0, d5
	lsl.w	#3, d5
	adda.w	d5, a1			; (not lea (a1,d5.w): emu68k lacks that form)
	moveq	#0, d5
	move.b	(a1), d5		; width
	moveq	#0, d6
	move.b	$1(a1), d6		; height
	mulu.w	d6, d5			; cells the region could need
	add.w	#VWFMENU_SWEEP_RESERVE, d5
	move.w	d0, d7			; the region index: Ready reads it from d0
	bsr.w	VWFMenu_FreeSlots
	move.w	d0, d1
	move.w	d7, d0
	cmp.w	d5, d1
	bcc.s	VWFMenu_RemapRegion_Swept
	jsr	(VWFMenu_Sweep).l
VWFMenu_RemapRegion_Swept:
	move.b	#1, (VWFMenu_StripReuseOK).l
	bra.s	VWFMenu_RemapRegion_Ready
VWFMenu_RemapRegion_NoSweep:
	; loc_6881E calls this label as a standalone subroutine while it is
	; animating the restored window.  It therefore needs the same save as
	; the sweeping entry; otherwise the common movem below consumes the
	; caller's return stack and the eventual rts jumps to address zero.
	move.w	#1, -(sp)		; per-invocation tag for the shared exit
	movem.l	d0-d7/a0-a4, -(sp)
	clr.b	(VWFMenu_StripReuseOK).l
	; This restores an animation frame, not a normal Window_Destroy reveal.
	; Its cells have not yet been remapped as a coherent saved region, so any
	; pressure-driven sweep/reuse would be able to recycle their source tiles.
	; Count nested/re-entrant entries; their normal shared exits carry tag 0.
	addq.b	#1, (VWFMenu_ReclaimInhibit).l
VWFMenu_RemapRegion_Ready:

	movea.l	(Win_Group_Start_Addr).w, a0
	move.w	d0, d7
	lsl.w	#3, d7
	lea	(a0,d7.w), a0
	moveq	#0, d1
	moveq	#0, d2
	moveq	#0, d3
	moveq	#0, d4
	move.b	(a0), d1		; width
	move.b	$1(a0), d2		; height
	move.b	$2(a0), d3		; X
	move.b	$3(a0), d4		; Y
	jsr	(GetPlaneAOffset).l	; a0 = the region in Plane_A_Buffer
	move.w	d2, d6
VWFMenu_RemapRegion_Row:
	movea.l	a0, a4
	move.w	d1, d5
VWFMenu_RemapRegion_Cell:
	if vwf_menu_hash=1
	; Only a marker cell needs RemapCell, and almost no cell is one: a
	; Status back-out walked 5760 cells to remap 290.  RemapCell's own
	; register frame cost more than the test, so test here first.
	move.w	(a4), d7
	andi.w	#$7FF, d7
	subi.w	#$700, d7
	bcs.s	VWFMenu_RemapRegion_Skip
	cmpi.w	#VWFMENU_SAVEN, d7
	bcc.s	VWFMenu_RemapRegion_Skip
	endif
	bsr.w	VWFMenu_RemapCell
VWFMenu_RemapRegion_Skip:
	addq.l	#2, a4
	move.w	a4, d7
	andi.w	#$7F, d7
	bne.s	VWFMenu_RemapRegion_NextCell
	lea	-$80(a4), a4		; back to the start of the row
VWFMenu_RemapRegion_NextCell:
	dbf	d5, VWFMenu_RemapRegion_Cell
	lea	$80(a0), a0
	move.w	a0, d7
	andi.w	#$F80, d7
	bne.s	VWFMenu_RemapRegion_NextRow
	lea	-$1000(a0), a0		; plane wrap
VWFMenu_RemapRegion_NextRow:
	dbf	d6, VWFMenu_RemapRegion_Row
	clr.b	(VWFMenu_StripReuseOK).l
	movem.l	(sp)+, d0-d7/a0-a4
	tst.w	(sp)			; this invocation's entry tag, below its register frame
	beq.s	VWFMenu_RemapRegion_DiscardTag
	tst.b	(VWFMenu_ReclaimInhibit).l
	beq.s	VWFMenu_RemapRegion_DiscardTag
	subq.b	#1, (VWFMenu_ReclaimInhibit).l
VWFMenu_RemapRegion_DiscardTag:
	addq.l	#2, sp
	rts

; ---------------------------------------------------------------------
; Remap one cell.  a4 addresses it and is preserved; everything the walk
; depends on is saved, because Alloc keeps only d2-d3/a1-a2.
; ---------------------------------------------------------------------
VWFMenu_RemapCell:
	; The cell carries a record index, not a tile, so no search is needed
	; and no intervening reveal can invalidate it.
	movem.l	d0-d5/a0-a3, -(sp)
	move.w	(a4), d4
	move.w	d4, d0
	andi.w	#$7FF, d0
	subi.w	#$700, d0
	bcs.w	VWFMenu_RemapCell_Done	; not a marker
	cmpi.w	#VWFMENU_SAVEN, d0
	bcc.w	VWFMenu_RemapCell_Done

	bsr.w	VWFMenu_SaveAddr
	movea.l	a1, a2
	if vwf_menu_strips=1
	move.w	(a2), d5		; bit 15 set: a strip, not a composed tile
	bmi.s	VWFMenu_RemapCell_Strip
	lea	2(a2), a0		; strip build's composer record keeps tile first
	else
	movea.l	a2, a0			; compact composed record is the key alone
	endif
	jsr	(VWFMenu_Alloc).l
	tst.w	d0
	bmi.s	VWFMenu_RemapCell_Blank
	tst.w	d1
	beq.s	VWFMenu_RemapCell_Point
	bsr.w	VWFMenu_UploadKey
VWFMenu_RemapCell_Point:
	lea	(VWFMenu_SlotTile).l, a3
	moveq	#0, d2
	move.w	d0, d2
	add.w	d2, d2		; VWFMenu_SlotTile holds word offsets
	move.w	(a3,d2.w), d2
	addi.w	#$680, d2
	andi.w	#$F800, d4
	or.w	d2, d4
	bra.s	VWFMenu_RemapCell_Write
	if vwf_menu_strips=1
VWFMenu_RemapCell_Strip:
	move.w	4(a2), d3		; offset within the strip
	move.w	2(a2), d0		; strip index
	bsr.w	VWFMenu_StripEnsure	; StripEnsure preserves d1-d4
	tst.w	d0
	bmi.s	VWFMenu_RemapCell_Blank
	tst.w	d3
	beq.s	VWFMenu_RemapCell_Point
	lea	(VWFMenu_StripNext).l, a3
	subq.w	#1, d3
VWFMenu_RemapCell_StripOffset:
	moveq	#0, d2
	move.b	(a3,d0.w), d2
	move.w	d2, d0
	dbf	d3, VWFMenu_RemapCell_StripOffset
	bra.s	VWFMenu_RemapCell_Point
	endif
VWFMenu_RemapCell_Blank:
	andi.w	#$F800, d4
	ori.w	#$680, d4
VWFMenu_RemapCell_Write:
	move.w	d4, (a4)
VWFMenu_RemapCell_Done:
	movem.l	(sp)+, d0-d5/a0-a3
	rts

; ---------------------------------------------------------------------
; Deferred reveal.
;
; Rudy's status Tech page (11 combat, 7 field techs) is the tightest screen
; in the game.  Backing out of its Skills page destroys two windows in a row,
; and the FIRST destroy's reveal remapped its region while the second window
; was still on the plane: the pool held both pages at once, Alloc ran out,
; and RemapCell wrote blanks that no later step repairs - Procedan drawn
; with two holes.  Neither window ever reaches the screen between the two
; destroys, so nothing is lost by revealing later: the region index is
; queued here and every queued region is remapped just before the plane is
; next DMA'd, or before a window is created (SaveRegion would otherwise
; record the markers, and the old group must still be current).
;   d0 = window index (VWFMenu_RemapIdx), as RemapRegion takes it
; ---------------------------------------------------------------------
VWFMenu_DeferReveal:
	movem.l	d0-d1/a0, -(sp)
	moveq	#0, d1
	move.b	(VWFMenu_DeferN).l, d1
	cmpi.w	#VWFMENU_DEFER_MAX, d1
	bcs.s	VWFMenu_DeferReveal_Room
	bsr.s	VWFMenu_FlushReveal	; full: resolve what is queued first
	moveq	#0, d1
VWFMenu_DeferReveal_Room:
	lea	(VWFMenu_DeferList).l, a0
	move.b	d0, (a0,d1.w)
	addq.b	#1, (VWFMenu_DeferN).l
	movem.l	(sp)+, d0-d1/a0
	rts

; Preserves every register: called from DMA_PlaneA, which keeps only d0-d2,
; and from Window_Create's entry.
VWFMenu_FlushReveal:
	tst.b	(VWFMenu_DeferN).l
	beq.s	VWFMenu_FlushReveal_Done
	movem.l	d0-d7/a0-a6, -(sp)
	lea	(VWFMenu_DeferList).l, a0
	moveq	#0, d7
	move.b	(VWFMenu_DeferN).l, d7
	clr.b	(VWFMenu_DeferN).l	; before remapping: a nested defer starts afresh
	subq.w	#1, d7
VWFMenu_FlushReveal_Next:
	moveq	#0, d0
	move.b	(a0)+, d0
	move.l	a0, -(sp)
	jsr	(VWFMenu_RemapRegion).l
	movea.l	(sp)+, a0
	dbf	d7, VWFMenu_FlushReveal_Next
	movem.l	(sp)+, d0-d7/a0-a6
VWFMenu_FlushReveal_Done:
	rts

; ---------------------------------------------------------------------
; Stack discipline for the record above, mirroring the window stack.
; ---------------------------------------------------------------------
VWFMenu_SaveMarkPush:
	movem.l	d0/a0, -(sp)
	moveq	#0, d0
	move.b	(Windows_Opened_Num).w, d0
	cmpi.w	#VWFMENU_DEPTH, d0
	bcc.s	VWFMenu_SaveMarkPush_Done
	add.w	d0, d0
	lea	(VWFMenu_SaveMark).l, a0
	move.w	(VWFMenu_SaveTop).l, (a0,d0.w)
VWFMenu_SaveMarkPush_Done:
	movem.l	(sp)+, d0/a0
	rts

VWFMenu_SaveMarkPop:
	movem.l	d0-d1/a0, -(sp)
	moveq	#0, d0
	move.b	(Windows_Opened_Num).w, d0
	cmpi.w	#VWFMENU_DEPTH, d0
	bcc.s	VWFMenu_SaveMarkPop_Untracked
	add.w	d0, d0
	lea	(VWFMenu_SaveMark).l, a0
	move.w	(a0,d0.w), d1
	move.w	d1, d0
	andi.w	#$7FFF, d0
	move.w	d0, (VWFMenu_SaveTop).l
	tst.w	d1
	bpl.s	VWFMenu_SaveMarkPop_NoOverflow
	tst.b	(VWFMenu_FieldReuseBlocked).l
	beq.s	VWFMenu_SaveMarkPop_NoOverflow
	subq.b	#1, (VWFMenu_FieldReuseBlocked).l
VWFMenu_SaveMarkPop_NoOverflow:
	; Window_Destroy reaches this only after the normal RemapRegion pass has
	; restored and repointed the saved cells.  Retire the capability last.
	tst.b	(VWFMenu_FieldReuseDepth).l
	beq.s	VWFMenu_SaveMarkPop_Done
	subq.b	#1, (VWFMenu_FieldReuseDepth).l
	bra.s	VWFMenu_SaveMarkPop_Done
VWFMenu_SaveMarkPop_Untracked:
	tst.b	(VWFMenu_FieldReuseBlocked).l
	beq.s	VWFMenu_SaveMarkPop_Done
	subq.b	#1, (VWFMenu_FieldReuseBlocked).l
VWFMenu_SaveMarkPop_Done:
	movem.l	(sp)+, d0-d1/a0
	rts

; Draw protagonist Rudy's translated name and right-aligned Level label in a
; title-screen save slot.  The caller passes the name's X/Y coordinates in
; d0/d1; the numeric field is drawn separately against the right edge.
VWFMenu_LoadSaveSlotName:
	movem.l	d0-d1/a0-a1, -(sp)
	moveq	#0, d0			; Character_Stats record 0 is Rudy
	lea	(CharNameData).l, a0
	jsr	(GetOffsetByID).l
	lea	($FFFFE220).w, a1
VWFMenu_LoadSaveSlotName_Copy:
	move.b	(a0)+, d0
	cmpi.b	#$FE, d0
	bcc.s	VWFMenu_LoadSaveSlotName_End
	move.b	d0, (a1)+
	bra.s	VWFMenu_LoadSaveSlotName_Copy
VWFMenu_LoadSaveSlotName_End:
	move.b	#$34, (a1)+		; colon in the window charset
	move.b	#$FE, (a1)
	movem.l	(sp)+, d0-d1/a0-a1
	lea	($FFFFE220).w, a0
	jsr	(VWFField_LoadWindowTiles).l	; RAM name must opt into the VWF
	addq.w	#5, d0			; Level at slot X+6, ending at the number
	lea	(VWFMenu_LoadSaveSlotLevel).l, a0
	jmp	(VWFField_LoadWindowTiles).l

VWFMenu_LoadSaveSlotLevel:
	dc.b	$0C, $3D, $4E, $3D, $44, $FE	; Level
	even

; Kept outside the chrome ranges so the fixed fallback writes every blank
; cell.  The party-bar status field is six cells, X+5..10: the pad cell
; before "Level" (the widest party name, Forren, is 28 px and ends in X+4),
; the three composed cells of "Level" at X+6..8 and the two fixed cells of
; its number at X+9..10.  Composing spaces emits no cells; clearing more
; than six crosses the window boundary.  Six cells is 48 px, which is what
; lets the status words be whole: PARALYZED is 46 px, POISONED 40, DYING
; 26.  The normal "     Level" redraw writes blank tiles through the pad
; cell (an ink-less composed cell gets the blank), so a cured status is
; wiped by the same draw that brings "Level" back.
VWFMenu_StatusLevelClear:
	dc.b	0,0,0,0,0,0,$FE
	even

; The whole words for the party-bar status field (vwf_menu_chrome=1; the
; fixed build keeps the stock five-cell "PARA "/"POIS " strings in ps4.asm).
; Extension source is outside ps4.asm's game-character mapping: A=1..Z=26.
VWFMenu_ParalyzedStr:
	dc.b	$10, $01, $12, $01, $0C, $19, $1A, $05, $04, $FE	; PARALYZED
VWFMenu_PoisonedStr:
	dc.b	$10, $0F, $09, $13, $0F, $0E, $05, $04, $FE	; POISONED
VWFMenu_PoisonedStr_End:
	even

	if vwf_menu_strips=1
; ---------------------------------------------------------------------
; Draw one name from its prerendered strip.
;
; a0 points at an entry inside one of the five name tables.  The offset map
; turns that address into a strip index in constant time - no walking, no
; search - and the tiles come out of ROM already composed and already 4bpp.
; The composer, the nibble expansion and the content-keyed allocator all
; drop out; what is left is a bump allocation and a copy.
;
; a1 advances by max(strip cells, stock characters).  Matching the stock
; length is what keeps the control-code handlers that position themselves
; relative to a1 - `move.w d2, -$80(a1)` and friends - landing where they
; did before.  18 of the 468 names are wider than the stock entry was and
; take the one or two extra cells they need; there is no way around that
; short of the name not fitting.
;
; In:  a0 entry address, a1 nametable pointer, d2 $680 + attribute
; Out: a0 on the terminator, a1 advanced
; ---------------------------------------------------------------------
; Rendered width of a name, in CELLS, in d1.  a0 is unchanged.
;
; The location banner sizes itself by picking a pre-centred window:
; WinGroup_PlaceName widens by one cell per index and steps its X origin left
; every second index, and the caller chooses index = length - 2.  In
; fixed-width Japanese a name's character count IS its cell count, so counting
; characters centred it exactly.  A proportional name is narrower than its
; character count, so the box came out too wide and the name sat left of
; centre - 24px out on the 16-character names.  Measure the strip instead.
;
; Falls back to counting characters when a0 is not a strip entry, which is
; what the caller did before, so a name outside the strip tables is no worse
; off than it was.
VWFMenu_StripCells:
	movem.l	d0/a2, -(sp)
	cmpa.l	#VWFMENU_NAMES_LO, a0
	bcs.s	VWFMenu_StripCells_Chars
	cmpa.l	#VWFMENU_NAMES_HI, a0
	bcc.s	VWFMenu_StripCells_Chars
	move.l	a0, d0
	subi.l	#VWFMENU_NAMES_LO, d0
	add.w	d0, d0
	lea	(VWFMenu_StripMap).l, a2
	adda.w	d0, a2
	move.w	(a2), d0
	cmpi.w	#$FFFF, d0		; not an entry start
	beq.s	VWFMenu_StripCells_Chars
	lsl.w	#2, d0
	lea	(VWFMenu_StripIdx).l, a2
	adda.w	d0, a2
	move.w	(a2)+, d0		; step over the word tile offset
	moveq	#0, d1
	move.b	(a2), d1		; cells
	bra.s	VWFMenu_StripCells_Done
VWFMenu_StripCells_Chars:
	moveq	#0, d1
	movea.l	a0, a2
VWFMenu_StripCells_Count:
	cmpi.b	#$FE, (a2)+
	bcc.s	VWFMenu_StripCells_Done
	addq.w	#1, d1
	bra.s	VWFMenu_StripCells_Count
VWFMenu_StripCells_Done:
	movem.l	(sp)+, d0/a2
	rts

VWFMenu_DrawStrip:
	move.l	a0, d0
	subi.l	#VWFMENU_NAMES_LO, d0
	add.w	d0, d0
	lea	(VWFMenu_StripMap).l, a2
	adda.w	d0, a2
	move.w	(a2), d0
	cmpi.w	#$FFFF, d0
	beq.w	VWFMenu_DrawString_Compose	; a0 is not an entry start

	move.w	d0, d6			; hold the strip index across the walk

	movea.l	a0, a3			; stock length, in characters
	moveq	#0, d7
VWFMenu_DrawStrip_Len:
	cmpi.b	#$FE, (a3)+
	bcc.s	VWFMenu_DrawStrip_LenDone
	addq.w	#1, d7
	bra.s	VWFMenu_DrawStrip_Len
VWFMenu_DrawStrip_LenDone:
	; ON the terminator, not past it.  loc_69AA6 does `move.b (a0)+` and
	; dispatches on the result, so the $FE has to still be there or the
	; caller reads the NEXT name's first byte as a continuation and keeps
	; drawing along the row - which is the saturated row in the field tech
	; menu.  The compose path has always left a0 here; this one did not.
	lea	-1(a3), a0

VWFMenu_DrawStrip_Ensure:
	move.w	d6, d0
	bsr.w	VWFMenu_StripEnsure	; d0 = head slot or -1, d5 = cells
	tst.w	d0
	bmi.w	VWFMenu_DrawStrip_Full
	move.w	d0, d4			; slot walker
	lea	(VWFMenu_StripNext).l, a3
	move.w	d5, d3
	subq.w	#1, d3
	bmi.s	VWFMenu_DrawStrip_Pad
VWFMenu_DrawStrip_Cell:
	lea	(VWFMenu_SlotTile).l, a2
	moveq	#0, d0
	move.w	d4, d0
	add.w	d0, d0		; VWFMenu_SlotTile holds word offsets
	move.w	(a2,d0.w), d0
	add.w	d2, d0			; d2 carries $680 plus the attribute
	move.w	d0, (a1)+
	bsr.w	VWFMenu_RowWrap
	moveq	#0, d0
	move.b	(a3,d4.w), d0
	move.w	d0, d4
	dbf	d3, VWFMenu_DrawStrip_Cell

VWFMenu_DrawStrip_Pad:
	tst.b	(VWFMenu_NoPad).l	; the location banner: no stock length to keep
	bne.s	VWFMenu_DrawStrip_Done
	sub.w	d5, d7			; pad out to the stock length with the
	bls.s	VWFMenu_DrawStrip_Done	; blank at $680, so a1 lands where it
	subq.w	#1, d7			; would have
VWFMenu_DrawStrip_PadCell:
	move.w	d2, (a1)+
	bsr.w	VWFMenu_RowWrap
	dbf	d7, VWFMenu_DrawStrip_PadCell
VWFMenu_DrawStrip_Done:
	bra.w	VWFMenu_DrawString_Exit

VWFMenu_DrawStrip_Full:
	; no room left this window: blank the field rather than point it at
	; another name's tiles, which is what made the old corruption legible
	move.w	d7, d3
	subq.w	#1, d3
	bmi.s	VWFMenu_DrawStrip_Done
VWFMenu_DrawStrip_FullCell:
	move.w	d2, (a1)+
	bsr.w	VWFMenu_RowWrap
	dbf	d3, VWFMenu_DrawStrip_FullCell
	bra.s	VWFMenu_DrawStrip_Done

; ---------------------------------------------------------------------
; Make sure strip `d0` is resident, and say where it lives.
;
; Shared by DrawStrip and by the reveal path: when a window closes over a
; covered strip cell, the cell has to be repointed at the strip wherever it
; now sits, which is the same find-or-allocate question.
;
; In:  d0 = strip index
; Out: d0 = head slot, or -1 if the pool cannot take it
;      d5 = cells the strip occupies
; ---------------------------------------------------------------------
VWFMenu_StripEnsure:
	movem.l	d1-d4/d6-d7/a2-a4, -(sp)
	lea	(VWFMenu_StripIdx).l, a2
	move.w	d0, d1
	lsl.w	#2, d1
	adda.w	d1, a2
	move.w	(a2)+, d6		; tile offset into the strip art
	moveq	#0, d5
	move.b	(a2), d5		; cells

	move.w	(VWFMenu_PoolTop).l, d3
	subq.w	#1, d3
	bmi.s	VWFMenu_StripEnsure_Grow
	moveq	#0, d4
	lea	(VWFMenu_StripOf).l, a2
VWFMenu_StripEnsure_Find:
	cmp.w	(a2), d0		; already resident?
	bne.s	VWFMenu_StripEnsure_Next

	; A recycled member can leave an old head behind.  Trust it only if its
	; complete circular chain still belongs to this strip.
	bsr.w	VWFMenu_StripValidate
	bne.s	VWFMenu_StripEnsure_Hit
VWFMenu_StripEnsure_Next:
	addq.l	#2, a2
	addq.w	#1, d4
	dbf	d3, VWFMenu_StripEnsure_Find
	bra.s	VWFMenu_StripEnsure_Grow
VWFMenu_StripEnsure_Hit:
	bsr.w	VWFMenu_StripEnsure_Live
	move.w	d4, d0
	bra.w	VWFMenu_StripEnsure_Out

	endif

; Return Z clear only while the normal field window lifetime proves that a
; sweep can reclaim and remap cells safely.  Preserve d0: callers branch on
; the condition code alone and may still hold a strip index in that register.
; Outside the strips block: the composed-string path gates its sweep on this
; under both settings of vwf_menu_strips.
VWFMenu_FieldReclaimAllowed:
	movem.l	d0, -(sp)
	move.w	(Game_Mode_Index).w, d0
	cmpi.w	#$C, d0
	bne.s	VWFMenu_FieldReclaimDenied
	tst.b	(VWFMenu_FieldReuseDepth).l
	beq.s	VWFMenu_FieldReclaimDenied
	tst.b	(VWFMenu_FieldReuseBlocked).l
	bne.s	VWFMenu_FieldReclaimDenied
	tst.b	(VWFMenu_ReclaimInhibit).l
	bne.s	VWFMenu_FieldReclaimDenied
	moveq	#1, d0			; Z clear: caller may reclaim
	bra.s	VWFMenu_FieldReclaimDone
VWFMenu_FieldReclaimDenied:
	moveq	#0, d0			; Z set: fail closed
VWFMenu_FieldReclaimDone:
	movem.l	(sp)+, d0
	rts

	if vwf_menu_strips=1
VWFMenu_StripEnsure_Grow:
	move.w	(VWFMenu_PoolTop).l, d4
	move.w	d4, d3
	add.w	d5, d3
	cmpi.w	#VWFMENU_SLOTS, d3
	bls.s	VWFMenu_StripEnsure_Append

	; An explicit RemapRegion scope remains sufficient on its own: it is
	; already sweeping and repointing the restored cells synchronously.
	tst.b	(VWFMenu_StripReuseOK).l
	bne.s	VWFMenu_StripEnsure_Free

	; Outside that explicit scope, only a managed field window may reclaim
	; under allocation pressure.  The capability is entered after its saved
	; region and mark exist, and is withheld for untracked nesting/no-sweep
	; remaps.  This excludes battle even though its Tech list can draw inside
	; Plane_A_Buffer.
	bsr.w	VWFMenu_FieldReclaimAllowed
	beq.w	VWFMenu_StripEnsure_Full
	jsr	(VWFMenu_Sweep).l

	; StripNext makes a strip one logical chain even when free slot indices are
	; fragmented.  Gather any d5 dead slots into the first words of Scratch.
	; StripEnsure is never entered from the composed-string path that owns this
	; buffer; that path routes name-table entries here before composing.
VWFMenu_StripEnsure_Free:
	lea	(VWFMenu_Refs).l, a2
	lea	(VWFMenu_Scratch).l, a3
	move.w	(VWFMenu_PoolTop).l, d3
	subq.w	#1, d3
	bmi.w	VWFMenu_StripEnsure_Full
	moveq	#0, d2			; current slot
	move.w	d5, d1			; cells still needed
VWFMenu_StripEnsure_FreeScan:
	tst.b	(a2,d2.w)
	bne.s	VWFMenu_StripEnsure_FreeNext
	move.w	d2, (a3)+
	subq.w	#1, d1
	beq.s	VWFMenu_StripEnsure_FreeFound
VWFMenu_StripEnsure_FreeNext:
	addq.w	#1, d2
	dbf	d3, VWFMenu_StripEnsure_FreeScan
	bra.w	VWFMenu_StripEnsure_Full
VWFMenu_StripEnsure_FreeFound:
	bra.s	VWFMenu_StripEnsure_Mark

VWFMenu_StripEnsure_Append:
	move.w	d3, (VWFMenu_PoolTop).l
	cmp.w	(VWFMenu_Peak).l, d3
	bls.s	VWFMenu_StripEnsure_AppendList
	move.w	d3, (VWFMenu_Peak).l
VWFMenu_StripEnsure_AppendList:
	lea	(VWFMenu_Scratch).l, a3
	move.w	d4, d2
	move.w	d5, d1
	subq.w	#1, d1
VWFMenu_StripEnsure_AppendCell:
	move.w	d2, (a3)+
	addq.w	#1, d2
	dbf	d1, VWFMenu_StripEnsure_AppendCell

VWFMenu_StripEnsure_Mark:
	lea	(VWFMenu_Scratch).l, a3
	lea	(VWFMenu_StripOf).l, a2
	lea	(VWFMenu_StripNext).l, a4
	move.w	(a3)+, d4		; the first logical cell is the head
	move.w	d4, d2
	add.w	d2, d2
	adda.w	d2, a2
	move.w	d0, (a2)			; only the head carries the index
	move.w	d5, d1
	subq.w	#1, d1
	move.w	d4, d7
	tst.w	d1
	beq.s	VWFMenu_StripEnsure_Close
VWFMenu_StripEnsure_Cont:
	move.w	(a3)+, d2
	movea.l	a4, a2
	adda.w	d7, a2
	move.b	d2, (a2)
	move.w	d2, d7
	add.w	d2, d2
	lea	(VWFMenu_StripOf).l, a2
	adda.w	d2, a2
	moveq	#-1, d2
	move.w	d2, (a2)			; continuation slots match nothing
	subq.w	#1, d1
	bne.s	VWFMenu_StripEnsure_Cont
VWFMenu_StripEnsure_Close:
	movea.l	a4, a2
	adda.w	d7, a2
	move.b	d4, (a2)			; circular: any member reaches the head

VWFMenu_StripEnsure_Art:
	move.w	d6, d1			; art = base + tile offset * 32
	andi.l	#$FFFF, d1
	lsl.l	#5, d1
	lea	(VWFMenu_StripArt).l, a4
	adda.l	d1, a4
	lea	(VWFMenu_StripNext).l, a3
	move.w	d5, d3
	subq.w	#1, d3
	bmi.s	VWFMenu_StripEnsure_Done
	move.w	d4, d7			; slot walker
VWFMenu_StripEnsure_Tile:
	lea	(VWFMenu_SlotTile).l, a2
	moveq	#0, d0
	move.w	d7, d0
	add.w	d0, d0		; VWFMenu_SlotTile holds word offsets
	move.w	(a2,d0.w), d0
	addi.w	#$680, d0
	movem.l	d0-d7/a0-a6, -(sp)
	lea	(VDP_Control_Port).l, a6
	jsr	(LoadVRAMAddressFromTileNumber).l
	lea	(VDP_Data_Port).l, a6
	moveq	#8-1, d0
VWFMenu_StripEnsure_Copy:
	move.l	(a4)+, (a6)
	dbf	d0, VWFMenu_StripEnsure_Copy
	movem.l	(sp)+, d0-d7/a0-a6
	lea	32(a4), a4
	moveq	#0, d2
	move.b	(a3,d7.w), d2
	move.w	d2, d7
	dbf	d3, VWFMenu_StripEnsure_Tile
VWFMenu_StripEnsure_Done:
	bsr.w	VWFMenu_StripEnsure_Live
	move.w	d4, d0
	bra.s	VWFMenu_StripEnsure_Out
VWFMenu_StripEnsure_Full:
	moveq	#-1, d0
VWFMenu_StripEnsure_Out:
	movem.l	(sp)+, d1-d4/d6-d7/a2-a4
	rts

; A resident strip occupies the same pool as composed text, but its slots do
; not have compositor keys.  Mark the whole chain live whenever it is requested
; so Alloc cannot recycle one of its visible cells as a dynamic glyph.
VWFMenu_StripEnsure_Live:
	lea	(VWFMenu_Refs).l, a2
	lea	(VWFMenu_StripNext).l, a3
	move.w	d5, d1
	subq.w	#1, d1
	move.w	d4, d7
VWFMenu_StripEnsure_LiveCell:
	move.b	#1, (a2,d7.w)
	moveq	#0, d2
	move.b	(a3,d7.w), d2
	move.w	d2, d7
	dbf	d1, VWFMenu_StripEnsure_LiveCell
	rts
	endif

	if vwf_menu_strips=0
; ---------------------------------------------------------------------
; Draw one name by composing its TRANSLATED text.
;
; The five name tables in ROM still hold the US text: the game walks them
; by $FE terminator to find an entry, and the stock character count is what
; every relative-positioned control code was laid out against.  Neither is
; the text we draw.  The offset map (shared with the strip build) turns the
; entry address into an index, and VWFMenu_NameIdx/NameText hold the
; translation in the menu charset - the same bytes tools/menustrip.py
; composes, so the cells are identical to the strip's, only allocated by
; content and deduplicated like every other composed string.
;
; The stock entry address is kept in VWFMenu_NameSrc for DrawString_Done,
; which pads out to the stock length and puts a0 back on the stock
; terminator.  a0 pointing anywhere but the stock table would break the
; caller's `move.b (a0)+` dispatch.
;
; In:  a0 entry address, a1 nametable pointer, d2 $680 + attribute
; Out: a0 on the stock terminator, a1 advanced by max(cells, stock chars)
; ---------------------------------------------------------------------
VWFMenu_DrawName:
	move.l	a0, d0
	subi.l	#VWFMENU_NAMES_LO, d0
	add.w	d0, d0
	lea	(VWFMenu_StripMap).l, a2
	adda.w	d0, a2
	move.w	(a2), d0
	cmpi.w	#$FFFF, d0
	beq.w	VWFMenu_DrawString_Compose	; a0 is not an entry start
	move.l	a0, (VWFMenu_NameSrc).l
	add.w	d0, d0
	lea	(VWFMenu_NameIdx).l, a2
	move.w	(a2,d0.w), d0		; byte offset of the translated text
	andi.l	#$FFFF, d0
	lea	(VWFMenu_NameText).l, a0
	adda.l	d0, a0
	bra.w	VWFMenu_DrawString_ComposeName

; ---------------------------------------------------------------------
; Rendered width of a name, in CELLS, in d1.  a0 is unchanged.
;
; The strip build reads this off the strip index; here it is measured from
; the translated text with the same width table the composer uses, so the
; two agree by construction.  Falls back to counting characters when a0 is
; not a name-table entry, exactly as the strip version does.
; ---------------------------------------------------------------------
VWFMenu_StripCells:
	movem.l	d0/a0/a2, -(sp)
	cmpa.l	#VWFMENU_NAMES_LO, a0
	bcs.s	VWFMenu_StripCells_Chars
	cmpa.l	#VWFMENU_NAMES_HI, a0
	bcc.s	VWFMenu_StripCells_Chars
	move.l	a0, d0
	subi.l	#VWFMENU_NAMES_LO, d0
	add.w	d0, d0
	lea	(VWFMenu_StripMap).l, a2
	adda.w	d0, a2
	move.w	(a2), d0
	cmpi.w	#$FFFF, d0		; not an entry start
	beq.s	VWFMenu_StripCells_Chars
	add.w	d0, d0
	lea	(VWFMenu_NameIdx).l, a2
	move.w	(a2,d0.w), d0
	andi.l	#$FFFF, d0
	lea	(VWFMenu_NameText).l, a0
	adda.l	d0, a0
	lea	(VWFMenu_Widths).l, a2
	moveq	#0, d1			; pixels
VWFMenu_StripCells_Px:
	moveq	#0, d0
	move.b	(a0)+, d0
	cmpi.b	#$80, d0
	bcc.s	VWFMenu_StripCells_PxDone
	add.b	(a2,d0.w), d1		; advances are all under 16px: no carry
	bra.s	VWFMenu_StripCells_Px
VWFMenu_StripCells_PxDone:
	addq.w	#7, d1
	lsr.w	#3, d1
	bne.s	VWFMenu_StripCells_Done
	moveq	#1, d1			; the composer never writes fewer than one
	bra.s	VWFMenu_StripCells_Done
VWFMenu_StripCells_Chars:
	moveq	#0, d1
	movea.l	a0, a2
VWFMenu_StripCells_Count:
	cmpi.b	#$FE, (a2)+
	bcc.s	VWFMenu_StripCells_Done
	addq.w	#1, d1
	bra.s	VWFMenu_StripCells_Count
VWFMenu_StripCells_Done:
	movem.l	(sp)+, d0/a0/a2
	rts
	endif

; Battle results: compact the short formatter's five-cell field left, then
; clear what it vacated.  The composed "EXP" suffix can be narrower than the
; fixed field, and without the clear a one-digit value survived to its right
; ("Each got 7 EXP 7").  Entered by jmp from loc_3138 in ps4.asm, whose stub
; keeps the stock size; a1 is left at the compact insertion point.
VWFMenu_BattleExpCompact:
	move.l	a2, -(sp)
	movea.l	a0, a1
	lea	10(a0), a2		; end of the formatter's five-cell field
	moveq	#5, d7
VWFMenu_BattleExpCompact_Skip:
	subq.w	#1, d7
	cmpi.w	#$E680, (a0)+
	beq.s	VWFMenu_BattleExpCompact_Skip
	subq.w	#2, a0
VWFMenu_BattleExpCompact_Copy:
	move.w	(a0)+, (a1)+
	dbf	d7, VWFMenu_BattleExpCompact_Copy
	movea.l	a1, a0
VWFMenu_BattleExpCompact_Clear:
	cmpa.l	a2, a0
	bcc.s	VWFMenu_BattleExpCompact_Done
	move.w	#$E680, (a0)+
	bra.s	VWFMenu_BattleExpCompact_Clear
VWFMenu_BattleExpCompact_Done:
	movea.l	(sp)+, a2
	rts

; ORDER's teardown restores its window through loc_6881E directly, and the
; reveal that restore animates reads VWFMenu_RemapIdx - which ORDER never
; set, so it remapped whichever region was last named and the party submenu
; came back with foreign tiles.  Name the region, then restore.  One jsr in
; ps4.asm replaces the stock jsr at the same size.
VWFMenu_OrderRestore:
	move.w	(a1), (VWFMenu_RemapIdx).l
	jmp	(loc_6881E).l

; Battle MACRO browser.  The letters window takes the pool mark on its
; first open; the preview window's draw (first open, then every hover, via
; loc_4E22) rewinds to it before composing the macro's five names; both
; closes rewind once more.  Without this every hover grew the pool - peak
; 88 after browsing a few macros - and COMMAND then took its base on top
; of that, so the Tech/Skill lists that followed were refused their cells.
; Each is a six-byte jsr standing in for a six-byte jsr in ps4.asm, so no
; battle address moves.
VWFMenu_BattleMacroOpen:
	move.w	(VWFMenu_PoolTop).l, (VWFMenu_BattleMacroMark).l
	jmp	(PlaneMapToRAM).l

VWFMenu_BattleMacroPreview:
	tst.w	(VWFMenu_BattleMacroMark).l
	beq.s	VWFMenu_BattleMacroPreview_Go	; no mark: leave the pool alone
	move.w	(VWFMenu_BattleMacroMark).l, (VWFMenu_PoolTop).l
VWFMenu_BattleMacroPreview_Go:
	jmp	(Battle_SetupWindow).l

VWFMenu_BattleMacroClose:
	tst.w	(VWFMenu_BattleMacroMark).l
	beq.s	VWFMenu_BattleMacroClose_Go
	move.w	(VWFMenu_BattleMacroMark).l, (VWFMenu_PoolTop).l
VWFMenu_BattleMacroClose_Go:
	jmp	(loc_5044).l

; A character's main options window (COMMAND / MACRO / RUN) composes three
; labels, and it is closed before the command menu opens - but battle never
; sweeps, so those eleven slots stayed below Battle_OpenCharComd's base and
; a two-page skill list on a two-enemy screen ran the pool dry on page two
; ("Rec er").  Take the mark before the labels compose and rewind at the
; close; the next turn's window recomposes them above the rewound level.
; Six-byte jsr replacements of six-byte jsrs in ps4.asm.
VWFMenu_BattleOptionsOpen:
	move.w	(VWFMenu_PoolTop).l, (VWFMenu_BattleOptionsMark).l
	jmp	(PlaneMapToRAM).l

VWFMenu_BattleOptionsClose:
	tst.w	(VWFMenu_BattleOptionsMark).l
	beq.s	VWFMenu_BattleOptionsClose_Go
	move.w	(VWFMenu_BattleOptionsMark).l, (VWFMenu_PoolTop).l
VWFMenu_BattleOptionsClose_Go:
	jmp	(loc_27DDFA).l

; The Defend command's action-name box ("DEFENSE", loc_49AC) is the one
; player action window that took no pool mark and never rewound, so every
; defending character leaked its five cells for the rest of the battle
; (five turns of Defend cost the Tech/Skill lists their page two).  Take
; VWFMenu_BattleActionMark at its open like loc_4A94 does, and rewind once
; its close animation has finished - the stock continuation was the eight-byte
; `move.w #$12,(Battle_Routine).l`, which this does after the rewind; the
; two bytes it frees in ps4.asm are a nop.
VWFMenu_BattleDefendOpen:
	move.w	(VWFMenu_PoolTop).l, (VWFMenu_BattleActionMark).l
	jmp	(Battle_SetupWindow).l

VWFMenu_BattleDefendClosed:
	move.w	(VWFMenu_BattleActionMark).l, (VWFMenu_PoolTop).l
	move.w	#$12, (Battle_Routine).l
	rts

; Mid-battle enemy rebuilds - the last two Zol Slugs' Fusion into a Meta
; Slug, ArthroPod + Wiredine's Combine into a Life Deleter, Blade Right +
; Haken Left's into Twin Arms, and the Sand Worm / Jr. Ooze spawns, all
; through loc_14D46 - recompose the enemy group name boxes while the acting
; enemy's action-name window ("Fusion") is still open, so the new names
; landed above VWFMenu_BattleEnemyMark; the window's close (loc_B59A) then
; rewound the pool beneath them and the next turn's COMMAND/MACRO/RUN labels
; took their cells (the Meta Slug's box read "ND MACRO").  A name box lives
; for the rest of the battle, so after each recompose lift every battle mark
; that sits under the new pool level up to it: nothing may rewind beneath
; the names again.  The label that was open at the time stays pinned under
; them (four cells, once per battle - the merges are one-way).  A mark that
; was never taken (zero) is left alone.  Six-byte jsr standing in for the
; six-byte jsr to EnemyGroup_SetupNames.
VWFMenu_BattleRebuildNames:
	jsr	(EnemyGroup_SetupNames).l
	move.w	(VWFMenu_PoolTop).l, d0
	lea	VWFMenu_BattleMarkList(pc), a0
	moveq	#(VWFMenu_BattleMarkList_End-VWFMenu_BattleMarkList)/4-1, d1
VWFMenu_BattleRebuildNames_Loop:
	movea.l	(a0)+, a1
	tst.w	(a1)
	beq.s	VWFMenu_BattleRebuildNames_Next
	cmp.w	(a1), d0
	bls.s	VWFMenu_BattleRebuildNames_Next	; mark already at or above the names
	move.w	d0, (a1)
VWFMenu_BattleRebuildNames_Next:
	dbf	d1, VWFMenu_BattleRebuildNames_Loop
	rts

VWFMenu_BattleMarkList:
	dc.l	VWFMenu_BattleBase
	dc.l	VWFMenu_BattleActionMark
	dc.l	VWFMenu_BattleEnemyMark
	dc.l	VWFMenu_BattleResultMark
	dc.l	VWFMenu_BattleEffectMark
	dc.l	VWFMenu_BattleMacroMark
	dc.l	VWFMenu_BattleOptionsMark
VWFMenu_BattleMarkList_End:

; Publish a newly composed battle-results panel before measuring Plane A.
; This lives in the VWF extension so the original battle-code addresses stay
; fixed and native savestates from the preceding build remain replayable.
VWFMenu_BattleResultCommit:
	if vwf_menu=1
	jsr	(PlaneMapToRAM).l
	jmp	(VWFMenu_Sweep).l
	else
	jmp	(PlaneMapToRAM).l
	endif
VWFMenu_BattleResultCommit_End:
