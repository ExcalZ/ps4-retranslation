; ---------------------------------------------------------------------------
; Constants and offsets
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Characters, vehicles and enemies statistics (not all of the below are applicable to both)
;
; 'mod' means a stat modified by equipment
profession = 6	; word
level = 8		; word
exp = $A		; longword
curr_hp = $E	; word
max_hp = $10	; word
curr_tp = $12	; word
max_tp = $14	; word
status = $16		; byte ; bit 0 = poisoned; bit 1 = paralyzed; bit 2 = dead; bit 3 = asleep; bit 4 = tech sealed; bit 5 = asleep; bit 6 = dead (for androids)
strength = $18		; byte
strength_mod = $19	; byte
strength_battle = $1A	; byte
mental = $1B			; byte
mental_mod = $1C		; byte
mental_battle = $1D		; byte
agility = $1E			; byte
agility_mod = $1F		; byte
agility_battle = $20	; byte
dexterity = $21			; byte
dexterity_mod = $22		; byte
dexterity_battle = $23	; byte
atk_pow = $24			; word
atk_pow_battle = $26	; word
dfs_pow = $28			; word
dfs_pow_battle = $2A	; word
magic_dfs = $2C			; word
magic_dfs_battle = $2E	; word
element_props = $30
physical_prop = $30		; word
energy_prop = $32		; word
fire_prop = $34			; word
grav_prop = $36			; word
water_prop = $38		; word
antievil_prop = $3A		; word
electric_prop = $3C		; word
holyword_prop = $3E		; word
brose_prop = $40		; word
bio_prop = $42			; word
psy_prop = $44			; word
mech_prop = $46			; word
efess_prop = $48		; word
destroy_prop = $4A		; word
equipment = $4C
right_hand = $4C		; byte
left_hand = $4D			; byte
head = $4E				; byte
body = $4F				; byte
techs = $52
skills = $62
curr_skill_uses = $6A
max_skill_uses = $6B
gain_exp_flag = $7A		; byte ; flag which is set if a character participates and wins a battle at least once. After that characters start gaining experience even if they are not in the party
physical_prop_save = $7B	; in case we use the physical_prop bugfix, we need to save the prop here so defend doesn't override the armor setting
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Character status
StatusPoisoned = 0
StatusParalyzed = 1
StatusDead = 2
StatusAsleep = 3
StatusTechSealed = 4
StatusAsleep2 = 5
StatusAndroidDead = 6

; Status masks
StatusPoisoned_Mask =  1<<StatusPoisoned	; $01
StatusParalyzed_Mask =  1<<StatusParalyzed	; $02
StatusDead_Mask =  1<<StatusDead	; $04
StatusAsleep_Mask =  1<<StatusAsleep	; $08
StatusTechSealed_Mask =  1<<StatusTechSealed	; $10
StatusAsleep2_Mask =  1<<StatusAsleep2	; $20
StatusAndroidDead_Mask =  1<<StatusAndroidDead	; $40
; ---------------------------------------------------------------------------
; Properties and constants applicable to both field and battle objects
obj_id = 0
render_flags = 2	; byte	; bit 2 = if set, animation is finished
mappings_addr = 8	; longword
mappings = $C		; longword
mappings_duration = $11	; byte
timer = $1C			; word

obj_size = $40
next_obj = $40
prev_obj = -$40
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Common field object properties
facing_dir = 6	; word ; 0 = DOWN;    4 = UP;     8 = RIGHT;    $C = LEFT
mappings_idx = $10	; byte ; index for Sprite mappings
offscreen_flag = $12 ; byte ; 0 = on-screen; 1 = off-screen
dialogue_id = $14 ; byte ; ID of dialogue
art_tile = $16		; word ; tile number in VRAM
art_ptr = $18		; longword ; ROM art pointer
x_step_constant = $20	; longword ; constant that changes objects' x position when moving; value is generally 2 or $FFFE
y_step_constant = $24	; longword ; constant that changes objects' y position when moving; value is generally 2 or $FFFE
x_step_duration = $28	; word ; updates characters' x position (one step) automatically until it becomes 0; it's generally 16 when moving from one tile to another
y_step_duration = $2A	; word ; updates characters' y position (one step) automatically until it becomes 0; it's generally 16 when moving from one tile to another
sprite_x_pos = $2C	; word	; used for the Sprite table
sprite_y_pos = $2E	; word	; used for the Sprite table
curr_x_pos = $30	; longword
curr_y_pos = $34	; longword
dest_x_pos = $38	; word ; used as destination when updating objects' x position
dest_y_pos = $3A	; word ; used as destination when updating objects' y position
x_max_move_boundary = $3C	; byte ; boundary which NPC's cannot move past when randomly updating their x position
y_max_move_boundary = $3D	; byte ; boundary which NPC's cannot move past when randomly updating their y position
x_move_boundary = $3E	; byte ; number of steps NPC's can take between 0 and the max boundary (x position)
y_move_boundary = $3F	; byte ; number of steps NPC's can take between 0 and the max boundary (y position)
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Battle objects offsets
battle_mappings_idx = 6	; word
sound = 6				; byte
sound_length = 8		; word
routine = $14			; word
battle_x_pos = $2C		; word
battle_y_pos = $2E		; word
target = $38			; longword
parent = $3C			; longword
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Fighters offsets
fighter_routine = 2		; word
stats_addr = 4			; longword
fighter_art_ptrs = 8		; longword
fighter_x_pos = $C		; word
vdp_dest_addr = $E		; word
fighter_id = $12	; word ; characters and enemies ID; characters' ID start from 1
fighter_pal_line = $1E
ability = $24		; word
palette_obj = $26	; longword
reaction_flags	= $2A	; bitfield ; mainly for enemies, determines what attacks to use depending on some actions
						; bit 0 = attacked physically; bit 1 = attacked magically; bit 2 = attacked with techniques; bit 3 = ambush ; bit 4 = multi-target damage
right_weapon = $2C	; byte ; weapon ID (see 'Battle_WeaponIndexes' in the disassembly)
left_weapon = $2D	; byte ;
action_routine = $32	; word
; ---------------------------------------------------------------------------


; ---------------------------------------------------------------------------
; Enemy sprites properties and constants
enm_spr_map_idx = 4
enm_spr_map_addr = 6
enm_spr_frame = $E
enm_spr_frame_timer = $F
enm_spr_obj_id = $1C

enemy_sprite_size = $20
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Palette objects properties and constants
pal_obj_frame_timer = 2
pal_obj_frame = 3
pal_line_offs = 4
pal_obj_data_addr = 8
pal_table_offs_addr = $C

palette_obj_size = $10
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Offsets specific to treasure chests
item_type = $39
chest_flag = $3A
item_id = $3B
; ---------------------------------------------------------------------------
; function to determine the id in a table
; ptr = address of pointer in the table
; offset = start address of the table
; ptrsize = size of the pointer
; idstart = id start number
id function ptr, ((ptr-offset)/ptrsize+idstart)

; Characters

offset	:=	InitialCharStats
ptrsize	:=	66
idstart	:=	0

CharID_Chaz =  id(Char_Chaz)	; 0
CharID_Alys =  id(Char_Alys)	; 1
CharID_Hahn =  id(Char_Hahn)	; 2
CharID_Rune =  id(Char_Rune)	; 3
CharID_Gryz =  id(Char_Gryz)	; 4
CharID_Rika =  id(Char_Rika)	; 5
CharID_Demi =  id(Char_Demi)	; 6
CharID_Wren =  id(Char_Wren)	; 7
CharID_Raja =  id(Char_Raja)	; 8
CharID_Kyra =  id(Char_Kyra)	; 9
CharID_Seth =  id(Char_Seth)	; $A

; Character masks

CharID_Chaz_Mask =  1<<CharID_Chaz	; $01
CharID_Alys_Mask =  1<<CharID_Alys	; $02
CharID_Hahn_Mask =  1<<CharID_Hahn	; $04
CharID_Rune_Mask =  1<<CharID_Rune	; $08
CharID_Gryz_Mask =  1<<CharID_Gryz	; $10
CharID_Rika_Mask =  1<<CharID_Rika	; $20
CharID_Demi_Mask =  1<<CharID_Demi	; $40
CharID_Wren_Mask =  1<<CharID_Wren	; $80
CharID_Raja_Mask =  1<<CharID_Raja	; $100
CharID_Kyra_Mask =  1<<CharID_Kyra	; $200
CharID_Seth_Mask =  1<<CharID_Seth	; $400

; Professions

ProfessionID_Hunter = 0
ProfessionID_Scholar = 1
ProfessionID_Wizard = 2
ProfessionID_Motavian = 3
ProfessionID_Numan = 4
ProfessionID_Android = 5
ProfessionID_Priest = 6
ProfessionID_Esper = 7

; Inventory

offset	:=	InventoryData
ptrsize	:=	22
idstart	:=	1

ItemID_Dagger = id(Item_Dagger)	 ; 1
ItemID_HuntKnife = id(Item_HuntKnife)	; 2
ItemID_Boomerang = id(Item_Boomerang)	; 3
ItemID_LthrCloth = id(Item_LthrCloth)	; 4
ItemID_LthrHelm = id(Item_LthrHelm)	; 5
ItemID_LthrCrown = id(Item_LthrCrown)	; 6
ItemID_LthrBand = id(Item_LthrBand)	; 7
ItemID_StelSword = id(Item_StelSword)	; 8
ItemID_Slasher = id(Item_Slasher)	; 9
ItemID_LthrShield = id(Item_LthrShield)	; $A
ItemID_CrbnSuit = id(Item_CrbnSuit)	; $B
ItemID_CrbnShield = id(Item_CrbnShield)	; $C
ItemID_CrbnHelm = id(Item_CrbnHelm)	; $D
ItemID_CrbnCrown = id(Item_CrbnCrown)	; $E
ItemID_Circlet = id(Item_Circlet)	; $F
ItemID_WoodCane = id(Item_WoodCane)	; $10
ItemID_WhiteMantl = id(Item_WhiteMantl)	; $11
ItemID_TitnSword = id(Item_TitnSword)	; $12
ItemID_TitnDagger = id(Item_TitnDagger)	; $13
ItemID_TitnSlashr = id(Item_TitnSlashr)	; $14
ItemID_TitnAxe = id(Item_TitnAxe)	; $15
ItemID_BroadAxe = id(Item_BroadAxe)	; $16
ItemID_TitnMail = id(Item_TitnMail)	; $17
ItemID_TitnShield = id(Item_TitnShield)	; $18
ItemID_TitnHelm = id(Item_TitnHelm)	; $19
ItemID_TitnCrown = id(Item_TitnCrown)	; $1A
ItemID_Nothing = id(Item_Nothing)	; $1B
ItemID_GrptSuit = id(Item_GrptSuit)	; $1C
ItemID_GrptShield = id(Item_GrptShield)	; $1D
ItemID_CrmcSword = id(Item_CrmcSword)	; $1E
ItemID_GrptCrown = id(Item_GrptCrown)	; $1F
ItemID_Claw = id(Item_Claw)	; $20
ItemID_CrmcKnife = id(Item_CrmcKnife)	; $21
ItemID_CrmcShield = id(Item_CrmcShield)	; $22
ItemID_LasrSlashr = id(Item_LasrSlashr)	; $23
ItemID_SaberClaw = id(Item_SaberClaw)	; $24
ItemID_StrugglAx = id(Item_StrugglAx)	; $25
ItemID_CrmcMail = id(Item_CrmcMail)	; $26
ItemID_CrmcHelm = id(Item_CrmcHelm)	; $27
ItemID_LasrSword = id(Item_LasrSword)	; $28
ItemID_LasrClaw = id(Item_LasrClaw)	; $29
ItemID_LasrBarrir = id(Item_LasrBarrir)	; $2A
ItemID_Impacter = id(Item_Impacter)	; $2B
ItemID_TitnArmor = id(Item_TitnArmor)	; $2C
ItemID_Headgear = id(Item_Headgear)	; $2D
ItemID_StunShot = id(Item_StunShot)	; $2E
ItemID_LasrAxe = id(Item_LasrAxe)	; $2F
ItemID_LasrKnife = id(Item_LasrKnife)	; $30
ItemID_CrmcArmor = id(Item_CrmcArmor)	; $31
ItemID_TitnGear = id(Item_TitnGear)	; $32
ItemID_PsyMail = id(Item_PsyMail)	; $33
ItemID_PsyShield = id(Item_PsyShield)	; $34
ItemID_PsyCrown = id(Item_PsyCrown)	; $35
ItemID_PsyCirclt = id(Item_PsyCirclt)	; $36
ItemID_ForceCane = id(Item_ForceCane)	; $37
ItemID_PsyRobe = id(Item_PsyRobe)	; $38
ItemID_PsycoWand = id(Item_PsycoWand)	; $39
ItemID_FradeMantl = id(Item_FradeMantl)	; $3A
ItemID_WaveShot = id(Item_WaveShot)	; $3B
ItemID_SpacedArmr = id(Item_SpacedArmr)	; $3C
ItemID_CrmcGear = id(Item_CrmcGear)	; $3D
ItemID_PlsmRifle = id(Item_PlsmRifle)	; $3E
ItemID_PulseLasr = id(Item_PulseLasr)	; $3F
ItemID_PlsmSword = id(Item_PlsmSword)	; $40
ItemID_PlsmClaw = id(Item_PlsmClaw)	; $41
ItemID_PlsmDagger = id(Item_PlsmDagger)	; $42
ItemID_PlsmField = id(Item_PlsmField)	; $43
ItemID_SilvRod = id(Item_SilvRod)	; $44
ItemID_SilvMantl = id(Item_SilvMantl)	; $45
ItemID_SilvCirclt = id(Item_SilvCirclt)	; $46
ItemID_SilvMail = id(Item_SilvMail)	; $47
ItemID_SilvShield = id(Item_SilvShield)	; $48
ItemID_SilvHelm = id(Item_SilvHelm)	; $49
ItemID_SilvCrown = id(Item_SilvCrown)	; $4A
ItemID_ZircGear = id(Item_ZircGear)	; $4B
ItemID_NapalmShot = id(Item_NapalmShot)	; $4C
ItemID_ZircoArmer = id(Item_ZircoArmer)	; $4D
ItemID_FlameSword = id(Item_FlameSword)	; $4E
ItemID_ThundrClaw = id(Item_ThundrClaw)	; $4F
ItemID_TorndDaggr = id(Item_TorndDaggr)	; $50
ItemID_DreamRod = id(Item_DreamRod)	; $51
ItemID_PhantaRobe = id(Item_PhantaRobe)	; $52
ItemID_SilvrTusk = id(Item_SilvrTusk)	; $53
ItemID_PulseVulcn = id(Item_PulseVulcn)	; $54
ItemID_CompoArmr = id(Item_CompoArmr)	; $55
ItemID_CompoGear = id(Item_CompoGear)	; $56
ItemID_RflcMail = id(Item_RflcMail)	; $57
ItemID_RflcShield = id(Item_RflcShield)	; $58
ItemID_RflcRobe = id(Item_RflcRobe)	; $59
ItemID_LacoSword = id(Item_LacoSword)	; $5A
ItemID_LacoDagger = id(Item_LacoDagger)	; $5B
ItemID_LacoClaw = id(Item_LacoClaw)	; $5C
ItemID_LacoSlashr = id(Item_LacoSlashr)	; $5D
ItemID_GuardRod = id(Item_GuardRod)	; $5E
ItemID_PlsmLaunch = id(Item_PlsmLaunch)	; $5F
ItemID_ElstArmor = id(Item_ElstArmor)	; $60
ItemID_ElstGear = id(Item_ElstGear)	; $61
ItemID_LacoRod = id(Item_LacoRod)	; $62
ItemID_GenocyClaw = id(Item_GenocyClaw)	; $63
ItemID_SwiftHelm = id(Item_SwiftHelm)	; $64
ItemID_MoonSlashr = id(Item_MoonSlashr)	; $65
ItemID_PowShield = id(Item_PowShield)	; $66
ItemID_LacoMail = id(Item_LacoMail)	; $67
ItemID_LacoHelm = id(Item_LacoHelm)	; $68
ItemID_LacoCrown = id(Item_LacoCrown)	; $69
ItemID_LacoCirclt = id(Item_LacoCirclt)	; $6A
ItemID_LacoShield = id(Item_LacoShield)	; $6B
ItemID_CyberSuit = id(Item_CyberSuit)	; $6C
ItemID_GuardSword = id(Item_GuardSword)	; $6D
ItemID_PhotnErasr = id(Item_PhotnErasr)	; $6E
ItemID_LacoArmor = id(Item_LacoArmor)	; $6F
ItemID_LacoGear = id(Item_LacoGear)	; $70
ItemID_MahlayDggr = id(Item_MahlayDggr)	; $71
ItemID_GuardClaw = id(Item_GuardClaw)	; $72
ItemID_GuardArmor = id(Item_GuardArmor)	; $73
ItemID_GuardRobe = id(Item_GuardRobe)	; $74
ItemID_GuardMail = id(Item_GuardMail)	; $75
ItemID_Nothing2 = id(Item_Nothing2)	; $76
ItemID_Elsydeon = id(Item_Elsydeon)	; $77
ItemID_LacoAxe = id(Item_LacoAxe)	; $78
ItemID_SonicBustr = id(Item_SonicBustr)	; $79
ItemID_DefeatAxe = id(Item_DefeatAxe)	; $7A
ItemID_Nothing3 = id(Item_Nothing3)	; $7B
ItemID_MahlayMail = id(Item_MahlayMail)	; $7C
ItemID_Monomate = id(Item_Monomate)	; $7D
ItemID_Dimate = id(Item_Dimate)	; $7E
ItemID_Trimate = id(Item_Trimate)	; $7F
ItemID_Antidote = id(Item_Antidote)	; $80
ItemID_CureParal = id(Item_CureParal)	; $81
ItemID_MoonDew = id(Item_MoonDew)	; $82
ItemID_StarDew = id(Item_StarDew)	; $83
ItemID_Telepipe = id(Item_Telepipe)	; $84
ItemID_Escapipe = id(Item_Escapipe)	; $85
ItemID_SolDew = id(Item_SolDew)	; $86
ItemID_GuardShild = id(Item_GuardShild)	; $87
ItemID_MahlayShld = id(Item_MahlayShld)	; $88
ItemID_ShadwBlade = id(Item_ShadwBlade)	; $89
ItemID_AlisSword = id(Item_AlisSword)	; $8A
ItemID_Dynamite = id(Item_Dynamite)	; $8B
ItemID_Nothing4 = id(Item_Nothing4)	; $8C
ItemID_Alshline = id(Item_Alshline)	; $8D
ItemID_EclpsTorch = id(Item_EclpsTorch)	; $8E
ItemID_AeroPrism = id(Item_AeroPrism)	; $8F
ItemID_RepairKit = id(Item_RepairKit)	; $90
ItemID_ShortCake = id(Item_ShortCake)	; $91
ItemID_PenguFeed = id(Item_PenguFeed)	; $92
ItemID_Perolymate = id(Item_Perolymate)	; $93
ItemID_Pennant = id(Item_Pennant)	; $94
ItemID_WoodCarvin = id(Item_WoodCarvin)	; $95
ItemID_LandRover = id(Item_LandRover)	; $96
ItemID_IceDigger = id(Item_IceDigger)	; $97
ItemID_HydroFoil = id(Item_HydroFoil)	; $98
ItemID_ControlKey = id(Item_ControlKey)	; $99
ItemID_Canceller = id(Item_Canceller)	; $9A
ItemID_PalmaRing = id(Item_PalmaRing)	; $9B
ItemID_MotaRing = id(Item_MotaRing)	; $9C
ItemID_DezoRing = id(Item_DezoRing)	; $9D
ItemID_RykrRing = id(Item_RykrRing)	; $9E
ItemID_AlgoRing = id(Item_AlgoRing)	; $9F
ItemID_MahlayRing = id(Item_MahlayRing)	; $A0


;  Weapon indexes (remapped in battle); some weapons have the same animation so they share the same ID
WeaponID_Dagger = 1
WeaponID_HuntKnife = 1
WeaponID_TitnDagger = 2
WeaponID_CrmcKnife = 2
WeaponID_LasrKnife = 3
WeaponID_PlsmDagger = 3
WeaponID_TorndDaggr = 4
WeaponID_LacoDagger = 4
WeaponID_MahlayDggr = 4
WeaponID_StelSword = 5
WeaponID_TitnSword = 5
WeaponID_CrmcSword = 5
WeaponID_AlisSword = 5
WeaponID_LasrSword = 6
WeaponID_PlsmSword = 6
WeaponID_FlameSword = 6
WeaponID_ShadwBlade = 6
WeaponID_LacoSword = 7
WeaponID_GuardSword = 7
WeaponID_Elsydeon = 8
WeaponID_WoodCane = 9
WeaponID_ForceCane = 9
WeaponID_PsycoWand = $A
WeaponID_SilvRod = $A
WeaponID_DreamRod = $A
WeaponID_GuardRod = $B
WeaponID_LacoRod = $B
WeaponID_TitnAxe = $C
WeaponID_BroadAxe = $C
WeaponID_StrugglAx = $C
WeaponID_LasrAxe = $D
WeaponID_LacoAxe = $E
WeaponID_DefeatAxe = $E
WeaponID_Claw = $F
WeaponID_SaberClaw = $F
WeaponID_LasrClaw = $10
WeaponID_PlsmClaw = $10
WeaponID_ThundrClaw = $10
WeaponID_SilvrTusk = $11
WeaponID_LacoClaw = $11
WeaponID_GenocyClaw = $11
WeaponID_GuardClaw = $12
WeaponID_Boomerang = $13
WeaponID_Slasher = $13
WeaponID_TitnSlashr = $14
WeaponID_LasrSlashr = $14
WeaponID_LacoSlashr = $15
WeaponID_MoonSlashr = $15
WeaponID_Impacter = $16
WeaponID_StunShot = $16
WeaponID_PulseLasr = $16
WeaponID_PulseVulcn = $16
WeaponID_WaveShot = $17
WeaponID_PlsmRifle = $18
WeaponID_NapalmShot = $19
WeaponID_PlsmLaunch = $1A
WeaponID_PhotnErasr = $1B
WeaponID_SonicBustr = $1C


; Techniques

offset	:=	TechniqueData
ptrsize	:=	8
idstart	:=	1

