; 0
	dc.b	"Who goes there!"
	dc.b	$FC
	dc.b	"I'll let no suspicious soul pass!"
	dc.b	$FF
; $1
	dc.b	"Oh, Shess!"
	dc.b	$FC
	dc.b	"Good of you to come home!"
	dc.b	$FF
; $2
	dc.b	"Ah, friends of Shess?"
	dc.b	$FC
	dc.b	"Please, come in."
	dc.b	$FF
; $3
	dc.b	"The wall of ice has shut this"
	dc.b	$FC
	dc.b	"mansion off from the world outside."
	dc.b	$FF
; $4
	dc.b	$FF

; $5
	dc.b	"When Shess loses her temper,"
	dc.b	$FC
	dc.b	"she acts before she even thinks!"
	dc.b	$FF
; $6
	dc.b	$FF

; $7
	dc.b	$FF

; $8
	dc.b	"Shess is a fine girl, but once her mind is"
	dc.b	$FC
	dc.b	"made up, she fixates on it really hard..."
	dc.b	$FF
; $9
	dc.b	$FF

; $A
	dc.b	$FF

; $B
	dc.b	"The snowstorm has cleared, but the"
	dc.b	$FC
	dc.b	"wall of ice..."
	dc.b	$FD
	dc.b	"It will take a long time for things to"
	dc.b	$FC
	dc.b	"return to normal."
	dc.b	$FF
; $C
	dc.b	$FF

; $D
	dc.b	"The weather should become a little"
	dc.b	$FC
	dc.b	"gentler now."
	dc.b	$FF
; $E
	dc.b	"The rooms around here belong to those"
	dc.b	$FC
	dc.b	"gone to Meese. Empty for now."
	dc.b	$FF
; $F
	dc.b	$FF

; $10
	dc.b	"Just as the strange wave weakened,"
	dc.b	$FC
	dc.b	"a huge explosion happened..."
	dc.b	$FD
	dc.b	"What in the world was that..."
	dc.b	$FF
; $11
	dc.b	"Espers are people too. We eat, and"
	dc.b	$FC
	dc.b	"we use the restroom, like anyone else."
	dc.b	$FD
	dc.b	"And if we don't sleep,"
	dc.b	$FC
	dc.b	"we'll die!"
	dc.b	$FF
; $12
	dc.b	$FF

; $13
	dc.b	$FF

; $14
	dc.b	"I feel it... weakened it may be,"
	dc.b	$FC
	dc.b	"but the Black Wave has not gone!"
	dc.b	$FF
; $15
	dc.b	$FF

; $16
	dc.b	"You came into the inner sanctum?"
	dc.b	$FC
	dc.b	"Who on earth are you...?"
	dc.b	$FF
; $17
	dc.b	"Something... something is coming..."
	dc.b	$FC
	dc.b	"My heart is racing...!"
	dc.b	$FF
; $18
	dc.b	"This is the training hall, where we"
	dc.b	$FC
	dc.b	"temper mind and body alike."
	dc.b	$FF
; $19
	dc.b	$FF

; $1A
	dc.b	$FF

; $1B
	dc.b	"I too must apply myself, if"
	dc.b	$FC
	dc.b	"Algol is to be saved!"
	dc.b	$FF
; $1C
	dc.b	$FF

; $1D
	dc.b	$FF

; $1E
	dc.b	"This is the chapel, though with all"
	dc.b	$FC
	dc.b	"these incidents, it's quiet in here!"
	dc.b	$FF
; $1F
	dc.b	$FF

; $20
	dc.b	"Oh, so that is the one they speak of"
	dc.b	$FC
	dc.b	"To think it would be in this mansion..."
	dc.b	$FF
; $21
	dc.b	$FF

; $22
	dc.b	"Oh, so that is the one they speak of"
	dc.b	$FC
	dc.b	"To think it would be in this mansion..."
	dc.b	$FF
; $23
	dc.b	$F4
	dc.b	$17
	dc.b	"Forgive my discourtesy!!"
	dc.b	$FF
