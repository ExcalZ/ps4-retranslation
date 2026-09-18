# Translation glossary

Convention chosen: **romanize the Japanese**, natural/characterful English prose,
in **American English** - spelling (color, armor, traveling, gray) and idiom
alike. Idiom is the half a spell-checker misses: "a fair way", "you lot", "do
they never", "by rights" and "in your debt" all had to go even though every word
in them is spelled the same on both sides of the Atlantic. Formal "indeed" is
kept for the Zema elder, where it reads as register rather than as British.
Long-established series terms keep their familiar spelling where the Japanese
supports it (Algol, Motavia, Dezolis, meseta, Laconia) — those are transliterations
of the same Japanese words, not localization inventions.

## Party and major characters

| JP | English | cells | note |
|---|---|---|---|
| ルディ | Rudy | 4 | protagonist |
| ライラ・ブラングウェン | Laila Brangwen | 5 | mentor; needs `il` |
| ハーン | Hahn | 4 | academy scholar |
| ルツ | Lutz | 4 | legendary esper, addressed as ルツさま |
| ジオ | Zio | 3 | black-robed antagonist |
| フォーレン | Forren | 6 | android, "Master Forren"; needs `or`+`re` |
| フレナ | Frena | 5 | android; needs `en` |
| シェス | Shess | 5 | esper girl; needs `et` |
| ラジャ | Raja | 4 | priest |
| スレイ | Thray | 5 | tied to Elsydeon; needs `ra` |
| ファル | Fal | 3 | |
| パイク | Pyke | 4 | fits plain |
| シアム | Siam | 4 | |
| ミャウ | Myau | 4 | |
| アリサ | Alis | 4 | PS1 heroine, referenced only |
| サーヤ | Saya | 4 | Hahn's fiancee, Krupp |
| 八ッ裂きのライラ | Laila the Dismemberer | - | her hunter epithet; 八つ裂き is dismemberment, and she finds the name tasteless |
| ドクタールベノ | Doctor Luveno | - | ancient scholar, "god of learning" |

## Technique names: what the project is actually doing

The aim, stated by the user 2026-09-06: **an accurate transliteration of the
Japanese ROM's own katakana, informed by etymological research, and juxtaposed
against modern official material.** Three inputs, in that order of standing.

What this is NOT: deference to the 1995 US localisation. Those names are the
thing this project exists to replace, they were truncated to about five
characters by a menu window we no longer have, and they carry no authority
here. "Official" in the rule below means **modern** material -- the roman-letter
FOIE in the Japanese guide art, and the names Sega has maintained from PSO
through PSO2 and NGS.

The rule that follows from it: **where modern official material prints an
English form of a katakana name, take it; otherwise transliterate the katakana
faithfully, using etymology to decide the ambiguous letters.**

Evidence beats hypothesis. That フォイエ probably began as German *Feuer* is an
inference about what inspired the designers; **FOIE**, printed in roman letters
in the PSIV-era Japanese manual art and carried unchanged through PSO, PSO2 and
NGS, is what the publisher writes. Sega romanises the katakana as written
rather than restoring a source word, and a house style held for thirty years is
a policy, not a slip.

Renamed on that basis (18 entries, both the Tech table and the enemy-skill
table, which share these names):

| JP | was | now |
|---|---|---|
| フォイエ / ギフォイエ / ラフォイエ | Feuer / Gifeuer / Rafeuer | Foie / Gifoie / Rafoie |
| バータ / ギバータ / ラバータ | Water / Giwater / Rawater | Barta / Gibarta / Rabarta |
| グランツ / ギグランツ / ラグランツ | Glanz / Giglanz / Raglanz | Grants / Gigrants / Ragrants |
| メギド | Megiddo | Megid |
| ジェルン | Geron | Jellen |
| リューカー | Rückkehr | Ryuker |
| リバーサー | Rebirther | Reverser |

`lz1E05B6#0010` names the forbidden technique in dialogue and moved with it.

**Kept**, because no modern official material gives them a form: Zan, Gravt,
Procedan, Bolt, Sabolt, Drunk, Sealis, Limiter, Schnella, FEEV, Limpas,
Regenes, Arouse, and the Resta/Saresta families beyond the official Resta.
These rest on transliteration of the katakana with etymology settling the
ambiguous letters -- which is why グラブト is Gravt and not Grabt, and why
シュネラ is Schnella.

シュネラ -> **Schnella**, corrected 2026-09-07. It was Schneller, but German
*schneller* is [ˈʃnɛlɐ]: that final -er is a full syllable and Japanese gives
it the long mark, as in Wagner -> ワーグナー, Kaiser -> カイザー, Meister ->
マイスター. *schneller* would be シュネラー, and the ROM has シュネラ.

The word was never the comparative. It is the stem *schnell* plus the -a the
series puts on support techniques -- the same morphology as シフタ -> **Shifta**
and レスタ -> **Resta**, both spellings Sega prints, and neither of which
becomes Shifter or Rester. Three morae, no long mark, nothing left over.

This is the ヒーナス mistake one step milder: there a whole German word was
invented that the katakana contradicted; here the root was right and only the
inflection was imported.

An earlier version of this line said "Sega has never printed an English form".
That was false and unverifiable from here: the 1995 US release named all forty
techniques. It carries no weight -- see the scope note above -- but the claim
should not have been made.

