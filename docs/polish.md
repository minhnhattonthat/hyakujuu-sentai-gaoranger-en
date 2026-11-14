# Polish list

Deferred Minor review findings, one `- [ ] id - note` line each. The polish pass ticks each `[x]`, fixed or
`waived: reason`; release refuses to run while any line is unticked.

- [x] ds01-00be - "the life of the Earth" -> "life on Earth" (p6 review, fixed)
- [x] ds03-008a - "Join your strength" awkward -> "Combine your powers and fight!" (p6 review, fixed)
- [x] option-0116 - "Settings done!" clipped -> "You're all set!" (p6 review, fixed)
- [x] load-015a, save-02fe - flat "Load/Save complete!" vs Tetomu's よ -> "Your game's loaded/saved!" (p6 re-review, fixed)
- [x] option-004a, option-00b2 - "set the sound" unidiomatic -> "Changing the sound settings?" (p6 re-review, fixed)
- [x] ds06-008a - "With your hearts of justice" -> "With justice in your hearts" (p6 codex re-run, fixed)
- [x] credits - staff readings (gfx/credits_en.py, D18). Checked against English credits of other Natsume/Bandai games (MobyGames: DICE, Godzilla PS4; Wikipedia: Gundam Battle Assault 2; bdjogos: Hokuto no Ken PS1): fixed 太田博久 Hirohisa Ohta, 山田一人 Kazuhito Yamada, 新保孝 Takashi Shinpo, 稲垣裕 Hiroshi Inagaki; confirmed Mitsuo Matsumoto, Seiji Noda, Hiroyuki Iwatsuki, Toshiyasu Miyabe, Kunio Suzuki, Shunichi Taniguchi, Takashi Aoyama, Seiko Fujisawa, Tomoaki Imanishi, Fuyuki Nishizawa. waived: the rest stay Hepburn guesses (no English source found; README known issue): 加藤正純 Masazumi Kato, 猪谷公彦 Kimihiko Igaya, 篠原智士 Satoshi Shinohara, 松山直美 Naomi Matsuyama, 久島裕一 Yuichi Kushima, 谷山謙二 Kenji Taniyama, 山崎匡史 Tadashi Yamazaki, 井上剛 Takeshi Inoue, 畠山健司 Kenji Hatakeyama, 大井英之 Hideyuki Oi, 中田理生 Rio Nakata, 大村亨 Toru Omura, 塩野勝美 Katsumi Shiono, 横須賀実 Minoru Yokosuka, 派矢涼平 Ryohei Haya, 有馬大作 Daisaku Arima, 中山秀紀 Hidenori Nakayama, 神村綾 Aya Kamimura; theme song 「ガオレンジャー吼えろ!!」 = "GaoRanger Hoero!!" (the song's usual romanised title)
- [x] save-00de, save-0132, save-029e, load-00f6 - story pass (menus): "three lines exceed the two-line budget" - waived: the save/load box takes 3 lines where the JP has 3 (lint budget, seen in game in the phase-8 tour); the reviewer prompt only named the story-box budget (tools/story.py fixed)
- [x] save-029e - "Saving game data." -> "Saving data." to match card-03a2 (p6 re-review, fixed)
