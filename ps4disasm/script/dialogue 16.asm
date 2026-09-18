; 0
	dc.b	$FF

; $1
	dc.b	$FF

; $2
	dc.b	$FF

; $3
	dc.b	$FF

; $4
	dc.b	$FF

; $5
	dc.b	$FF

; $6
	dc.b	$FF

; $7
	dc.b	$FF

; $8
	dc.b	$FF

; $9
	dc.b	$FF

; $A
	dc.b	$FF

; $B
	dc.b	$FF

; $C
	dc.b	$FF

; $D
	dc.b	$FF

; $E
	dc.b	$FF

; $F
	dc.b	$FF

; $10
	dc.b	$FF

; $11
	dc.b	$FF

; $12
	dc.b	$FF

; $13
	dc.b	$FF

; $14
	dc.b	$FF

; $15
	dc.b	$FF

; $16
	dc.b	$FF

; $17
	dc.b	$FF

; $18
	dc.b	$FF

; $19
	dc.b	$FF

; $1A
	dc.b	$FF

; $1B
	dc.b	$FF

; $1C
	dc.b	$FF

; $1D
	dc.b	$FF

; $1E
	dc.b	$FF

; $1F
	dc.b	$FF

; $20
	dc.b	$FF

; $21
	dc.b	$FF

; $22
	dc.b	$FF

; $23
	dc.b	$FF

; $24
	dc.b	$FF

; $25
	dc.b	$FF

; $26
	dc.b	$FF

; $27
	dc.b	$FF

; $28
	dc.b	$F4
	dc.b	$09
	dc.b	"Drink, drink!"
	dc.b	$FC
	dc.b	"Ho ho ho!"
	dc.b	$FF
; $29
	dc.b	$F4
	dc.b	$09
	dc.b	"Mmm. Fine drink and fine food."
	dc.b	$FC
	dc.b	"Thisss is happiness, it really is."
	dc.b	$FF
; $2A
	dc.b	"Drinkers come from all over Dezolis,"
	dc.b	$FC
	dc.b	"swap their idle talk, and go home..."
	dc.b	$FD
	dc.b	"And Gyuna hears every word of it,"
	dc.b	$FC
	dc.b	"and passes it on down the line..."
	dc.b	$FD
	dc.b	"This is where folk's thoughts"
	dc.b	$FC
	dc.b	"gather, and where they set out from."
	dc.b	$FF
; $2B
	dc.b	"The master here, Gyuna, knows a lot,"
	dc.b	$FC
	dc.b	"but that old country accent is thick!"
	dc.b	$FF
; $2C
	dc.b	$FA
	dc.b	$A1, $01
	dc.b	"Heard there was a local brew that"
	dc.b	$FC
	dc.b	"was mighty fine, came a long way..."
	dc.b	$FD
	dc.b	"Now the snowstorm's buried the road"
	dc.b	$FC
	dc.b	"in ice and I can't get home. Hic."
	dc.b	$FF
; $2D
	dc.b	"Heard there was a local brew that"
	dc.b	$FC
	dc.b	"was mighty fine, came a long way..."
	dc.b	$FD
	dc.b	"Storm's stopped, but the ice walls"
	dc.b	$FC
	dc.b	"won't melt. Can't get home. Hic."
	dc.b	$FF
; $2E
	dc.b	"Whoa! What's all this, then?"
	dc.b	$FC
	dc.b	"A shady-looking bunch if ever I saw."
	dc.b	$FD
	dc.b	"You're spoiling my drink."
	dc.b	$FC
	dc.b	"Keep your distance, would you?"
	dc.b	$FF
; $2F
	dc.b	"Waaaaahhh. It was me, it was all"
	dc.b	$FC
	dc.b	"my fault. Please come back..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"A weepy drunk..."
	dc.b	$FC
	dc.b	"There's no dealing with him."
	dc.b	$FF
; $30
	dc.b	$F6
	dc.w	$005C	; => Event_Gyuna
	dc.b	$FF