TechID_Foi = id(Tech_Foi)	; 1
TechID_Gifoi = id(Tech_Gifoi)	; 2
TechID_Nafoi = id(Tech_Nafoi)	; 3
TechID_Wat = id(Tech_Wat)	; 4
TechID_Giwat = id(Tech_Giwat)	; 5
TechID_Nawat = id(Tech_Nawat)	; 6
TechID_Tsu = id(Tech_Tsu)	; 7
TechID_Githu = id(Tech_Githu)	; 8
TechID_Nathu = id(Tech_Nathu)	; 9
TechID_Zan = id(Tech_Zan)	; $A
TechID_Gizan = id(Tech_Gizan)	; $B
TechID_Nazan = id(Tech_Nazan)	; $C
TechID_Gra = id(Tech_Gra)	; $D
TechID_Gigra = id(Tech_Gigra)	; $E
TechID_Nagra = id(Tech_Nagra)	; $F
TechID_Megid = id(Tech_Megid)	; $10
TechID_Brose = id(Tech_Brose)	; $11
TechID_Vol = id(Tech_Vol)	; $12
TechID_Savol = id(Tech_Savol)	; $13
TechID_Gelun = id(Tech_Gelun)	; $14
TechID_Doran = id(Tech_Doran)	; $15
TechID_Seals = id(Tech_Seals)	; $16
TechID_Rimit = id(Tech_Rimit)	; $17
TechID_Res = id(Tech_Res)	; $18
TechID_Gires = id(Tech_Gires)	; $19
TechID_Nares = id(Tech_Nares)	; $1A
TechID_Sar = id(Tech_Sar)	; $1B
TechID_Gisar = id(Tech_Gisar)	; $1C
TechID_Nasar = id(Tech_Nasar)	; $1D
TechID_Shift = id(Tech_Shift)	; $1E
TechID_Saner = id(Tech_Saner)	; $1F
TechID_Deban = id(Tech_Deban)	; $20
TechID_Feeve = id(Tech_Feeve)	; $21
TechID_Anti = id(Tech_Anti)	; $22
TechID_Rimpa = id(Tech_Rimpa)	; $23
TechID_Rever = id(Tech_Rever)	; $24
TechID_Regen = id(Tech_Regen)	; $25
TechID_Arows = id(Tech_Arows)	; $26
TechID_Ryuka = id(Tech_Ryuka)	; $27
TechID_Hinas = id(Tech_Hinas)	; $28

; Skills

offset	:=	SkillData
ptrsize	:=	8
idstart	:=	1

SkillID_Crosscut = id(Skill_Crosscut)	; 1
SkillID_Rayblade = id(Skill_Rayblade)	; 2
SkillID_DblSlash = id(Skill_DblSlash)	; 3
SkillID_Flaeli = id(Skill_Flaeli)	; 4
SkillID_Flare = id(Skill_Flare)	; 5
SkillID_Vortex = id(Skill_Vortex)	; 6
SkillID_Astral = id(Skill_Astral)	; 7
SkillID_Airslash = id(Skill_Airslash)	; 8
SkillID_Disrupt = id(Skill_Disrupt)	; 9
SkillID_Hewn = id(Skill_Hewn)	; $A
SkillID_Tandle = id(Skill_Tandle)	; $B
SkillID_Efess = id(Skill_Efess)	; $C
SkillID_Legeon = id(Skill_Legeon)	; $D
SkillID_Burstroc = id(Skill_Burstroc)	; $E
SkillID_Posibolt = id(Skill_Posibolt)	; $F
SkillID_Sweeping = id(Skill_Sweeping)	; $10
SkillID_Phonon = id(Skill_Phonon)	; $11
SkillID_StFire = id(Skill_StFire)	; $12
SkillID_Corrsion = id(Skill_Corrsion)	; $13
SkillID_Explode = id(Skill_Explode)	; $14
SkillID_Eliminat = id(Skill_Eliminat)	; $15
SkillID_Diem = id(Skill_Diem)	; $16
SkillID_Spark = id(Skill_Spark)	; $17
SkillID_Death = id(Skill_Death)	; $18
SkillID_Holyword = id(Skill_Holyword)	; $19
SkillID_Dthspell = id(Skill_Dthspell)	; $1A
SkillID_Negatis = id(Skill_Negatis)	; $1B
SkillID_Illusion = id(Skill_Illusion)	; $1C
SkillID_Telele = id(Skill_Telele)	; $1D
SkillID_Shadow = id(Skill_Shadow)	; $1E
SkillID_Earth = id(Skill_Earth)	; $1F
SkillID_Hijammer = id(Skill_Hijammer)	; $20
SkillID_Moonshad = id(Skill_Moonshad)	; $21
SkillID_Crash = id(Skill_Crash)	; $22
SkillID_StasisBm = id(Skill_StasisBm)	; $23
SkillID_Bindwa = id(Skill_Bindwa)	; $24
SkillID_Mindblst = id(Skill_Mindblst)	; $25
SkillID_Barrier = id(Skill_Barrier)	; $26
SkillID_WarCry = id(Skill_WarCry)	; $27
SkillID_Blessing = id(Skill_Blessing)	; $28
SkillID_Warla = id(Skill_Warla)	; $29
SkillID_Recover = id(Skill_Recover)	; $2A
SkillID_Medice = id(Skill_Medice)	; $2B
SkillID_Miracle = id(Skill_Miracle)	; $2C
SkillID_MedicPw = id(Skill_MedicPw)	; $2D
SkillID_Ataraxia = id(Skill_Ataraxia)	; $2E
SkillID_Vision = id(Skill_Vision)	; $2F
SkillID_Eliminat2 = id(Skill_Eliminat2)	; $30
SkillID_Flaeli2 = id(Skill_Flaeli2)	; $31
SkillID_Hewn2 = id(Skill_Hewn2)	; $32
SkillID_Tandle2 = id(Skill_Tandle2)	; $33
SkillID_Spark2 = id(Skill_Spark2)	; $34
SkillID_Barrier2 = id(Skill_Barrier2)	; $35
SkillID_Recover2 = id(Skill_Recover2)	; $36

; Combo

offset	:=	ComboData
ptrsize	:=	8
idstart	:=	0

ComboID_None = id(Combo_None) ; 0
ComboID_Paradinblw = id(Combo_Paradinblw) ; 1
ComboID_Firestorm = id(Combo_Firestorm) ; 2
ComboID_Blizzard = id(Combo_Blizzard) ; 3
ComboID_Condctthnd = id(Combo_Condctthnd) ; 4
ComboID_Grandcross = id(Combo_Grandcross) ; 5
ComboID_Silentwave = id(Combo_Silentwave) ; 6
ComboID_Shootnstar = id(Combo_Shootnstar) ; 7
ComboID_Triblaster = id(Combo_Triblaster) ; 8
ComboID_Holocaust = id(Combo_Holocaust) ; 9
ComboID_BlackHole = id(Combo_BlackHole) ; $A
ComboID_Circuitbrk = id(Combo_Circuitbrk) ; $B
ComboID_Purfylight = id(Combo_Purfylight) ; $C
ComboID_LethalImg = id(Combo_LethalImg) ; $D
ComboID_Destruct = id(Combo_Destruct) ; $E

; Vehicles

offset	:=	VehicleData
ptrsize	:=	26
idstart	:=	1

VehicleID_LandRover = id(Vehicle_LandRover)	; 1
VehicleID_IceDigger = id(Vehicle_IceDigger)	; 2
VehicleID_Hydrofoil = id(Vehicle_Hydrofoil)	; 3

; Vehicle Skills

offset	:=	VehicleSkillData
ptrsize	:=	8
idstart	:=	1

VehicleSkillID_Cluster = id(VehicleSkill_Cluster)	; 1
VehicleSkillID_Gravitn = id(VehicleSkill_Gravitn)	; 2
VehicleSkillID_ThGrid = id(VehicleSkill_ThGrid)	; 3
VehicleSkillID_XBurst = id(VehicleSkill_XBurst)	; 4
VehicleSkillID_Napalm = id(VehicleSkill_Napalm)	; 5
VehicleSkillID_Nothing = id(VehicleSkill_Nothing)	; 6
VehicleSkillID_NSpher = id(VehicleSkill_NSpher)	; 7
VehicleSkillID_Nothing2 = id(VehicleSkill_Nothing2)	; 8

; Vehicle Skill masks
VehicleSkillID_Cluster_Mask = 1<<(VehicleSkillID_Cluster-idstart)	; $01
VehicleSkillID_Gravitn_Mask = 1<<(VehicleSkillID_Gravitn-idstart)	; $02
VehicleSkillID_ThGrid_Mask = 1<<(VehicleSkillID_ThGrid-idstart)	; $04
VehicleSkillID_XBurst_Mask = 1<<(VehicleSkillID_XBurst-idstart)	; $08
VehicleSkillID_Napalm_Mask = 1<<(VehicleSkillID_Napalm-idstart)	; $10
VehicleSkillID_Nothing_Mask = 1<<(VehicleSkillID_Nothing-idstart)	; $20
VehicleSkillID_NSpher_Mask = 1<<(VehicleSkillID_NSpher-idstart)	; $40
VehicleSkillID_Nothing2_Mask = 1<<(VehicleSkillID_Nothing2-idstart)	; $80

; Enemies

offset	:=	EnemyData
ptrsize	:=	48
idstart	:=	0

EnemyID_Helex = id(Enemy_Helex)	; 0
EnemyID_MonsterFly = id(Enemy_MonsterFly)	; 1
EnemyID_GunnerBit = id(Enemy_GunnerBit)	; 2
EnemyID_SensorBit = id(Enemy_SensorBit)	; 3
EnemyID_ProtectBit = id(Enemy_ProtectBit)	; 4
EnemyID_ForcedFly = id(Enemy_ForcedFly)	; 5
EnemyID_Neowhistle = id(Enemy_Neowhistle)	; 6
EnemyID_Seeker = id(Enemy_Seeker)	; 7
EnemyID_Sweeper = id(Enemy_Sweeper)	; 8
EnemyID_Xanafalgue = id(Enemy_Xanafalgue)	; 9
EnemyID_ZoranBult = id(Enemy_ZoranBult)	; $A
EnemyID_Gicefalgue = id(Enemy_Gicefalgue)	; $B
EnemyID_Igglanova = id(Enemy_Igglanova)	; $C
EnemyID_Guilgenova = id(Enemy_Guilgenova)	; $D
EnemyID_Locusta = id(Enemy_Locusta)	; $E
EnemyID_Fanbite = id(Enemy_Fanbite)	; $F
EnemyID_Grasshound = id(Enemy_Grasshound)	; $10
EnemyID_Slave = id(Enemy_Slave)	; $11
EnemyID_Servant = id(Enemy_Servant)	; $12
EnemyID_Blauzen = id(Enemy_Blauzen)	; $13
EnemyID_Silvalt = id(Enemy_Silvalt)	; $14
EnemyID_Goldine = id(Enemy_Goldine)	; $15
EnemyID_Tarantella = id(Enemy_Tarantella)	; $16
EnemyID_ArthroPod = id(Enemy_ArthroPod)	; $17
EnemyID_WorkerPod = id(Enemy_WorkerPod)	; $18
EnemyID_Wiredine = id(Enemy_Wiredine)	; $19
EnemyID_LifeDeletr = id(Enemy_LifeDeletr)	; $1A
EnemyID_BalDuel = id(Enemy_BalDuel)	; $1B
EnemyID_DragerDuel = id(Enemy_DragerDuel)	; $1C
EnemyID_JurafaDuel = id(Enemy_JurafaDuel)	; $1D
EnemyID_Crawler = id(Enemy_Crawler)	; $1E
EnemyID_CarrionCr = id(Enemy_CarrionCr)	; $1F
EnemyID_Caterpillr = id(Enemy_Caterpillr)	; $20
EnemyID_Blob = id(Enemy_Blob)	; $21
EnemyID_ZolSlug = id(Enemy_ZolSlug)	; $22
EnemyID_JrOoze = id(Enemy_JrOoze)	; $23
EnemyID_MetaSlug = id(Enemy_MetaSlug)	; $24
EnemyID_SnowSlug = id(Enemy_SnowSlug)	; $25
EnemyID_FractOoze = id(Enemy_FractOoze)	; $26
EnemyID_Tower = id(Enemy_Tower)	; $27
EnemyID_CRayTube = id(Enemy_CRayTube)	; $28
EnemyID_ArmDrone = id(Enemy_ArmDrone)	; $29
EnemyID_SatMinion = id(Enemy_SatMinion)	; $2A
EnemyID_StarDrone = id(Enemy_StarDrone)	; $2B
EnemyID_FloatMine = id(Enemy_FloatMine)	; $2C
EnemyID_CommndBall = id(Enemy_CommndBall)	; $2D
EnemyID_VopalSphre = id(Enemy_VopalSphre)	; $2E
EnemyID_Warren286 = id(Enemy_Warren286)	; $2F
EnemyID_Siren386 = id(Enemy_Siren386)	; $30
EnemyID_Browren486 = id(Enemy_Browren486)	; $31
EnemyID_FloatMine2 = id(Enemy_FloatMine2)	; $32
EnemyID_Loader = id(Enemy_Loader)	; $33
EnemyID_Debugger = id(Enemy_Debugger)	; $34
EnemyID_Dominator = id(Enemy_Dominator)	; $35
EnemyID_Whistle = id(Enemy_Whistle)	; $36
EnemyID_Tracer = id(Enemy_Tracer)	; $37
EnemyID_SandNewt = id(Enemy_SandNewt)	; $38
EnemyID_Mistralgec = id(Enemy_Mistralgec)	; $39
EnemyID_FlameNewt = id(Enemy_FlameNewt)	; $3A
EnemyID_StoneHeads = id(Enemy_StoneHeads)	; $3B
EnemyID_CrminHeads = id(Enemy_CrminHeads)	; $3C
EnemyID_BlindHeads = id(Enemy_BlindHeads)	; $3D
EnemyID_AbeFrog = id(Enemy_AbeFrog)	; $3E
EnemyID_GerotLux = id(Enemy_GerotLux)	; $3F
EnemyID_DarkMaraud = id(Enemy_DarkMaraud)	; $40
EnemyID_DeathBearr = id(Enemy_DeathBearr)	; $41
EnemyID_ChaosBrngr = id(Enemy_ChaosBrngr)	; $42
EnemyID_Scorpirus = id(Enemy_Scorpirus)	; $43
EnemyID_Rajago = id(Enemy_Rajago)	; $44
EnemyID_BiterFly = id(Enemy_BiterFly)	; $45
EnemyID_ShadowSabr = id(Enemy_ShadowSabr)	; $46
EnemyID_FrostSaber = id(Enemy_FrostSaber)	; $47
EnemyID_BloodSaber = id(Enemy_BloodSaber)	; $48
EnemyID_DimensWorm = id(Enemy_DimensWorm)	; $49
EnemyID_OuterBeast = id(Enemy_OuterBeast)	; $4A
EnemyID_FlattrPlnt = id(Enemy_FlattrPlnt)	; $4B
EnemyID_FlyScreamr = id(Enemy_FlyScreamr)	; $4C
EnemyID_TechPlant = id(Enemy_TechPlant)	; $4D
EnemyID_ToadStool = id(Enemy_ToadStool)	; $4E
EnemyID_Shrieker = id(Enemy_Shrieker)	; $4F
EnemyID_SandWorm = id(Enemy_SandWorm)	; $50
EnemyID_DesrtLeach = id(Enemy_DesrtLeach)	; $51
EnemyID_Leviathan = id(Enemy_Leviathan)	; $52
EnemyID_Ripper = id(Enemy_Ripper)	; $53
EnemyID_BladeRight = id(Enemy_BladeRight)	; $54
EnemyID_Piercer = id(Enemy_Piercer)	; $55
EnemyID_HakenLeft = id(Enemy_HakenLeft)	; $56
EnemyID_TwinArms = id(Enemy_TwinArms)	; $57
EnemyID_SoldrFiend = id(Enemy_SoldrFiend)	; $58
EnemyID_Ismounos = id(Enemy_Ismounos)	; $59
EnemyID_Depcen = id(Enemy_Depcen)	; $5A
EnemyID_HewGilla = id(Enemy_HewGilla)	; $5B
EnemyID_Elmelew = id(Enemy_Elmelew)	; $5C
EnemyID_MiniWorm = id(Enemy_MiniWorm)	; $5D
EnemyID_InfantWorm = id(Enemy_InfantWorm)	; $5E
EnemyID_SnowWorm = id(Enemy_SnowWorm)	; $5F
EnemyID_Centaur = id(Enemy_Centaur)	; $60
EnemyID_KingSaber = id(Enemy_KingSaber)	; $61
EnemyID_DarkRider = id(Enemy_DarkRider)	; $62
EnemyID_TechUser = id(Enemy_TechUser)	; $63
EnemyID_TechMaster = id(Enemy_TechMaster)	; $64
EnemyID_DarkWitch = id(Enemy_DarkWitch)	; $65
EnemyID_Speard = id(Enemy_Speard)	; $66
EnemyID_ZiosGuard = id(Enemy_ZiosGuard)	; $67
EnemyID_Acacia = id(Enemy_Acacia)	; $68
EnemyID_ShadMirage = id(Enemy_ShadMirage)	; $69
EnemyID_Haunt = id(Enemy_Haunt)	; $6A
EnemyID_Spector = id(Enemy_Spector)	; $6B
EnemyID_Phantom = id(Enemy_Phantom)	; $6C
EnemyID_Zombie = id(Enemy_Zombie)	; $6D
EnemyID_Ghoul = id(Enemy_Ghoul)	; $6E
EnemyID_ChaosSorcr = id(Enemy_ChaosSorcr)	; $6F
EnemyID_Illusionst = id(Enemy_Illusionst)	; $70
EnemyID_ImagioMage = id(Enemy_ImagioMage)	; $71
EnemyID_Juza = id(Enemy_Juza)	; $72
EnemyID_Greneris = id(Enemy_Greneris)	; $73
EnemyID_Radhin = id(Enemy_Radhin)	; $74
EnemyID_GyLaguiah = id(Enemy_GyLaguiah)	; $75
EnemyID_LwAddmer = id(Enemy_LwAddmer)	; $76
EnemyID_CulaBellr = id(Enemy_CulaBellr)	; $77
EnemyID_DeVars = id(Enemy_DeVars)	; $78
EnemyID_SaLews = id(Enemy_SaLews)	; $79
EnemyID_DElmLars = id(Enemy_DElmLars)	; $7A
EnemyID_XeAThoul = id(Enemy_XeAThoul)	; $7B
EnemyID_LeFawGan = id(Enemy_LeFawGan)	; $7C
EnemyID_GiLeFarg = id(Enemy_GiLeFarg)	; $7D
EnemyID_Ryre = id(Enemy_Ryre)	; $7E
EnemyID_ReFaze = id(Enemy_ReFaze)	; $7F
EnemyID_Lashiec = id(Enemy_Lashiec)	; $80
EnemyID_CarnivorousTree = id(Enemy_CarnivorousTree)	; $81
EnemyID_DarkForce1 = id(Enemy_DarkForce1)	; $82
EnemyID_DarkForce2 = id(Enemy_DarkForce2)	; $83
EnemyID_DarkForce3 = id(Enemy_DarkForce3)	; $84
EnemyID_ProfoundDarkness1 = id(Enemy_ProfoundDarkness1)	; $85
EnemyID_ProfoundDarkness2 = id(Enemy_ProfoundDarkness2)	; $86
EnemyID_ProfoundDarkness3 = id(Enemy_ProfoundDarkness3)	; $87
EnemyID_SandWorm2 = id(Enemy_SandWorm2)	; $88
EnemyID_FractOoze2 = id(Enemy_FractOoze2)	; $89
EnemyID_ChaosSorcr2 = id(Enemy_ChaosSorcr2)	; $8A
EnemyID_Zio = id(Enemy_Zio)	; $8B
EnemyID_Zio2 = id(Enemy_Zio2)	; $8C
EnemyID_DezoOwl = id(Enemy_DezoOwl)	; $8D
EnemyID_Skytiara = id(Enemy_Skytiara)	; $8E
EnemyID_Owltalon = id(Enemy_Owltalon)	; $8F
EnemyID_SnowMole = id(Enemy_SnowMole)	; $90
EnemyID_RedMole = id(Enemy_RedMole)	; $91
EnemyID_HungryMole = id(Enemy_HungryMole)	; $92
EnemyID_Rappy = id(Enemy_Rappy)	; $93
EnemyID_BlueRappy = id(Enemy_BlueRappy)	; $94
EnemyID_KingRappy = id(Enemy_KingRappy)	; $95
EnemyID_InfantWorm2 = id(Enemy_InfantWorm2)	; $96
EnemyID_Prophallus = id(Enemy_Prophallus)	; $97
EnemyID_Zio3 = id(Enemy_Zio3)	; $98

; Enemy Skills

offset	:=	EnemySkillData
ptrsize	:=	8
idstart	:=	1