ヒーナス left this list on 2026-09-06 and is now **Hinas**. The German
reconstruction *hinaus* was always the weakest in the set: [hɪˈnaʊs] should
give ヒナウス, so both the long ヒー and the missing ウ were wrong, and it survived
only on its pairing with Rückkehr -- which is itself now Ryuker. Dropping the
etymology and simply transliterating gives Hinas: the long mark goes unmarked
in English and the epenthetic ス clips, the same convention that yields Megid
from メギド and Drunk from ドランク.

**Skills were checked and not renamed.** PSIV's 54 player skills are original to
this game -- Sword Cross, Rayblade, Astral Flare, Ephes, Negatis, Hyperjammer
-- and none recurs in a later title under the same katakana, so the rule has
nothing to bite on. The enemy-skill table changed only where it repeats a Tech
name.

Two side effects worth knowing. Rückkehr was the only non-ASCII name in any
table and the sole reason `menustrip.py` carries its diacritic-synthesis
overlay; that machinery is now unexercised, and `test_fieldtext.py` lost its
one check that a diacritic survives field encoding.

## Monster names

Same rule as the techniques: transliterate the katakana faithfully, let
etymology decide the ambiguous letters, and check against modern official
material where any exists. For this table there is none -- the 1995 US list is
what the project replaces -- so etymology and internal consistency carry it.

Settled 2026-09-07:

| JP | ships as | why |
|---|---|---|
| ゴルダイン / ワイヤーダイン | Goldyne / Wiredyne | one suffix, ダイン = dyne; it had been spelled two ways, and the JP has no separator |
| ゲロトラックス | Gerothrax | アントラックス = anthrax attests トラックス = *-thrax* |
| ゾランバルト | Zoranbult | Dutch *bult* "hump", read as English spelling |
| ゼナファーグ | Xenophage | *-phage* read from the spelling gives ファーグ |
| ガイスファーグ | Gaisphage | restore the morpheme we understand, transliterate the one we do not |
| エイブフロッグ | Ape Frog | kept: see below |

**The mis-transcription model.** Several of the Motavia Academy bio-monsters
are English, Greek or Dutch words transcribed by someone working from the
spelling rather than the sound. ファーグ is "-phage" read as /faːg/; バルト is
Dutch *bult* read as /bʌlt/ rather than its actual /bʊlt/. The model earns its
keep by explaining several names with one mechanism, and it is what licenses
restoring the intended word rather than shipping the artifact -- the same
licence that makes グラブト *Gravt* and not *Grabuto*.

It cuts both ways, though: エイブフロッグ stays **Ape Frog** precisely because a
mis-voiced "ape" is what エイブ looks like under the same model, where "Abe"
would mean nothing for a frog.

**Two method errors worth not repeating.** Name families were proposed from
orthography -- "-farg", "-balt" -- without checking what the creatures are;
Gi-Le-Farg is a sorcerer and Silvalt is mechanical, so neither family existed.
And a sprite sheet's labels are usually the US names copied off a wiki, so they
are not independent evidence.

**Unsolved:** ガイス. Xenophage and Gaisphage are a straight palette swap and
the blue one additionally poisons, but no poison word reaches ガイス -- German
*Gift*, Dutch *gif*, Greek ἰός, and the ordinary loans ポイズン / トキシン /
ヴェノム all fail. The trait is probably not in the name.

## Places and proper nouns

| JP | English |
|---|---|
| アルゴル | Algol (star system) |
| モタビア | Motavia |
| デゾリス | Dezolis |
| パルマ | Palma |
| デゾリアン | Dezolian |
| モタビア・アカデミー | Motavia Academy |
| ハンターギルド | Hunters Guild |
| ゼラン | Zelan (artificial satellite) |
| ナルバス | Nurvus |
| ガルベルク | Gallberg |
| ガンビアス | Gungbius |
| バースバレー | Birth Valley |
| リュクロス | Ryucross |
| ゼマ | Zema |
| ピアタ | Piata |
| モンセン | Monsen |
| トノエ | Tonoe |
| クルップ | Krupp |
| アイード | Aiedo |
| ミース | Meese |
| マイル | Mile |
| リシェル | Richelle |
| ナルヤ | Nalya |
| テルミ | Termi |
| ウーゾ | Uzo |
| エティ | Ettie | Monsen; Tallas's mother |
| ラデア | Ladea |
| ホルト | Holt |
| モルカム | Molcum |
| エアキャッスル | Air Castle |
| ランディール | Landeel (ship) |
| ファルス | Falz (Dark Falz = ダーク・ファルス) |
| エスパー | esper |
| メセタ | meseta (currency) |
| ラシーク | LaSheek | PS1 tyrant of the Air Castle; capitalised as a noble's name, not the US "Lassic" |
| ガイラ | Gaira | the satellite whose impact destroyed Palma, AW 1284 |
| 勇気の塔 / 力の塔 | Tower of Courage / Tower of Strength |
| 大僧正 | High Priest | of the Gungbius Grand Temple |
| レ・ルーフ | Le Roof |
| 奥の院 | the inner sanctum | of the Esper Mansion |
| 深遠なる闇 | the Profound Darkness |

## People named only in dialogue

