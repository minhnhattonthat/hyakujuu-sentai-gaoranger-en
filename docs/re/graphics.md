# Graphics text survey

Static sweep: `python -X utf8 tools/timscan.py --per 30 --thumb 180` -> `work/gfx/sweep/sheet_NNN.png` + `index.tsv`
(164 unique TIMs from 797 occurrences in all unpacked PACs; ids below are sweep ids, files = first occurrence, see
index.tsv for every copy). Skipped: 43 leaves that start with `10 00 00 00` but are not TIMs (A_BURU 9_8, A_RED 9_9 ...;
model/other formats, no image found). Tour shots: `work/qa/tour1` (new game -> first stage).

| id | first file | content (Japanese) | notes |
|---|---|---|---|
| 4 | A_DEMO.PAC 15_3 | 斬 (slash effect kanji) | per-stage copies |
| 5 | A_DEMO.PAC 15_4 | digit font + オルゲット (Orgette counter label) | HUD |
| 6 | A_DEMO.PAC 15_5 | 破 削 烈 魂 滅 痛 砕 (hit-effect kanji) | |
| 7 | A_DEMO.PAC 16_3 | ゲームオーバー, もっとたたかう, たたかいをやめる, をつづける, STARTボタンをおせ!! | game over / continue |
| 8 | A_DEMO.PAC 17_3 | 牙吹 滅鬼 (special-move kanji) | |
| 77 | BA_ST01B 1_14_5 | 好機 (chance) | robo battle effect |
| 96 | BC_ST07 1_12_3 | ゲームオーバー, もっとたたかう, たたかいをやめる (+ lower part, 8bpp?) | robo battle game over |
| 124 | B_ST07 1_18_1 | red kanji-like marks (check: texture or text?) | |
| 126 | CARDMS.PAC 1 | dialogue font | engine font, text.md |
| 128 | DE_ST01 9_1 | speaker portraits (no text) | |
| 131 | DE_ST01 9_4 | データのロード, はい いいえ, データのセーブ, しんどう, サウンド, ステレオ モノラル, あり なし, ▼; speaker names キングオルグ ラセツ シュテン ロウキ ブルドーザーオルグ はんせんオルグ, ロードスタート | option/save menus + box name plates |
| 135 | DE_ST01 9_9 | stylised ガオ.. lettering (check) | |
| 136 | DE_ST03 4 | ガオマッスルストライカー 誕生, ガオイカロス, 覚醒, 誕生, ガオシルバー | story banners |
| 142 | DE_ST07 9_10 | (c) 2001 テレビ朝日・東映, cast list (オルゲット 大村亨 ...) | credits |
| 148 | DE_ST07 9_7 | スタッフ, cast/role list (ガオレッド 金子昇 ...) | credits |
| 149 | DE_ST07 9_8 | エグゼクティブプロデューサー ... staff | credits |
| 150 | DE_ST07 9_9 | スペシャルサンクス, 総合監修, 制作協力, 製作 バンダイ ... | credits |
| 154 | DE_ST07E 9_3 | おわり (The End) | ending |
| 158, 163 | O_TITLE 10, Y_TITLE 12_4 | 百獣戦隊ガオレンジャー logo | logo: keep unless an official English logo exists (D5) |
| 159 | O_TITLE 11 | STARTボタンをおせ!!, オルゲットッ, はじめから, つづきから, サウンド ファイト, しんどうゆったり(?), かんたん むずかしい, データ.., TEST USER | title menu (8bpp/4bpp mix, needs a proper CLUT render) |

Also seen in VRAM at the intermission (`work/qa/vd6000`): the same #131 and #136 sheets loaded together.

## Not yet covered
- FMVs `XA/*.STR` (OP0 opening, RB*/RN* = robo/ranger sequences?): check for burned-in Japanese (jPSXdec or an
  emulator tour) in phase 2/8.
- Non-TIM image formats inside `41 00 00 00` / other leaves: the sweep only renders TIMs; the 43 skipped
  `10 00 00 00` leaves were checked by header only.
- Stage-select / debug-menu screens and every stage's HUD: tour them once the debug tool exists (phase 2).

