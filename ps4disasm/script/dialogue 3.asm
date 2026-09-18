; 0
	dc.b	$FF

; $1
	dc.b	"Seen the quicksand outside? It keeps"
	dc.b	$FC
	dc.b	"spreading! How long can this town last..."
	dc.b	$FF
; $2
	dc.b	"The soil around here was rich once,"
	dc.b	$FC
	dc.b	"and farming did well enough."
	dc.b	$FD
	dc.b	"Now the wells have run dry,"
	dc.b	$FC
	dc.b	"and the fields have withered away..."
	dc.b	$FF
; $3
	dc.b	$FA
	dc.b	$33, $01
	dc.b	"If it's Birth Valley you want, go and"
	dc.b	$FC
	dc.b	"ask in the village of Zema."
	dc.b	$FD
	dc.b	"Zema lies further northeast of here."
	dc.b	$FC
	dc.b	"Although..."
	dc.b	$FD
	dc.b	"there's been no sign of anyone there"
	dc.b	$FC
	dc.b	"lately. Did they all flee in the night?"
	dc.b	$FF
; $4
	dc.b	"If it's Birth Valley you want, go and"
	dc.b	$FC
	dc.b	"ask in the village of Zema."
	dc.b	$FD
	dc.b	"The ones who fled in the night seem"
	dc.b	$FC
	dc.b	"to be coming back now."
	dc.b	$FF
; $5
	dc.b	$FA
	dc.b	$65, $01
	dc.b	"Some strange religion is catching on"
	dc.b	$FC
	dc.b	"lately, I heard."
	dc.b	$FD
	dc.b	"And it's being spread by a man dressed all"
	dc.b	$FC
	dc.b	"in black, apparently!"
	dc.b	$FD
	dc.b	"What was his name again..."
	dc.b	$FC
	dc.b	"Zio! Zio, that was it, I'm sure of it."
	dc.b	$FF
; $6
	dc.b	"Haven't heard about that religion lately."
	dc.b	$FC
	dc.b	"Young folk tire of things so fast!"
	dc.b	$FF
; $7
	dc.b	$FA
	dc.b	$65, $01
	dc.b	"The castle that you can see beyond the"
	dc.b	$FC
	dc.b	"quicksand..."
	dc.b	$FD
	dc.b	"I could swear it wasn't there when I"
	dc.b	$FC
	dc.b	"went to bed, and suddenly there it was..."
	dc.b	$FD
	dc.b	"It must be my imagination, though!"
	dc.b	$FF
; $8
	dc.b	"The castle that you can see beyond the"
	dc.b	$FC
	dc.b	"quicksand..."
	dc.b	$FD
	dc.b	"It went up in a single night, and now it's"
	dc.b	$FC
	dc.b	"gone in a single night."
	dc.b	$FD
	dc.b	"I-it's my imagination, isn't it?"
	dc.b	$FF
; $9
	dc.b	"No matter how much I sweep, the sand"
	dc.b	$FC
	dc.b	"just blows right back in again."
	dc.b	$FD
	dc.b	"It's so frustrating!"
	dc.b	$FF
; $A
	dc.b	$FA
	dc.b	$33, $01
	dc.b	"Zema has been wiped out!!!!"
	dc.b	$FD
	dc.b	"......Or so they say?"
	dc.b	$FD
	dc.b	"Somebody go see, would you."
	dc.b	$FC
	dc.b	"N-not me. I'm a busy man."
	dc.b	$FF
; $B
	dc.b	"Zema lives!!!! That's actually true, I hear."
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
	dc.b	$FA
	dc.b	$1D, $06
	dc.b	$FA
	dc.b	$1C, $05
	dc.b	$FA
	dc.b	$1B, $04
	dc.b	$FA
	dc.b	$1A, $03
	dc.b	$FA
	dc.b	$19, $02
	dc.b	$FA
	dc.b	$18, $01
	dc.b	$FA
	dc.b	$35, $01
	dc.b	"This is the village of Mile. And this"
	dc.b	$FC
	dc.b	"here is my sand worm ranch, newly built!"
	dc.b	$FD
	dc.b	"Well? Aren't they charming?"
	dc.b	$FC
	dc.b	"The sightseers will come flocking now!"
	dc.b	$FF
; $12
	dc.b	"This is the village of Mile. And this"
	dc.b	$FC
	dc.b	"here is my sand worm ranch, but......"
	dc.b	$FD
	dc.b	"I've overfed them, I'd say. The"
	dc.b	$FC
	dc.b	"worms have grown a good deal bigger!"
	dc.b	$FD
	dc.b	"It's frightening, honestly it is."
	dc.b	$FC
	dc.b	"Wh-what do you think I should do...?"
	dc.b	$FF