EnemySkillID_Nothing = id(EnemySkill_Nothing)	; 1
EnemySkillID_FlameBolt = id(EnemySkill_FlameBolt)	; 2
EnemySkillID_RailGun = id(EnemySkill_RailGun)	; 3
EnemySkillID_LasrCannon = id(EnemySkill_LasrCannon)	; 4
EnemySkillID_Lightning = id(EnemySkill_Lightning)	; 5
EnemySkillID_Fission = id(EnemySkill_Fission)	; 6
EnemySkillID_Fission2 = id(EnemySkill_Fission2)	; 7
EnemySkillID_SpiralBld = id(EnemySkill_SpiralBld)	; 8
EnemySkillID_MotrCannon = id(EnemySkill_MotrCannon)	; 9
EnemySkillID_TwinClaw = id(EnemySkill_TwinClaw)	; $A
EnemySkillID_StasisBall = id(EnemySkill_StasisBall)	; $B
EnemySkillID_Combine = id(EnemySkill_Combine)	; $C
EnemySkillID_Combine2 = id(EnemySkill_Combine2)	; $D
EnemySkillID_MicroMissl = id(EnemySkill_MicroMissl)	; $E
EnemySkillID_FlamLaunch = id(EnemySkill_FlamLaunch)	; $F
EnemySkillID_Thread = id(EnemySkill_Thread)	; $10
EnemySkillID_Poison = id(EnemySkill_Poison)	; $11
EnemySkillID_Fusion = id(EnemySkill_Fusion)	; $12
EnemySkillID_CellSplit = id(EnemySkill_CellSplit)	; $13
EnemySkillID_Warning = id(EnemySkill_Warning)	; $14
EnemySkillID_ChargCnnon = id(EnemySkill_ChargCnnon)	; $15
EnemySkillID_Flash = id(EnemySkill_Flash)	; $16
EnemySkillID_Waiting = id(EnemySkill_Waiting)	; $17
EnemySkillID_Explosion = id(EnemySkill_Explosion)	; $18
EnemySkillID_Detonation = id(EnemySkill_Detonation)	; $19
EnemySkillID_CyanicBomb = id(EnemySkill_CyanicBomb)	; $1A
EnemySkillID_Fission3 = id(EnemySkill_Fission3)	; $1B
EnemySkillID_FlareShot = id(EnemySkill_FlareShot)	; $1C
EnemySkillID_Barrier = id(EnemySkill_Barrier)	; $1D
EnemySkillID_Spark = id(EnemySkill_Spark)	; $1E
EnemySkillID_DblSlash = id(EnemySkill_DblSlash)	; $1F
EnemySkillID_PhononMasr = id(EnemySkill_PhononMasr)	; $20
EnemySkillID_FireBreath = id(EnemySkill_FireBreath)	; $21
EnemySkillID_RayBreath = id(EnemySkill_RayBreath)	; $22
EnemySkillID_SuperSonic = id(EnemySkill_SuperSonic)	; $23
EnemySkillID_PoisonMist = id(EnemySkill_PoisonMist)	; $24
EnemySkillID_SleepGas = id(EnemySkill_SleepGas)	; $25
EnemySkillID_Shift = id(EnemySkill_Shift)	; $26
EnemySkillID_Saner = id(EnemySkill_Saner)	; $27
EnemySkillID_Doran = id(EnemySkill_Doran)	; $28
EnemySkillID_Seals = id(EnemySkill_Seals)	; $29
EnemySkillID_Rimit = id(EnemySkill_Rimit)	; $2A
EnemySkillID_Needle = id(EnemySkill_Needle)	; $2B
EnemySkillID_Airslash = id(EnemySkill_Airslash)	; $2C
EnemySkillID_Deban = id(EnemySkill_Deban)	; $2D
EnemySkillID_Giwat = id(EnemySkill_Giwat)	; $2E
EnemySkillID_Vol = id(EnemySkill_Vol)	; $2F
EnemySkillID_Distortion = id(EnemySkill_Distortion)	; $30
EnemySkillID_Gra = id(EnemySkill_Gra)	; $31
EnemySkillID_Gigra = id(EnemySkill_Gigra)	; $32
EnemySkillID_AcidBreath = id(EnemySkill_AcidBreath)	; $33
EnemySkillID_Voice = id(EnemySkill_Voice)	; $34
EnemySkillID_Gizan = id(EnemySkill_Gizan)	; $35
EnemySkillID_StrngLight = id(EnemySkill_StrngLight)	; $36
EnemySkillID_SandStorm = id(EnemySkill_SandStorm)	; $37
EnemySkillID_Earthquake = id(EnemySkill_Earthquake)	; $38
EnemySkillID_Maelstrom = id(EnemySkill_Maelstrom)	; $39
EnemySkillID_Combine3 = id(EnemySkill_Combine3)	; $3A
EnemySkillID_Combine4 = id(EnemySkill_Combine4)	; $3B
EnemySkillID_BladeShine = id(EnemySkill_BladeShine)	; $3C
EnemySkillID_HakenBolt = id(EnemySkill_HakenBolt)	; $3D
EnemySkillID_Gires = id(EnemySkill_Gires)	; $3E
EnemySkillID_FlodBreath = id(EnemySkill_FlodBreath)	; $3F
EnemySkillID_Wat = id(EnemySkill_Wat)	; $40
EnemySkillID_Nothing2 = id(EnemySkill_Nothing2)	; $41
EnemySkillID_RaySpear = id(EnemySkill_RaySpear)	; $42
EnemySkillID_ThrowLancr = id(EnemySkill_ThrowLancr)	; $43
EnemySkillID_Foi = id(EnemySkill_Foi)	; $44
EnemySkillID_Res = id(EnemySkill_Res)	; $45
EnemySkillID_Sar = id(EnemySkill_Sar)	; $46
EnemySkillID_Zan = id(EnemySkill_Zan)	; $47
EnemySkillID_Gifoi = id(EnemySkill_Gifoi)	; $48
EnemySkillID_Gisar = id(EnemySkill_Gisar)	; $49
EnemySkillID_StarDust = id(EnemySkill_StarDust)	; $4A
EnemySkillID_ShadowBind = id(EnemySkill_ShadowBind)	; $4B
EnemySkillID_EvilEye = id(EnemySkill_EvilEye)	; $4C
EnemySkillID_Corrsion = id(EnemySkill_Corrsion)	; $4D
EnemySkillID_DthSpell = id(EnemySkill_DthSpell)	; $4E
EnemySkillID_Hewn = id(EnemySkill_Hewn)	; $4F
EnemySkillID_BadSmell = id(EnemySkill_BadSmell)	; $50
EnemySkillID_MindBlst = id(EnemySkill_MindBlst)	; $51
EnemySkillID_Tandle = id(EnemySkill_Tandle)	; $52
EnemySkillID_Nightmare = id(EnemySkill_Nightmare)	; $53
EnemySkillID_BlackWave = id(EnemySkill_BlackWave)	; $54
EnemySkillID_Legeon = id(EnemySkill_Legeon)	; $55
EnemySkillID_ForceFlash = id(EnemySkill_ForceFlash)	; $56
EnemySkillID_Gelun = id(EnemySkill_Gelun)	; $57
EnemySkillID_LghtBreath = id(EnemySkill_LghtBreath)	; $58
EnemySkillID_DisruptArm = id(EnemySkill_DisruptArm)	; $59
EnemySkillID_Flaeli = id(EnemySkill_Flaeli)	; $5A
EnemySkillID_Bindwa = id(EnemySkill_Bindwa)	; $5B
EnemySkillID_ThndrBlast = id(EnemySkill_ThndrBlast)	; $5C
EnemySkillID_Tandil = id(EnemySkill_Tandil)	; $5D
EnemySkillID_Megid = id(EnemySkill_Megid)	; $5E
EnemySkillID_ThndHalbrt = id(EnemySkill_ThndHalbrt)	; $5F
EnemySkillID_Posession = id(EnemySkill_Posession)	; $60
EnemySkillID_AnothrGate = id(EnemySkill_AnothrGate)	; $61
EnemySkillID_Reinforce = id(EnemySkill_Reinforce)	; $62
EnemySkillID_Burstroc = id(EnemySkill_Burstroc)	; $63
EnemySkillID_ShdwBreath = id(EnemySkill_ShdwBreath)	; $64
EnemySkillID_LightShowr = id(EnemySkill_LightShowr)	; $65
EnemySkillID_DestrocRay = id(EnemySkill_DestrocRay)	; $66
EnemySkillID_Nothing3 = id(EnemySkill_Nothing3)	; $67
EnemySkillID_Nothing4 = id(EnemySkill_Nothing4)	; $68
EnemySkillID_Canceling = id(EnemySkill_Canceling)	; $69
EnemySkillID_WindStorm = id(EnemySkill_WindStorm)	; $6A
EnemySkillID_MagBarrir = id(EnemySkill_MagBarrir)	; $6B
EnemySkillID_BlackWave2 = id(EnemySkill_BlackWave2)	; $6C
EnemySkillID_RoundEyes = id(EnemySkill_RoundEyes)	; $6D
EnemySkillID_LovelEyes = id(EnemySkill_LovelEyes)	; $6E
EnemySkillID_Casting = id(EnemySkill_Casting)	; $6F
EnemySkillID_BlackWave3 = id(EnemySkill_BlackWave3)	; $70

; Music

offset	:=	MusicPtrs
ptrsize	:=	4
idstart	:=	$81

MusicID_TonoeDePon = id(PtrMusic_TonoeDePon)	; $81
MusicID_Inn = id(PtrMusic_Inn)	; $82
MusicID_MotabiaVillage = id(PtrMusic_MotabiaVillage)	; $83
MusicID_MotabiaTown = id(PtrMusic_MotabiaTown)	; $84
MusicID_OrganicBeat = id(PtrMusic_OrganicBeat)	; $85
MusicID_DezorisTown1 = id(PtrMusic_DezorisTown1)	; $86
MusicID_NowOnSale = id(PtrMusic_NowOnSale)	; $87
MusicID_BehindTheCircuit = id(PtrMusic_BehindTheCircuit)	; $88
MusicID_MachineCenter = id(PtrMusic_MachineCenter)	; $89
MusicID_InTheCave = id(PtrMusic_InTheCave)	; $8A
MusicID_Winners = id(PtrMusic_Winners)	; $8B
MusicID_FieldMotabia = id(PtrMusic_FieldMotabia)	; $8C
MusicID_LandMaster = id(PtrMusic_LandMaster)	; $8D
MusicID_RequiemForLutz = id(PtrMusic_RequiemForLutz)	; $8E
MusicID_MeetThemHeadOn = id(PtrMusic_MeetThemHeadOn)	; $8F
MusicID_RyucrossField = id(PtrMusic_RyucrossField)	; $90
MusicID_DungeonArrange1 = id(PtrMusic_DungeonArrange1)	; $91
MusicID_Fal = id(PtrMusic_Fal)	; $92
MusicID_TempleNgangbius = id(PtrMusic_TempleNgangbius)	; $93
MusicID_Thray = id(PtrMusic_Thray)	; $94
MusicID_DefeatAtABlow = id(PtrMusic_DefeatAtABlow)	; $95
MusicID_CyberneticCarnival = id(PtrMusic_CyberneticCarnival)	; $96
MusicID_TerribleSight = id(PtrMusic_TerribleSight)	; $97
MusicID_EdgeOfDarkness = id(PtrMusic_EdgeOfDarkness)	; $98
MusicID_DezorisField1 = id(PtrMusic_DezorisField1)	; $99
MusicID_Tower = id(PtrMusic_Tower)	; $9A
MusicID_TakeOffLandeel = id(PtrMusic_TakeOffLandeel)	; $9B
MusicID_DezorisTown2 = id(PtrMusic_DezorisTown2)	; $9C
MusicID_DezorisField2 = id(PtrMusic_DezorisField2)	; $9D
MusicID_AHappySettlement = id(PtrMusic_AHappySettlement)	; $9E
MusicID_Suspicion = id(PtrMusic_Suspicion)	; $9F
MusicID_TheKingOfTerrors = id(PtrMusic_TheKingOfTerrors)	; $A0
MusicID_TheAgeOfFables = id(PtrMusic_TheAgeOfFables)	; $A1
MusicID_Abyss = id(PtrMusic_Abyss)	; $A2
MusicID_EnemyAppearance = id(PtrMusic_EnemyAppearance)	; $A3
MusicID_HerLastBreath = id(PtrMusic_HerLastBreath)	; $A4
MusicID_Pain = id(PtrMusic_Pain)	; $A5
MusicID_JijyNoRag = id(PtrMusic_JijyNoRag)	; $A6
MusicID_DungeonArrange2Cont = id(PtrMusic_DungeonArrange2Cont)	; $A7
MusicID_TheBlackBlood = id(PtrMusic_TheBlackBlood)	; $A8
MusicID_RedAlert = id(PtrMusic_RedAlert)	; $A9
MusicID_Laughter = id(PtrMusic_Laughter)	; $AA
MusicID_Mystery = id(PtrMusic_Mystery)	; $AB
MusicID_EndOfTheMillennium = id(PtrMusic_EndOfTheMillennium)	; $AC
MusicID_Explosion = id(PtrMusic_Explosion)	; $AD
MusicID_StaffRoll = id(PtrMusic_StaffRoll)	; $AE
MusicID_ThePromisingFuture1 = id(PtrMusic_ThePromisingFuture1)	; $AF
MusicID_PaoPao = id(PtrMusic_PaoPao)	; $B0
MusicID_DungeonArrange2 = id(PtrMusic_DungeonArrange2)	; $B1
MusicID_ThePromisingFuture2 = id(PtrMusic_ThePromisingFuture2)	; $B2
MusicID_DezorisDeDon = id(PtrMusic_DezorisDeDon)	; $B3
MusicID_Ooze = id(PtrMusic_Ooze)	; $B4

; SFX

offset	:=	SFXPtrs
ptrsize	:=	4
idstart	:=	$B5

SFXID_Rod = id(PtrSFX_Rod)	; $B5
SFXID_Shot = id(PtrSFX_Shot)	; $B6
SFXID_Slasher = id(PtrSFX_Slasher)	; $B7
SFXID_AttackMiss = id(PtrSFX_AttackMiss)	; $B8
SFXID_EnemyKilled = id(PtrSFX_EnemyKilled)	; $B9
SFXID_EnemyAttack1 = id(PtrSFX_EnemyAttack1)	; $BA
SFXID_TechCast = id(PtrSFX_TechCast)	; $BB
SFXID_BuffCast = id(PtrSFX_BuffCast)	; $BC
SFXID_HealTechCast = id(PtrSFX_HealTechCast)	; $BD
SFXID_Foi = id(PtrSFX_Foi)	; $BE
SFXID_Legeon = id(PtrSFX_Legeon)	; $BF
SFXID_Megid = id(PtrSFX_Megid)	; $C0
SFXID_Phonon = id(PtrSFX_Phonon)	; $C1
SFXID_FireBreath = id(PtrSFX_FireBreath)	; $C2
SFXID_Efess = id(PtrSFX_Efess)	; $C3
SFXID_Moonshad = id(PtrSFX_Moonshad)	; $C4
SFXID_LaserAttack = id(PtrSFX_LaserAttack)	; $C5
SFXID_Zan = id(PtrSFX_Zan)	; $C6
SFXID_Gra = id(PtrSFX_Gra)	; $C7
SFXID_Vol = id(PtrSFX_Vol)	; $C8
SFXID_Saner = id(PtrSFX_Saner)	; $C9
SFXID_Rimit = id(PtrSFX_Rimit)	; $CA
SFXID_Brose = id(PtrSFX_Brose)	; $CB
SFXID_Res = id(PtrSFX_Res)	; $CC
SFXID_Recovery = id(PtrSFX_Recovery)	; $CD
SFXID_Tandle = id(PtrSFX_Tandle)	; $CE
SFXID_AndroidSkillImplant = id(PtrSFX_AndroidSkillImplant)	; $CF
SFXID_Rifle = id(PtrSFX_Rifle)	; $D0
SFXID_SleepGas = id(PtrSFX_SleepGas)	; $D1
SFXID_Eliminat = id(PtrSFX_Eliminat)	; $D2
SFXID_Spark = id(PtrSFX_Spark)	; $D3
SFXID_WarCry = id(PtrSFX_WarCry)	; $D4
SFXID_MoleAttack = id(PtrSFX_MoleAttack)	; $D5
SFXID_MechEnemyAlarm = id(PtrSFX_MechEnemyAlarm)	; $D6
SFXID_EnemyAttack3 = id(PtrSFX_EnemyAttack3)	; $D7
SFXID_EnemyAttack4 = id(PtrSFX_EnemyAttack4)	; $D8
SFXID_Fusion = id(PtrSFX_Fusion)	; $D9
SFXID_EnemyAttack5 = id(PtrSFX_EnemyAttack5)	; $DA
SFXID_Alarm = id(PtrSFX_Alarm)	; $DB
SFXID_Deban = id(PtrSFX_Deban)	; $DC
SFXID_GraveOpening = id(PtrSFX_GraveOpening)	; $DD
SFXID_Teleport = id(PtrSFX_Teleport)	; $DE
SFXID_Stairs = id(PtrSFX_Stairs)	; $DF
SFXID_RidingElevator = id(PtrSFX_RidingElevator)	; $E0
SFXID_ChestOpened = id(PtrSFX_ChestOpened)	; $E1
SFXID_DoorOpened = id(PtrSFX_DoorOpened)	; $E2
SFXID_SpaceshipPropelled = id(PtrSFX_SpaceshipPropelled)	; $E3
SFXID_PowerDown = id(PtrSFX_PowerDown)	; $E4
SFXID_ElevatorOpen = id(PtrSFX_ElevatorOpen)	; $E5
SFXID_BarrierBroken = id(PtrSFX_BarrierBroken)	; $E6
SFXID_ConveyorBelt = id(PtrSFX_ConveyorBelt)	; $E7
SFXID_Claw = id(PtrSFX_Claw)	; $E8
SFXID_Unused1 = id(PtrSFX_Unused1)	; $E9
SFXID_BlackWave = id(PtrSFX_BlackWave)	; $EA
SFXID_EnemySpellCast = id(PtrSFX_EnemySpellCast)	; $EB
SFXID_Lightning = id(PtrSFX_Lightning)	; $EC
SFXID_AnotherGate = id(PtrSFX_AnotherGate)	; $ED
SFXID_IceBroken = id(PtrSFX_IceBroken)	; $EE
SFXID_FallingIntoHole = id(PtrSFX_FallingIntoHole)	; $EF
SFXID_Telepipe = id(PtrSFX_Telepipe)	; $F0
SFXID_Souvenir = id(PtrSFX_Souvenir)	; $F1
SFXID_MovingCursor = id(PtrSFX_MovingCursor)	; $F2
SFXID_Selection = id(PtrSFX_Selection)	; $F3
SFXID_Surprise = id(PtrSFX_Surprise)	; $F4
SFXID_Sword = id(PtrSFX_Sword)	; $F5
SFXID_Nothing = id(PtrSFX_Nothing)	; $F6
SFXID_Unused2 = id(PtrSFX_Unused2)	; $F7

; Special SFX

offset	:=	SpcSFXPtrs
ptrsize	:=	4
idstart	:=	$F8

SpcSFXID_SpaceshipRadar = id(PtrSpcSFX_SpaceshipRadar)	; $F8
SpcSFXID_LandRover = id(PtrSpcSFX_LandRover)	; $F9
SpcSFXID_Hydrofoil = id(PtrSpcSFX_Hydrofoil)	; $FA

Sound_StopMusic = $FB
Sound_StopSFX = $FC
Sound_StopSpcSFX = $FD
Sound_StopAll = $FE


; Field Maps

offset	:=	FieldMapPtrs
ptrsize	:=	4
idstart	:=	0

