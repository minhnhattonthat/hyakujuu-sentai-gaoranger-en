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
