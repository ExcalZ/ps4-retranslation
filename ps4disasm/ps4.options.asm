
bugfixes = 1			; if 1, include bug fixes
optional_fixes  = 0		; if 1, include optional (larger) fixes
restore_unused_enemies = 1	; if 1, Acacia and Shadow Mirage will show up
dialogue_uncompressed = 1	; if 1, dialogue is stored uncompressed
vwf_menu = 1			; if 1, menu text is proportional (see docs/devlog.md: pool)
vwf_menu_fixedlabels = 1	; if 1, short all-caps labels come from $7C0
vwf_menu_strips = 0		; 0 composes item/tech/skill names from their
				; translated text through the tile pool - the
				; shipping configuration since 2026-09-14 (see
				; work/STATUS.md).  1 builds the older prerendered
				; strips instead (expands the rom to 4MB); kept
				; buildable as the fallback.
vwf_menu_hash = 1		; if 1, the composer finds resident tiles through a
				; 128-bucket hash over the key table instead of a
				; linear scan (composed build only: it reuses the
				; strip arrays).  Experimental - see work/STATUS.md.
vwf_menu_chrome = 1		; if 1, the fixed-width window labels compose too:
				; party menu, Meseta, Level, the attribute names,
				; with pad spaces snapping to cells.  Experimental.
vwf_measure = 0			; if 1, count cells drawn per window-text call