MapID_Motavia = id(PtrMap_Motavia)	; 0
MapID_Dezolis = id(PtrMap_Dezolis)	; 1
MapID_Rykros = id(PtrMap_Rykros)	; 2
MapID_Null3 = id(PtrMap_Null3)	; 3
MapID_Null4 = id(PtrMap_Null4)	; 4
MapID_Null5 = id(PtrMap_Null5)	; 5
MapID_Null6 = id(PtrMap_Null6)	; 6
MapID_Null7 = id(PtrMap_Null7)	; 7
MapID_Null8 = id(PtrMap_Null8)	; 8
MapID_Null9 = id(PtrMap_Null9)	; 9
MapID_NullA = id(PtrMap_NullA)	; $A
MapID_NullB = id(PtrMap_NullB)	; $B
MapID_NullC = id(PtrMap_NullC)	; $C
MapID_NullD = id(PtrMap_NullD)	; $D
MapID_NullE = id(PtrMap_NullE)	; $E
MapID_NullF = id(PtrMap_NullF)	; $F
MapID_Piata = id(PtrMap_Piata)	; $10
MapID_PiataAcademy = id(PtrMap_PiataAcademy)	; $11
MapID_PiataAcademyNearBasement = id(PtrMap_PiataAcademyNearBasement)	; $12
MapID_PiataAcademy_F1 = id(PtrMap_PiataAcademy_F1)	; $13
MapID_AcademyPrincipalOffice = id(PtrMap_AcademyPrincipalOffice)	; $14
MapID_AcademyBasement = id(PtrMap_AcademyBasement)	; $15
MapID_AcademyBasement_B1 = id(PtrMap_AcademyBasement_B1)	; $16
MapID_AcademyBasement_B2 = id(PtrMap_AcademyBasement_B2)	; $17
MapID_PiataDorm = id(PtrMap_PiataDorm)	; $18
MapID_PiataInn = id(PtrMap_PiataInn)	; $19
MapID_PiataHouse1 = id(PtrMap_PiataHouse1)	; $1A
MapID_PiataItemShop = id(PtrMap_PiataItemShop)	; $1B
MapID_PiataHouse2 = id(PtrMap_PiataHouse2)	; $1C
MapID_Mile = id(PtrMap_Mile)	; $1D
MapID_MileDead = id(PtrMap_MileDead)	; $1E
MapID_MileWeaponShop = id(PtrMap_MileWeaponShop)	; $1F
MapID_MileHouse1 = id(PtrMap_MileHouse1)	; $20
MapID_MileItemShop = id(PtrMap_MileItemShop)	; $21
MapID_MileHouse2 = id(PtrMap_MileHouse2)	; $22
MapID_MileInn = id(PtrMap_MileInn)	; $23
MapID_Zema = id(PtrMap_Zema)	; $24
MapID_ZemaHouse1 = id(PtrMap_ZemaHouse1)	; $25
MapID_ZemaWeaponShop = id(PtrMap_ZemaWeaponShop)	; $26
MapID_ZemaInn = id(PtrMap_ZemaInn)	; $27
MapID_ZemaHouse2 = id(PtrMap_ZemaHouse2)	; $28
MapID_ZemaHouse2_B1 = id(PtrMap_ZemaHouse2_B1)	; $29
MapID_ZemaItemShop = id(PtrMap_ZemaItemShop)	; $2A
MapID_BirthValley = id(PtrMap_BirthValley)	; $2B
MapID_BirthValley_B1 = id(PtrMap_BirthValley_B1)	; $2C
MapID_ValleyMazeUnused = id(PtrMap_ValleyMazeUnused)	; $2D
MapID_Null2E = id(PtrMap_Null2E)	; $2E
MapID_Null2F = id(PtrMap_Null2F)	; $2F
MapID_Null30 = id(PtrMap_Null30)	; $30
MapID_Null31 = id(PtrMap_Null31)	; $31
MapID_Null32 = id(PtrMap_Null32)	; $32
MapID_Null33 = id(PtrMap_Null33)	; $33
MapID_Null34 = id(PtrMap_Null34)	; $34
MapID_Null35 = id(PtrMap_Null35)	; $35
MapID_Null36 = id(PtrMap_Null36)	; $36
MapID_Null37 = id(PtrMap_Null37)	; $37
MapID_Null38 = id(PtrMap_Null38)	; $38
MapID_Krup = id(PtrMap_Krup)	; $39
MapID_KrupKindergarten = id(PtrMap_KrupKindergarten)	; $3A
MapID_KrupWeaponShop = id(PtrMap_KrupWeaponShop)	; $3B
MapID_KrupItemShop = id(PtrMap_KrupItemShop)	; $3C
MapID_KrupHouse = id(PtrMap_KrupHouse)	; $3D
MapID_KrupInn = id(PtrMap_KrupInn)	; $3E
MapID_KrupInn_F1 = id(PtrMap_KrupInn_F1)	; $3F
MapID_Molcum = id(PtrMap_Molcum)	; $40
MapID_Tonoe = id(PtrMap_Tonoe)	; $41
MapID_TonoeStorageRoom = id(PtrMap_TonoeStorageRoom)	; $42
MapID_TonoeGryzHouse = id(PtrMap_TonoeGryzHouse)	; $43
MapID_TonoeHouse1 = id(PtrMap_TonoeHouse1)	; $44
MapID_TonoeHouse2 = id(PtrMap_TonoeHouse2)	; $45
MapID_TonoeInn = id(PtrMap_TonoeInn)	; $46
MapID_TonoeBasement = id(PtrMap_TonoeBasement)	; $47
MapID_TonoeBasement_B1 = id(PtrMap_TonoeBasement_B1)	; $48
MapID_TonoeBasement_B2 = id(PtrMap_TonoeBasement_B2)	; $49
MapID_TonoeBasement_B3 = id(PtrMap_TonoeBasement_B3)	; $4A
MapID_Nalya = id(PtrMap_Nalya)	; $4B
MapID_NalyaHouse1 = id(PtrMap_NalyaHouse1)	; $4C
MapID_NalyaHouse2 = id(PtrMap_NalyaHouse2)	; $4D
MapID_NalyaItemShop = id(PtrMap_NalyaItemShop)	; $4E
MapID_NalyaHouse3 = id(PtrMap_NalyaHouse3)	; $4F
MapID_NalyaHouse4 = id(PtrMap_NalyaHouse4)	; $50
MapID_NalyaHouse5 = id(PtrMap_NalyaHouse5)	; $51
MapID_NalyaInn = id(PtrMap_NalyaInn)	; $52
MapID_NalyaInn_F1 = id(PtrMap_NalyaInn_F1)	; $53
MapID_Aiedo = id(PtrMap_Aiedo)	; $54
MapID_AiedoBakery = id(PtrMap_AiedoBakery)	; $55
MapID_AiedoBakery_B1 = id(PtrMap_AiedoBakery_B1)	; $56
MapID_HuntersGuild = id(PtrMap_HuntersGuild)	; $57
MapID_HuntersGuildStorage = id(PtrMap_HuntersGuildStorage)	; $58
MapID_StripClubDressingRoom = id(PtrMap_StripClubDressingRoom)	; $59
MapID_StripClub = id(PtrMap_StripClub)	; $5A
MapID_AiedoWeaponShop = id(PtrMap_AiedoWeaponShop)	; $5B
MapID_AiedoPrison = id(PtrMap_AiedoPrison)	; $5C
MapID_AiedoHouse1 = id(PtrMap_AiedoHouse1)	; $5D
MapID_ChazHouse = id(PtrMap_ChazHouse)	; $5E
MapID_AiedoHouse2 = id(PtrMap_AiedoHouse2)	; $5F
MapID_AiedoHouse3 = id(PtrMap_AiedoHouse3)	; $60
MapID_AiedoHouse4 = id(PtrMap_AiedoHouse4)	; $61
MapID_AiedoHouse5 = id(PtrMap_AiedoHouse5)	; $62
MapID_AiedoSupermarket = id(PtrMap_AiedoSupermarket)	; $63
MapID_AiedoPub = id(PtrMap_AiedoPub)	; $64
MapID_RockyHouse = id(PtrMap_RockyHouse)	; $65
MapID_AiedoHouse6 = id(PtrMap_AiedoHouse6)	; $66
MapID_AiedoHouse7 = id(PtrMap_AiedoHouse7)	; $67
MapID_Kadary = id(PtrMap_Kadary)	; $68
MapID_KadaryChurch = id(PtrMap_KadaryChurch)	; $69
MapID_KadaryPub = id(PtrMap_KadaryPub)	; $6A
MapID_KadaryPub_F1 = id(PtrMap_KadaryPub_F1)	; $6B
MapID_KadaryStorageRoom = id(PtrMap_KadaryStorageRoom)	; $6C
MapID_KadaryHouse1 = id(PtrMap_KadaryHouse1)	; $6D
MapID_KadaryHouse2 = id(PtrMap_KadaryHouse2)	; $6E
MapID_KadaryHouse3 = id(PtrMap_KadaryHouse3)	; $6F
MapID_KadaryItemShop = id(PtrMap_KadaryItemShop)	; $70
MapID_KadaryInn = id(PtrMap_KadaryInn)	; $71
MapID_KadaryInn_F1 = id(PtrMap_KadaryInn_F1)	; $72
MapID_Monsen = id(PtrMap_Monsen)	; $73
MapID_MonsenInn = id(PtrMap_MonsenInn)	; $74
MapID_MonsenHouse1 = id(PtrMap_MonsenHouse1)	; $75
MapID_MonsenHouse2 = id(PtrMap_MonsenHouse2)	; $76
MapID_MonsenHouse3 = id(PtrMap_MonsenHouse3)	; $77
MapID_MonsenHouse4 = id(PtrMap_MonsenHouse4)	; $78
MapID_MonsenHouse5 = id(PtrMap_MonsenHouse5)	; $79
MapID_MonsenItemShop = id(PtrMap_MonsenItemShop)	; $7A
MapID_Termi = id(PtrMap_Termi)	; $7B
MapID_TermiItemShop = id(PtrMap_TermiItemShop)	; $7C
MapID_TermiHouse1 = id(PtrMap_TermiHouse1)	; $7D
MapID_TermiWeaponShop = id(PtrMap_TermiWeaponShop)	; $7E
MapID_TermiInn = id(PtrMap_TermiInn)	; $7F
MapID_TermiHouse2 = id(PtrMap_TermiHouse2)	; $80
MapID_Passageway = id(PtrMap_Passageway)	; $81
MapID_ZioFort = id(PtrMap_ZioFort)	; $82
MapID_ZioFort_Part2 = id(PtrMap_ZioFort_Part2)	; $83
MapID_ZioFort_F1 = id(PtrMap_ZioFort_F1)	; $84
MapID_ZioFort_F2West = id(PtrMap_ZioFort_F2West)	; $85
MapID_ZioFortWestTunnel = id(PtrMap_ZioFortWestTunnel)	; $86
MapID_ZioFortJuzaRoom = id(PtrMap_ZioFortJuzaRoom)	; $87
MapID_ZioFortEastTunnel = id(PtrMap_ZioFortEastTunnel)	; $88
MapID_ZioFort_F2East = id(PtrMap_ZioFort_F2East)	; $89
MapID_ZioFort_F3 = id(PtrMap_ZioFort_F3)	; $8A
MapID_ZioFort_F4 = id(PtrMap_ZioFort_F4)	; $8B
MapID_LadeaTower = id(PtrMap_LadeaTower)	; $8C
MapID_LadeaTower_F1 = id(PtrMap_LadeaTower_F1)	; $8D
MapID_LadeaTower_F2 = id(PtrMap_LadeaTower_F2)	; $8E
MapID_LadeaTower_F3 = id(PtrMap_LadeaTower_F3)	; $8F
MapID_LadeaTower_F4 = id(PtrMap_LadeaTower_F4)	; $90
MapID_LadeaTower_F5 = id(PtrMap_LadeaTower_F5)	; $91
MapID_IslandCave = id(PtrMap_IslandCave)	; $92
MapID_IslandCave_F1 = id(PtrMap_IslandCave_F1)	; $93
MapID_IslandCave_F1_Part2 = id(PtrMap_IslandCave_F1_Part2)	; $94
MapID_IslandCave_Part2 = id(PtrMap_IslandCave_Part2)	; $95
MapID_IslandCave_B1 = id(PtrMap_IslandCave_B1)	; $96
MapID_IslandCave_F2 = id(PtrMap_IslandCave_F2)	; $97
MapID_IslandCave_F3 = id(PtrMap_IslandCave_F3)	; $98
MapID_SoldiersTempleOutside = id(PtrMap_SoldiersTempleOutside)	; $99
MapID_SoldiersTemple = id(PtrMap_SoldiersTemple)	; $9A
MapID_ValleyMaze = id(PtrMap_ValleyMaze)	; $9B
MapID_ValleyMaze_Part2 = id(PtrMap_ValleyMaze_Part2)	; $9C
MapID_ValleyMaze_Part3 = id(PtrMap_ValleyMaze_Part3)	; $9D
MapID_ValleyMaze_Part4 = id(PtrMap_ValleyMaze_Part4)	; $9E
MapID_ValleyMaze_Part5 = id(PtrMap_ValleyMaze_Part5)	; $9F
MapID_ValleyMaze_Part6 = id(PtrMap_ValleyMaze_Part6)	; $A0
MapID_ValleyMaze_Part7 = id(PtrMap_ValleyMaze_Part7)	; $A1
MapID_BioPlant = id(PtrMap_BioPlant)	; $A2
MapID_BioPlant_Part2 = id(PtrMap_BioPlant_Part2)	; $A3
MapID_BioPlant_Part3 = id(PtrMap_BioPlant_Part3)	; $A4
MapID_NullA5 = id(PtrMap_NullA5)	; $A5
MapID_BioPlant_B1 = id(PtrMap_BioPlant_B1)	; $A6
MapID_BioPlant_B2 = id(PtrMap_BioPlant_B2)	; $A7
MapID_BioPlant_B2_Part2 = id(PtrMap_BioPlant_B2_Part2)	; $A8
MapID_BioPlant_B3 = id(PtrMap_BioPlant_B3)	; $A9
MapID_BioPlant_B3_Part2 = id(PtrMap_BioPlant_B3_Part2)	; $AA
MapID_BioPlant_B4 = id(PtrMap_BioPlant_B4)	; $AB
MapID_BioPlant_B4_Part2 = id(PtrMap_BioPlant_B4_Part2)	; $AC
MapID_BioPlant_B4_Part3 = id(PtrMap_BioPlant_B4_Part3)	; $AD
MapID_Wreckage = id(PtrMap_Wreckage)	; $AE
MapID_Wreckage_Part2 = id(PtrMap_Wreckage_Part2)	; $AF
MapID_Wreckage_Part3 = id(PtrMap_Wreckage_Part3)	; $B0
MapID_Wreckage_F1 = id(PtrMap_Wreckage_F1)	; $B1
MapID_Wreckage_F1_Part2 = id(PtrMap_Wreckage_F1_Part2)	; $B2
MapID_Wreckage_F2 = id(PtrMap_Wreckage_F2)	; $B3
MapID_Wreckage_F2_Part2 = id(PtrMap_Wreckage_F2_Part2)	; $B4
MapID_Wreckage_F2_Part3 = id(PtrMap_Wreckage_F2_Part3)	; $B5
MapID_Wreckage_F2_Part4 = id(PtrMap_Wreckage_F2_Part4)	; $B6
MapID_MachineCenter = id(PtrMap_MachineCenter)	; $B7
MapID_MachineCenter_B1 = id(PtrMap_MachineCenter_B1)	; $B8
MapID_MachineCenter_B1_Part2 = id(PtrMap_MachineCenter_B1_Part2)	; $B9
MapID_PlateSystem = id(PtrMap_PlateSystem)	; $BA
MapID_PlateSystem_F1 = id(PtrMap_PlateSystem_F1)	; $BB
MapID_PlateSystem_F2 = id(PtrMap_PlateSystem_F2)	; $BC
MapID_PlateSystem_F3 = id(PtrMap_PlateSystem_F3)	; $BD
MapID_PlateSystem_F4 = id(PtrMap_PlateSystem_F4)	; $BE
MapID_MotaSpaceport = id(PtrMap_MotaSpaceport)	; $BF
MapID_ClimCenter = id(PtrMap_ClimCenter)	; $C0
MapID_ClimCenter_F1 = id(PtrMap_ClimCenter_F1)	; $C1
MapID_ClimCenter_F2 = id(PtrMap_ClimCenter_F2)	; $C2
MapID_ClimCenter_F3 = id(PtrMap_ClimCenter_F3)	; $C3
MapID_WeaponPlant = id(PtrMap_WeaponPlant)	; $C4
MapID_WeaponPlant_F1 = id(PtrMap_WeaponPlant_F1)	; $C5
MapID_WeaponPlant_F2 = id(PtrMap_WeaponPlant_F2)	; $C6
MapID_WeaponPlant_F3 = id(PtrMap_WeaponPlant_F3)	; $C7
MapID_VahalFort = id(PtrMap_VahalFort)	; $C8
MapID_VahalFort_F1 = id(PtrMap_VahalFort_F1)	; $C9
MapID_VahalFort_F2 = id(PtrMap_VahalFort_F2)	; $CA
MapID_VahalFort_F3 = id(PtrMap_VahalFort_F3)	; $CB
MapID_Nurvus_Part2 = id(PtrMap_Nurvus_Part2)	; $CC
MapID_Nurvus_Part3 = id(PtrMap_Nurvus_Part3)	; $CD
MapID_Nurvus_B1 = id(PtrMap_Nurvus_B1)	; $CE
MapID_Nurvus_B2 = id(PtrMap_Nurvus_B2)	; $CF
MapID_Nurvus_B3 = id(PtrMap_Nurvus_B3)	; $D0
MapID_Nurvus_B1Tunnel = id(PtrMap_Nurvus_B1Tunnel)	; $D1
MapID_Nurvus_B4 = id(PtrMap_Nurvus_B4)	; $D2
MapID_Nurvus_B4_Part2 = id(PtrMap_Nurvus_B4_Part2)	; $D3
MapID_DezoSpaceport = id(PtrMap_DezoSpaceport)	; $D4
MapID_Nurvus_B5 = id(PtrMap_Nurvus_B5)	; $D5
MapID_Nurvus_B3Tunnel = id(PtrMap_Nurvus_B3Tunnel)	; $D6
MapID_Nurvus = id(PtrMap_Nurvus)	; $D7
MapID_ValleyMazeOutside = id(PtrMap_ValleyMazeOutside)	; $D8
MapID_ValleyMazeOutside2 = id(PtrMap_ValleyMazeOutside2)	; $D9
MapID_PassagewayNearAiedo = id(PtrMap_PassagewayNearAiedo)	; $DA
MapID_PassagewayNearKadary = id(PtrMap_PassagewayNearKadary)	; $DB
MapID_NullDC = id(PtrMap_NullDC)	; $DC
MapID_NullDD = id(PtrMap_NullDD)	; $DD
MapID_NullDE = id(PtrMap_NullDE)	; $DE
MapID_NullDF = id(PtrMap_NullDF)	; $DF
MapID_Uzo = id(PtrMap_Uzo)	; $E0
MapID_UzoHouse1 = id(PtrMap_UzoHouse1)	; $E1
MapID_UzoHouse2 = id(PtrMap_UzoHouse2)	; $E2
MapID_UzoInn = id(PtrMap_UzoInn)	; $E3
MapID_UzoHouse3 = id(PtrMap_UzoHouse3)	; $E4
MapID_UzoItemShop = id(PtrMap_UzoItemShop)	; $E5
MapID_Torinco = id(PtrMap_Torinco)	; $E6
MapID_CulversHouse = id(PtrMap_CulversHouse)	; $E7
MapID_TorincoHouse1 = id(PtrMap_TorincoHouse1)	; $E8
MapID_TorincoHouse2 = id(PtrMap_TorincoHouse2)	; $E9
MapID_TorincoItemShop = id(PtrMap_TorincoItemShop)	; $EA
MapID_TorincoInn = id(PtrMap_TorincoInn)	; $EB
MapID_MonsenCave = id(PtrMap_MonsenCave)	; $EC
MapID_RappyCave = id(PtrMap_RappyCave)	; $ED
MapID_NullEE = id(PtrMap_NullEE)	; $EE
MapID_NullEF = id(PtrMap_NullEF)	; $EF
MapID_LeRoofRoom = id(PtrMap_LeRoofRoom)	; $F0
MapID_SilenceTm = id(PtrMap_SilenceTm)	; $F1
MapID_StrengthTower = id(PtrMap_StrengthTower)	; $F2
MapID_StrengthTower_F1 = id(PtrMap_StrengthTower_F1)	; $F3
MapID_StrengthTower_F2 = id(PtrMap_StrengthTower_F2)	; $F4
MapID_StrengthTower_F3 = id(PtrMap_StrengthTower_F3)	; $F5
MapID_StrengthTower_F4 = id(PtrMap_StrengthTower_F4)	; $F6
MapID_CourageTower = id(PtrMap_CourageTower)	; $F7
MapID_CourageTower_F1 = id(PtrMap_CourageTower_F1)	; $F8
MapID_CourageTower_F2 = id(PtrMap_CourageTower_F2)	; $F9
MapID_CourageTower_F3 = id(PtrMap_CourageTower_F3)	; $FA
MapID_CourageTower_F4 = id(PtrMap_CourageTower_F4)	; $FB
MapID_AngerTower = id(PtrMap_AngerTower)	; $FC
MapID_AngerTower_F1 = id(PtrMap_AngerTower_F1)	; $FD
MapID_AngerTower_F2 = id(PtrMap_AngerTower_F2)	; $FE
MapID_NullFF = id(PtrMap_NullFF)	; $FF
MapID_TheEdge = id(PtrMap_TheEdge)	; $100
MapID_TheEdge_Part2 = id(PtrMap_TheEdge_Part2)	; $101
MapID_TheEdge_Part3 = id(PtrMap_TheEdge_Part3)	; $102
MapID_TheEdge_Part4 = id(PtrMap_TheEdge_Part4)	; $103
MapID_TheEdge_Part5 = id(PtrMap_TheEdge_Part5)	; $104
MapID_TheEdge_Part6 = id(PtrMap_TheEdge_Part6)	; $105
MapID_TheEdge_Part7 = id(PtrMap_TheEdge_Part7)	; $106
MapID_TheEdge_Part8 = id(PtrMap_TheEdge_Part8)	; $107
MapID_TheEdge_Part9 = id(PtrMap_TheEdge_Part9)	; $108
MapID_Null109 = id(PtrMap_Null109)	; $109
MapID_Null10A = id(PtrMap_Null10A)	; $10A
MapID_Null10B = id(PtrMap_Null10B)	; $10B
MapID_Null10C = id(PtrMap_Null10C)	; $10C
MapID_Null10D = id(PtrMap_Null10D)	; $10D
MapID_Null10E = id(PtrMap_Null10E)	; $10E
MapID_Null10F = id(PtrMap_Null10F)	; $10F
MapID_Null110 = id(PtrMap_Null110)	; $110
MapID_Null111 = id(PtrMap_Null111)	; $111
MapID_Null112 = id(PtrMap_Null112)	; $112
MapID_Null113 = id(PtrMap_Null113)	; $113
MapID_Null114 = id(PtrMap_Null114)	; $114
MapID_Null115 = id(PtrMap_Null115)	; $115
MapID_Null116 = id(PtrMap_Null116)	; $116
MapID_Null117 = id(PtrMap_Null117)	; $117
MapID_Null118 = id(PtrMap_Null118)	; $118
MapID_Null119 = id(PtrMap_Null119)	; $119
MapID_Null11A = id(PtrMap_Null11A)	; $11A
MapID_Null11B = id(PtrMap_Null11B)	; $11B
MapID_Null11C = id(PtrMap_Null11C)	; $11C
MapID_Null11D = id(PtrMap_Null11D)	; $11D
MapID_Null11E = id(PtrMap_Null11E)	; $11E
MapID_Null11F = id(PtrMap_Null11F)	; $11F
MapID_Tyler = id(PtrMap_Tyler)	; $120
MapID_TylerHouse1 = id(PtrMap_TylerHouse1)	; $121
MapID_TylerWeaponShop = id(PtrMap_TylerWeaponShop)	; $122
MapID_TylerItemShop = id(PtrMap_TylerItemShop)	; $123
MapID_TylerHouse2 = id(PtrMap_TylerHouse2)	; $124
MapID_TylerInn = id(PtrMap_TylerInn)	; $125
MapID_Zosa = id(PtrMap_Zosa)	; $126
MapID_ZosaHouse1 = id(PtrMap_ZosaHouse1)	; $127
MapID_ZosaHouse2 = id(PtrMap_ZosaHouse2)	; $128
MapID_ZosaWeaponShop = id(PtrMap_ZosaWeaponShop)	; $129
MapID_ZosaItemShop = id(PtrMap_ZosaItemShop)	; $12A
MapID_ZosaInn = id(PtrMap_ZosaInn)	; $12B
MapID_ZosaHouse3 = id(PtrMap_ZosaHouse3)	; $12C
MapID_Meese = id(PtrMap_Meese)	; $12D
MapID_MeeseHouse1 = id(PtrMap_MeeseHouse1)	; $12E
MapID_MeeseItemShop2 = id(PtrMap_MeeseItemShop2)	; $12F
MapID_MeeseItemShop1 = id(PtrMap_MeeseItemShop1)	; $130
MapID_MeeseWeaponShop = id(PtrMap_MeeseWeaponShop)	; $131
MapID_MeeseInn = id(PtrMap_MeeseInn)	; $132
MapID_MeeseClinic = id(PtrMap_MeeseClinic)	; $133
MapID_MeeseClinic_F1 = id(PtrMap_MeeseClinic_F1)	; $134
MapID_Null135 = id(PtrMap_Null135)	; $135
MapID_Jut = id(PtrMap_Jut)	; $136
MapID_JutHouse1 = id(PtrMap_JutHouse1)	; $137
MapID_JutHouse2 = id(PtrMap_JutHouse2)	; $138
MapID_JutHouse3 = id(PtrMap_JutHouse3)	; $139
MapID_JutHouse4 = id(PtrMap_JutHouse4)	; $13A
MapID_JutHouse5 = id(PtrMap_JutHouse5)	; $13B
MapID_JutWeaponShop = id(PtrMap_JutWeaponShop)	; $13C
MapID_JutItemShop = id(PtrMap_JutItemShop)	; $13D
MapID_JutHouse6 = id(PtrMap_JutHouse6)	; $13E
MapID_JutHouse6_F1 = id(PtrMap_JutHouse6_F1)	; $13F
MapID_JutHouse7 = id(PtrMap_JutHouse7)	; $140
MapID_JutHouse8 = id(PtrMap_JutHouse8)	; $141
MapID_JutInn = id(PtrMap_JutInn)	; $142
MapID_JutChurch = id(PtrMap_JutChurch)	; $143
MapID_Ryuon = id(PtrMap_Ryuon)	; $144
MapID_RyuonItemShop = id(PtrMap_RyuonItemShop)	; $145
MapID_RyuonWeaponShop = id(PtrMap_RyuonWeaponShop)	; $146
MapID_RyuonHouse1 = id(PtrMap_RyuonHouse1)	; $147
MapID_RyuonHouse2 = id(PtrMap_RyuonHouse2)	; $148
MapID_RyuonHouse3 = id(PtrMap_RyuonHouse3)	; $149
MapID_RyuonPub = id(PtrMap_RyuonPub)	; $14A
MapID_RyuonInn = id(PtrMap_RyuonInn)	; $14B
MapID_RajaTemple = id(PtrMap_RajaTemple)	; $14C
MapID_Reshel1 = id(PtrMap_Reshel1)	; $14D
MapID_Reshel2 = id(PtrMap_Reshel2)	; $14E
MapID_Reshel3 = id(PtrMap_Reshel3)	; $14F
MapID_Reshel2House = id(PtrMap_Reshel2House)	; $150
MapID_Reshel2WeaponShop = id(PtrMap_Reshel2WeaponShop)	; $151
MapID_Reshel3House1 = id(PtrMap_Reshel3House1)	; $152
MapID_Reshel3ItemShop = id(PtrMap_Reshel3ItemShop)	; $153
MapID_Reshel3House2 = id(PtrMap_Reshel3House2)	; $154
MapID_Reshel3WeaponShop = id(PtrMap_Reshel3WeaponShop)	; $155
MapID_Reshel3Inn = id(PtrMap_Reshel3Inn)	; $156
MapID_Reshel3House3 = id(PtrMap_Reshel3House3)	; $157
MapID_MystVale = id(PtrMap_MystVale)	; $158
MapID_MystVale_Part2 = id(PtrMap_MystVale_Part2)	; $159
MapID_MystVale_Part3 = id(PtrMap_MystVale_Part3)	; $15A
MapID_MystVale_Part4 = id(PtrMap_MystVale_Part4)	; $15B
MapID_MystVale_Part5 = id(PtrMap_MystVale_Part5)	; $15C
MapID_ElsydeonCave = id(PtrMap_ElsydeonCave)	; $15D
MapID_ElsydeonCave_B1 = id(PtrMap_ElsydeonCave_B1)	; $15E
MapID_Hangar = id(PtrMap_Hangar)	; $15F
MapID_GumbiousEntrance = id(PtrMap_GumbiousEntrance)	; $160
MapID_Gumbious = id(PtrMap_Gumbious)	; $161
MapID_Gumbious_F1 = id(PtrMap_Gumbious_F1)	; $162
MapID_Gumbious_B1 = id(PtrMap_Gumbious_B1)	; $163
MapID_Gumbious_B2 = id(PtrMap_Gumbious_B2)	; $164
MapID_Gumbious_B2_Part2 = id(PtrMap_Gumbious_B2_Part2)	; $165
MapID_EspMansionEntrance = id(PtrMap_EspMansionEntrance)	; $166
MapID_EspMansion = id(PtrMap_EspMansion)	; $167
MapID_EspMansionWestRoom = id(PtrMap_EspMansionWestRoom)	; $168
MapID_EspMansionEastRoom = id(PtrMap_EspMansionEastRoom)	; $169
MapID_EspMansionNorth = id(PtrMap_EspMansionNorth)	; $16A
MapID_EspMansionNorthEastRoom = id(PtrMap_EspMansionNorthEastRoom)	; $16B
MapID_EspMansionNorthWestRoom = id(PtrMap_EspMansionNorthWestRoom)	; $16C
MapID_EspMansionCourtyard = id(PtrMap_EspMansionCourtyard)	; $16D
MapID_InnerSanctuary = id(PtrMap_InnerSanctuary)	; $16E
MapID_InnerSanctuary_B1 = id(PtrMap_InnerSanctuary_B1)	; $16F
MapID_AirCastle_Part6 = id(PtrMap_AirCastle_Part6)	; $170
MapID_AirCastle = id(PtrMap_AirCastle)	; $171
MapID_AirCastle_Part2 = id(PtrMap_AirCastle_Part2)	; $172
MapID_AirCastle_Part3 = id(PtrMap_AirCastle_Part3)	; $173
MapID_AirCastle_Part4 = id(PtrMap_AirCastle_Part4)	; $174
MapID_AirCastle_Part5 = id(PtrMap_AirCastle_Part5)	; $175
MapID_AirCastle_F1_Part9 = id(PtrMap_AirCastle_F1_Part9)	; $176
MapID_AirCastle_F1_Part5 = id(PtrMap_AirCastle_F1_Part5)	; $177
MapID_AirCastle_F1_Part2 = id(PtrMap_AirCastle_F1_Part2)	; $178
MapID_AirCastle_F1_Part10 = id(PtrMap_AirCastle_F1_Part10)	; $179
MapID_AirCastleInner = id(PtrMap_AirCastleInner)	; $17A
MapID_AirCastle_F1_Part11 = id(PtrMap_AirCastle_F1_Part11)	; $17B
MapID_AirCastle_F1_Part12 = id(PtrMap_AirCastle_F1_Part12)	; $17C
MapID_AirCastle_F1_Part13 = id(PtrMap_AirCastle_F1_Part13)	; $17D
MapID_AirCastle_Part8 = id(PtrMap_AirCastle_Part8)	; $17E
MapID_AirCastle_Part7 = id(PtrMap_AirCastle_Part7)	; $17F
MapID_AirCastle_F1_Part4 = id(PtrMap_AirCastle_F1_Part4)	; $180
MapID_AirCastle_F1 = id(PtrMap_AirCastle_F1)	; $181
MapID_AirCastle_F1_Part3 = id(PtrMap_AirCastle_F1_Part3)	; $182
MapID_AirCastle_F2 = id(PtrMap_AirCastle_F2)	; $183
MapID_AirCastleXeAThoulRoom = id(PtrMap_AirCastleXeAThoulRoom)	; $184
MapID_AirCastleInner_B1 = id(PtrMap_AirCastleInner_B1)	; $185
MapID_AirCastleInner_B1_Part2 = id(PtrMap_AirCastleInner_B1_Part2)	; $186
MapID_AirCastleInner_B1_Part3 = id(PtrMap_AirCastleInner_B1_Part3)	; $187
MapID_AirCastleInner_B2 = id(PtrMap_AirCastleInner_B2)	; $188
MapID_AirCastleInner_B3 = id(PtrMap_AirCastleInner_B3)	; $189
MapID_AirCastleInner_B4 = id(PtrMap_AirCastleInner_B4)	; $18A
MapID_AirCastleInner_B5 = id(PtrMap_AirCastleInner_B5)	; $18B
MapID_ZelanSpace = id(PtrMap_ZelanSpace)	; $18C
MapID_Zelan = id(PtrMap_Zelan)	; $18D
MapID_Zelan_F1 = id(PtrMap_Zelan_F1)	; $18E
MapID_KuranSpace = id(PtrMap_KuranSpace)	; $18F
MapID_Kuran = id(PtrMap_Kuran)	; $190
MapID_Kuran_F1 = id(PtrMap_Kuran_F1)	; $191
MapID_Kuran_F2 = id(PtrMap_Kuran_F2)	; $192
MapID_Kuran_F1_Part2 = id(PtrMap_Kuran_F1_Part2)	; $193
MapID_Kuran_F1_Part3 = id(PtrMap_Kuran_F1_Part3)	; $194
MapID_Kuran_F1_Part5 = id(PtrMap_Kuran_F1_Part5)	; $195
MapID_Kuran_F2_Part2 = id(PtrMap_Kuran_F2_Part2)	; $196
MapID_Kuran_F1_Part4 = id(PtrMap_Kuran_F1_Part4)	; $197
MapID_Kuran_F3 = id(PtrMap_Kuran_F3)	; $198
MapID_GaruberkTower = id(PtrMap_GaruberkTower)	; $199
MapID_GaruberkTower_Part2 = id(PtrMap_GaruberkTower_Part2)	; $19A
MapID_GaruberkTower_Part3 = id(PtrMap_GaruberkTower_Part3)	; $19B
MapID_GaruberkTower_Part4 = id(PtrMap_GaruberkTower_Part4)	; $19C
MapID_GaruberkTower_Part5 = id(PtrMap_GaruberkTower_Part5)	; $19D
MapID_GaruberkTower_Part6 = id(PtrMap_GaruberkTower_Part6)	; $19E
MapID_GaruberkTower_Part7 = id(PtrMap_GaruberkTower_Part7)	; $19F
MapID_AirCastleSpace = id(PtrMap_AirCastleSpace)	; $1A0



