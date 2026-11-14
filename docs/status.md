# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate next (phase 5 engine + marker build done 2026-11-14). Last build:
  `build/gaoranger_en.bin` 2026-11-14, English font + VWF hook, text still Japanese (no `en` yet), SHA-1 87a077df...,
  smoke ok (`work/qa/smoke`).
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
- **Next (phase 6):** translate the 77 strings (ds01-07, save, load, option, card) in `script/*.json` `en`
  (glossary.md, decisions D1-D4; lint budgets). Small script: one or two translator batches, then reviewer pass.
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
- **Waiting on the user:** nothing.