; $31
	dc.b	$FA
	dc.b	$81, $01
	dc.b	$F4
	dc.b	$15
	dc.b	"Well, a first-time customer,"
	dc.b	$FC
	dc.b	"I reckon. Ho, a friend of Raja's?"
	dc.b	$FD
	dc.b	"Then I'll tell ya whatever ya like."
	dc.b	$FC
	dc.b	"Whatcha'll wanna hear, man?"
	dc.b	$FD
	dc.b	"The damage from that ol' snowstorm,"
	dc.b	$FC
	dc.b	"I reckon?"
	dc.b	$F5
	dc.b	$02, $04
	dc.b	$FF
; $32
	dc.b	$F4
	dc.b	$15
	dc.b	"Ah, Raja's friend, I reckon."
	dc.b	$FC
	dc.b	"What else y'all wanna know?"
	dc.b	$FD
	dc.b	"The damage from that ol' snowstorm,"
	dc.b	$FC
	dc.b	"I reckon?"
	dc.b	$F5
	dc.b	$01, $03
	dc.b	$FF
; $33
	dc.b	$FA
	dc.b	$A1, $01
	dc.b	"Ol' snowstorm started three months"
	dc.b	$FC
	dc.b	"back and it'll be going still, I reckon."
	dc.b	$FD
	dc.b	"Hats blown off, skin done gone rough"
	dc.b	$FC
	dc.b	"all over. Terrible disaster, man!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"..........."
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"Ahem! Tell ya the real trouble,"
	dc.b	$FC
	dc.b	"I reckon, is them walls of ice!"
	dc.b	$FD
	dc.b	"Storm's done heaped the snow up"
	dc.b	$FC
	dc.b	"everywhere and frozen it into dang walls."
	dc.b	$FD
	dc.b	"Dezolis's all cut into pieces, I tell ya."
	dc.b	$FC
	dc.b	"No getting around at all, man!"
	dc.b	$FF
; $34
	dc.b	"Heaven called or the earth cried out,"
	dc.b	$FC
	dc.b	"man, but that ol' storm plumb stopped."
	dc.b	$FD
	dc.b	"'Cept, from what I hear, man, that"
	dc.b	$FC
	dc.b	"Gungbius Grand ol' Temple has uhh..."
	dc.b	$FD
	dc.b	"No, no. Can't believe it, man."
	dc.b	$FC
	dc.b	"I won't."
	dc.b	$FF
; $35
	dc.b	"Dang ol' Gallberg Tower, I reckon?"
	dc.b	$F5
	dc.b	$00, $03
	dc.b	$FA
	dc.b	$A1, $02
	dc.b	$FA
	dc.b	$94, $01
	dc.b	"Some dang tower somewhere in Dezolis"
	dc.b	$FC
	dc.b	"where devils are said to dwell, man."
	dc.b	$FD
	dc.b	"Tell ya what, man, heard it rose up out of"
	dc.b	$FC
	dc.b	"nowhere in a single night!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$09
	dc.b	"That's it! Those devils will"
	dc.b	$FC
	dc.b	"be the ruin of this world!"
	dc.b	$FD
	dc.b	"Algol lies under a curse!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"What Raja says... could it be true?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"Couldn't tell ya, man."
	dc.b	$FD
	dc.b	"But him being what he is, might be he"
	dc.b	$FC
	dc.b	"has one o' them feelings, I reckon."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"And you've got no idea at all where"
	dc.b	$FC
	dc.b	"this Gallberg Tower stands?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"Every man who's come here'n seen it says"
	dc.b	$FC
	dc.b	"different. North, s'all I know, man."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"...I see."
	dc.b	$FF
; $36
	dc.b	"Some ol' tower somewhere in Dezolis"
	dc.b	$FC
	dc.b	"where devils are said to dwell, man."
	dc.b	$FD
	dc.b	"Tell ya what, man, heard it rose up out of"
	dc.b	$FC
	dc.b	"nowhere in a single night!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"And you've got no idea at all where"
	dc.b	$FC
	dc.b	"this Gallberg Tower stands?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"Narrowing down, I reckon!"
	dc.b	$FC
	dc.b	"North of Meese looks likely to me, man."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"...I see."
	dc.b	$FF