; Event flags
EventFlag_PiataFirstTime = 7	; Set when Chaz is alone in Piata at the start of the game
EventFlag_AlysFound = 8	; Set when Chaz finds Alys in Piata
EventFlag_PrincipalMeeting = 9	; Set after talking to the principal the first time
EventFlag_HahnJoined = $A	; Set when Hahn joins your party for the first time
EventFlag_Igglanova = $B	; Set when you fight the Igglanova in the Piata basement
EventFlag_PrincipalConfession = $C	; Set after talking to the principal revealing the cause of the monsters' outbreak
EventFlag_BasementContainers = $D	; Set when you arrive at the room with the containers
EventFlag_PrincipalSuspicious = $E	; Set after Alys brings up the principal being suspicious
EventFlag_AfterIgglanova = $F	; Set after the Igglanova fight and the discussion about the monsters
EventFlag_HoltPetrified = $10	; Set after discovering that professor Holt is petrified
EventFlag_RuneJoined = $11	; Set after Rune joins the party the first time
EventFlag_Saya = $12	; Set after meeting Saya
EventFlag_TonoePathOpen = $13	; Set after Rune destroys the rocks blocking the passageway to Tonoe
EventFlag_ZemaPetrified = $14	; Set when the people of Zema are petrified
EventFlag_PiataChazControl = $15	; Set when you gain control of Chaz in Piata at the start of the game
EventFlag_TheRanchOwner = $19	; Set when you take on the Ranch Owner commission
EventFlag_MileRanchOwner = $1A	; Set after talking to the ranch owner and he moves left
EventFlag_MileSandWorm = $1B	; Set when you fight the Mile Sand Worm
EventFlag_RanchOwnerAfterBattle = $1C	; Set when you talk to the ranch owner after defeating the Sand Worm
EventFlag_RanchOwnerFee = $1D	; Set when you accept the fee from the guild for the Ranch Owner commission
EventFlag_TinkerbellsDog = $1E	; Set when you take on the Tinkerbell's Dog commission
EventFlag_RockyOwner = $1F	; Set when you talk to Rocky's owner
EventFlag_RockyFound = $20	; Set when you find Rocky
EventFlag_RockyTermiEscape = $21	; Set when Rocky runs out of Termi if you don't have the shortcake
EventFlag_RockyKrupEscape = $22	; Set when Rocky runs out of Krup if you don't have the shortcake
EventFlag_RockyMonsenEscape = $23	; Set when Rocky runs out of Monsen if you don't have the shortcake
EventFlag_RockyHome = $24	; Set when you bring Rocky back to his house
EventFlag_RockyFee = $25	; Set when you accept the fee from the guild for the Rocky commission
EventFlag_MissingStudent = $26	; Set when you take on the Missing Student commission
EventFlag_DormOwner = $27	; Set when you talk to the Piata dorm owner about the missing student
EventFlag_StudentSick = $28	; Set when you talk to the missing student and she falls sick
EventFlag_Perolymate = $29	; Set when you talk to the old man when you have the Perolymate
EventFlag_StudentRecovered = $2A	; Set when you talk to the student in bed after giving her the perolymate
EventFlag_StudentFee = $2B	; Set when you accept the fee from the guild after the Missing Student mission
EventFlag_FissureOfFear = $2C	; Set when you take on the Fissure of Fear commission
EventFlag_TallasMother = $2D	; Set when you talk to Tallas' mother before going to the crevice
EventFlag_InsideCave = $2E	; Set when you fall through the crevice and end up in the cave under Monsen
EventFlag_FractOoze = $2F	; Set when you fight the Fract Ooze in the Monsen cave
EventFlag_GryzJoined = $30	; Set after the conversation with Dorin and Rune leaves
EventFlag_TonoeDoorOpen = $31	; Set when Gryz opens the door leading to the basement
EventFlag_AlshlineFound = $32	; Set after finding the Alshline and having the conversation about it
EventFlag_IgglanovaZema = $33	; Set when you fight the Igglanova in Zema
EventFlag_BioPlantEscape = $34	; Set after escaping the Bio Plant
EventFlag_RikaJoined = $35	; Set when you're outside Zema after the Bio Plant events
EventFlag_Dorin = $36	; Set right before the cutscene with Dorin starts
EventFlag_AfterIgglanovaZema = $37	; Set after defeating the Igglanova and deciding to go to Birth Valley
EventFlag_AfterCrevice = $3C	; Set when you talk to Tallas' mother after defeating Fract Ooze
EventFlag_FissureOfFearFee = $3D	; Set when you accept the fee from the guild after the Fissure of Fear commission
EventFlag_TallasSaved = $3E	; Set after the Fract Ooze battle and you save Tallas
EventFlag_WreckageSystem = $40	; Set when you analyze the system in the wreckage
EventFlag_Juza = $41	; Set when you fight Juza
EventFlag_Zio = $42	; Set when you fight Zio for the first time
EventFlag_MachineCenter = $43	; Set after Machine Center appears
EventFlag_LandRover = $44	; Set when you get the Land Rover
EventFlag_FortuneTeller = $45	; Set when talking to the fortune teller in Aiedo with Alys
EventFlag_GirlsCaught = $46	; Set after resting in the Aiedo supermarket and the girls get arrested
EventFlag_DemiJoined = $47	; Set after Zio wounds Alys and you decide to go find Rune
EventFlag_JuzaDefeated = $48	; Set after the battle against Juza and the stairs appear
EventFlag_Hijammer = $5E	; Set after getting Hijammer
EventFlag_PlateSystem = $60	; Set when you take on the mission of stopping the earthquakes from happening
EventFlag_PlateEngine = $61	; Set when you analyze the engine in the Plate System
EventFlag_RuneJoinedAgain = $62	; Set when Rune joins in the Ladea Tower
EventFlag_AfterAlysDeath = $63	; Set after the cutscene with Alys dying
EventFlag_ZioFortBarrier = $64	; Set after breaking the invisible barrier blocking the way to Nurvus
EventFlag_ZioNurvus = $65	; Set when you fight Zio in Nurvus
EventFlag_MotaSpaceport = $66	; Set after the spaceport in Motavia appears
EventFlag_AfterAlysDeath2 = $67	; Set after the cutscene with Alys dying
EventFlag_GryzGone = $68	; Set after Gryz leaves the party
EventFlag_GyLaguiah = $69	; Set when you fight Gy-Laguiah in the Ladea Tower
EventFlag_WrenJoined = $70	; Set when Wren joins your party
EventFlag_ChaosSorcr = $71	; Set when you fight the Chaos Sorcr in the spaceship
EventFlag_Canceller = $72	; Set when you get the Canceller
EventFlag_CancellerReminder = $73	; Set when Wren reminds you to get the Canceller
EventFlag_Burstroc = $74	; Set after getting Burstroc
EventFlag_StainInLife = $78	; Set when you take on the Stain in Life commission
EventFlag_MissingGirlsMom = $79	; Set when you talk to the mom of the missing girls
EventFlag_GirlPrison = $7A	; Set when you talk to one of the girl in the Aiedo prison
EventFlag_PrisonGuard = $7B	; Set when you talk to the guard in the prison regarding the girls
EventFlag_BailPaid = $7C	; Set after accepting to pay for the girls' bail
EventFlag_GirlsBailedOut = $7D	; Set after bringing the girls back home
EventFlag_StainInLifeFee = $7E	; Set after accepting the fee from the guild for the Stain in Life commision
EventFlag_Bail = $7F	; Set when you talk to the guard in the prison regarding the bail
EventFlag_Snowstorm = $80	; Set when you step out of the Raja's temple and have the conversation about the snowstorm
EventFlag_LandaleWhereabouts = $81	; Set after Gyuna tells you about the Landale
EventFlag_DezoSpaceport = $82	; Set after the Dezolis spaceport appears
EventFlag_DarkForce1 = $83	; Set when you fight the 1st Dark Force
EventFlag_TylerGrave = $84	; Set after you open Tyler's grave for the first time
EventFlag_RajaTemple = $85	; Set after the crash landing on Raja's temple
EventFlag_Kuran = $86	; Set when you reach Kuran for the first time
EventFlag_NearDarkForce1 = $87	; Set when you are approaching the 1st Dark Force
EventFlag_RajaJoined = $88	; Set when Raja joins
EventFlag_IceDigger = $89	; Set after defeating the 1st Dark Force and getting the Ice Digger
EventFlag_Penguin = $8A	; Set when you have the Penguin in Zosa follow you; cleared when you enter Zosa or come out of a building in Zosa
EventFlag_Reshel = $8B	; Set when you fight the zombies as you enter Reshel for the first time
EventFlag_PenguinNoMoney = $8C	; Set if you talk to the Penguin guy when you don't have enough money; cleared otherwise
EventFlag_MuskCats = $90	; Set when you talk to the 2 musk cats guarding the room entrance
EventFlag_SilverTusk = $91	; Set when you receive the Silver Tusk
EventFlag_DezoGyLaguiah = $92	; Set when you fight a Gy Laguiah in the Dezolis climate center
EventFlag_DElmLars = $93	; Set when you fight the D-Elm-Lars in the Dezolis climate center
EventFlag_RajaSick = $94	; Set when Raja falls sick
EventFlag_CarnivorousTrees = $95	; Set when you fight the carnivorous trees when you go save Kyra
EventFlag_InnerSanctuary = $96	; Set when rune convinces the esper guards to let you enter the Inner Sanctuary
EventFlag_LutzRevelation = $97	; Set after Rune reveals that he's Lutz and then you decide to go to the Garuberk Tower
EventFlag_EclipseTorchStolen = $98	; Set when the Eclipse Torch is stolen
EventFlag_AirCastleFound = $99	; Set when you locate the Air Castle
EventFlag_XeAThoul = $9A	; Set when you fight the 3 Xe-A-Thouls in the Air Castle
EventFlag_Lashiec = $9B	; Set when you fight Lashiec
EventFlag_EclipseTorch = $9C	; Set when you use the Eclipse Torch to destroy the carnivorous trees
EventFlag_Hydrofoil = $9D	; Set after giving the Eclipse Torch back and you get the Hydrofoil
EventFlag_DarkForce2 = $9E	; Set when you fight the 2nd Dark Force
EventFlag_AirCastle = $9F	; Set when you arrive at the Air Castle
EventFlag_KyraJoined = $A0	; Set when Kyra joins the party
EventFlag_SnowstormGone = $A1	; Set after defeating the 2nd Dark Force
EventFlag_InnerSanctGuard1 = $A2	; Set when talking to the old man in the Inner Sanctuary the first time
EventFlag_InnerSanctGuard2 = $A3	; Set when talking to the old man in the Inner Sanctuary before getting Elsydeon
EventFlag_ClimateCenter = $A4	; Set after the fight with the Gy Laguiah in the Dezolis climate center
EventFlag_DElmLarsDefeated = $A5	; Set after the fight with the D-Elm-Lars in the Dezolis climate center
EventFlag_Spector = $A6	; Set when you fight the Spector after opening the chest with the fake Eclipse Torch
EventFlag_DyingBoy = $A8	; Set when you take on the Dying Boy commission
EventFlag_Culvers = $A9	; Set after talking to Culvers, the dying boy's father
EventFlag_AlisSword = $AA	; Set after using the Alis sword to help the boy recover
EventFlag_CulversAfterRecovery = $AB	; Set when you talk to Culvers after the boy recovers
EventFlag_DyingBoyFee = $AC	; Set after accepting the Dying Boy fee from the guild
EventFlag_ManWithTwist = $AD	; Set when you take on the Man with twist commission
EventFlag_Sekreas = $AE	; Set when you talk to Sekreas during the commission
EventFlag_KingRappy = $AF	; Set when you fight the King Rappy
EventFlag_ManWithTwistFee = $B0	; Set after talking to the Hunters' Guild receptionist after ending the Man with Twist commission
EventFlag_SilverSoldier = $B1	; Set when you take on the Silver Soldier commission
EventFlag_Servants = $B2	; Set when you fight the Servants as you enter Zema
EventFlag_ZemaOldMan = $B3	; Set after talking to the old man in Zema explaining the robots situation
EventFlag_VahalFort = $B4	; Set when you enter Vahal Fort and have the conversation about the robots
EventFlag_VahalFortMidway = $B5	; Set when you enter the room with the conveyor belts and have the conversation in Vahal Fort
EventFlag_Dominators = $B6	; Set when you fight the Dominators in Vahal Fort
EventFlag_OldManZemaAfterDaughter = $B7	; Set after talking to the old man in Zema after shutting down Daughter
EventFlag_SilverSoldierFee = $B8	; Set after accepting the fee from the guild for the Silver Soldier mission
EventFlag_VahFortBarrier = $B9	; Set after you have the conversation about the barrier in Vahal Fort
EventFlag_SekreasReason = $BA	; Set after defeating King Rappy and Sekreas explains why he commissioned hunters
EventFlag_DaughterShutDown = $BB	; Set after shutting down Daughter in Vahal Fort
EventFlag_Hydrofoil2 = $C0	; Set after giving the Eclipse Torch back and you get the Hydrofoil
EventFlag_SethJoined = $C1	; Set when Seth joins your party
EventFlag_SethConversation1 = $C2	; Set when you have a conversation with Seth on the way up
EventFlag_SethConversation2 = $C3	; Set when you have a conversation with Seth on the way up
EventFlag_SoldiersTemple = $C4	; Set when you exit the cave leading to the Soldier's Temple
EventFlag_DarkForce3 = $C5	; Set when you fight Dark Force 3
EventFlag_DarkForce3Defeated = $C6	; Set after defeating Dark Force 3
EventFlag_WeaponPlant = $C7	; Set when you enter the Weapon Plant on Dezolis
EventFlag_AeroPrism1 = $C8	; Set when you find the Aero-Prism
EventFlag_AeroPrism2 = $C9	; Set when you find the Aero-Prism
EventFlag_Rykros = $D0	; Set when you find Rykros
EventFlag_LeRoof = $D1	; Set when you talk to Le Roof for the first time
EventFlag_SaLews = $D2	; Set when you fight Sa-Lews
EventFlag_CourageTowerChests = $D3	; Set after you open all the chests at the top of the Courage Tower
EventFlag_DeVars = $D4	; Set when you fight De-Vars
EventFlag_StrengthTowerChests = $D5	; Set after you open all the chests at the top of the Strength Tower
EventFlag_LeRoofStory1 = $D6	; Set after Le Roof tells you the story of Algo's origin
EventFlag_LeRoofStory2 = $D7	; Set after Le Roof tells you the story of Algo's origin
EventFlag_ElsydeonCave = $D8	; Set when Rune tells you about Elsydeon and opens the cave to it
EventFlag_Elsydeon = $D9	; Set when you trigger the Elsydeon cutscene
EventFlag_Reunion = $DA	; Set when everyone gathers together before the final dungeon
EventFlag_HahnPicked = $DB	; Set when you choose Hahn as the 5th character; cleared when you choose someone else
EventFlag_GryzPicked = $DC	; Set when you choose Gryz as the 5th character; cleared when you choose someone else
EventFlag_DemiPicked = $DD	; Set when you choose Demi as the 5th character; cleared when you choose someone else
EventFlag_RajaPicked = $DE	; Set when you choose Raja as the 5th character; cleared when you choose someone else
EventFlag_KyraPicked = $DF	; Set when you choose Kyra as the 5th character; cleared when you choose someone else
EventFlag_AngerTower = $E0	; Set when you are allowed to enter the Anger Tower
EventFlag_ReFaze = $E1	; Set when you either choose to learn about Megid or not
EventFlag_StrengthTowerTop = $E2	; Set when you reach the top of the Strength Tower and De-Vars kills the monsters
EventFlag_CourageTowerTop = $E3	; Set when you reach the top of the Courage Tower and Sa-Lews kills the monsters
EventFlag_AlysFight = $E4	; Set when you fight Alys in the Anger Tower
EventFlag_DeVarsDefeated = $E5	; Set after defeating De-Vars
EventFlag_SaLewsDefeated = $E6	; Set after defeating Sa-Lews
EventFlag_AngerTowerEnd = $E7	; Set when you exit the top of the Anger Tower and Chaz reunites with his friends
EventFlag_ProfoundDarkness = $E8	; Set when you fight Profound Darkness
EventFlag_GuildPlaceholder = $EB	; Always cleared; used as a placeholder in the Hunters' Guild section to mean that, once a request is available,
					; you can do it anytime