| JP | EN | note |
|---|---|---|
| シェス・ティアニー | Shess Tierney | Shess's full name, given when she is rescued |
| ルディ・アシュレ | Rudy Ashley | Rudy gives his full name to the High Priest |
| アイリーン | Eileen | the Hunters Guild receptionist |
| ギュナ | Gyuna | Ryuon's innkeeper. Ends every sentence in ズラ, a broad rustic
tic; a passer-by says outright that his old country accent is thick, so it has
to be audible in English. Rendered as heavy dialect plus a recurring
"I reckon" rather than left flat |
| アイード・ヘルナンデス | Aiedo Hernandez | founder of Aiedo's market, named on a portrait |

## Items and recurring terms

| JP | English |
|---|---|
| モノメイト / ディメイト / トリメイト | Monomate / Dimate / Trimate |
| ラコニア | Laconia |
| エルシディオン | Elsydeon |
| イクリプストーチ | Eclipse Torch |
| サイコウォンド | Psycho Wand |
| エアロプリズム | Aero Prism |
| ペロリーメイト | PelorieMate | corruption of the real product *CalorieMate* |
| 戦士の神殿 | Warriors' Temple |
| アルシュリン | Alshlin | transliteration of the katakana keeping the シュ; chosen 2026-09-17 over the earlier *Alsulin*. Same length, so the dialogue block below `$21A000` is unaffected |
| ランドマスター | Land Master |
| サンドワーム | sand worm |
| 環境維持システム | climate control system |

## Raja's puns: the test is two meanings, not two occurrences

Raja's wordplay is built on one shape carrying two senses. Repeating a word in
the SAME sense is not a pun, it is a tautology, and it reads as a mistake.

`lz1D4446#0025` -- 「こタエルけど、タエル！」 The setup ends on **こたえる**
(応える, "it afflicts them") and the punchline splits out **タエル** (耐える,
"they endure"). Two different verbs that happen to share a sound.

    rejected: "UnBEARable... but they BEAR it!"
              both BEARs mean tolerate, so it says "it cannot be borne,
              but they bear it" -- a contradiction, not a joke
    used:     "Very TRYING... but they keep TRYING!"
              trying = taxing / trying = persevering. One word, two senses.

`lz1DB6F6#0021` -- ユカイ (愉快, merry) rhymed with コーカイ (後悔, regret),
which is also 航海 (voyage), landing on a conversation about finding a
spaceship. Rendered "rare mirth / never rue the berth": mirth-berth rhymes,
rue carries the regret, and berth is both a bed at the inn and a ship's berth.

`lz1DB6F6#0048` -- アルゴル / アルコール survives intact in English as
Algol / alcohol.

`lz1DFCB6#0014` -- ユメ (夢, dream) stretched into ユーメーどころ (有名, the
famous spots). Both in katakana, one sentence apart, which is how Raja's puns
mark themselves. Rendered on **sights**: "I've had my SIGHTS set on it for
years" (an ambition) then "I mean to see the SIGHTS" (the famous places).

`lz1D38E6#0008` -- the crash landing, and two puns in one scene.
キカイ is both 機械 (machine) and 奇怪 (weird): "machines falling out of the
sky -- how kikai!" Rendered on **bolt**: "Nuts and BOLTS falling from the sky!
Now there's a BOLT from the blue!" -- a machine part, then a total surprise,
and "out of the blue" is where they are literally falling from.
Then ソラ飛ぶ船 (a sky-flying ship) turned into ソラぁトんでもない (outrageous),
the トん of 飛ぶ doing the work. Rendered on **flight**: "Quite a FLIGHT! And
quite a FLIGHT of fancy!!" -- a journey through the air, then an absurdity.

### The hidden-word device is fine: leave it alone

Raja's other mode is hiding one word inside another -- ふツーノ人 for ふつうの人
with ツノ (horn) exposed, サケて通れない with 酒 in it, ほっタイラーかし with Tyler in
it. Japanese marks the hidden word by switching to katakana; English marks it
with capitals and a hyphen, which does bend the host word's spelling:

    HORN-est folk       FOUR-warned
    ICY-nough           en-TYLER-ly         KURAN-ium
    "I can't BEER to pass it by"      "What AUGH-ful luck"

**These are kept on purpose.** They were rewritten once into single
double-meaning words (SPIRITS, STANDING, COLD, GRAVE...) on the argument that
the bent spelling reads as a typo, and that rewrite was rejected: the device
carries Raja's voice, the joke is legible in play, and the "improved" versions
read as ordinary lines with a word shouted in the middle. Do not sand them
down again.

The two-meanings test below still governs the OTHER kind -- a pun on one word
used twice, where a repeat in the same sense is a tautology rather than a joke.
That is what "unBEARable ... but they BEAR it" failed, and it is a different
failure from a deliberately bent spelling.

Before settling one, ask what the second meaning is. If there isn't one, it is
not finished.

## Britishisms: the recurring drift

Spelling is the easy half and a scan catches it. Idiom is what keeps coming
back, and a spell-checker never sees it. Caught and removed in a dedicated pass
(93 rows), listed so the same ones stop returning:

| don't | use |
|---|---|
| I'll not, I shan't | I won't |
| you lot, the lads | you people, the men |
| come along | come on |
| go and see / look / get | go see, go look, go get |
| ought to | should |
| Fancy coming... | Imagine coming... |
| Aye, | Yes, |
| daft | ridiculous, silly |
| grubby | filthy |
| hereabouts | around here |
| wandering / getting about | wandering / getting around |
| hasn't the, haven't got | doesn't have, don't have |
| that's not on! | that's no good! |
| make a fuss of | make a fuss over |
| mind you | even so |
| Well now | Well |
| ever so | so very |
| I dare say | I'd say |
| rather good at | pretty good at |
| driving X mad | driving X crazy |
| whilst, amongst | while, among |
| straight away | right away |

