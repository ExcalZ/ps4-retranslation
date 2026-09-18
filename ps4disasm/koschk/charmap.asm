ASCIIStart: equ $20 ; First ASCII code in table

ASCIIMap:
	dc.b $00	; SPACE (ASCII code $20)
	dc.b $28   ; ! Exclamation mark
	dc.b $2B   ; " Double quotes
	dc.b $2E   ; # Hash
	dc.b $00	; UNUSED
	dc.b $00	; UNUSED
	dc.b $00	; UNUSED
	dc.b $2C   ; ' Single quote
	dc.b $29   ; ( Open parenthesis
	dc.b $2A   ; ) Close parenthesis
	dc.b $00	; UNUSED
	dc.b $2F   ; + Plus
	dc.b $26   ; , Comma
	dc.b $30   ; - Minus
	dc.b $25   ; . Full stop
	dc.b $31   ; / Slash or divide
	dc.b $1B   ; 0 Zero
	dc.b $1C   ; 1 One
	dc.b $1D   ; 2 Two
	dc.b $1E   ; 3 Three
	dc.b $1F   ; 4 Four
	dc.b $20   ; 5 Five
	dc.b $21   ; 6 Six
	dc.b $22   ; 7 Seven
	dc.b $23   ; 8 Eight
	dc.b $24   ; 9 Nine
	dc.b $2D   ; : Colon
	dc.b $00	; UNUSED
	dc.b $00	; UNUSED
	dc.b $00	; UNUSED
	dc.b $00	; UNUSED
	dc.b $27   ; ? Question mark
	dc.b $00	; UNUSED
	dc.b $01	; A
	dc.b $02   ; B
	dc.b $03	; C
	dc.b $04   ; D
	dc.b $05	; E
	dc.b $06	; F
	dc.b $07	; G
	dc.b $08	; H
	dc.b $09	; I
	dc.b $0A	; J
	dc.b $0B	; K
	dc.b $0C	; L
	dc.b $0D	; M
	dc.b $0E	; N
	dc.b $0F	; O
	dc.b $10	; P
	dc.b $11	; Q
	dc.b $12	; R
	dc.b $13	; S
	dc.b $14	; T
	dc.b $15	; U
	dc.b $16	; V
	dc.b $17	; W
	dc.b $18	; X
	dc.b $19	; Y
	dc.b $1A	; Z (ASCII code $5A)
