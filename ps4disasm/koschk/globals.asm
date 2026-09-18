vdp_control				equ $00C00004
vdp_data				equ $00C00000

vdp_write_palettes		equ $F0000000
vdp_write_tiles			equ $40000000
vdp_write_plane_a		equ $40000003
vdp_write_sprite_tiles	equ $60000000
vdp_write_sprite_table	equ $60000003

; ram area where we uncompress the data
ramaddr function x,-(-x)&$FFFFFFFF

uncompress_area			equ ramaddr($FFFF1000)