**Blanket find-and-replace is not safe on idiom.** Two of the substitutions
above damaged lines rather than fixing them, and both had to be repaired by
hand:

- `ever so` -> `so very` turned "Thanks ever so!" into "Thanks so very!",
  which is not English. `ever so` is only an intensifier when it modifies
  something; standing alone it means "so much".
- `mind you` -> `even so` destroyed "Big sister will just have to come and
  **mind you**!", where `mind` was the British verb *to look after*, not the
  discourse marker. The line became meaningless rather than merely British.

Match on the whole phrase, and read every hit before replacing it.

**The `, is it` tag** is the one to watch hardest, because it reads as natural
narration until you look for it: "Palmans, is it.", "An altar, is it?",
"Money, is it...". The JP has no such tag; it is an English translator's tic.
Use ", huh." or drop it: "An altar?"

Kept on purpose, so they are not "fixed" later by mistake:

- **"shall"** for Frena, Forren, Daughter, Le Roof, Zio, LaSheek and the
  priests. It is register, the same licence the Zema elder has for "indeed".
  Party members in casual speech get "will" / "should" / "let's".
- **Gyuna's dialect** -- `ye`, `summat`, `I reckon`. He is described in the
  script as having a thick old country accent, so it has to be audible.
- **"a bit", "properly", "at once", "or rather", "a fellow believer"** all read
  as ordinary American English and were deliberately left alone.

## Quotation marks in dialogue

Open with `"` and close with `''`. In the dialogue VWF the double quote curls
to the RIGHT and the apostrophe curls to the LEFT, so `"word''` encapsulates
the word properly, where `"word"` would close with a mark curling the wrong
way. Two apostrophes also avoid the extra advance a fixed-width closing quote
would carry.

This applies to the dialogue face only. The 8x8 system font used by the shop,
examine and credits blocks is a different face, and AS cannot take a `"` inside
`dc.b "..."` there anyway, so those blocks use single quotes -- as the US build
itself does for the epitaph and Laila's grave marker.

## Voice notes

- **Laila** — brash, teasing, older-sister register. Contractions, sentence
  fragments, light sarcasm. Her Japanese is blunt (`〜しな`, `あたし`).
- **Rudy** — young, earnest, uses `オレ`. Plain and direct.
- **Hahn** — fussy, over-explains, deferential.
- **Foren / Frena** — androids; Frena uses `〜ですわ`, formal and precise.
- **Raja** — comic, wheedling, drops `〜ズラ` (52 uses); render as a rustic
  verbal tic rather than transliterating it.

## Status-menu name field: 4 cells

The field holds 4 cells of the 8x8 system font. The original solves the same
problem with ligatures: `フォーレン` is stored as `4d 7b 7c 7d` — `フ` plus the
composite glyph `$7B`, which draws BOTH `ォ` and `ー` inside one cell. Verified
by rendering `$7B` out of VRAM; the README's reading of `$7B-$7D` as plain
duplicate glyphs was wrong.

`table.py` already longest-matches 3/2/1-character fragments, so a `7B=il` line
in `ps4.tbl` needs no code change. Dropping kana frees 134 codes.

| name | cells | ligature |
|---|---|---|
| Rudy, Hahn, Lutz, Raja, Pyke, Siam, Myau, Zio, Fal | <=4 | none |
| Laila | `L a il a` | `il` |
| Forren | `F o(r) re n` | `or`, `re` |
| Frena | `F r en a` | `en` |
| Thray | `T h ra y` | `ra` |
| Shess | `S h et h` | `et` |

Six ligature glyphs total: `en et il or ra re`, plus 26 lowercase.

**Blocked on locating the 8x8 font.** It is compressed in ROM. Ruled out by
exact-bitmap search against the VRAM dump: raw 1bpp, raw 4bpp, inverted,
bit-reversed, 2bpp, and all 240 4bpp ink/background index pairs. The font is
1bpp with ink `$F` when expanded, and the exact target bitmaps are now known,
which is a sharper handle on the search than the ink-coverage heuristic that
failed before.

Until then the 8x8 bank is uppercase-only. Casing does not change cell counts,
so re-casing is a mechanical pass, not a re-translation.

## Romanization authority

The Japanese ROM carries the developers' own romanizations in the sound-test
track list (8x8 segment `01:004`, already English in the original): `THRAY`,
`FAL`, `REQUIEM FOR LUTZ`, `TAKE OFF! LANDEEL`, `TEMPLE NGANGBIUS`, `MOTABIA`,
`DEZORIS`, `RYUCROSS`.

Adopted selectively, by decision: **Ryucross** and **Landeel** follow the ROM;
**Motavia** and **Dezolis** keep the familiar spellings over the ROM's
`MOTABIA`/`DEZORIS`; **Gungbius** is used for ガンビアス rather than the ROM's
`NGANGBIUS`. Thray already matched.

## Etymology first: work out the source word before fixing a spelling

