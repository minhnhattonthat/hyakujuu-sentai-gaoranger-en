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