; $13
	dc.b	$F6
	dc.w	$0070	; => Event_RanchOwner
	dc.b	$FF

; $14
	dc.b	"P-please, do something quickly."
	dc.b	$FF
; $15
	dc.b	$F6
	dc.w	$0072	; => Event_RanchOwnerAfterBattle
	dc.b	$FF

; $16
	dc.b	"Thank you kindly, hunter."
	dc.b	$FC
	dc.b	"Go and collect your reward at the guild."
	dc.b	$FF
; $17
	dc.b	"This is Mile... oh, it's you. Thanks for your"
	dc.b	$FC
	dc.b	"help last time."
	dc.b	$FD
	dc.b	"I'm pondering what to try next. Look"
	dc.b	$FC
	dc.b	"forward to it!"
	dc.b	$FF
; $18
	dc.b	$FA
	dc.b	$1B, $03
	dc.b	$FA
	dc.b	$19, $02
	dc.b	$FA
	dc.b	$35, $01
	dc.b	"My husband spent the last coin we had"
	dc.b	$FC
	dc.b	"on building that sand worm ranch,"
	dc.b	$FD
	dc.b	"but I do wonder whether anyone will ever"
	dc.b	$FC
	dc.b	"want to come see those things..."
	dc.b	$FF
; $19
	dc.b	"Our ranch's sand worms have grown so"
	dc.b	$FC
	dc.b	"large it's unsettling..."
	dc.b	$FF
; $1A
	dc.b	"Hunter, about those sand worms."
	dc.b	$FC
	dc.b	"I'm counting on you......"
	dc.b	$FF
; $1B
	dc.b	"If they'd been left as they were, sooner"
	dc.b	$FC
	dc.b	"or later the village would have suffered."
	dc.b	$FD
	dc.b	"And by the time that happened it would"
	dc.b	$FC
	dc.b	"have been too late."
	dc.b	$FD
	dc.b	"I feel sorry for the sand worms,"
	dc.b	$FC
	dc.b	"but it was for the best......"
	dc.b	$FD
	dc.b	"Thank you, hunter."
	dc.b	$FC
	dc.b	"We're in your debt."
	dc.b	$FF
; $1C
	dc.b	$FA
	dc.b	$1B, $03
	dc.b	$FA
	dc.b	$19, $02
	dc.b	$FA
	dc.b	$35, $01
	dc.b	"I'm the only daughter of the innkeeper."
	dc.b	$FC
	dc.b	"If working helps the family a little..."
	dc.b	$FF
; $1D
	dc.b	"They had some charm back when they"
	dc.b	$FC
	dc.b	"were little..."
	dc.b	$FD
	dc.b	"But now those sand worms just frighten"
	dc.b	$FC
	dc.b	"me..."
	dc.b	$FF
; $1E
	dc.b	"Please do something about the"
	dc.b	$FC
	dc.b	"sand worms at the ranch."
	dc.b	$FF
; $1F
	dc.b	"Father... he's gone and failed at"
	dc.b	$FC
	dc.b	"something again..."
	dc.b	$FD
	dc.b	"He can chase his whims because Mother"
	dc.b	$FC
	dc.b	"keeps the inn together so soundly."
	dc.b	$FD
	dc.b	"I love them both. Mother for that, and"
	dc.b	$FC
	dc.b	"Father for never being downhearted."
	dc.b	$FF
; $20
	dc.b	"Y-you're the hunters from the guild?"
	dc.b	$FD
	dc.b	"The sand worms I've been raising on this"
	dc.b	$FC
	dc.b	"ranch have grown beyond our control!"
	dc.b	$FD
	dc.b	"P-please! Do something about them!"
	dc.b	$FD
	dc.b	"I won't complain about the consequences,"
	dc.b	$FC
	dc.b	"just handle it!"
	dc.b	$FF
; $21
	dc.b	"Aaaah. The sand worms I'd finally managed"
	dc.b	$FC
	dc.b	"to tame... the ranch... my dream......"
	dc.b	$FD
	dc.b	"........."
	dc.b	$FD
	dc.b	"Thank you, hunter."
	dc.b	$FC
	dc.b	"What's done is done."
	dc.b	$FD
	dc.b	"Better to move on and put all my"
	dc.b	$FC
	dc.b	"efforts into the next thing."
	dc.b	$FD
	dc.b	"I'll send the fee over, so"
	dc.b	$FC
	dc.b	"collect it at the Guild."
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
	dc.b	$FF

; $29
	dc.b	$FF

; $2A
	dc.b	$FF

; $2B
	dc.b	$FF