; $24
	dc.b	$FA
	dc.b	$A2, $01
	dc.b	$F6
	dc.w	$0051	; => Event_InnerSanctGuard
	dc.b	$FF

; $25
	dc.b	$F4
	dc.b	$19
	dc.b	"All is as the Fifth Lord wills it."
	dc.b	$FF
; $26
	dc.b	$FA
	dc.b	$D9, $03
	dc.b	$FA
	dc.b	$A3, $02
	dc.b	$FA
	dc.b	$D7, $01
	dc.b	$F4
	dc.b	$19
	dc.b	"I pray for your safe return."
	dc.b	$FF
; $27
	dc.b	$F6
	dc.w	$0052	; => Event_InnerSanctGuardBeforeElsydeon
	dc.b	$FF

; $28
	dc.b	$F4
	dc.b	$19
	dc.b	"Fifth Lord, I have faith in you."
	dc.b	$FF
; $29
	dc.b	$F4
	dc.b	$19
	dc.b	"Ohh, to think that you'd actually hold"
	dc.b	$FC
	dc.b	"it in your hands..."
	dc.b	$FD
	dc.b	"As expected of someone whom the Fifth"
	dc.b	$FC
	dc.b	"Lord held in such high regard...!"
	dc.b	$FF
; $2A
	dc.b	$F4
	dc.b	$04
	dc.b	"Beyond the inner sanctum lies one more"
	dc.b	$FC
	dc.b	"room: the Chamber of Lutz."
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"Then... it's really happening..."
	dc.b	$FC
	dc.b	"We're finally going to meet Lord Lutz!"
	dc.b	$FD
	dc.b	"Oh! Are my clothes clean?"
	dc.b	$FC
	dc.b	"How's my hair?"
	dc.b	$FD
	dc.b	"Oh, what do I do."
	dc.b	$FC
	dc.b	"I'm so nervous!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"I wonder what kind of person he is..."
	dc.b	$FC
	dc.b	"Rudy, what do you think?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Lutz..."
	dc.b	$FC
	dc.b	"The legendary mage..."
	dc.b	$FF
; $2B
	dc.b	$F4
	dc.b	$04
	dc.b	"Here, I'll heal you..."
	dc.b	$FC
	dc.b	"Now go on, hurry up."
	dc.b	$FF
; $2C
	dc.b	$FF

; $2D
	dc.b	$F4
	dc.b	$06
	dc.b	"Rudy... be strong!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$08
	dc.b	"Humans are such complex beings, aren't"
	dc.b	$FC
	dc.b	"they..."
	dc.b	$FF
; $2E
	dc.b	$F4
	dc.b	$17
	dc.b	"Shess! You may not pass here"
	dc.b	$FC
	dc.b	"without permission!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"There's a special reason for it! You could"
	dc.b	$FC
	dc.b	"at least announce our arrival!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$17
	dc.b	"That will not do!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"You're so stubborn!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Let her through...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$17
	dc.b	"And who are you--!"
	dc.b	$FC
	dc.b	"A refusal is a refusal, no matter h......"
	dc.b	$FD
	dc.b	"Ah!??"
	dc.b	$FD
	dc.b	"Y-you are............!!"
	dc.b	$FD
	dc.b	"F-forgive me!"
	dc.b	$FC
	dc.b	"Please, go right ahead!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Thray...?"
	dc.b	$FF