Japanese collapses v/b and r/l and drops final consonants, so transliterating
katakana mechanically often lands on the wrong word. Worse, the official English
release was itself squeezed by the same cell limits documented above, so its
spellings are evidence of a width budget rather than of an intended reading.
Before settling a name, ask what word the Japanese is borrowing and from which
language.

| JP | shipped EN | likely source | reasoning |
|---|---|---|---|
| フォイエ | foi | German *Feuer* | fire technique; "foi" is the 5-cell budget, not a reading. With ligatures, `gifeuer`/`rafeuer` become reachable |
| バータ | wat | *withdrawn* | the Dutch *water* reading was an assumption; see the caveat below. "wat"/"giwat" are still the 5-cell budget either way |
| デバンド | Deban | *D-Wand* | same v/b collapse |
| テルル | telele | *terror* | PS1 had a fear ability TERR; シェス descends from PS1 magic users. Notable that the developers did not use the more obvious テロ |

The ligature budget matters here: restoring the full etymological form is only
possible where the extra width exists. That makes the 5-cell technique table
both the most distorted by the original limits and the biggest beneficiary of
ligatures.

Record new findings of this kind in this table as they are made.

## Technique and skill etymology survey

Structural finding: the two tables were named by different methods. **Techniques**
(the magic system, 5 cells) draw on German, Hebrew, Latin and Greek roots and are
the ones the official release mangled. **Skills** (combat arts, 8 cells) are
almost entirely transparent English compounds - Sword Cross, Air Slash, Mind
Blast - and need no etymological recovery, only width management.

German is the dominant source. ガルベルク ends in ベルク = *Berg*, which is
unambiguous, and Feuer / Glanz / schnell / Wand all fit the same pattern.

### High confidence

| JP | source | language | reasoning |
|---|---|---|---|
| フォイエ | *Feuer* | German | fire technique; "foi" was the 5-cell budget |
| グランツ | *Glanz* (radiance) | German | light technique; gu-ra-n-tsu maps cleanly to G-l-a-n-z with r/l collapse and tsu for final z |
| シュネラ | *schneller* (fast) | German | speed buff; near-exact phonetic match |
| メギド | *Megiddo* | Hebrew | via Har Megiddo / Armageddon; the dark instant-death technique |
| アタラクシア | *ataraxia* (tranquility) | Greek | a real philosophical term, borrowed intact |
| ガルベルク | *-berg* (mountain) | German | ベルク is unambiguous; Gallberg reads as a German compound |
| アウルデゾリア | Owl Dezoria | English + setting coinage | Species name; preserve the katakana order rather than the US localization's “Dezo Owl” |
| レスタ | *restare* / restore | Latin | heal |
| レジェオン | *legio* / legion | Latin | |
| ボルト, シフタ, アンティ, リバーサー, リジェネス, アロウズ | bolt, shift, anti(dote), reverser, regenesis, arouse | English | transparent |

### Medium confidence

| JP | source | note |
|---|---|---|
| バータ | *unresolved* | the Dutch *water* reading was an assumption and is withdrawn pending better evidence; see the caveat below |
| デバンド | *Wand* (wall), German | defense buff; "D-Wand" |
| テルル | *terror* | PS1 precedent (TERR); シェス descends from PS1 magic users |
| リミタ | *limiter* | English |
| ザン | 斬 *zan* (to slash) | wind-blade technique. Would be the one NATIVE Japanese root in a loanword set, which is why it is only medium |
| ヒューン | ヒュー, wind onomatopoeia | plausibly not a loanword at all |
| ネガティス | *negate* | |
| メディス | *medicus* / medicine | Latin |
| タンドレ | *tonnerre* + *foudre* | French portmanteau: thunder + lightning. Fits ta-n-do-re better than either word alone, and explains why neither matches cleanly on its own |

### Unresolved - do not guess in the translation

グラブト, プロセダン, ジェルン, ドランク, シーリス, フィーヴ, リムパス,
リューカー, ヒーナス, フレエリ, エフェス, カロジアン, ディーム,
ビンドワ, ワーラ

Candidates considered and NOT adopted: ドランク as German *Trank* (potion) or
English "drunk"; リューカー as German *zurück* (back) - semantically perfect for
a return-to-town spell but phonetically weak; シーリス as *Seele* (soul).
None is strong enough to act on.

### Caveat on バータ, worth recording

The skill list contains ヴォルテックス (Vortex) and スィーピング (Sweeping) - so
the developers had ヴ and スィ available and used them when they wanted /v/ and
/swi/. That weakens the argument that バ was chosen to represent a /v/ sound. If
they had meant "water" by spelling, ウォーター was available too. The hypothesis
survives only if バータ transliterates a heard Dutch pronunciation rather than a
spelling. Worth flagging rather than treating as settled.

### What this buys at 5 cells

With lowercase and ligatures, the recovered forms fit where the abbreviations do
not:

| wanted | plain | with ligatures |
|---|---|---|
| Feuer | 5 - already fits | - |
| Gifeuer | 7 | `G if eu er` = 4 |
| Rafeuer | 7 | `R af eu er` = 4 |
| Glanz | 5 - already fits | - |
| Giglanz | 7 | `gi g la n z` = 5 |
| Giwater | 7 | `gi w at er` = 4 |
| Schnell | 7 | `s ch ne ll` = 4 |
| Megiddo | 7 | `m eg id do` = 4 |

Note Feuer and Glanz already fit 5 cells in plain uppercase - those two can be
corrected immediately, without waiting on the font work.

