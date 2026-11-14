# FMVs (XA/*.STR)

Verified 2026-11-14 (phase 8). Tools: `tools/strv.py` (codec), `tools/fmvcap.py` (captions, run by build.py),
`tools/fmvmap.py` (scene -> STR from `warp.py --trace` logs), `tests/test_strv.py`. jPSXdec was not used: running
the downloaded jar was refused by the agent's permission check, so the codec is our own (numpy, ~300 lines).

## Format
- Files as dumpsxiso writes them: raw 2336-byte sectors (subheader + 2328, EDC/ECC included and valid). Layout
  type `mixed`. Video sectors: form 1, submode 0x48; XA audio sectors: form 2 (submode 0x64), interleaved.
- Video sector: 32-byte header (`u32 0x80010160, u16 chunk, u16 chunks, u32 frame, u32 frame size, u16 w=320,
  u16 h=208`, then the frame's first 8 bytes, 4 zero bytes) + 2016 bytes of frame data. 30 fps (about 5 sectors a
  frame at 2x).
- Frame data: `u16 count, u16 0x3800, u16 qscale, u16 version=2` + bitstream (u16 LE words, MSB first).
  count = ceil(MDEC codes / 2) rounded up to 32, codes = per block DC + one per AC + EOB (a block a frame lacks
  still counts 2). Macroblocks column by column, blocks Cr Cb Y1 Y2 Y3 Y4, DC 10-bit signed, AC MPEG-1
  dct_coeff_next + sign, escape `000001` + 6-bit run + 10-bit level, EOB `10`, end of frame `0111111111` in the
  next DC slot. Quant table = MPEG intra default with [0] = 2.
- `strv.py check` re-encodes every frame bit for bit except three odd frames, all untouched by the patch: OP0 394
  (64 zero bytes in the middle of its data), RB0 246 (ends one block early; parsed), RB0 1190 (parse drifts by 4
  blocks near column 17: unknown quirk, the frame is never edited).

## Burned-in text (survey of every STR, every 8th frame; OP0 every 20th: work/qa/fmv/survey/s*.png)
| STR | Frames | Text | Handling |
|---|---|---|---|
| OP0 (opening, title attract) | 480-640, 2180-2252 | title logo 百獣戦隊ガオレンジャー | kept (D5/D12: no official English logo) |
| OP0 | 880-1060 | brush hit kanji 痛, 砕鬼 | kept (D13 class) |
| RN0, RN0_B | ~226-236 | brush calligraphy 破邪百獣剣 flashing behind a burst | kept (D13 class, D17) |
| RB0 (GaoKing forms) | 1367-1449 | caption ガオキング | GAOKING |
| RB2 (GaoMuscle Striker) | 480-534 | caption ガオマッスルストライカー | GAOMUSCLE STRIKER |
| RB4 (GaoIcarus) | 668-733 | caption ガオイカロス | GAOICARUS |
RB1/RB1_B/RB3/RB5/RN1/RN2/RN2_B: no text.

## Where they play (`fmvmap.py work/qa/warp` after `warp.py --all --trace`)
OP0 is sought at boot (~f1010) by every scene (title attract). RB0: bb00b, bb01a-c, bb02a-c, bb03b-c (bb01c caption
~f6100-6270); RB2: bb04b-c, bb05b-c (bb04c caption ~f4290-4400); RB4: bb06a-c, ba02 (bb06c caption ~f4770-4900);
RN1: a11-a51, ba01b, pausea, ytitle; RN2: bb00b, bb01a-b, bb02a-b. Proof shots: work/qa/p8/fmv/<scene>.

## Caption replacement (fmvcap.py)
The caption is static over a moving scene. Mask = pixels caption-coloured (white fill, blue outline) in >= 60% of
the full-strength frames, holes filled, dilated 2 px. Per frame: harmonic inpaint of the mask, English drawn in
Liberation Sans Bold (outline 3 px, colours = darkest/brightest caption pixels, height = the Japanese one, centred
on it) at the Japanese caption's strength (contrast vs the inpainted scene, relative to full strength, minus the
inpaint error on the caption-free first frame: tracks fades in and out). Only macroblocks the mask or the new text
touch are re-encoded at the frame's qscale; if a frame then overflows its sectors, the edited blocks drop zigzag
coefficients past an index (printed; lowest 36 in RB0, 45 in RB4). Sector headers, count and EDC/ECC rewritten.
Output cached in build/fmvcache/<hash of fmvcap.py, strv.py, font> (90 s to regenerate). verify.check_fmv: same
size, only caption-frame sectors change, EDC/ECC valid, caption frames decode.