; $2F
	dc.b	$F4
	dc.b	$0A
	dc.b	"Eh...? There's no one here...?"
	dc.b	$FD
	dc.b	"Lord Lutz!"
	dc.b	$FC
	dc.b	"Please, show yourself!"
	dc.b	$F7
	dc.b	$F4
	dc.b	$04
	dc.b	"Lutz is not here..."
	dc.b	$FC
	dc.b	"He departed this world long ago...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"What...?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$08
	dc.b	$F2
	dc.b	$00, $00, $9F
	dc.b	"As I thought. No one could have gone on"
	dc.b	$FC
	dc.b	"living for two thousand years."
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"That can't be! But I saw him...!"
	dc.b	$FD
	dc.b	"And besides... besides..."
	dc.b	$FC
	dc.b	"everyone believes in him!"
	dc.b	$FD
	dc.b	"That Lutz, the legendary Esper, lives"
	dc.b	$FC
	dc.b	"even now and guides us!!"
	dc.b	$FD
	dc.b	"That is why... that is why everyone"
	dc.b	$FC
	dc.b	"keeps going... it can't be true!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Shess! Calm down..."
	dc.b	$FD
	dc.b	"It is true... Lutz has already"
	dc.b	$FC
	dc.b	"left this world."
	dc.b	$FD
	dc.b	"But though his body perished,"
	dc.b	$FC
	dc.b	"his spirit still lives on."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"???"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $01, $00
	dc.b	$F4
	dc.b	$04
	dc.b	"Just before he died, he left his will"
	dc.b	$FC
	dc.b	"and his memory in this telepathy ball..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"Then... you're saying that orb"
	dc.b	$FC
	dc.b	"is Lutz now?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"No... He is not here now..."
	dc.b	$FD
	dc.b	"If one is found fit in mind and body"
	dc.b	$FC
	dc.b	"to carry on what he left behind,"
	dc.b	$FD
	dc.b	"then to that person... Lutz's will and"
	dc.b	$FC
	dc.b	"memory shall pass..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"........."
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"And at present..."
	dc.b	$F2
	dc.b	$02
	dc.b	$F9
	dc.b	$B3
	dc.b	$F2
	dc.b	$00, $01, $01
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"!!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"Thray is...... Lutz......!?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$19
	dc.b	"That is so."
	dc.b	$FD
	dc.b	"Thray Walsh..."
	dc.b	$FC
	dc.b	"the fifth Lord Lutz."
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $01, $02
	dc.b	$F4
	dc.b	$0A
	dc.b	"Y-you are..."
	dc.b	$FC
	dc.b	"Lord... Lutz...? It can't be..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Rudy, listen!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $01, $03
	dc.b	"Since ancient times, calamity has come"
	dc.b	$FC
	dc.b	"to Algol in a thousand-year cycle."
	dc.b	$FD
	dc.b	"The incarnation of evil called Dark"
	dc.b	$FC
	dc.b	"Falz returns every thousand years!"
	dc.b	$FD
	dc.b	"Each time, the brave souls of that age"
	dc.b	$FC
	dc.b	"struck the evil down,"
	dc.b	$FD
	dc.b	"and secured a fleeting peace..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"But we beat Dark Falz on Kuran,"
	dc.b	$FC
	dc.b	"we know we did..."
	dc.b	$FD
	dc.b	"and still there's no sign of Algol's"
	dc.b	$FC
	dc.b	"anomalies subsiding...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"What does that mean!?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"When Palma was destroyed a thousand"
	dc.b	$FC
	dc.b	"years ago, it shook Algol...!"
	dc.b	$FD
	dc.b	"The delicate balance it had held"
	dc.b	$FC
	dc.b	"until then shattered."
	dc.b	$FD
	dc.b	"This may be a result of that."
	dc.b	$FC
	dc.b	"I feel the Black Wave still..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Are you saying Dark Falz"
	dc.b	$FC
	dc.b	"is alive!?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Who knows..."
	dc.b	$FC
	dc.b	"Even I can't be certain."
	dc.b	$FD
	dc.b	$F2
	dc.b	$02
	dc.b	$F2
	dc.b	$00, $01, $04
	dc.b	"But one thing is certain: the root of"
	dc.b	$FC
	dc.b	"all evil has not perished yet!"
	dc.b	$FD
	dc.b	"And if it still lives,"
	dc.b	$FC
	dc.b	"then it must be destroyed!"
	dc.b	$FD
	dc.b	"For that reason... Rudy,"
	dc.b	$FC
	dc.b	"I chose you."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"You are the warrior I chose for the"
	dc.b	$FC
	dc.b	"final decisive battle!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Eh?"
	dc.b	$FD
	dc.b	"Chose...? Me...??"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"That's right."
	dc.b	$FC
	dc.b	"You're the man I set my hopes on."
	dc.b	$FD
	dc.b	"Whether my judgment is wrong"
	dc.b	$FC
	dc.b	"or not..."
	dc.b	$FD
	dc.b	"we'll know in time... Rudy."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"???"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $01, $05
	dc.b	$F4
	dc.b	$04
	dc.b	"Well, that's how it is. Sorry for"
	dc.b	$FC
	dc.b	"keeping it from you until now."
	dc.b	$FD
	dc.b	"I'm counting on you"
	dc.b	$FC
	dc.b	"from here on, all right?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"????"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"In any case!"
	dc.b	$FC
	dc.b	"The Gallberg Tower!"
	dc.b	$FD
	dc.b	"The answer is there!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$19
	dc.b	$F2
	dc.b	$00, $01, $06
	dc.b	"As for the man-eating trees that bar"
	dc.b	$FC
	dc.b	"the way, the sacred flame the"
	dc.b	$FD
	dc.b	"Dezolians revere, the Eclipse Torch,"
	dc.b	$FC
	dc.b	"will surely destroy them."
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Right, our path is decided!"
	dc.b	$FC
	dc.b	"The Gungbius Grand Temple."
	dc.b	$FD
	dc.b	$F4
	dc.b	$19
	dc.b	"It's a Dezolian temple which lies"
	dc.b	$FC
	dc.b	"in the mountains west of here."
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Let's go! Rudy, quit standing"
	dc.b	$FC
	dc.b	"there in a daze!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"Oh my! To think that Lord Lutz should"
	dc.b	$FC
	dc.b	"speak so callously!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Sorry about that."
	dc.b	$FC
	dc.b	"I've always been this way!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$0A
	dc.b	"Oh my..."
	dc.b	$FF