## Zero truncation is achievable

Goal: no technique or skill name truncated, since the Japanese never needed to be.
Solved against the real constraints - table.py's greedy longest-match, the 5-cell
technique window and the 8-cell skill window.

**The pixel budget is measured, not assumed.** Glyph `$7B` packs ォ into columns
0-4 and ー into columns 6-7: 7px of ink plus a 1px separator inside an 8px cell.
So a ligature needs `ink(a) + ink(b) <= 7`. Note the ォ inside `$7B` is 5px, the
same as standalone `$61` - the original never condensed a glyph to make a pair
fit, it simply picked a pair whose second element was a 2px mark.

At standard widths (i/l 1px, j 2px, t/f/r/s 3px, most letters 4px, m/w 6px):

- **82 of 87** full names fit, with a 25-ligature set
- 5 do not: prosedan, deband, doubleattack, phononmaser, medicalpower - all of
  them runs of consecutive 4px round letters with no thin letter to pair against

Drawing **a, e and o at 3px inside ligature cells only** recovers all five. A
ligature is its own 8x8 bitmap, so a narrow `a` there does not affect standalone
`a`. There is no precedent for this in the original, but nothing prevents it.

**Result: 87/87 full names, 30 ligatures.**

    ac al an as at ba bo ed el en er fi gi he in is it ja le
    on ou po ra rd re ro sa sc sh st

Slot cost 26 lowercase + 30 ligatures = **56 of 134** free codes.

Worked examples (uppercase marks a ligature cell):

    gisaresta     GI|SA|RE|ST|a          5/5
    gifeuer       GI|f|e|u|ER            5/5
    barrierfield  b|a|RR|IE|r|f|IE|LD    8/8
    hyperjammer   h|y|p|ER|JA|m|m|ER     8/8

Caveat: this set is fitted to the 87 names currently targeted. Changing a name -
adopting a different etymology, say - can change which pairs are needed, so
re-run the solve before committing the font work. The 152 enemy names and 112
battle actions at 10 cells are not in this solve and are far less constrained.

## Prefix variants, and cross-table linkage

### Structure, verified against the data

Five damage roots carry the full set, and the heal root carries an extra サ:

| root | base | ギ | ラ | サ |
|---|---|---|---|---|
| フォイエ, バータ, グランツ, ザン, グラブト | yes | yes | yes | - |
| レスタ | yes | yes | yes | yes |
| サレスタ | yes | yes | yes | - |
| ボルト | yes | - | - | yes |

**Enemies never cast the ラ variants.** The enemy-action table contains ギフォイエ,
ギバータ, ギザン, ギグラブト, ギレスタ, ギサレスタ - and no ラ form at all. The four
ラ-initial entries there (ライトニングシャワー etc.) are unrelated words. So the
group-target tier is player-only.

### The prefixes are not loanwords - do not hunt them

ギ and ラ are the series' strength and scope markers (stronger / all-targets).
They are not borrowed words and no etymology should be sought for them; an
earlier revision of this file speculated about ギガ and that was a wrong turn.
Romanize them Gi- and Ra- and move on.

The only real question about them is **space**, and it is answered: every one of
the 23 prefixed forms fits the 5-cell technique window under the ligature set,
worst case exactly 5/5.

    feuer      f|e|u|ER          4/5      resta      RE|ST|a         3/5
    gifeuer    GI|f|e|u|ER       5/5      gisaresta  GI|SA|RE|ST|a   5/5
    rafeuer    RA|f|e|u|ER       5/5      rasaresta  RA|SA|RE|ST|a   5/5

Note the R/L ambiguity is moot for the prefixes, since they are not words. It
still applies to roots, where the ROM's own romanizations go by source word
rather than by kana rule: ランドマスター → LAND MASTER and ランディール → LANDEEL
use L, while スレイ → THRAY uses "ra" for レ.

### Cross-table linkage is a hard constraint

37 names appear in more than one table. Every player technique is also an enemy
action, and three vehicles (ランドマスター, アイスデッカー, フロームーバー) are both
items and name-table entries.

The binding cap is therefore the SMALLEST window a name appears in, not the one
for the table being edited. ギフォイエ is capped at 5 by the technique menu even
though the enemy-action window allows 10. `trpatch8.effective_limits()` computes
this and also refuses two different English strings for one Japanese name.

Turning that check on immediately found three live conflicts - LANDMASTER (10),
ICEDIGGER (9) and FLOWMOVER (9) were all written against the item cap of 10 while
also appearing in the 8-cell vehicle list. Shortened to LANDMSTR, ICEDIGGR,
FLOWMOVR.

## Class and vehicle names have no enforced limit

The reader at `$05DF28` indexes the list by counting `$FF` and copies until the
next `$FF` into `$FFE220` with **no length check**:

```
05DF28  lea ($2AA220).l,a0     ; class/vehicle base
05DF2E  lea ($FFE220).w,a1     ; RAM buffer
05DF3A  cmpi.b #$FF,(a0)+      ; skip to entry d0
05DF46  cmpi.b #$FF,(a0)       ; copy until $FF
05DF4C  move.b (a0)+,(a1)+     ; no bound
```

The list mixes two roles with different windows:

| role | entries | cap |
|---|---|---|
| job titles | ハンター .. エスパー | **8 cells** |
| vehicles | ランドマスター, アイスデッカー, フロームーバー | uncapped |