; $2C
	dc.b	$FF

; $2D
	dc.b	$FF

; $2E
	dc.b	$FF

; $2F
	dc.b	$FF

; $30
	dc.b	$FF

; $31
	dc.b	$FF

; $32
	dc.b	$FF

; $33
	dc.b	$FF

; $34
	dc.b	$FF

; $35
	dc.b	$FF

; $36
	dc.b	$FF

; $37
	dc.b	$FF

; $38
	dc.b	$FF

; $39
	dc.b	$FF

; $3A
	dc.b	$FF

; $3B
	dc.b	$FF

; $3C
	dc.b	$FF

; $3D
	dc.b	$FF

; $3E
	dc.b	$FF

; $3F
	dc.b	$FF

; $40
	dc.b	$FF

; $41
	dc.b	$FF

; $42
	dc.b	$FF

; $43
	dc.b	$FF

; $44
	dc.b	$FF

; $45
	dc.b	$FF

; $46
	dc.b	$FF

; $47
	dc.b	$FF

; $48
	dc.b	$FF

; $49
	dc.b	$FF

; $4A
	dc.b	$FF

; $4B
	dc.b	$FF

; $4C
	dc.b	$FF

; $4D
	dc.b	$FF

; $4E
	dc.b	$FF

; $4F
	dc.b	$FF

; $50
	dc.b	$FF

; $51
	dc.b	$FF

; $52
	dc.b	$FF

; $53
	dc.b	$FF

; $54
	dc.b	$FF

; $55
	dc.b	$FF

; $56
	dc.b	$FF

; $57
	dc.b	$FF

; $58
	dc.b	$FF

; $59
	dc.b	$FF

; $5A
	dc.b	$FF

; $5B
	dc.b	$FF

; $5C
	dc.b	$FF

; $5D
	dc.b	$FF

; $5E
	dc.b	$FF

; $5F
	dc.b	$FF

; $60
	dc.b	$FF

; $61
	dc.b	$FF

; $62
	dc.b	$FF

; $63
	dc.b	$F3
	dc.b	"Ugh... monsters, from deeper in..."
	dc.b	$FF
; $64
	dc.b	$F3
	dc.b	"Professor Holt went in and never came"
	dc.b	$FC
	dc.b	"back... He's probably... already..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"No...!"
	dc.b	$FF
; $65
	dc.b	$F3
	dc.b	$F4
	dc.b	$01
	dc.b	"He's turned to stone..."
	dc.b	$FF
; $66
	dc.b	$F2
	dc.b	$03, $9F
	dc.b	$F2
	dc.b	$00, $00, $0A
	dc.b	$F9
	dc.b	$13
	dc.b	$F2
	dc.b	$00, $00, $0B
	dc.b	$F9
	dc.b	$13
	dc.b	$F2
	dc.b	$00, $00, $0C
	dc.b	$F4
	dc.b	$03
	dc.b	"Ah! Professor Holt!!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $0D
	dc.b	$F4
	dc.b	$01
	dc.b	"What in the world happened here...?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"...An ancient curse?! To think there's"
	dc.b	$FC
	dc.b	"someone capable of this nowadays...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"Is there no way to reverse this?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"I've heard of a medicine called Alshlin"
	dc.b	$FC
	dc.b	"that can undo petrification, but..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"Where can we find it?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"I heard of it in a Motavian village"
	dc.b	$FC
	dc.b	"once... though that was a long while back."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"A Motavian village, you say?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"The village of Molcum, a good long"
	dc.b	$FC
	dc.b	"way south of here."
	dc.b	$FD
	dc.b	$F2
	dc.b	$01
	dc.b	$F4
	dc.b	$03
	dc.b	"Right! Then let's go right away!!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $0E
	dc.b	$F4
	dc.b	$02
	dc.b	"To Molcum... let's see. I'll give you a huge"
	dc.b	$FC
	dc.b	"discount: 500 meseta."
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $0F
	dc.b	$F4
	dc.b	$03
	dc.b	"............Monster."
	dc.b	$F9
	dc.b	$3B
	dc.b	$FF