; $30
	dc.b	$F4
	dc.b	$04
	dc.b	"Rudy, the holy sword Elcidion"
	dc.b	$FC
	dc.b	"is waiting for you within!"
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $01, $28
	dc.b	$F4
	dc.b	$01
	dc.b	"Holy sword Elcidion!?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"That's right. Probably the one weapon"
	dc.b	$FC
	dc.b	"with the power to destroy the"
	dc.b	$FD
	dc.b	"Profound Darkness!"
	dc.b	$FD
	dc.b	"Go, Rudy... and go alone!"
	dc.b	$FC
	dc.b	"Go and meet Elcidion...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Meet... Elcidion...?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"That's right. And then..."
	dc.b	$FC
	dc.b	"you will find the answer you seek..."
	dc.b	$FF
; $31
	dc.b	$F4
	dc.b	$01
	dc.b	"So this is the holy sword,"
	dc.b	$FC
	dc.b	"Elcidion..."
	dc.b	$FD
	dc.b	"...!"
	dc.b	$FD
	dc.b	$F9
	dc.b	$3B
	dc.b	$F2
	dc.b	$00, $01, $2A
	dc.b	"A voice, from somewhere...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$00
	dc.b	"Welcome, Rudy Ashley..."
	dc.b	$FD
	dc.b	"This is where the souls of those"
	dc.b	$FC
	dc.b	"who fought to guard Algol return..."
	dc.b	$FD
	dc.b	"And Elcidion is the sword in which"
	dc.b	$FC
	dc.b	"those souls are lodged...!"
	dc.b	$FD
	dc.b	"Now, Rudy... take Elcidion"
	dc.b	$FC
	dc.b	"into your hands..."
	dc.b	$F7
	dc.b	$F4
	dc.b	$01
	dc.b	"!!"
	dc.b	$F7
	dc.b	$F4
	dc.b	$01
	dc.b	"!!"
	dc.b	$F7
	dc.b	$F4
	dc.b	$00
	dc.b	"Rudy... whom Thray selected..."
	dc.b	$FC
	dc.b	"You understand, do you not...?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Aah...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$00
	dc.b	$F2
	dc.b	$00, $01, $37
	dc.b	"Rudy..."
	dc.b	$FC
	dc.b	"Elcidion is in your care now...!"
	dc.b	$FD
	dc.b	"All of our feelings"
	dc.b	$FC
	dc.b	"are imbued within that sword..."
	dc.b	$FD
	dc.b	$F2
	dc.b	$00, $01, $38
	dc.b	"We are with you always..."
	dc.b	$FC
	dc.b	"We beg you, Rudy..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Yes!"
	dc.b	$FC
	dc.b	"Leave it to me!!"
	dc.b	$FF
