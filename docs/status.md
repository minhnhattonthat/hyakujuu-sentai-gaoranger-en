# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build next (phase 2 debug tool done 2026-11-14: 87/87 scenes from a cold boot). Last build: none yet.
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
- **Next (phase 3):** identity rebuild with mkpsxiso from `work/disc/layout.xml` (byte-identical .bin as a test),
  then a moved/grown-file test (lookup is by name: prove a moved PAC still loads, e.g. warp a scene on that build).
  PAC repack (add + lzs compressor) roundtrip as part of it or phase 4.
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