; Chest flags
ChestFlag_Alshline = 8
ChestFlag_PsycoWand = 9
ChestFlag_ControlKey = $A
ChestFlag_Canceller = $B
ChestFlag_EclpsTorch = $C
ChestFlag_AeroPrism = $D
ChestFlag_GrbrkTwTrimate = $10
ChestFlag_GrbrkTwPowShield = $11
ChestFlag_GrbrkTwTrimate2 = $12
ChestFlag_GrbrkTwMoonSlashr = $13
ChestFlag_GrbrkTwStarDew = $14
ChestFlag_GrbrkTwMoonDew = $15
ChestFlag_GrbrkTwEscapipe = $16
ChestFlag_GrbrkTwStarDew2 = $17
ChestFlag_PiataMonomate = $18
ChestFlag_Piata100Meseta = $19
ChestFlag_PiataAntidote = $1A
ChestFlag_BrthVllyCrbnShield = $1B
ChestFlag_BrthVllyMonomate = $1C
ChestFlag_VllyMazeAntidote = $1D
ChestFlag_VllyMaze300Meseta = $1E
ChestFlag_Tonoe100Meseta = $1F
ChestFlag_TonoeMonomate = $20
ChestFlag_Tonoe300Meseta = $21
ChestFlag_Tonoe500Meseta = $22
ChestFlag_TonoeTitnCrown = $23
ChestFlag_TonoeAntidote = $24
ChestFlag_BrthVllyCrbnSuit = $25
ChestFlag_BioPlantCureParal = $26
ChestFlag_BioPlantOpen1 = $27
ChestFlag_BioPlantOpen2 = $28
ChestFlag_BioPlantGrptCrown = $29
ChestFlag_BioPlantOpen3 = $2A
ChestFlag_BioPlantCrmcSword = $2B
ChestFlag_BioPlantAntidote = $2C
ChestFlag_WreckageCrmcShield = $2D
ChestFlag_Wreckage1500Meseta = $2E
ChestFlag_WreckageDimate = $2F
ChestFlag_WreckageCrmcKnife = $30
ChestFlag_WreckageCrmcMail = $31
ChestFlag_HntGuild1000Meseta = $32
ChestFlag_HntGuildTrimate = $33
ChestFlag_HntGuildOpen = $34
ChestFlag_PassagewayDimate = $35
ChestFlag_PassagewayCureParal = $36
ChestFlag_KadaryLasrSlashr = $37
ChestFlag_KadaryOpen = $38
ChestFlag_ZioFort2000Meseta = $39
ChestFlag_ZioFortDimate = $3A
ChestFlag_ZioFortLasrBarrir = $3B
ChestFlag_ZioFortMoonDew = $3C
ChestFlag_ZioFortLasrSword = $3D
ChestFlag_ZioFortLasrClaw = $3E
ChestFlag_PlateSysRepairKit = $3F
ChestFlag_PlateSysCrmcArmor = $40
ChestFlag_PlateSysTitnGear = $41
ChestFlag_Phonon = $42
ChestFlag_PlateSysLasrAxe = $43
ChestFlag_PlateSysLasrKnife = $44
ChestFlag_PlateSysLasrBarrir = $45
ChestFlag_PlateSysStunShot = $46
ChestFlag_LadeaTwDimate = $47
ChestFlag_LadeaTwEscapipe = $48
ChestFlag_LadeaTwStarDew2 = $49
ChestFlag_LadeaTw1000Meseta = $4A
ChestFlag_LadeaTwFradeMantl = $4B
ChestFlag_NurvusWaveShot = $4D
ChestFlag_NurvusRepairKit = $4E
ChestFlag_NurvusCrmcGear = $4F
ChestFlag_NurvusOpen = $50
ChestFlag_NurvusSpacedArmr = $51
ChestFlag_NurvusPlsmClaw = $52
ChestFlag_ZelanPlsmSword = $53
ChestFlag_ZelanPlsmClaw = $54
ChestFlag_ZelanPlsmDagger = $55
ChestFlag_ZelanPlsmField = $56
ChestFlag_ZelanPulseLasr = $57
ChestFlag_HangarZircGear = $59
ChestFlag_HangarDimate = $5A
ChestFlag_HangarOpen = $5B
ChestFlag_KuranZircoArmer = $5C
ChestFlag_KuranOpen = $5D
ChestFlag_Hijammer = $5E
ChestFlag_KuranRepairKit = $5F
ChestFlag_Kuran3000Meseta = $60
ChestFlag_KuranRepairKit2 = $61
ChestFlag_KuranNapalmShot = $62
ChestFlag_MystValeTrimate = $63
ChestFlag_MystValeStarDew = $64
ChestFlag_ClimCntrRepairKit = $65
ChestFlag_ClimCntrPulseVulcn = $66
ChestFlag_ClimCntrCompoGear = $67
ChestFlag_ClimCntr5000Meseta = $68
ChestFlag_ClimCntrRepairKit2 = $69
ChestFlag_ClimCntrCompoArmr = $6A
ChestFlag_ClimCntrOpen = $6B
ChestFlag_EspManLacoRod = $6C
ChestFlag_EspManRflcRobe = $6D
ChestFlag_EspMan10000Meseta = $6E
ChestFlag_EspManSolDew = $6F
ChestFlag_GumbiousTrimate = $70
ChestFlag_GumbiousMoonDew = $71
ChestFlag_GumbiousStarDew = $72
ChestFlag_GumbiousSolDew = $73
ChestFlag_Burstroc = $74
ChestFlag_WpnPlntPlsmLaunch = $75
ChestFlag_WpnPlntElstArmor = $76
ChestFlag_WpnPlntElstGear = $77
ChestFlag_WpnPlntRepairKit = $78
ChestFlag_AirCstlTrimate = $79
ChestFlag_AirCstlSwiftHelm = $7A
ChestFlag_AirCstl1000Meseta = $7B
ChestFlag_AirCstl4000Meseta = $7C
ChestFlag_AirCstl2000Meseta = $7D
ChestFlag_AirCstlEscapipe = $7E
ChestFlag_AirCstlTrimate2 = $7F
ChestFlag_AirCstlGenocyClaw = $80
ChestFlag_AirCstl8000Meseta = $81
ChestFlag_AirCstlSolDew = $82
ChestFlag_AirCstlMoonDew = $84
ChestFlag_AirCstlStarDew = $85
ChestFlag_IslandCaveEscapipe = $86
ChestFlag_IslandCaveMoonDew = $87
ChestFlag_IslandCaveStarDew = $88
ChestFlag_IslandCaveSolDew = $89
ChestFlag_IslandCaveTrimate = $8A
ChestFlag_VahFortRepairKit = $8C
ChestFlag_VahFortPhotnErasr = $8D
ChestFlag_VahFortLacoGear = $8E
ChestFlag_VahFortLacoArmor = $8F
ChestFlag_Posibolt = $90
ChestFlag_SilenceTmTrimate = $91
ChestFlag_SilenceTmGuardSword = $92
ChestFlag_SilenceTmTelepipe = $93
ChestFlag_SilenceTmGuardShild = $94
ChestFlag_StrengthTwMoonDew = $95
ChestFlag_StrengthTwGuardClaw = $96
ChestFlag_StrengthTwMoonDew2 = $97
ChestFlag_StrengthTwGuardRod = $98
ChestFlag_StrengthTwGuardClaw2 = $99
ChestFlag_CourageTwStarDew = $9A
ChestFlag_CourageTwStarDew2 = $9B
ChestFlag_CourageTwGuardRobe = $9C
ChestFlag_CourageTwGuardMail = $9D
ChestFlag_CourageTwGuardArmor = $9E
ChestFlag_AngerTwSolDew = $9F
ChestFlag_AngerTwGuardMail = $A0
ChestFlag_PalmaRing = $A1
ChestFlag_MotaRing = $A2
ChestFlag_DezoRing = $A3
ChestFlag_RykrRing = $A4
ChestFlag_AlgoRing = $A5
ChestFlag_TonoeEscapipe = $A6
ChestFlag_TonoeOpen = $A7
ChestFlag_LadeaTwStarDew = $A8
ChestFlag_Unused = $A9 			; This is used in one (not referenced) of the subroutines in the Main Map Update section.

