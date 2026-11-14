# Visual-QA reviewer brief - Hyakujuu Sentai GaoRanger (PS1)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/tour/verdicts/<chunk>.tsv`.
- The original disc's shots for the same scene: `work/qa/warp/<scene>/sheet*.png` (scene = the id's first part,
  shots every 150 frames, so timing differs) and `glossary.md`.

## How to look
- Read each sheet whole first. The tiles are named by frame. Where text is small, zoom into a frame with
  `python -X utf8 <SKILL>/scripts/sheet.py work/qa/tour/<scene>/fNNNNNN.png --crop x,y,w,h --zoom 3 --out <scratch>.png`
  (the frames sit next to the sheet; `python tools/skill.py` prints SKILL).
- When something looks wrong, compare with the original's sheet. If the original shows the same thing, it is the
  game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, menu title, option value and speaker name plate.

## Judge
An `issue` is any of:
- Japanese still visible (except the standing items below);
- text overflowing a box, clipped by a frame or a sprite edge (e.g. a menu title cut mid-letter), or off screen;
- text off-centre where the original centres it;
- garbage tiles, wrong or missing glyphs, stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade, a cursor caught mid-blink; black frames between scenes; a scene loading;
- anything identical in the original's sheet;
- the title logo (ガオレンジャー logo art) stays Japanese (decision D5);
- brush impact kanji on hits in action/robo stages (斬, 破, 削, 烈, 魂, 滅, 痛, 砕, 牙, 吹, 鬼) stay (D13);
- in the videos (FMV): the brush calligraphy 破邪百獣剣 flashing behind a light burst in the rangers' sword attack,
  and 痛/砕鬼 in the opening, stay (D17); the robot-name captions under a robot at the end of a video are English
  (GAOKING, GAOMUSCLE STRIKER, GAOICARUS) and are judged like any text;
- the action-stage gauge and HUD numbers; the title screen's TEST USER (debug) label;
- runs that end on the title screen or loop back (demo scenes b00, bb00c, ademo);
- credits names are romanised guesses listed in docs/polish.md (judge only layout there).
- the save prompt after an ending (de01, de02, de03s-de05s, ~f5600 on): its background is leftover framebuffer
  junk in the original too (raw texture data drawn as orange/green "clouds", repeated おわり/THE END, sprite
  scraps). Which of the two leftover buffers shows depends on load timing, so the original's de01/de02 happen to
  show a blue sky and de03s-05s the orange junk (work/qa/warp/de03s..de05s); either is the game's own behaviour.
  Judge only the prompt text and choices there.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile/frame, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