An earlier revision capped the WHOLE list at 8, inferred from the largest entry
(モタビアンマニア). That swept the vehicles in with the job titles and wrongly
forced three item names to be abbreviated, since the vehicles also appear in the
item list. The 8 is right for job titles; it does not apply to vehicles.

Related: `$280D30` is entry index 22, exactly where the monster names begin,
which confirms the big table's party/class/vehicle head (`02:000`) has no code
reference of its own and duplicates the small table at `$2AA1F0`/`$2AA220`.

### Vehicles

Unabbreviated, and they appear in three places that must agree:

| JP | EN | where |
|---|---|---|
| ランドマスター | LANDMASTER | item list, `02:000`, and `03:001` as ` LANDMASTER` |
| アイスデッカー | ICE DECKER | Decker, not Digger - faithful transliteration preferred |
| フロームーバー | FLOWMOVER | |

`r03s001#008` is ` ランドマスター` with a **leading space** (hex begins `00`), so it
is a different string from the other copies and the linkage check does not tie
them together. The space looks like display padding and is preserved in English.

### Job titles

Eight cells. モタビアンマニア is Pyke's, and renders simply as MOTAVIAN - the
マニア half does not survive the budget and adds nothing in English.

| JP | EN | cells |
|---|---|---|
| ハンター | HUNTER | 6 |
| がくしゃ | SCHOLAR | 7 |
| まどうし | WIZARD | 6 |
| モタビアンマニア | MOTAVIAN | 8 |
| ニューマン | NEWMAN | 6 |
| アンドロイド | ANDROID | 7 |
| そうりょ | PRIEST | 6 |
| エスパー | ESPER | 5 |

### Party names are still blocked

All 22 party-name slots (11 in each table) remain untranslated. Rudy, Hahn,
Lutz, Raja, Pyke, Fal and Siam fit 4 cells in plain uppercase today; Laila,
Forren, Frena, Thray and Sheth need the ligatures, which need the 8x8 font
located. Entry index 7 in both tables decodes as `フ{7B}{7C}{7D}` - Forren, still
carrying the original's own ォー ligature, which ps4.tbl cannot represent yet.

## Etymology: resolved set

Confirmed with the user, effects supplied by them. German dominates, with Dutch,
Hebrew/biblical, Latin, French and English alongside.

**This table is research, not a naming instruction.** The `origin` column is
the presumed source word; `ships as` is what the ROM actually says, which for
several names is the modern official form instead. Do not "restore" a name from
the origin column -- that would undo the 2026-09-06 pass. Where the two differ
the origin is still worth keeping: it is why the ambiguous letters fall the way
they do.

| JP | origin | ships as | source | effect / note |
|---|---|---|---|---|
| フォイエ | Feuer | **Foie** | German | fire |
| バータ | Water | **Barta** | Dutch | ice/cold; Dutch w = /v/, and Japanese does not split v from b |
| グランツ | Glanz | **Grants** | German | light |
| ザン | Zan | Zan | 斬 (Japanese) | wind blade; the one native root. Romanizes to Zan either way |
| グラブト | Gravt | Gravt | Latin *gravis* | gravity. b/v collapse favours Gravt over Grabt |
| メギド | Megid | Megid | Hebrew | Megiddo / Armageddon; dark instant-kill |
| プロセダン | Procedan | Procedan | English + 断 | instant kill. Japanese renders "process" as プロセス, so セ = "ce" |
| ジェルン | Geron | **Jellen** | gerontology | ages the enemy, cutting attack. ジェ is the soft g of ジェロントロジー |
| ドランク | Drunk | Drunk | English | cuts agility; ドランカー = drunker is the standard loan |
| リューカー | Ruckkehr | **Ryuker** | German *Rückkehr* | returns the party to town |
| ヒーナス | -- | **Hinas** | none; retracted | exits a dungeon |
| エフェス | Ephes | Ephes | Ephesus | instant-kills evil enemies |
| ディーム | Deem | Deem | English | instant-kills weak enemies; ディーム = /diːm/ exactly |
| タンドレ | Tondre | Tondre | French *tonnerre*+*foudre* | thunder + lightning portmanteau |
| テルル | Terror | Terror | PS1 TERR | fear |
| シュネラ | *schnell* + a | **Schnella** | German root + the series suffix | speed |
| デバンド | Deband | Deband | German *Wand* | defence |
| アタラクシア | Ataraxia | Ataraxia | Greek | intact borrowing |

**Mutually reinforcing pairs** - the strongest evidence in the set:

* リューカー *Rückkehr* (back to town) and ヒーナス *hinaus* (out of the dungeon)
  are both German words of motion, for the two escape spells.
* メギド *Megiddo* and エフェス *Ephesus* are both biblical place names, for the
  two instant-kills - dark, and anti-evil.
* デバンド *Wand* and ワーラ *Wall* would be two German wall words for the two
  defensive techniques.

### Still open