## Subtitles (spoken lines; 2026-11-14, D21)
- Source of the lines: `tools/xawav.py` (STR/XA audio -> one WAV per XA channel through ffmpeg's psxstr demuxer;
  the 2336-byte sectors get a sync + header back) -> `tools/asr.py` (faster-whisper large-v3, gitignored venv
  `tools/asr/`, setup in its docstring; `--no-vad` for voice under music) -> `work/subs/asr*.tsv`. Whisper's text is
  a draft (names: GaoMuscle came out ガオマンスル; 光の道 as 怒りの道): fix it against the in-game text and other
  takes of the same line (CDXA00 holds the narrations again).
- `script/subs.tsv` (src, start s, end s, ja, en). STR rows are burned in by `fmvcap.subtitle` (build.py, cached
  with the captions): white Liberation Sans Bold 13, 2 px black outline, max 2 lines of 304 px, bottom at y 204;
  frame = int(s * 30) + 1. The text's macroblocks are re-encoded; most frames are packed full, so a frame whose
  text doesn't fit even with AC cuts is re-encoded whole at a coarser qscale (RN2 test frame: q 10). verify and
  `caption_sectors` cover captions + subtitle frames (`fmvcap.edited()`).
- What talks where (`fmvmap.py`, now with .XA): OP0 theme song (not subtitled); RB0/RB2/RN1 Tetomu's narration;
  RB1/RB3/RN0/RN2 attack calls and the Org revival chant. In-game voice: `O_XAHEAD.PAC` leaf 1 = clip table (u16
  count 0x5f at 0, then 8-byte rows from 0x10: u16 channel, u16 start, u16 length, u16 bank 0-2 = CDXA00-02).
  CDXA00 (16 ch): Tetomu's narration (story/endings) and menu voice; CDXA01: boss taunts in action stages and
  story intros; CDXA02: robo-scene Org chants and attack calls. CDXA lines are rows with src `CDXA0n_c<ch>`, drawn
  by the engine (§In-game voice).

## In-game voice (2026-11-15, D22)
- Every voice clip plays through `xa_play` 0x80034F78 (flags a0, a1 = &{channel, lba, length in sectors};
  `tools/lua/xalog.lua` logs them). Driver globals (gp = 0x80063B54): +0x290 play mode (3 seeking, 0x13 playing, 0
  stopped), +0x2a0/+0x2a4 clip start/end LBA, +0x2a8 LBA of the last sector read (advances ~2.5 sectors/frame at 2x),
  +0x2ac XA flag, +0x2b5 channel. The drive reads on past +0x2a4 until the game stops it.
- Hook (`asm/subs.asm`, data from `tools/subs.py` -> build/subs_data.asm): frame end `jal DrawSync` 0x8002E8B4 ->
  MainStub, flip `jal DrawOTag` 0x8002E468 -> FlipStub, crt0 0x8004C970 -> CopyStub. Stubs sit in dead code
  0x8002F10C-0x8002F444 (build.DEAD). The blob (code, font, SubTable, texts) is appended to the EXE image at
  0x80064000 (t_size grows; BSS, so CopyStub copies it before crt0 clears BSS) and runs at 0x800C8000-0x800CD000
  (never written by the original game: `tools/lua/subwatch.lua`, only the BIOS boot clear; `tools/memfree.py`).
  MainStub checks the blob's magic and code checksum each frame and falls back to the plain calls if it was ever
  overwritten.
- Once a frame FindRow maps (+0x2a8 - file LBA, channel) to a SubTable row (only while mode & 3, XA, and sector <
  clip end); a new row must come back 4 main-loop passes in a row (debounce), then Render draws the line with the English VWF font into a 1-bit mask, outlines it into a
  304x28 4bpp canvas and LoadImages it to VRAM x 768 y 416 (+ the 48 px right part at y 444) with its CLUT at
  800,412. The flip then sprites it over the game OT at the bottom centre of the DRAWENV clip (0x800A2448), top
  56 px above the clip bottom (some screens show only 224 lines). Pause/stop follow the audio.
- Rows: times are the channel's own audio (asr.py on xawav.py output); `subs.table` maps them to file sectors by
  the channel's audio-sector list and starts a mid-channel row 2 sectors late (a clip's last sector can hold the
  next line's first words: a 2-6 frame flash; the debounce catches the rest). Check on a build: `warp.py SCENE --cue build/gaoranger_en.cue
  --script tools/lua/subshot.lua --var CURROW=.. --var OKFLAG=..` (addresses from build/subs.sym) logs each row
  change and shoots it. Warp routes mash circle, which cuts some clips short.