; $67
	dc.b	$F2
	dc.b	$00, $00, $23
	dc.b	$F4
	dc.b	$0D
	dc.b	"Oh? Why, if it isn't Hahn!"
	dc.b	$FC
	dc.b	"What a marvelous place this is!!"
	dc.b	$FD
	dc.b	"Relics of the earlier civilization are lying"
	dc.b	$FC
	dc.b	"around everywhere!"
	dc.b	$FD
	dc.b	"Perfect timing -- you others can also..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"Professor Holt! What are you saying!"
	dc.b	$FD
	dc.b	"Until a moment ago, Zio had you"
	dc.b	$FC
	dc.b	"turned to stone!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0D
	dc.b	"Eh? Did he now?"
	dc.b	$FD
	dc.b	"Well, I'm hale and hearty as you see,"
	dc.b	$FC
	dc.b	"so never mind that!"
	dc.b	$FD
	dc.b	"Right! We resume the survey at once!"
	dc.b	$FC
	dc.b	"Hahn!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"Yes!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0D
	dc.b	"You are to go back to the Academy and"
	dc.b	$FC
	dc.b	"report what has happened."
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"......Ugh, okay."
	dc.b	$FD
	dc.b	$F4
	dc.b	$0D
	dc.b	"All right then! Into the depths of"
	dc.b	$FC
	dc.b	"Birth Valley!!"
	dc.b	$F2
	dc.b	$00, $00, $24
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"What an odd old man...!"
	dc.b	$FC
	dc.b	"But anyway, that settles that."
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"I'm sorry, he hardly even thanked"
	dc.b	$FC
	dc.b	"you. He's always been like that."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Don't worry about that, Hahn!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"Well, the job's done and I'm tired."
	dc.b	$FC
	dc.b	"Let's take a load off today. Rudy?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Yeah!"
	dc.b	$FD
	dc.b	$F7
	dc.b	$F2
	dc.b	$00, $00, $27
	dc.b	$F4
	dc.b	$03
	dc.b	"I'll go back to the Academy."
	dc.b	$FC
	dc.b	"I must report all of this."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Right... and you, Pyke?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$05
	dc.b	"Me? I'm... I'm going to bring Zio down."
	dc.b	$FC
	dc.b	"Even if it means doing it alone!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"That's crazy!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$05
	dc.b	"Crazy or not, what do I care!"
	dc.b	$FC
	dc.b	"I've... I've made up my mind!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $28
	dc.b	$F9
	dc.b	$4F
	dc.b	$F2
	dc.b	$00, $00, $29
	dc.b	$F4
	dc.b	$02
	dc.b	"...And the job comes to an end..."
	dc.b	$FD
	dc.b	"Normally we'd be going home to Aiedo,"
	dc.b	$FC
	dc.b	"where the Hunters Guild is..."
	dc.b	$FD
	dc.b	$F2
	dc.b	$03, $FE
	dc.b	$F4
	dc.b	$00
	dc.b	"Aaaaaah!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $2A
	dc.b	$F2
	dc.b	$03, $A9
	dc.b	$F4
	dc.b	$02
	dc.b	"What was that?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"A scream!!"
	dc.b	$FF
; $68
	dc.b	$F2
	dc.b	$00, $00, $2B
	dc.b	$F4
	dc.b	$03
	dc.b	"Wh-what is this..."
	dc.b	$FC
	dc.b	"Oh no... Professor?!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"Let's go, Rudy!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Right!!"
	dc.b	$FF
; $69
	dc.b	$F2
	dc.b	$00, $00, $2C
	dc.b	$F4
	dc.b	$01
	dc.b	"Phew... how was it this time, Laila?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"Not bad. You're getting a little"
	dc.b	$FC
	dc.b	"better at it."
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $2D
	dc.b	$F4
	dc.b	$00
	dc.b	"A curse! This is what comes of"
	dc.b	$FC
	dc.b	"defiling the sanctuary!!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $2E
	dc.b	$F4
	dc.b	$01
	dc.b	"A curse... What in the world is in there...!?"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $00, $2F
	dc.b	$F4
	dc.b	$03
	dc.b	"Oh no! The Professor is still inside!"
	dc.b	$FD
	dc.b	".........."
	dc.b	$FD
	dc.b	"Um...... Miss Laila?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"Let's say 1000 meseta."
	dc.b	$FD
	dc.b	$F4
	dc.b	$03
	dc.b	"......M-my wedding fund......"
	dc.b	$FF
; $6A
	dc.b	$FA
	dc.b	$10, $04
	dc.b	$F6
	dc.w	$8002	; => Cutscene_ProfHolt
	dc.b	$FF

; $6B
	dc.b	$F3
	dc.b	$F4
	dc.b	$01
	dc.b	"It's been blocked by rocks."
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"Seed..."
	dc.b	$FF
; $6C
	dc.b	$FF

; $6D
	dc.b	$FF

; $6E
	dc.b	$F4
	dc.b	$03
	dc.b	"Professor Holt......"
	dc.b	$FD
	dc.b	$F4
	dc.b	$02
	dc.b	"Honestly, that's enough moping."
	dc.b	$FC
	dc.b	"We're going to Molcum!"
	dc.b	$FF
