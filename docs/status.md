# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator in progress: all graphics text English incl. credits (2026-11-14).
  Last build: `build/gaoranger_en.bin` SHA-1 2379bb2cc655..., build+verify exit 0, smoke ok, check.py green.
  THE END seen in game on it (warp de07e, work/qa/p8/w6/de07e/f006000.png). **warp.py's default --cue is the
  original disc: always pass `--cue build/gaoranger_en.cue` for English shots.**
- **Done:**
  - Step 0: repo setup (PCSX-Redux nightly + SCPH-5500 BIOS in tools/, mkpsxiso 2.30, armips 0.11.0, pre-commit
    hook runs `tools/check.py`, guard hook verified, rom.sha1). Original boots: `work/qa/smoke-orig`.
  - Phase 1: disc unpacked (`docs/re/disc.md`), PAC add/lzs format + decoder (`docs/re/pac.md`), text encoding,
    control codes, string tables (22 tables, 307 strings incl. duplicates; `docs/re/text.md`), font geometry,
    graphics-text static sweep of 164 unique TIMs (`docs/re/graphics.md`).
  - Phase 2 (`docs/re/flow.md`): file table (lookup by name), loader chain, sequence-script ops incl. the scene-entry
    sequence (03 load, 39 fade, 05/06 engine mode), chapter variable 0x8009ec28. Debug tool `tools/debug/warp.py` +
    `warp.lua` + `scenes.txt`: **87 scenes, all OK from a cold boot** (`warp.py --all --jobs 4 --state`, ~12 min;
    proof: `work/qa/warp/<scene>/final.png` + sheets, overview `work/qa/warp/finals*.png`, checked by eye
    2026-11-14). States for every scene in `work/states/<scene>.sstate`; save fixture `work/saves/savedone.mcd`
    (written by the game in scene savedone). Covers: title + all 5 wheel items, difficulty select, opening, every
    chapter story intro (ds01-07), every action stage incl. extras and demo, every robo scene/battle, all endings
    (de01-05, de07 credits, de07e), save/load/option screens, save flows (save done, overwrite, unformatted card),
    continue with a save, the オルゲットファイト minigame (menu + stage, appears once the card has a save), pause menus
    (action, robo), robo game over. Each run gets its own blank card (`tools/blankcard.py`).
  - Files with no loader (no warp scene needed, give them the same edits as the shown copies): Y_GAGE (no text),
    CARDMS (= Y_TITLE/21 + font), Y_IVENT (= stage game-over TIM), O_TITLE (its data sits inside Y_TITLE), DEBUG.PRG.
  - Phase 3 (`docs/re/disc.md` §Rebuild, `pac.md` §Repack): `tools/build.py` -> `tools/mkdisc.py` (mkpsxiso from
    committed `disc/layout.xml` + `fix_image` for 4 mastering quirks) gives a byte-identical .bin with an empty
    overlay (`build/overlay/`, same paths as the tree; changed files go there). `pac.parse/build` repacks every PAC
    byte-identical; `pac.lzs_encode` roundtrips all 2252 blocks. Moved-file test (`tools/movetest.py`: every block
    re-encoded, 65 PACs resized, files moved): all 87 warps OK, files loaded from new LBAs. Tests: `tests/test_disc.py`.
  - Phase 4 (`docs/re/text.md` §Extraction): `tools/extract.py` -> `script/*.json` (15 unique tables in 22 files,
    280 strings; no text in the EXE/PRGs). Rebuild from jp == original for every file; coverage tests
    (`tests/test_extract.py`).
  - Phase 5 (`docs/re/text.md` §Renderer, §English font and VWF, §Box budgets, §Marker build): VWF hook in the EXE
    cell renderer (`asm/vwf.asm`, armips via build.py with original-byte checks), width table in dead PCdrv code,
    story box 20 -> 48 columns; font `fonts/vwf.txt` (Dual Orb MIT font + shadow) into all 19 font TIM copies
    (`tools/font.py`, writes `tbl/en.tbl`); insertion `tools/insert.py` (pads rebuilt blocks: a block moving earlier
    broke the de01 cloud colours, docs/re/pac.md). `build.py --marker` / `--qa ID=TEXT`. Lint `tools/lint.py`
    (px budgets, lines, control codes; check.py runs it), `tools/jpleft.py` (Japanese left in built PAC tables),
    coverage probe `tools/lua/textptr.lua` + `tools/textcov.py`. Marker tour `work/qa/mk` (31 scenes, all boxes
    show ids), coverage `work/qa/cov`. Budgets: story 2 lines x 232 px; save/load/option same box, 3 lines where
    the jp has 3; card table guess. Debug/unreachable tables kept Japanese: `script/keep_jp.txt` (76 ids).
  - Phase 6: all 77 player-visible strings translated in one batch by the worker itself (Orca brief: no
    subagents): `work/tl/p6.tsv` -> `tools/merge.py` (id<TAB>en -> script/*.json, refuses unknown ids/escapes;
    `tests/test_merge.py`). Glossary filled (Tetomu voice, Org names: Boat Org = はんせん(帆船)オルグ, Highness Duke
    Org, Memory Card wording, card choice spacing). Independent review: `codex exec --sandbox read-only` on
    `work/tl/p6_pairs.txt`: 0 Critical, 1 Important (card-0446, waived: glossary rule was wrong, JP is Tetomu's
    voice), 3 Minors fixed now (`docs/polish.md`, all ticked). Widest line 192/232 px.
  - Phase 6 harness review fixed (H:\translation\.harness\reviews\...-phase6.md): lint enforces glossary.md (JP term
    -> EN form, Avoid spellings; `tests/test_lint_glossary.py`), check.py passes `--untranslated`, 帆船オルグ ->
    Sailing Ship Org (D9), Tetomu voice/idiom Minors fixed, codex re-review saved `docs/reviews/p6-review.md`
    (0 Critical/Important; its one Minor fixed), skipped style-reference/translator-brief recorded (D10).
  - Phase 7 (docs/re/disc.md §Build verification, pac.md §Decode targets): `tools/verify.py`, run at the end of every
    build: EXE romdiff + hook-site original bytes, no branch into a replaced span, PAC leaf diff (only text/font
    leaves change), every string read back through every slot, built disc dumped back = tree + overlay. Mutation
    tests `tests/test_verify.py`. Runtime: decoded tables grew ~50% but blocks are placed back to back (heap-like),
    `tools/lzsmap.py` on lzslog traces: 0 overlaps. Lint covers widths, lines, control codes.
  - Phase 7 harness review fixed (H:\translation\.harness\reviews\...-phase7.md): lzslog logs stream heads, lzsmap
    names decodes by content, requires each scene's table (EXPECT), ignores next-scene heap reuse; regression set
    `lzsmap.py --scenes` (33 runs, `work/qa/lzs_all`): every grown table decoded, 0 overlaps; new scenes de03s-05s
    (ending save prompt), ytitle. Card table decoded by no scene (`tools/slotcalls.py`, D11). `insert.TRACED` caps
    table sizes. verify: independent armips writes, PRG/word branch scan, leaf growth, overlay file set, jpleft.
    Lint: blanks both ways, GUESSED budgets named. warp.py `--out` on another drive fixed.
  - Phase 8 so far: graphics pipeline `tools/gfx.py` (TIM index arrays, show/preview) + `tools/gfx_edit.py`
    (label: clear rect, OFL font without antialiasing, per-row fill + outline read from the original, glow ramps,
    align, composite labels across pieces) + `gfx/edits.py` (one entry per TIM) + `gfx/tims.tsv` (every TIM copy);
    insert.py writes every copy, verify.py checks them. Fonts: Anton, Liberation Sans (OFL, docs/fonts.md). Done:
    TIM 131 (menus, plates), 7 + 96 (game over), 159 (title wheel). Per-row state: docs/re/graphics.md §Redraw
    status. Wording: D12.
  - Phase 8 session 2: TIM 136 story banners (composites; layout from the 12_17 sprite groups), 154 THE END,
    5 ORGETTE HUD label, 77 好機 -> CHANCE!; hit kanji 4/6/8 kept (D13). `tools/sprgroups.py` decodes 12_17
    sprite-group leaves (credits, banners); `warp.py --shot-every N`.
  - Phase 8 session 3: credits rebuilt in English (`tools/credits.py` + `gfx/credits_en.py`: new atlas strips +
    rewritten DE_ST07 12_17 groups; D14; guessed readings in docs/polish.md, unticked for the user/phase 9), every
    page seen in game (work/qa/p8/credits_en, © lines credits_en2 ~f14100). tests/test_credits.py. de07 now 14500
    frames. Glossary: Gao colours, Yabaiba/TsueTsue, Shuten/Rouki/Rasetsu, King Org.
- **Next (phase 8):** In-game shots still missing for banners (no trigger found in ds01/ds04/de03-05 within 12000 frames: try the
  robo-battle/robo-scene files after those chapters, or the 12_18 script ops that pick 12_17 groups), ORGETTE
  (HUD shows it only in some state: not on screen in a11's first 9000 frames), CHANCE! (robo battle prompt; not in
  b00 demo or b01 at shots every 20 frames, work/qa/p8/robo; a white+purple pixel scan of the frames found none).
  Then: QA tour of
  every text scene with visual-QA verdicts (`qa_gate.py`), graphics text (the bulk:
  menus, name plates, banners, game over, credits, chapter cards; translator brief + style reference first, D10),
  `inkbox.py` on choice/centred boxes, `textcover.py`. Story boxes beyond the first page of each ds scene were not
  shot yet (warps stop at the first box). Card table: idle オルゲットファイト (20000 frames, work/qa/p7card) never
  ends, so its record-save prompt (likely where card-* shows) is still unreached; needs a kill/lose cheat.
  Space = normal ASCII space (VWF glyph); never `{sp81}` (0x81 takes no width under the VWF).
- **Open questions (non-blocking):**
  - Action-stage game over not in the scene list: player HP not found (0x8007c6f8 is a sprite x, not HP; idle 15000
    frames barely dents the bar). It uses the same game-over texture as the robo one (scene overb). Find HP for
    GOD/kill if phase 8 needs the action layout.
  - No-card memory-card messages (メモリーカードがセットされていません): emu.py always inserts a card; needs a
    no-card run option if phase 8 wants that shot.
  - FMV burned-in Japanese not checked yet (`XA/*.STR`: OP0, RB0-5, RN0-2).
  - Title logo: keep Japanese unless an official English logo exists (D5) - check in phase 8.
  - Graphics are the bulk of the work (menus, name plates, banners, game over, credits); dialogue text is small.
  - Card table (Y_TITLE/21, CARDMS/0) never shown by any tour: its 232 px budget is a guess; find its screen in
    phase 8 (maybe no-card / minigame high-score flows).
  - Coverage gaps for phase 8 scenes: no card, card check, format progress/done/failed, not enough space,
    save/load failed, corrupted data, option-0092/00e6/0116 (docs/re/text.md §Marker build and coverage).
  - Debug menu tables left Japanese (unreachable); they would draw as garbage now that hiragana cells hold English.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) D13: brush hit kanji (斬 etc.) kept as decoration; say if they should
  become English words.