| JP | effect | note |
|---|---|---|
| シーリス | seals technique use | "Seals" does not fit the romanization. Latin *silere*/*silens* (to be silent) matches the effect exactly and fits シー |
| リムパス | removes paralysis | possibly "limb"+"pass"; r/l collapse means Limpas is as likely as Rimpas |
| カロジアン | heavy damage vs machines | "Corrosion" fits the sense but not the vowels - コロージョン is the normal loan |
| フレエリ | fire projectile | NOT "flare": the game spells flare フレア (フレアショット, アストラルフレア) |
| ビンドワ | binds enemies | NOT English "bind": the game spells bind バインド (シャドウバインド, アースバインド). German *binden* fits ビンド better |
| ワーラ | physical barrier | German *Wall* -> Warla/Walla; pairs with Deband |
| フィーヴ | unknown | unresolved |
| リミタ | unknown | Rimit / Limit |

### Charset gap

*Rückkehr* needs **ü**, which the font has no glyph for. Either spell it
Ruckkehr, or add ü - there is slot room.

## Phonetic cross-check

Re-tested each reading against the spoken realization of the kana rather than a
letter-by-letter mapping. Four changed.

**Strengthened**

| JP | spoken | source | why it works |
|---|---|---|---|
| フォイエ | [ɸo.i.e] | *Feuer* [ˈfɔʏɐ] | German "eu" is [ɔʏ] -> オイ, and final -er [ɐ] -> エ. Near-exact |
| バータ | [baː.ta] | Dutch *water* [ˈʋaːtər] | the long aː is carried straight over; ʋ is heard as b |
| グランツ | [ɡu.ɾan.tsɯ] | *Glanz* [ɡlants] | the final [ts] is exactly ツ |
| ジェルン | [dʑe.ɾɯɴ] | geron- | dʑ = dʒ exactly, as in ジェロントロジー |
| ディーム | [diː.mɯ] | deem [diːm] | exact |

**Changed by the check**

* **シーリス -> Sealis.** "Seal" plus the pseudo-Latin *-is* the game already uses
  in ネガティス, メディス, ヒーナス, リムパス. シー is [ɕiː], the "sea" of seal;
  リス is the suffix. This reconciles the obvious sense with the romanization.
* **ワーラ -> Wahra**, German *wahren* [ˈvaːʁən], to guard or preserve. The long
  aː plus r matches ワーラ; *Wall* [val] would give ワル. Same Proto-Germanic
  *war- root as the user's "vare" instinct, and as English ward/beware.
* **リムパス -> Limpas.** With リミタ confirmed as Limiter, the two share a lim-
  root: Limiter imposes the paralysis, Limpas makes it pass.
* **グラブト -> Gravt**, but from Latin *gravis* rather than a German word. No
  Germanic term fits [ɡu.ɾa.bɯ.to]; a clipping of the grav- root does.

**Weakened**

* **ヒーナス / hinaus - RETRACTED 2026-09-06.** It was the shakiest in the set:
  *hinaus* is [hɪˈnaʊs], which should give ヒナウス, so the long ヒー and the
  missing ウ were both wrong, and it stood only on its pairing with Rückkehr --
  now Ryuker, so the prop is gone too. Ships as **Hinas**, a plain
  transliteration with no etymology claimed.
* **カロジアン / corrosion**: [ka.ɾo.dʑi.aɴ] is closer to "Carrosian" than to
  corrosion, whose normal loan is コロージョン.
* **ビンドワ**: German/Dutch *binden* fits ビンド where English bind (バインド)
  does not, but the trailing ワ stays unexplained.

**Settled**

リミタ = **Limiter** (paralyses; l|im|it|er = 4 cells). フィーヴ is an unused
technique slot and needs no decision.

## Font design: settled

Two faces, split by role.

| role | face | cells | packing |
|---|---|---|---|
| party names | creep (MIT, romeovs) | 4 | fully paired, 2 glyphs per cell |
| techniques | small caps | 5 | minimal pairing |
| skills | small caps | 8 (10 for the two combos) | no pairing, abbreviated instead |

### Glyph budget

    25  creep party glyphs   (21 pairs + 4 singles)
    26  small caps
     1  u-umlaut
    30  small-caps technique ligatures
    --
    82  of 109 free low-bank slots,  27 spare

### Why the split

creep is drawn for a 5px advance. One creep glyph alone in an 8px cell reads
sparse - the "R u d y" failure. Party names dodge that by being fully paired at
x=0 and x=4, which yields a uniform 4px advance and, because creep has real
2-row descenders, genuine mixed case: **Rudy**, not RUDY. That matters most in
the status window, which is the most-looked-at text in the game.

Techniques and skills stay small caps. Skills are abbreviated to <=8 precisely
so they need no pairing, and creep unpaired would be sparse; techniques read
acceptably in creep but show irregular gaps where narrow letters fall
("Bol t", "Schnel l"), and creep's 4px m reads as rn ("Liriter").

### Two things tried and rejected, with the evidence

* **Proportional placement inside a creep cell.** Fitting each glyph to its ink
  extent instead of fixed x=0/x=4 looked like the obvious fix for the narrow
  letter gaps. It is worse: it discards creep's side bearings, strokes merge,
  and n reads as r - "Schrell", "Forrer", "Glorz".
* **Bespoke party-only ligatures in the small-caps face.** The extra freedom was
  illusory. Column 7 is not slack; it is what separates one cell from the next.
  Filling it made LAILA read "LA1A".

### Attribution

creep glyphs are baked into `tools/creepfont.py` with the MIT notice. The
licence requires the copyright notice travel with the work, so that file must
keep its header and the README should credit it.
## Historical terms

- `大崩壊` — **Great Collapse**. Preserve “Great” wherever the named historical
  catastrophe appears; do not shorten it to “Collapse.”