; $32
	dc.b	$F4
	dc.b	$04
	dc.b	"Just as I thought."
	dc.b	$FD
	dc.b	"Elcidion has promised to lend you"
	dc.b	$FC
	dc.b	"its strength as well..."
	dc.b	$FD
	dc.b	"My judgment did not betray me!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Thray...!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	$F2
	dc.b	$00, $01, $3C
	dc.b	"Rudy, let us protect Algol...!"
	dc.b	$FC
	dc.b	"Not merely as a seal upon it, but..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Yes! For every living thing in"
	dc.b	$FC
	dc.b	"Algol... and beyond that..."
	dc.b	$FD
	dc.b	"to sever the past and build a future"
	dc.b	$FC
	dc.b	"that is truly free, unbound by anything!"
	dc.b	$FD
	dc.b	"That is what I choose to fight for!!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"Rudy..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Let's win this, Rudy!"
	dc.b	$FC
	dc.b	"For our Algol!!"
	dc.b	$F9
	dc.b	$3B
	dc.b	$FD
	dc.b	$F2
	dc.b	$03, $A9
	dc.b	$F4
	dc.b	$08
	dc.b	"Emergency alert from Frena:"
	dc.b	$FC
	dc.b	"something has happened on Motavia!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$06
	dc.b	"Rudy!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"Right!"
	dc.b	$FC
	dc.b	"To Motavia, quickly!!"
	dc.b	$FF
; $33
	dc.b	$F6
	dc.w	$004F	; => Event_EsperGuardPermission
	dc.b	$FF

; $34
	dc.b	$F6
	dc.w	$0045	; => Event_PersistentEsperGuards
	dc.b	$FF

; $35
	dc.b	$F4
	dc.b	$19
	dc.b	"Ah, Lord Thray!"
	dc.b	$FC
	dc.b	"I am glad you are safe. And this time..."
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"Never mind the formalities."
	dc.b	$FC
	dc.b	"I'm going inside."
	dc.b	$FD
	dc.b	$F4
	dc.b	$19
	dc.b	"Y-yes, of course..."
	dc.b	$FC
	dc.b	"As you will it."
	dc.b	$FF
; $36
	dc.b	$F4
	dc.b	$04
	dc.b	"We'll borrow the inner room again."
	dc.b	$FC
	dc.b	"There's something there for Rudy."
	dc.b	$FD
	dc.b	$F4
	dc.b	$19
	dc.b	"S-surely you don't mean to give"
	dc.b	$FC
	dc.b	"that to a boy like this!?"
	dc.b	$FD
	dc.b	$F4
	dc.b	$01
	dc.b	"??"
	dc.b	$FD
	dc.b	$F4
	dc.b	$04
	dc.b	"There is no one else but Rudy."
	dc.b	$FC
	dc.b	"...Trust me on this!"
	dc.b	$FD
	dc.b	$F4
	dc.b	$19
	dc.b	"Understood, Fifth Lord."
	dc.b	$FC
	dc.b	"I shall say no more."
	dc.b	$FF
; $37
	dc.b	$F6
	dc.w	$0067	; => Event_RuneHealingChaz
	dc.b	$FF