; $37
	dc.b	"Tell ya what, man, the Gallberg Tower has"
	dc.b	$FC
	dc.b	"up and vanished, I reckon."
	dc.b	$FD
	dc.b	"That's why that ol' storm stopped. Some"
	dc.b	$FC
	dc.b	"great strapping hero, they say,"
	dc.b	$FD
	dc.b	"with his hangers-on behind him,"
	dc.b	$FC
	dc.b	"brought that wicked ol' tower down."
	dc.b	$FD
	dc.b	"Now, who the heck could it be, I reckon?"
	dc.b	$FC
	dc.b	"Tell ya, nobody comes to mind, man."
	dc.b	$FF
; $38
	dc.b	"About Raja, I reckon?"
	dc.b	$F5
	dc.b	$00, $04
	dc.b	$FA
	dc.b	$DE, $03
	dc.b	$FA
	dc.b	$A1, $02
	dc.b	$FA
	dc.b	$94, $01
	dc.b	"Known him a long time, man."
	dc.b	$FC
	dc.b	"Weird dude. ...Tell ya what, though, man,"
	dc.b	$FD
	dc.b	"got a dang fine hand at the arts, and"
	dc.b	$FC
	dc.b	"mighty well respected at Gungbius."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Really. That old man?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"Some jealous types resented him for it,"
	dc.b	$FC
	dc.b	"set a dang ol' trap for him or whatever,"
	dc.b	$FD
	dc.b	"and Raja got sent off to this here"
	dc.b	$FC
	dc.b	"backwater, I reckon."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"That happened...?"
	dc.b	$FC
	dc.b	"You'd never know it to look at him."
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"And he's happy as can be, too, man! Free"
	dc.b	$FC
	dc.b	"of that stuffy ol' temple, I reckon!"
	dc.b	$FD
	dc.b	"Man's a good egg, tell ya what!"
	dc.b	$FC
	dc.b	"Dang ol' best of friends!"
	dc.b	$FF
; $39
	dc.b	"Raja's fallen, I reckon? Man's the"
	dc.b	$FC
	dc.b	"sort ya couldn't kill with an axe."
	dc.b	$FD
	dc.b	"......Kinda dang ol' worried, man......"
	dc.b	$FF
; $3A
	dc.b	"Raja's down, and dang ol' rumors say"
	dc.b	$FC
	dc.b	"the Gungbius Grand ol' Temple has..."
	dc.b	$FD
	dc.b	"It's a lie, I reckon. Why we gotta get"
	dc.b	$FC
	dc.b	"nothing but bad news, man?"
	dc.b	$FF
; $3B
	dc.b	"Known him a long time, man."
	dc.b	$FC
	dc.b	"Weird dude. ...Tell ya what, though, man,"
	dc.b	$FD
	dc.b	"got a dang fine hand at the arts, and"
	dc.b	$FC
	dc.b	"mighty well respected at Gungbius."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Really. That old man?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"Some jealous types resented him for it,"
	dc.b	$FC
	dc.b	"set a dang ol' trap for him or whatever,"
	dc.b	$FD
	dc.b	"and Raja got sent off to this here"
	dc.b	$FC
	dc.b	"backwater, I reckon."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"That happened...?"
	dc.b	$FC
	dc.b	"You'd never know it to look at him."
	dc.b	$FD
	dc.b	$F4
	dc.b	$15
	dc.b	"And he's happy as can be, too, man! Free"
	dc.b	$FC
	dc.b	"of that stuffy ol' temple, I reckon!"
	dc.b	$FD
	dc.b	"Man's a good egg, tell ya what!"
	dc.b	$FC
	dc.b	"Dang ol' best of friends!"
	dc.b	$FF
; $3C
	dc.b	"Where the spaceship lies, I reckon?"
	dc.b	$F5
	dc.b	$00, $02
	dc.b	$FA
	dc.b	$82, $01
	dc.b	"Dang ol' spaceship, would that be the one"
	dc.b	$FC
	dc.b	"I heard's under the town of Tyler?"
	dc.b	$FD
	dc.b	"I dunno the details, but search"
	dc.b	$FC
	dc.b	"them graves well and a way opens, man."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Graves...?"
	dc.b	$FF
; $3D
	dc.b	"...What are y'all on about now, I reckon."
	dc.b	$FF
; $3E
	dc.b	"Come on back again, man."
	dc.b	$FF