## Redraw status (phase 8; tools/gfx.py, tools/gfx_edit.py, edits in gfx/edits.py, copies from gfx/tims.tsv)
Build writes every copy of each edited TIM (insert.py), verify.py checks each graphics leaf equals gfx/edits.py.
Preview: `python -X utf8 tools/gfx.py preview` (original | English per image, work/gfx/preview). Find rects:
`gfx_edit.boxes`, per-row/column ink profiles; pieces touch, so split on ink-column minima.

| id | state | shot (cold boot warp, English build) |
|---|---|---|
| 131 | English (menu titles, Yes/No, Stereo/Mono, On/Off, speaker plates, START LOADING) | load, save, option, tsound, tvib: work/qa/p8/w1 |
| 7 | English (GAME OVER, KEEP FIGHTING/GIVE UP/CONTINUE both sets, PRESS START!!) | action game over not reachable yet (no HP found) |
| 96 | English top part (same rects as 7; rows 112+ are other data) | overb: work/qa/p8/w5 |
| 159 | English title wheel/submenus (composites), copyright line; TEST USER kept (debug) | title, tnew, ofmenu, tload: w2-w5 |
| 158, 163, 135 | logo / logo art: kept Japanese (D5, D12) | - |
| 124 | no text (skull textures): drop from the list | - |
| 136 | English: GAOMUSCLE STRIKER IS BORN!, GAOICARUS IS BORN!, GAOSILVER AWAKENS! (composites: each banner is one line of two pieces, name + 誕生/覚醒, sprite groups g00-g05 of the PAC's 12_17 leaf) | not shown by ds01/ds04/de03-05 in 12000 frames (HOLD=0 and default mash, shots every 20 frames, work/qa/p8/story20): trigger unknown |
| 154 | English: THE END | de07e |
| 5 | English: ORGETTE (HUD label) | action stage |
| 77 | English: 好機 -> CHANCE! (robo battle prompt); rest of the sheet is effects | robo battle, when the prompt fires |
| 4, 6, 8 | kept: brush impact kanji 斬 / 破削烈魂滅痛砕 / 牙吹 滅鬼 shown on hits (sound-effect-like decoration, glossary: no sound effects in text); D13 | - |
| 142, 148, 149, 150 | English: whole staff roll rebuilt (tools/credits.py, lines in gfx/credits_en.py, §Credits layout) | de07 (`--shot-every 30`): work/qa/p8/credits_en (cast, staff, thanks, companies), © lines at ~f14100 (work/qa/p8/credits_en2) |

## Credits layout (DE_ST07)
`python -X utf8 tools/sprgroups.py DE_ST07.PAC/12_17 --tpage-x 9,10,11,12` lists every credits sprite (u32 offset
table from 0x3c, group = u16 count + count x {s16 x, s16 y, u8 u, v, w, h, u16 tpage, u16 clut}). Atlases: tpage x 9
= TIM 148 (cast, 576,256), 10 = 149 (staff), 11 = 150 (special thanks/companies), 12 = 142 ((c) lines, Orgette
cast). Lines are built from fragments, often single 16x16 kana reused across groups (g32 = 4 single cells + a
name; ツエ drawn twice = ツエツエ; ナ+レー+ション), so a per-rect redraw can't give English. Plan: a credits builder that
renders each group's English line(s) as new strips packed into the 4 atlases (16 px rows, sans 12-13 px) and
rewrites each sprite's u/v/w/h (and x for centring) in 12_17, keeping every group's sprite count (unused sprites ->
w 0). Romanisation per D2 (official cast spellings; staff readings Hepburn, guessed readings listed in
docs/polish.md for the user). Same 12_17 format holds the story banners (DS/DE story PACs, tpage x 9).

Built (`tools/credits.py`, `render` draws every group as on screen: `--jp` for the original): the four atlases are
cleared (g20's 96x24 スタッフ title relabelled in place as STAFF), each English line is one 16 px strip (Liberation
Sans Bold 13, index 15 core, index 1 rim; every CLUT row is a 0-15 ramp, so white/orange is only the sprite's CLUT:
name 7c48 / role 7cc8 in TIM 148, 7c00 / 7c80 in the others), shelf-packed, identical lines share a strip. Spare
sprites get w = h = 0 (draw nothing, seen in game). **The roll draws quads with u+w and v+h as u8**: a strip whose
right edge is u 256 came out mirrored or sheared, so strips keep u+w and v+h <= 255 (tests/test_credits.py). Groups
slide and fade as a whole, so the English keeps each group's x/y and the motion matches the original.
