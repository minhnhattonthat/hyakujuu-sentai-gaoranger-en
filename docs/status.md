# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build next (phase 4 extract done 2026-11-14). Last build:
  `build/gaoranger_en.bin` 2026-11-14, no edits, SHA-1 20df603f... = original (identity).
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
- **Next (phase 5):** English font/encoding decision (12 px cells; half-width / VWF / digraph glyphs; font TIM
  copies listed in text.md), insertion: `extract.build(json, "en")` -> replace the leaf (`pac.parse` -> node with
  `payload` for lzs leaves, `_z_` paths through the payload's add) -> `pac.build` into `build/overlay/DATA/` for
  every file in the JSON's `files`. Marker build `[id] ...`, warp tour, mark non-text (debug tables, ruler, hex
  digits), measure box widths per variant (story box ~2 x 17 glyphs, save/load/card boxes, title labels).
- **Open questions (non-blocking):**
  - Action-stage game over not in the scene list: player HP not found (0x8007c6f8 is a sprite x, not HP; idle 15000
    frames barely dents the bar). It uses the same game-over texture as the robo one (scene overb). Find HP for
    GOD/kill if phase 8 needs the action layout.
  - No-card memory-card messages (メモリーカードがセットされていません): emu.py always inserts a card; needs a
    no-card run option if phase 8 wants that shot.
  - FMV burned-in Japanese not checked yet (`XA/*.STR`: OP0, RB0-5, RN0-2).
  - Title logo: keep Japanese unless an official English logo exists (D5) - check in phase 8.
  - Graphics are the bulk of the work (menus, name plates, banners, game over, credits); dialogue text is small.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