; Temporary event flags
TempEveFlag_BioPlantDoor = 0	; Set when you open the door leading to the Bio Plant
TempEveFlag_BioPlantAlarm = 8	; Set when the alarm goes off at the start of the Bio Plant; cleared when you get out of the Bio Plant
TempEveFlag_VahFortMovingPltfrm1 = 9	; Set when a moving platform in Vahal Fort has moved down; cleared when moved up
TempEveFlag_VahFortMovingPltfrm2 = $A	; Set when a moving platform in Vahal Fort has moved up; cleared when moved down
TempEveFlag_VahFortTerminal = $B	; Set when you use the small terminal that changes conveyor belts direction; cleared when you restore to original moving direction
TempEveFlag_VahFortTerminal2 = $C	; Set when you use the small terminal that changes conveyor belts direction; cleared when you restore to original moving direction
TempEveFlag_WpnPlantMovingPltfrm1 = $D	; Set when a moving platform in the Weapon Plant has moved down; cleared when moved up
TempEveFlag_WpnPlantMovingPltfrm2 = $E	; Set when a moving platform in the Weapon Plant has moved down; cleared when moved up
TempEveFlag_WpnPlantMovingPltfrm3 = $F	; Set when a moving platform in the Weapon Plant has moved down; cleared when moved up
TempEveFlag_WpnPlantMovingPltfrm4 = $10	; Set when a moving platform in the Weapon Plant has moved down; cleared when moved up
TempEveFlag_WpnPlantTerminal = $11	; Set when you use the small terminal that changes conveyor belts direction; cleared when you restore to original moving direction
TempEveFlag_WpnPlantTerminal2 = $12	; Set when you use the small terminal that changes conveyor belts direction; cleared when you restore to original moving direction
TempEveFlag_Xanafalgue = $13	; Set when the Xanafalgue runs away when you are in the Piata basement
TempEveFlag_GrbkTwEyeball = $14	; Set when you touch the 1st eyeball in the Garuberk Tower
TempEveFlag_GrbkTwMoonSlshrRoom = $15	; Set when you get in the room with a chest containing a Moon Slasher; cleared when you enter the same map but in a different location
TempEveFlag_GrbkTwEyeball2 = $16	; Set when you touch the 2nd eyeball in the Garuberk Tower
TempEveFlag_GrbkTwEyeball2Door = $17	; Set when you enter the room where you can touch the 2nd eyeball
TempEveFlag_ChazHouse = $18	; Set when you're in Chaz's house; cleared when you get out
TempEveFlag_SilenceTm = $19	; Only gets cleared when loading the map Silence Tm (Le Roof's room)
TempEveFlag_EspMansionGuards = $1A	; Set when the guards move aside and let you enter the Esper Mansion; cleared when you leave
TempEveFlag_StrippersDance = $1B	; Set when strippers show up and dance; cleared when you leave
TempEveFlag_Pennant = $1C	; Set when you choose to decorate your house with the Pennant
TempEveFlag_WoodCarving = $1D	; Set when you choose to decorate your house with the Wood Carving

; Town flags -- Set when you enter a new town
TownFlag_Piata = 0
TownFlag_Mile = 1
TownFlag_Zema = 2
TownFlag_Molcum = 3
TownFlag_Krup = 4
TownFlag_Tonoe = 5
TownFlag_Nalya = 6
TownFlag_Aiedo = 7
TownFlag_Kadary = 8
TownFlag_Monsen = 9
TownFlag_Termi = $A
TownFlag_Uzo = $B
TownFlag_Torinco = $C
TownFlag_RajaTemple = $10
TownFlag_Ryuon = $11
TownFlag_Tyler = $12
TownFlag_Zosa = $13
TownFlag_Reshel = $14
TownFlag_Meese = $15
TownFlag_EspMansion = $16
TownFlag_Jut = $17
TownFlag_Gumbious = $18
TownFlag_SilenceTm = $19

; ---------------------------------------------------------------------------
; Controller Buttons
;
; Buttons bit numbers
ButtonUp =  0
ButtonDown =  1
ButtonLeft =  2
ButtonRight =  3
ButtonCancel =  4
ButtonSpeak =  5
ButtonCamp =  6
ButtonStart =  7
; Buttons masks
ButtonUp_Mask = 1<<ButtonUp	; $01
ButtonDown_Mask =  1<<ButtonDown	; $02
ButtonLeft_Mask =  1<<ButtonLeft	; $04
ButtonRight_Mask =  1<<ButtonRight	; $08
ButtonCancel_Mask =  1<<ButtonCancel	; $10
ButtonSpeak_Mask =  1<<ButtonSpeak	; $20
ButtonCamp_Mask =  1<<ButtonCamp	; $40
ButtonStart_Mask =  1<<ButtonStart	; $80
; ---------------------------------------------------------------------------

; ---------------------------------------------------------------------------
; Facing directions
FacingDir_Down  = 0
FacingDir_Up    = 4
FacingDir_Right = 8
FacingDir_Left  = $C

; ---------------------------------------------------------------------------
; Battle commands
Command_Attack  = 1
Command_Tech    = 2
Command_Skill = 3
Command_Item  = 4
Command_Defense  = 5


WindowSize_CombatTransient = $12	; width of "Cannot flee!"/"Surprise Attack!" window
Title_ScrollDelay = $25				; 37 line steps; one extra 96-frame beat for music sync
Hunter_guild_cursor_x = $108		; X position of red cursor (pixels) for Hunter's guild window

; ---------------------------------------------------------------------------
; Credits
; ---------------------------------------------------------------------------
; delays are in frames, there are $20 frames per credits page. However, stage
; 1 and 2 page must come in pair, so if you want to increase those, increase
; them by multiples of $40.
;
; Stage 1 is from start of credits until Motavia shows up (last big planet)
; Stage 2 is from start of Motavia showing up to start of title font only
; pages (starts with "Thank you for playing")
; Stage 3 is from start of title font only pages to fade to white before
; showing the "Fin" screen with Alis & Myau's statue in Termi
; You usually only want to mess with the stage 1 delay, mainly because Motavia
; will stick there for too long if you increase stage 2, and stage 3 has a more
; hardcoded command sequence.
CreditsStage1_ScrollDelay = $380 
CreditsStage2_ScrollDelay = CreditsStage1_ScrollDelay + $80
CreditsStage3_ScrollDelay = CreditsStage2_ScrollDelay + $80

; ---------------------------------------------------------------------------
; Address Constants
; ---------------------------------------------------------------------------


; VDP
VDP_Data_Port =  $C00000
VDP_Control_Port =  $C00004
VDP_Counter =  $C00008

PSG_Input =  $C00011

; Z80
Z80_RAM =  $A00000	; start of Z80 RAM
Z80_RAM_End =  $A02000	; end of non-reserved Z80 RAM
Z80_Bus_Request =  $A11100
Z80_Reset =  $A11200

Security_Addr =  $A14000

; I/O area
HW_Version =  $A10001
HW_Port_1_Data =  $A10003
HW_Port_2_Data =  $A10005
HW_Expansion_Data =  $A10007
HW_Port_1_Control =  $A10009
HW_Port_2_Control =  $A1000B
HW_Expansion_Control =  $A1000D

HW_Write_Mode =  $A130F1

; SRAM
SRAM_Start =  $200001

Game_Cleared_Flag = $200035

SRAM_End = $203FFF


; RAM

; Make sure RAM address constants work in both 16-bit and 32-bit addressing modes
ramaddr function x,-(-x)&$FFFFFFFF


RAM_Start = ramaddr($FFFF0000)

Battle_Palette_Objects = ramaddr($FFFF2A90)
Dialogue_Trees = ramaddr($FFFF3000)

; If your dialogue is too large, you can gain $1000 bytes by
; commenting the two lines above and uncommenting the two below.
; This is not fully tested yet but appears to work.
;Dialogue_Trees = ramaddr($FFFF2000)
;Battle_Palette_Objects = ramaddr($FFFF2A90)


Battle_Routine = ramaddr($FFFF4100)
Battle_Total_Comd_Input = ramaddr($FFFF4106)	; number is incremented each time a command for a character has been selected
Battle_Routine_2 = ramaddr($FFFF4108)			; used for command input and messages
Battle_Command_Data = ramaddr($FFFF410A)		; 4 bytes per character; values are as follows:
												;    byte 1 = Index of command; 1 = attack; 2 = technique; 3 = skill; 4 = item; 5 = defense
												;    byte 2 = when command is technique, skill or item, this is the ID of the respective command
												;    bytes 3-4 = target index
												
Character_Command_Data = ramaddr($FFFF410A)
Enemy_Command_Data = ramaddr($FFFF411E)
												
Battle_Tech_List = ramaddr($FFFF412E)
Current_Turn_Number = ramaddr($FFFF4140)
Battle_Skill_List = ramaddr($FFFF4142)
Current_Actor_Index = ramaddr($FFFF4142)	; word
Current_Target_Index = ramaddr($FFFF4144)	; word
Current_Command = ramaddr($FFFF4146)
Fighters_Hit_Flags = ramaddr($FFFF4150)	; $00 = normal attack; $01 = critical hit; $FF = not being targeted or miss
Battle_Item_List = ramaddr($FFFF4152)
Battle_Ability_Effects = ramaddr($FFFF4170) ; if 0 the effect for a skill, technique, etc doesn't work; other numbers are the effects
Battle_Ability_Range = ramaddr($FFFF4182)	; range (e.g. single target) of techniques and skills
Battle_Skill_Done_Flag = ramaddr($FFFF4188)	; byte ; set to true when battle objects for skills have finished processing
Battle_Saved_Char_Stats = ramaddr($FFFF4194)	; longword ; holds address of current character's stats after battle is won
Battle_Next_Level_Data = ramaddr($FFFF4198)	; longword ; holds address of data for the next level after battle is won
Battle_Party_Slots_Addr = ramaddr($FFFF419C)	; longword ; holds address of Current_Party_Slots and is used after battle is won
Battle_Main_Option_Index = ramaddr($FFFF41A0)	; index of the 3 main battle options (COMD, MACR, RUN); it's also the index for displaying each stat message upon level-up
Battle_Char_Comd_Index = ramaddr($FFFF41A2)
Battle_Enemy_Index = ramaddr($FFFF41AC)		; index of target enemy
Battle_Tech_Index = ramaddr($FFFF41AE)		; index of tech selected (this is the cursor option, not the ID of the technique)
Battle_Char_Index = ramaddr($FFFF41B8)		; index of target character
Battle_Skill_Index = ramaddr($FFFF41BA)		; index of skill selected (this is the cursor option, not the ID of the skill)
Battle_Item_Index = ramaddr($FFFF41C4)		; index of item selected (this is the cursor option, not the ID of the Item)
Battle_Macro_Index = ramaddr($FFFF41D6)
Battle_Macro_Flag = ramaddr($FFFF41D8)		; set if a macro is going on

Enemy_Formation_Data = ramaddr($FFFF41F0)
Item_Drop_Rate = ramaddr($FFFF41F2)
Dropped_Item = ramaddr($FFFF41F3)

Enemy_Stats = ramaddr($FFFF4200)
Enemy_Stats_2 = ramaddr($FFFF4280)
Enemy_Stats_3 = ramaddr($FFFF4300)
Enemy_Stats_4 = ramaddr($FFFF4380)

Obj_Fighters = ramaddr($FFFF4400)	; RAM section storing properties of characters and enemies
Fighter_Char_1 = ramaddr($FFFF4400)
Fighter_Char_2 = ramaddr($FFFF4440)
Fighter_Char_3 = ramaddr($FFFF4480)
Fighter_Char_4 = ramaddr($FFFF44C0)
Fighter_Char_5 = ramaddr($FFFF4500)
Fighter_Enemy_1 = ramaddr($FFFF4540)
Fighter_Enemy_2 = ramaddr($FFFF4580)
Fighter_Enemy_3 = ramaddr($FFFF45C0)
Fighter_Enemy_4 = ramaddr($FFFF4600)
Fighter_Enemy_Group_1 = ramaddr($FFFF4640)
Fighter_Enemy_Group_2 = ramaddr($FFFF4680)

Vehicle_Stats = ramaddr($FFFF4700)

System_Stack = ramaddr($FFFF4FF0)

Sound_Index = ramaddr($FFFF500A)

Chunk_Table = ramaddr($FFFF6000)	; 32x32 definitions; 32 bytes (16 words) per definition; each word holds plane mappings; bit 6 is the collision flag, 0 = no collision, 1 = collision
									; When windows are opened, plane mappings are saved here
Text_Buffer = ramaddr($FFFF7000)
Plane_A_Buffer = ramaddr($FFFF8000)
Plane_B_Buffer = ramaddr($FFFF9000)
Plane_A_Buffer_DMA = $7FFFC000		; when we refer to plane buffers through DMA, value has to be divided by 2
Plane_B_Buffer_DMA = $7FFFC800		; if you change location of those plane buffers make sure you change the
					; _DMA values as well
Map_Layout_FG = ramaddr($FFFFA000)
Map_Layout_BG = ramaddr($FFFFB000)

Field_Objects_Memory = ramaddr($FFFFC000)
Character_1 = ramaddr($FFFFC000)
Character_2 = ramaddr($FFFFC040)
Character_3 = ramaddr($FFFFC080)
Character_4 = ramaddr($FFFFC0C0)
Character_5 = ramaddr($FFFFC100)
Red_Cursor = ramaddr($FFFFC280)
Text_Scroll_Arrow = ramaddr($FFFFC2C0)
Field_Obj_Secondary = ramaddr($FFFFC300)	; all objects except the characters, the red cursor and scroll text arrow are stored here
Hahn_Near_Basement = ramaddr($FFFFC300)
Alys_Piata = ramaddr($FFFFC4C0)

Battle_Objects_Memory = ramaddr($FFFFD000)
Command_Cursor = ramaddr($FFFFD000)
Target_Cursor = ramaddr($FFFFD040)

DMA_Commands_Buffer = ramaddr($FFFFE000)

Nem_Code_Table = ramaddr($FFFFE200)


Win_Char_Num = ramaddr($FFFFE3F0)	; number of characters in the menu
Win_Saved_Char_ID = ramaddr($FFFFE3F2)
Saved_Char_Stats_Offset = ramaddr($FFFFE3F4)

Nem_Decomp_Queue = ramaddr($FFFFE400)
Nem_Decomp_Destination = ramaddr($FFFFE404)
Nem_Decomp_Vars = ramaddr($FFFFE440)
Nem_Repeat_Count = ramaddr($FFFFE444)
Nem_Palette_Index = ramaddr($FFFFE448)
Nem_Previous_Row = ramaddr($FFFFE44C)
Nem_Data_Word = ramaddr($FFFFE450)
Nem_Shift_Value = ramaddr($FFFFE454)
Nem_Patterns_Left = ramaddr($FFFFE458)
Saved_Nem_Frame_Patterns_Left = ramaddr($FFFFE45A)
Nem_Frame_Patterns_Left = ramaddr($FFFFE484)

Sprite_Table_Input = ramaddr($FFFFE600)

Tile_Anim_Memory = ramaddr($FFFFE800)	; holds definitions for tile animations; $200 bytes; $20 bytes per definition

Enemy_Sprites = ramaddr($FFFFEA00)

Sprite_Table_Input_2 = ramaddr($FFFFEC00)

Game_Mode_Routine = ramaddr($FFFFEC20)

Routine_Exit_Flags = ramaddr($FFFFEC27)	; determines what to do when field routine is about to finish
										; bitfield; if bit is set, run function after testing the bit; bit 0 = Exit menu for teleport; bit 1 = Exit menu for event; bit 2 = Exit menu for Map (unused);
																									 ; bit 3 = Run battle after event

Field_Map_Index = ramaddr($FFFFEC28)
Field_Map_Index_2 = ramaddr($FFFFEC2A)
Map_Chunk_Addr = ramaddr($FFFFEC2C)
Map_Update_Addr = ramaddr($FFFFEC30)
Map_Transition_Data_Addr = ramaddr($FFFFEC34)
Map_Transition_Data_2_Addr = ramaddr($FFFFEC38)
Map_Interaction_Areas = ramaddr($FFFFEC3C)
Map_Events_Addr = ramaddr($FFFFEC40)
Map_Start_Facing_Dir = ramaddr($FFFFEC44)	; initial facing direction when loading a map; 0 = DOWN;    4 = UP;    8 = RIGHT;    $C = LEFT
Map_Start_Char_Align = ramaddr($FFFFEC46)	; alignment of the characters relative to the lead character
											; 0 = Characters overlap
											; 4 = Characters below lead character
											; 8 = Characters above lead character
											; $C = Characters on the left of lead character
											; $10 = Characters on the right of lead character
Map_Start_X_Pos = ramaddr($FFFFEC48)
Map_Start_Y_Pos = ramaddr($FFFFEC4A)
Field_Input_Buffer = ramaddr($FFFFEC4C)			; byte
Map_Load_Flags = ramaddr($FFFFEC4E)	; bitfield ; bit 0 = object reload (generally between battles); bit 1 = render characters at saved coordinates upon loading the game;
											   ; bit 2 = object reload (used during cutscenes); bit 3 = keep objects (used for map refresh during events)
											   ; bit 7 = skip palette fade in
BG_Alternate_Color_Flag = ramaddr($FFFFEC4F)	; byte; if set, for Plane B use the first palette line; also render tiles at lower priority
												; when loading the Chunk table, all patterns are set to use the second palette line by default for Plane A
Camera_X_Step_Counter_FG = ramaddr($FFFFEC50)
Camera_Y_Step_Counter_FG = ramaddr($FFFFEC54)
Camera_X_Step_Counter_BG = ramaddr($FFFFEC58)
Camera_Y_Step_Counter_BG = ramaddr($FFFFEC5C)
Map_Row_Size_FG = ramaddr($FFFFEC64)
Map_Column_Size_FG = ramaddr($FFFFEC65)
Map_Row_Size_BG = ramaddr($FFFFEC66)
Map_Column_Size_BG = ramaddr($FFFFEC67)
Map_X_Refresh_Flags_FG = ramaddr($FFFFEC68)	; bitfield	; determines when to refresh tiles or map layout when moving; bit 0 = if set, refresh every 32 pixels; bit 1 = if set, refresh every 256 pixels
Map_Y_Refresh_Flags_FG = ramaddr($FFFFEC69)	; bitfield	; determines when to refresh tiles or map layout when moving; bit 0 = if set, refresh every 32 pixels; bit 1 = if set, refresh every 256 pixels
Map_X_Refresh_Flags_BG = ramaddr($FFFFEC6A)	; bitfield	; determines when to refresh tiles or map layout when moving; bit 0 = if set, refresh every 32 pixels; bit 1 = if set, refresh every 256 pixels
Map_Y_Refresh_Flags_BG = ramaddr($FFFFEC6B)	; bitfield	; determines when to refresh tiles or map layout when moving; bit 0 = if set, refresh every 32 pixels; bit 1 = if set, refresh every 256 pixels
Saved_Chunk_Number = ramaddr($FFFFEC6C)
Saved_Chunk_Column = ramaddr($FFFFEC6E)
Saved_Map_Row_Size = ramaddr($FFFFEC70)
Saved_Map_Column_Size = ramaddr($FFFFEC72)
Map_Data_Manager_Addr = ramaddr($FFFFEC74)

Vehicle_Boarding_Flags = ramaddr($FFFFEC7F)	; determines if you can board a vehicle on the tile you're standing on
											; bitfield; if bit is set it means you can board the vehicle; bit 0 = Land Rover; bit 1 = Ice Digger; bit 2 = Hydrofoil

Tile_Collision_Array = ramaddr($FFFFEC80)	; holds collision indexes for tiles adjacent to the leading character; one byte per direction
											; collision indexes are as follows:
												; 0 = Empty
												; 1 = Map change (e.g. towns, stairs)
												; 2 = Recovery (e.g. at spaceports)
												; 8 = Solid
												; 9 = Water
												; $A = Sand
												; $B = Ice block
												; $C = Shop
Tile_Collision_Standing = ramaddr($FFFFEC80)	; tile leading character is currently standing on
Saved_Tile_Collision_Standing = ramaddr($FFFFEC81)
Tile_Collision_Shop = ramaddr($FFFFEC82)
Tile_Collision_Left_1 = ramaddr($FFFFEC83)
Tile_Collision_Top_Left_1 = ramaddr($FFFFEC84)
Tile_Collision_Up_1 = ramaddr($FFFFEC85)
Tile_Collision_Top_Right_1 = ramaddr($FFFFEC86)
Tile_Collision_Right = ramaddr($FFFFEC87)
Tile_Collision_Bottom_Right = ramaddr($FFFFEC88)
Tile_Collision_Down = ramaddr($FFFFEC89)
Tile_Collision_Bottom_Left = ramaddr($FFFFEC8A)
Tile_Collision_Left_2 = ramaddr($FFFFEC8B)
Tile_Collision_Top_Left_2 = ramaddr($FFFFEC8C)
Tile_Collision_Up_2 = ramaddr($FFFFEC8D)
Tile_Collision_Top_Right_2 = ramaddr($FFFFEC8E)

Map_General_Var = ramaddr($FFFFEC8F)

Window_Index = ramaddr($FFFFEC90)
Saved_Window_Index = ramaddr($FFFFEC92)
Win_Group_Start_Addr = ramaddr($FFFFEC94)
Win_Saved_Plane_Maps_End = ramaddr($FFFFEC98)	; word; points past all plane mappings which are saved while windows are open 
Windows_Opened_Num = ramaddr($FFFFEC9A)
Window_Init_Flag = ramaddr($FFFFEC9B)	; bit 0 = set if current window has been initialized

Window_Render_Mode = ramaddr($FFFFEC9C)
Window_Option_Index = ramaddr($FFFFEC9E)
Window_Option_Index_2 = ramaddr($FFFFEC9F)
Window_Option_Index_3 = ramaddr($FFFFECA0)
Window_Option_Index_4 = ramaddr($FFFFECA1)
Window_Option_Index_5 = ramaddr($FFFFECA2)

Event_Index = ramaddr($FFFFECA8)

Interaction_Event_Flag = ramaddr($FFFFECAA)	; when using the Talk function, get the event, chest or temp event in the Map Interaction Areas and then determine what to do with the flag
Found_Item_Location = ramaddr($FFFFECAB)	; if value is 0, item was found inside a treasure chest. The only item not found in a treasure chest is the Repair Kit in the Weapon Plant
Treasure_Chest_Addr = ramaddr($FFFFECAC)

HInt_Jump = ramaddr($FFFFECB0)
HInt_Addr = ramaddr($FFFFECB2)

Found_Item = ramaddr($FFFFECC2)	; if content type is 0, then it's the ID of the item; if content type is 1, it's the amount of money divided by 100
Interaction_Event_Type = ramaddr($FFFFECC3)	; type of event when using the Talk function; 0 = Story; 1 = Chest; 2 = Temporary
Found_Item_Type = ramaddr($FFFFECC4)	; 0 = content is an item; 1 = content is money

Map_Palettes_Addr = ramaddr($FFFFECD2)

Tile_Coll_Run_Event_Flag = ramaddr($FFFFECE1)	; only bit 0 seems to be used; if set, it disables tile collision and event checks; this can only be changed in the Debug Window
Field_Poison_Flag = ramaddr($FFFFECE6)	; if 0, poison won't hurt you while walking, otherwise set to 1
Random_Battles_Flag = ramaddr($FFFFECE7)

Saved_Sound_Index = ramaddr($FFFFECEC)

Battle_Type = ramaddr($FFFFECEE)	; 0 = Profound Darkness battle; 1 = event (or boss) battle; 2 = random battle
Mota_Battle_BG_Index = ramaddr($FFFFECEF)	; Motavia (outside) has different backgrounds depending on the tile you're standing on
Char_Move_Flags = ramaddr($FFFFECFE)	; bitfield ; bit 0 = follow lead character; bit 1 = update movement order (X first, Y second or viceversa)
												   ; bit 2 = lock camera

	if dialogue_uncompressed = 1
Saved_Dialogue_Addr = ramaddr($FFFFED64)	; dword if dlg uncompressed since we must point at correct ROM address AND there's more than 64 kb of dialogue... Note that this is used by a macro so this is mostly for documenting
	else
Saved_Dialogue_Addr = ramaddr($FFFFECF0)	; word if dlg compresssed, since it's in RAM it just gets sign-extended
	endif
Map_Dialogue_Trees_Addr = ramaddr($FFFFECF8)

Event_Battle_Index = ramaddr($FFFFECFC)

Render_Sprites_In_Cutscenes = ramaddr($FFFFECFD)	; byte ; 0 = render sprites in cutscenes; 1 = don't render sprites in cutscenes

Panel_Index = ramaddr($FFFFED00)
Panel_Num = ramaddr($FFFFED02)
Panel_Tile_Backup_Curr = ramaddr($FFFFED04)
Panel_Data = ramaddr($FFFFED10)
Panel_VRAM_Destination = ramaddr($FFFFED10)
Panel_Art_Addr = ramaddr($FFFFED12)
Panel_Row_Size = ramaddr($FFFFED16)
Panel_Col_Size = ramaddr($FFFFED17)
Panel_X_Pos = ramaddr($FFFFED18)
Panel_Y_Pos = ramaddr($FFFFED19)
Panel_Art_Tile_1 = ramaddr($FFFFED1A)
Panel_Palette_Addr_1 = ramaddr($FFFFED1C)
Panel_Pattern_Addr_1 = ramaddr($FFFFED20)
Panel_Art_Tile_2 = ramaddr($FFFFED24)
Panel_Palette_Addr_2 = ramaddr($FFFFED26)
Panel_Pattern_Addr_2 = ramaddr($FFFFED2A)
Panel_Tile_Backup_List = ramaddr($FFFFED30)

Town_Teleport_Flag = ramaddr($FFFFED50)	; if 0, you can use Ryuka and Telepipe
Dungeon_Teleport_Index = ramaddr($FFFFED51)	; index which determines the coordinates you get teleported at (through Escapipe or Hinas) for every dungeon; if 0, teleport doesn't work
Yes_No_Option = ramaddr($FFFFED53)		; byte ; 0 = Yes; 1 = No
Saved_Char_ID_Mem_1 = ramaddr($FFFFED54)
Saved_Char_ID_Mem_2 = ramaddr($FFFFED55)
Saved_Char_ID_Mem_3 = ramaddr($FFFFED56)
Saved_Char_ID_Mem_4 = ramaddr($FFFFED57)
Saved_Char_ID_Mem_5 = ramaddr($FFFFED58)

; this is only used if uncompressed_dialogs is true
Current_Dialogue_Tree = ramaddr($FFFFED60)

TextCounter = ramaddr($FFFFED90)		; Used to count scrolling intro text or ending credits frame count
FadeControl = ramaddr($FFFFED95)		; Used to count palette fade in/out frames
CredText_A = ramaddr($FFFFED96)			; Additional flags for palette fade in/out
CredText_B = ramaddr($FFFFED98)			; additional flags for palette fade in/out

Battle_Priority = ramaddr($FFFFEE45)	; 0 = normal; 1 = surprise attack; $FF = ambush

Ability_Effect_Type = ramaddr($FFFFEE4A)	; word ; 0 = physical attack; 1 = enemy skill; 2 = technique; 3 = skill; 4 = item

Close_Range_Wpn_Sound = ramaddr($FFFFEE61)

Macro_Item_Slots = ramaddr($FFFFEE6A)
Macro_Item_Slot_1 = ramaddr($FFFFEE6A)	; inventory index of item used in a macro (character 1)
Macro_Item_Slot_2 = ramaddr($FFFFEE6B)	; inventory index of item used in a macro (character 2)
Macro_Item_Slot_3 = ramaddr($FFFFEE6C)	; inventory index of item used in a macro (character 3)
Macro_Item_Slot_4 = ramaddr($FFFFEE6D)	; inventory index of item used in a macro (character 4)
Macro_Item_Slot_5 = ramaddr($FFFFEE6E)	; inventory index of item used in a macro (character 5)

Saved_Sound_Index_2 = ramaddr($FFFFEEE0)
Saved_Sound_Index_3 = ramaddr($FFFFEEE4)
Saved_Sound_Index_4 = ramaddr($FFFFEEE6)

Game_Mode_Index = ramaddr($FFFFEF00)

Joypad_Ctrl = ramaddr($FFFFEF02)
Joypad_Held = ramaddr($FFFFEF02)	; byte
Joypad_Pressed = ramaddr($FFFFEF03)	; byte
Button_Held_Frames = ramaddr($FFFFEF04)	; byte
Button_Held_Timer = ramaddr($FFFFEF08)	; byte

VDP_Reg1_Val = ramaddr($FFFFEF0A)
RNG_Seed = ramaddr($FFFFEF0C)

VInt_Flag = ramaddr($FFFFEF12)
DMA_Last_Write = ramaddr($FFFFEF14)

VDP_Reg12_Val = ramaddr($FFFFEF16)

Main_Frame_Count = ramaddr($FFFFEF1C)
DMA_Commands_Buf_Slot = ramaddr($FFFFEF1E)

VDP_Status_Reg = ramaddr($FFFFEF22)
VInt_Frame_Count = ramaddr($FFFFEF24)
CRAM_Update_Flag = ramaddr($FFFFEF26)

Camera_Y_Pos_FG = ramaddr($FFFFEF90)
Camera_X_Pos_FG = ramaddr($FFFFEF94)
Camera_Y_Pos_BG = ramaddr($FFFFEF98)
Camera_X_Pos_BG = ramaddr($FFFFEF9C)

Battle_Turn_Order = ramaddr($FFFFEFB0)	; Index and agility of characters and enemies; order is from highest to lowest agility
											; bytes 1-2 = index; bytes 3-4 = agility

; --------------------------------------------------
; Data saved in SRAM
SRAM_Buffer = ramaddr($FFFFF000)

PS4_String = ramaddr($FFFFF000)
Save_Slot = ramaddr($FFFFF012)	; Starts from 0
SRAM_Bytes_Sum = ramaddr($FFFFF014)

Event_Flags = ramaddr($FFFFF100)
Chest_Flags = ramaddr($FFFFF120)
Temp_Event_Flags = ramaddr($FFFFF140)
Town_Flags = ramaddr($FFFFF160)

World_Index = ramaddr($FFFFF400)	; 0 = Motavia; 1 = Dezolis; 2 = Rykros; 3 = Zelan; 4 = Kuran; 5 = Air Castle
Saved_Field_Map_Index_2 = ramaddr($FFFFF402)
Saved_Field_Map_Index = ramaddr($FFFFF404)
Saved_Char_X_Pos = ramaddr($FFFFF406)
Saved_Char_Y_Pos = ramaddr($FFFFF408)
Current_Party_Slots = ramaddr($FFFFF40A)
Current_Party_Slot_1 = ramaddr($FFFFF40A)
Current_Party_Slot_2 = ramaddr($FFFFF40B)
Current_Party_Slot_3 = ramaddr($FFFFF40C)
Current_Party_Slot_4 = ramaddr($FFFFF40D)
Current_Party_Slot_5 = ramaddr($FFFFF40E)
Char_ID_Mem_End = ramaddr($FFFFF40F)

Inventory = ramaddr($FFFFF410)

Current_Money = ramaddr($FFFFF438)

Vehicle_Index = ramaddr($FFFFF43C)	; 0 = No vehicle; 1 = Land Rover; 2 = Ice Digger; 3 = Hydrofoil

Button_Mappings_Index = ramaddr($FFFFF43E)
Message_Speed = ramaddr($FFFFF440)
Battle_Speed = ramaddr($FFFFF442)

Macro_Data = ramaddr($FFFFF444)	; 8 slots for the Macro data; each slot takes up 20 bytes which in turn contain 4 bytes per character;
								; Character values are as follows:
								;   Byte 1 = Character ID
								;   Byte 2 = Command index
								;   Byte 3 = Technique, Skill or Item ID; 0 when command chosen is attack or defense
								;   Byte 4 = empty; most likely included for alignment purposes; can be used to store other data

Character_Stats = ramaddr($FFFFF500)
Chaz_Stats = ramaddr($FFFFF500)
Alys_Stats = ramaddr($FFFFF580)
Hahn_Stats = ramaddr($FFFFF600)
Rune_Stats = ramaddr($FFFFF680)
Gryz_Stats = ramaddr($FFFFF700)
Rika_Stats = ramaddr($FFFFF780)
Demi_Stats = ramaddr($FFFFF800)
Wren_Stats = ramaddr($FFFFF880)
Raja_Stats = ramaddr($FFFFF900)
Kyra_Stats = ramaddr($FFFFF980)
Seth_Stats = ramaddr($FFFFFA00)


Saved_Vehicle_Stats = ramaddr($FFFFFA80)	; used outside of battle
Land_Rover_Stats = ramaddr($FFFFFA80)
Ice_Digger_Stats = ramaddr($FFFFFAA0)
Hydrofoil_Stats = ramaddr($FFFFFAC0)

; End of data saved in SRAM
; --------------------------------------------------


Palette_Table_Buffer = ramaddr($FFFFFB00)
Palette_Line_2 = ramaddr($FFFFFB20)
Palette_Line_3 = ramaddr($FFFFFB40)
Palette_Line_4 = ramaddr($FFFFFB60)

Palette_Table_Buffer_2 = ramaddr($FFFFFB80)
Palette_2_Line_2 = ramaddr($FFFFFBA0)
Palette_2_Line_3 = ramaddr($FFFFFBC0)
Palette_2_Line_4 = ramaddr($FFFFFBE0)

Sprite_Table_Buffer = ramaddr($FFFFFC00)

Palette_Table_Buffer_3 = ramaddr($FFFFFE80)
Sprite_Num = ramaddr($FFFFFE80)
Sprite_Table_Buf_Addr = ramaddr($FFFFFE82)

Init_String_Addr = ramaddr($FFFFFFFC)

RAM_End = ramaddr($FFFFFFFF)

; --- variable-width font -------------------------------------------
; Declared here rather than squatted on. $FF500A (Sound_Index) is the
; last symbol below and $FF6000 (Chunk_Table) the first above, giving
; 4086 bytes; the Japanese-ROM savestates independently showed this
; region quiet across fifteen captures.
VWF_RAM_Base = ramaddr($FFFF5400)
VWF_Scratch  = VWF_RAM_Base		; 7 rows x 12 bytes = 84
VWF_Tiles    = VWF_RAM_Base+$60		; composed 4bpp output
VWF_Dbg_Run   = VWF_RAM_Base+$40	; cells written by the current call
VWF_Dbg_Max   = VWF_RAM_Base+$42	; largest single call seen
VWF_Dbg_Calls = VWF_RAM_Base+$44	; calls counted

; dialogue VWF state.  Placed at +$80 to clear VWF_Scratch, which is 84
; bytes ($00-$53) -- the debug counters at +$40 sit inside it.
VWFDia_DirtyCell = VWF_RAM_Base+$80	; first cell touched by the last glyph
VWFDia_DirtyLine = VWF_RAM_Base+$82	; 0 or 1
VWFDia_DirtySpan = VWF_RAM_Base+$84	; cells to flush, 1 or 2

; --- menu VWF pool ------------------------------------------------
; Tiles are allocated by content: a composed tile that already exists in
; the pool is reused rather than duplicated.  The camp technique window
; costs nothing this way, since every one of its names also appears in
; the battle list.
; Bank layout, settled by measurement rather than assumption:
;   $680        the blank used for the space (from ArtNem_WindowTiles)
;   $681-$696   fixed glyphs for labels, packed through VWFMenu_FixedMap
;   $697-$6EC   the pool
;   $6ED-$6FF   window frames, compacted from their scattered positions
; Numbers are not in this bank at all - HP/TP, levels and stat values are
; drawn from the second font copy at $7C0, which is live and untouched.
; Labels are drawn proportionally along with everything else: the colon
; belongs to the numeric field, not the label, so a left-aligned
; proportional label and a right-aligned fixed colon-plus-digits keep
; their columns.  Expanding an abbreviation into mixed case is cheaper
; than the abbreviation was, since small caps are 5.08px against 6.08 for
; true caps.
; The tables the pool exists for.  Taken from the ASSEMBLED symbols in
; ps4.lst, not from script_translated.json: the json's `offset` fields are
; the original ROM's, and the translated tables land somewhere else
; entirely.  Using them put the floor above almost the whole group, so
; every name failed the test and drew fixed-width - which is exactly what
; the first build showed.
;   InventoryNames   $2AAFA6
;   TechniqueNames   $2AB614
;   SkillNames       $2AB6F4
;   PlaceNames       $2AB894
;   InventoryNames2  $2ABA62 .. $2AC0D0
; They run together, so one range covers the group.  Place names are
; included deliberately: they truncate in stock too.
; Taken as SYMBOLS, not literals.  A hardcoded address here is what put
; the floor above the whole group once already, and EnemyNames has since
; moved from $280D52 to $280D58 on its own - the assembler tracks that,
; a constant does not.
VWFMENU_NAMES_LO = InventoryNames
VWFMENU_NAMES_HI = loc_2AC0DE		; first symbol past InventoryNames2
; Enemy names and enemy skill names, drawn in battle.  A separate range
; because party and class names sit just below EnemyNames, and those must
; stay fixed - they are creep-coded and the VWF face gives them width 0.
;   EnemyNames       $280D52
;   EnemySkillNames  $2812F4 .. EnemyData $2816CC
VWFMENU_ENEMY_LO = EnemyNames
VWFMENU_ENEMY_HI = EnemyData
; Combination names, drawn in the battle combo window.  They sit in their own
; bank far below both other groups - ComboNames $29F69C, with the vehicle
; attack names directly above them - so neither existing range reaches them
; and every one of them was still drawing fixed-width out of the US table:
; TRIBLASTER for what the JP ROM calls トリニティブラスター.
; Composed, not stripped: the strip index is keyed off VWFMENU_NAMES_LO and
; has no entries for this table.
; VehicleAttackNames is covered too.  Its field is narrower -
; Battle_VehOpenSkills frames 14 cells, writes a cursor at column 1 and the
; two state icons at columns 11 and 12, so the name owns columns 3..10 - which
; is eight cells, not the seven the US names suggest.
;
; The ceiling is VehicleSkillData, NOT VehicleData.  The order in ROM is
; ComboNames $29F69C, VehicleData $29F74E, VehicleAttackNames $29F79C: the
; stats table sits BETWEEN the two name tables.  Stopping at VehicleData
; therefore covered only ComboNames and left every vehicle attack drawing
; fixed-width, which is what test_paths caught.  Taking the range past both
; also spans VehicleData, which is harmless - it is stats, never handed to
; the composer as text.
VWFMENU_COMBO_LO = ComboNames
VWFMENU_COMBO_HI = VehicleSkillData
; The nine Hunters Guild job titles.  Composed rather than drawn fixed-width,
; which is what lets them say what the Japanese says: "The Ranch Owner of
; Mile" is 23 characters and would never have fit the 16-cell fixed field, but
; it composes to 15 cells.
;
; This one costs pool.  The board draws all eight rows at once and they are
; all live on the plane together, so the sweep cannot reclaim any of them -
; measured at 75 of 83 slots for the worst case.  tools/guildnames.py checks
; the COMBINED demand of the whole board, not just each title's width, so a
; later edit cannot quietly push it over.
VWFMENU_GUILD_LO = GuildText_RanchOwner
VWFMENU_GUILD_HI = Event_RuneHealingChaz
; The spaceship's destination menu: the prompt, the RAM-appended
; confirmation tail and the six destination names, contiguous at
; loc_2AAA46.  Composed so the names need not be abbreviated to seven
; fixed cells (A.CASTL); tools/spacemenu.py ports them from the JSON.
VWFMENU_SPACE_LO = loc_2AAA46
VWFMENU_SPACE_HI = SpaceMenuText_End
; Battle status-effect messages ("Energy Barrier UP!", " has slept!"): the
; 18x3 message window holds 16 fixed cells, which forced the abbreviations.
; Composed, the longest is 11 cells with room for a party name in front.
VWFMENU_EFFECT_LO = loc_27E5D2
VWFMENU_EFFECT_HI = BattleEffectText_End
; Battle result tails that follow an item name (" found!", " received!",
; " discarded.", " used!", " was" / "given up.").  Composed so the 20-wide
; box (18 inside) takes the widest item name plus an unabbreviated tail:
; "Plasma Launcher discarded." is 16.  The Yes/No prompts between the
; two ranges stay fixed-width - they are cursor targets.
VWFMENU_RESULT_LO = loc_27E76E
VWFMENU_RESULT_HI = loc_27E784
VWFMENU_RESULT2_LO = loc_27E7C6
VWFMENU_RESULT2_HI = BattleResultText_End
; Everything between the status-effect messages and the result tails:
; the battle command menu (" COMD/ MACRO/ RUN"), "Surprise Attack!",
; "DEFENSE", " retreated!", "Cannot escape!", " defeated...!",
; " recovered!", "ATTACK" and the vehicle menu ("ATTACK/OPTION/RUN").
; The name in front of the four tails already composed - party and enemy
; records take the record paths - so they were the last bold fixed-width
; run on a proportional line; ATTACK and DEFENSE sit in the macro window
; next to composed technique names; and the two menus are vertical lists
; whose cursor is the $67 tile at a fixed column, which the composer
; lets through as a graphic (width 0) before composing the label after
; it.  Composed, the vehicle menu no longer has to say ATTAC and OPTIN.
VWFMENU_FLOW_LO = loc_27E6E8
VWFMENU_FLOW_HI = loc_27E76E		; = VWFMENU_RESULT_LO
; Window chrome (vwf_menu_chrome=1) is gated by a table in vwfmenu.asm,
; VWFMenu_ChromeTable, not by constants here.  Two kinds of entry.  Plain
; ones compose like anything else: the menus and captions, whose only
; furniture is the $67 cursor tile the composer already lets through.
; PAD ones are the labels that position themselves with spaces against
; numbers the numeric path draws at fixed columns: there a space that
; starts a run, sits in a run of spaces, or precedes a colon / graphic /
; control advances the pixel cursor to the NEXT CELL BOUNDARY (a whole
; cell when already on one), a lone space between glyphs is a word space,
; and the colon is the stock tile from the $7C0 copy in one cell.  So
; "Strength   :" puts its colon exactly where "STRNGTH:" did, and
; "Strength increased by    !" composes as prose and leaves the blank
; cells the level-up code scans for.  The pad counts in the strings are
; derived from the face by tools/test_paths.py, which asserts every colon,
; cursor and control code lands on its stock column.
; Width of that window.  Stock is 18 (16 inside); nothing sits to its right
; on rows 18-20 (or 12-14 in a vehicle) and the teardown restores all 40
; columns.  Composed and unabbreviated the widest line is "GrassSlaughterer
; is paralyzed!" at 18 cells, so 20 wide fills the box without slack.
	if vwf_menu=1
BATTLE_EFFECT_W = 20
	else
BATTLE_EFFECT_W = $12
	endif
VWFMENU_FIXED0  = $681          ; the colon, which stays with the digits
VWFMENU_FIXEDN  = 1
VWFMENU_TILE0   = $682          ; first pool tile
; Every slot has VRAM behind it.  A VWFMENU_VRAM constant used to be
; described here as capping which slots were backed - 'slots at or above
; VWFMENU_VRAM draw blank' - but no such constant exists in the source and
; nothing reads one.  It reads like an explanation for a missing name; it
; is not one.
; How far VWFMenu_TileSlot reaches, as an offset from $680.  It must cover
; the highest tile the pool can name; tools/menupool.py asserts that and
; sizes pooltile.bin to match.  128 only reached the $680 bank.
VWFMENU_TILESPAN = 384
VWFMENU_BASE_SLOTS = 114        ; arrays in VWF_RAM_Base remain this size.
                                ; The field-only tail lives in the quiet
                                ; battle setup RAM at $FFFF4200-$443F.
VWFMENU_SLOTS   = 146           ; 114 established slots plus 32 field-only
                                ; glyph tiles reclaimed from the dead
                                ; lowercase / Japanese fixed-font banks.
	if vwf_menu_chrome=1
VWFMENU_ACTIVE_SLOTS = VWFMENU_SLOTS
	else
VWFMENU_ACTIVE_SLOTS = 88
	endif
VWFMENU_BATTLE_SLOTS = 88       ; $7C0 bank can hold battle sprite art
                                ; frame range.  tools/menupool.py derives
                                ; this: savestate evidence gives the
                                ; candidates, then every tile named by a
                                ; code immediate is removed.  Seven were:
                                ; $6E0 $6EB $6EC $6EF $6F0 $6F2 $6FF.
; NOTE: there is no frame compaction.  A VWFMENU_FRAME0 constant used to
; sit here describing frames "compacted" to $6ED-$6FF; nothing ever read
; it and no code moved a frame tile.  Believing it cost 28 tiles of pool
; that measurement says are free.  Frame tiles are wherever the stock
; game leaves them, and tools/menupool.py finds the unused ones by
; scanning savestates rather than by trusting a layout that was only
; ever aspirational.
VWFMENU_PAPER   = $EEEEEEEE     ; ink is $F, and $E|$1 = $F
VWFMENU_DEPTH   = 16            ; window nesting we track marks for

VWFMenu_PoolTop = VWF_RAM_Base+$100     ; next free slot
; VWFMENU_DEPTH words = 32 bytes, so this owns +$102..+$121 and NOTHING else
; may sit inside it.  Peak, Mark_Cur and RemapIdx used to live at +$106,
; +$108 and +$10A - which is Marks[2], Marks[3] and Marks[4].  A window three
; deep wrote PoolTop over Mark_Cur, and every Mark_Cur update corrupted the
; mark stack in return; Release then restored PoolTop from a slot holding a
; window index, which is how savestates show PoolTop at 202 and 457 against a
; cap of 83.  Confirmed from three savestates where Marks[2..4] equal Peak,
; Mark_Cur and RemapIdx exactly.
VWFMenu_Marks   = VWF_RAM_Base+$102     ; VWFMENU_DEPTH words, one per window
VWFMenu_Keys    = VWF_RAM_Base+$140     ; VWFMENU_BASE_SLOTS * 8-byte keys
VWFMenu_Peak    = VWF_RAM_Base+$122     ; high-water mark of PoolTop
VWFMenu_Refs    = VWF_RAM_Base+$4D0     ; VWFMENU_BASE_SLOTS bytes
; A strip still has one head (StripOf=head index, continuations=$FFFF and
; composer slots=$FFFE), but its members need not be adjacent in slot-index
; space.  StripNext links every member to the next logical cell and the final
; member back to the head.  +$54C..+$597 is clear of Refs (+$500..+$54B) and
; Scratch (+$600), with the size tied to VWFMENU_SLOTS in checkbuild.py.
VWFMenu_StripNext = VWF_RAM_Base+$542   ; VWFMENU_BASE_SLOTS bytes, next slot
VWFMenu_Mark_Cur = VWF_RAM_Base+$124    ; innermost window's mark; slots below
                                        ; it belong to windows further out
; Keys run from +$140 for VWFMENU_SLOTS*8 bytes, ending at +$4D0; refs and
; the hash links then occupy +$4D0..+$5B4.  Scratch stays above the saved-key
; ledger and ends at SaveTop.
VWFMenu_Scratch = VWF_RAM_Base+$980

; Recompose-on-reveal.  A window that covers menu text used to pin that
; text's tiles for as long as it stayed open, because the saved plane map
; still referenced them.  Instead we record each covered tile's
; composition key here, let the tile be reclaimed, and re-allocate it when
; the window closes - rewriting the saved map to wherever it lands.
; In the composed build, records are deduplicated globally by their immutable
; 8-byte key.  Comparing the old physical tile number across save passes was
; unsafe after that tile had been recycled; limiting dedup to one pass instead
; made Status > Tech > Skills exhaust all 96 old records at depths 12-13 and
; leave raw pool references under the later windows.  Dropping the redundant
; physical tile word first made room for 104 keys, but the field pool later
; grew to 114 slots; the ledger must cover every one of them or a deep window
; can still restore a tile after its slot was reassigned.  The strip build
; retains its old bound/layout because its records carry strip metadata.
	if vwf_menu_strips=0
VWFMENU_SAVEN   = 146
VWFMENU_SAVERECSZ = 8
	else
VWFMENU_SAVEN   = 88
VWFMENU_SAVERECSZ = 10
	endif
VWFMenu_SaveTop = VWF_RAM_Base+$A88     ; next free entry
VWFMenu_SaveMark = VWF_RAM_Base+$A8A    ; VWFMENU_DEPTH words, stack marks
VWFMenu_RemapIdx = VWF_RAM_Base+$126    ; window index, held across loc_6881E
; +$102..+$121 is the window-mark stack.  WrapFlag used to sit at +$10C,
; which is Marks[5]: opening a five-deep Status window wrote $0100 into that
; mark, and closing it restored PoolTop=$0100 against an 83-slot pool.  The
; loctest1-status state captured that exact failure and the resulting missing
; strips.  +$128 is outside the mark stack and below Keys at +$140.
VWFMenu_WrapFlag = VWF_RAM_Base+$128   ; 1 while LoadWindowTiles is the
                                       ; caller: its per-character loop
                                       ; folds column 63 back to column 0
                                       ; of the same row, and a run of
                                       ; cells has to fold the same way
VWFMenu_StripReuseOK = VWF_RAM_Base+$12A ; non-zero only while the field Item
                                         ; page is synchronously repainting
VWFMenu_ForceCompose = VWF_RAM_Base+$12B ; dynamic field message explicitly
                                         ; requests the menu VWF for every run
VWFMenu_FieldReuseDepth = VWF_RAM_Base+$12C ; tracked windows whose saved
                                             ; regions can be reclaimed
VWFMenu_FieldReuseBlocked = VWF_RAM_Base+$12D ; untracked nesting: fail closed
VWFMenu_ReclaimInhibit = VWF_RAM_Base+$12E ; nesting count for no-sweep remaps
; nothing to give back", which are different bugs with different fixes.
; Strip slot -> the strip index living there, or $FFFF for a continuation
; slot.  Redrawing a window must be idempotent: without this the bump
; allocator hands out a fresh run every redraw and the pool fills with
; orphans - measured at 83 slots handed out against 32 actually on screen.
; Only slots below PoolTop are ever consulted, so a pool rewind implicitly
; invalidates the table and it never needs clearing.
VWFMenu_StripOf = VWF_RAM_Base+$900    ; strip build only: slot ownership
; Key index (vwf_menu_hash=1).  Both strip arrays are dead in the composed
; build.  The enlarged save ledger ends at +$950, so 32 bucket heads live
; immediately after it; the chain links still take StripNext (one byte per
; slot).  Both hold slot+1 so
; that zero - fresh RAM, an old savestate's cleared arrays, what Reset
; writes - is an empty chain.  Links from a savestate saved under another
; build are garbage: every walk is bounded and validated, and a garbage
; chain only costs a miss.
VWFMENU_BUCKETS = 32
VWFMenu_Bucket = VWF_RAM_Base+$950
VWFMenu_Next = VWFMenu_StripNext
VWFMenu_StripHit = VWF_RAM_Base+$AAA   ; non-zero when the strip was reused
; Pool level at the moment a character's command menu opens - after the
; enemy-name box and the party HUD are drawn, before any list is.  The
; tech/skill/item lists rewind to HERE, not to zero.  Rewinding to zero
; handed the enemy-name box's tiles to the item list, so the box displayed
; the first item in it.
VWFMenu_BattleBase = VWF_RAM_Base+$AAC ; word
; Set by SaveRegion while it records a covered strip cell, read when the
; record is appended.  A strip slot has no entry in VWFMenu_Keys - Keys is
; only written by the composer - so a strip record stores the strip index
; and the cell's offset within the strip instead, flagged by bit 15 of the
; record's tile word.
VWFMenu_SaveStripIdx = VWF_RAM_Base+$AAE  ; word
VWFMenu_SaveStripOff = VWF_RAM_Base+$AB0  ; word
; Battle has no field-style save/remap stack, but three short-lived surfaces
; have exact teardown boundaries.  Preserve the pool level at each open and
; restore it only after that surface is gone.  Results reuse one panel, so its
; active byte distinguishes the first draw from replacement of an older draw.
VWFMenu_BattleActionMark = VWF_RAM_Base+$AB2 ; word, player action-name window
VWFMenu_BattleEnemyMark  = VWF_RAM_Base+$AB4 ; word, enemy action-name window
VWFMenu_BattleResultMark = VWF_RAM_Base+$AB6 ; word, recurring results panel
VWFMenu_BattleResultActive = VWF_RAM_Base+$AB8 ; byte
; Composed names (vwf_menu_strips=0): the stock table entry being drawn,
; kept across the compose loop so DrawString_Done can pad to the stock
; character count and leave a0 on the stock terminator.  Zero when the
; string being composed is not a name.
VWFMenu_NameSrc = VWF_RAM_Base+$ABA ; long
; Non-zero while a name is drawn that must NOT be padded to its stock
; character count.  The padding exists for the menus' relative-positioned
; control codes; the location banner has none, centres the text on its
; real width, and "SPACEPORT" -> "AIRPORT" padded four blanks through
; the right frame.
VWFMenu_NoPad = VWF_RAM_Base+$ABE ; byte
; Pool level when the battle status-effect message window opens; each
; per-fighter rebuild of that window and its teardown rewind to it.
VWFMenu_BattleEffectMark = VWF_RAM_Base+$AC0 ; word
; Window_Destroy defers the reveal remap of its region until the plane is
; next sent (DMA_PlaneA) or a window is created, so a run of destroys
; reveals against the pool AFTER every one of them has released.  The
; list holds the window indices; VWFMENU_DEFER_MAX is its capacity.
VWFMENU_DEFER_MAX = 8
VWFMenu_DeferN = VWF_RAM_Base+$AC2   ; byte
VWFMenu_DeferList = VWF_RAM_Base+$AC3 ; VWFMENU_DEFER_MAX bytes
; SaveTop when the current SaveRegion pass began: its tile dedup must
; not match an older window's record for a reassigned slot.
VWFMenu_SavePassBase = VWF_RAM_Base+$ACC ; word
; Battle HUD name cache.  Stock code redraws the party status bar every
; frame, and with the menu VWF that composed all five names sixty times a
; second: sixteen pool hits a frame, each a linear scan of the key table,
; which was a third to a half of the frame in the Profound Darkness fight
; and dropped it to 30-40 fps.  It also wrapped the byte refcounts every
; 256 frames, so a list composed on that frame took the HUD's slots as free.
; One entry per Character_Stats record: the pool generation it was composed
; under, its cell count, and the tile offsets.  Valid only while TakeGen
; still matches - any Take or Reset moves the generation on.
VWFMENU_PARTY_N   = 11                   ; Character_Stats records
VWFMENU_PARTY_CELLS = 6                  ; a six-letter name is at most 6 cells
VWFMenu_TakeGen   = VWF_RAM_Base+$ACE    ; word
VWFMenu_PartyCache = VWF_RAM_Base+$AD0   ; 11 * 16: gen.w, cells.b, pad.b, tile.w x6
VWFMenu_PartyEntry = VWF_RAM_Base+$B80   ; long: entry being (re)composed, or 0
; Non-zero while the battle Item window pre-renders its off-screen pages:
; names draw as stock-length blanks instead of composing.  Every page is
; rebuilt by Battle_ItemPageRender on its way in, so those composes only
; ran the pool dry and cost a dozen frames on every open.
VWFMenu_SkipNames = VWF_RAM_Base+$B84    ; byte
VWFMenu_PadMode = VWF_RAM_Base+$B85      ; byte: this run is a PAD-range label
VWFMenu_PadRun = VWF_RAM_Base+$B86       ; byte: inside a run of pad spaces
	if vwf_menu_chrome=1
; A composed tail can arrive in a separate DrawString call after a party/name
; run.  Keep enough state to reopen that run's final cell: its plane end,
; content key and slot, plus the pixel phase within the cell.  Candidate is
; set only when the current call finished on a resident pool cell; Active and
; Deref belong to an in-progress merge.  The key copy validates the slot
; against reassignment before the next scratch buffer is seeded from it.
VWFMenu_GlueEnd = VWF_RAM_Base+$B88       ; long: a1 immediately after last cell
VWFMenu_GlueKey = VWF_RAM_Base+$B8C       ; 8 bytes: last cell's 1bpp key
VWFMenu_GluePhase = VWF_RAM_Base+$B94     ; byte: pixels used in last cell (1..7)
VWFMenu_GlueSlot = VWF_RAM_Base+$B95      ; byte: slot that owns GlueKey
VWFMenu_GlueCandidate = VWF_RAM_Base+$B96 ; byte: this call can become prior run
VWFMenu_GlueActive = VWF_RAM_Base+$B97    ; byte: first output replaces a1-2
VWFMenu_GlueDeref = VWF_RAM_Base+$B98     ; byte: old slot ref was decremented
VWFMenu_GlueFailed = VWF_RAM_Base+$B99    ; byte: an output cell was refused
VWFMenu_GlueOwned = VWF_RAM_Base+$B9A     ; byte: remembered cell owns a pool ref
	endif
VWFMenu_LayoutMagic = VWF_RAM_Base+$B9C   ; long: compressed save-record layout
; Pool level when the battle MACRO letters window opens; every macro
; preview redraw and both window closes rewind to it (see
; VWFMenu_BattleMacroOpen).
VWFMenu_BattleMacroMark = VWF_RAM_Base+$BA0 ; word
; Pool level when a character's main options window (COMMAND/MACRO/RUN)
; opens, before its labels compose; the close rewinds to it so the
; command menu's base does not carry eleven dead label slots.
VWFMenu_BattleOptionsMark = VWF_RAM_Base+$BA2 ; word
; Zero-count slots the composer keeps in hand past the frontier before it
; skips a pressure sweep (see VWFMenu_DrawString_NoSweep).
VWFMENU_SWEEP_RESERVE = 4
VWFMenu_SaveStack = VWF_RAM_Base+$5C0   ; composed: VWFMENU_SAVEN * 8-byte keys;
                                        ; strips: tile word + 8-byte payload

; The base VWF block cannot grow past $FFFF6000: Window_Create's saved-plane
; maps and several game-owned buffers begin there.  The composed field pool
; therefore keeps its first 114 entries exactly where VWF4 placed them and
; stores only slots/records 114..145 in battle setup RAM.  Battle_Reset runs
; before Enemy_Stats and Fighter data occupy this range, while battle
; allocation is hard-capped at 88 and never indexes these tails.
VWFMenu_KeysX      = ramaddr($FFFF4200) ; 32 * 8 = $100, $4200..$42FF
VWFMenu_RefsX      = ramaddr($FFFF4300) ; 32 bytes,     $4300..$431F
VWFMenu_NextX      = ramaddr($FFFF4320) ; 32 bytes,     $4320..$433F
VWFMenu_SaveStackX = ramaddr($FFFF4340) ; 32 * 8 = $100, $4340..$443F
