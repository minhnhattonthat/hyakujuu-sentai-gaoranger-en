# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool in progress (warp works for 66 of 75 scenes; 2026-11-14). Last build: none yet.
- **Done:**
  - Step 0: repo setup (PCSX-Redux nightly + SCPH-5500 BIOS in tools/, mkpsxiso 2.30, armips 0.11.0, pre-commit
    hook runs `tools/check.py`, guard hook verified, rom.sha1). Original boots: `work/qa/smoke-orig`.
  - Phase 1: disc unpacked (`docs/re/disc.md`), PAC add/lzs format + decoder (`docs/re/pac.md`), text encoding,
    control codes, string tables (22 tables, 307 strings incl. duplicates; `docs/re/text.md`), font geometry,
    graphics-text static sweep of 164 unique TIMs (`docs/re/graphics.md`).
  - Phase 2 so far (`docs/re/flow.md`): file table found (files are looked up **by name**, disc.md updated: the
    phase-3 LBA worry is mostly gone), loader chain, sequence-script interpreter + ops, chapter variable 0x8009ec28.
    Debug tool: `tools/debug/warp.py` + `warp.lua` + `scenes.txt` (75 scenes), no debugger, full speed:
    `python -X utf8 tools/debug/warp.py --all --jobs 4` runs all in ~8 min (all report OK = target file loaded).
    Probes: `tools/lua/cdlog.lua` (file loads, debugger), `tools/lua/seqtrace.lua` (script trace), helpers
    `tools/filetable.py`, `tools/loadgraph.py`, `tools/cdmap.py`, `tools/binfind.py`.
  - Visually verified (final-frame overview, run of 09:26): title, ba01, ds01-07 (story shown ~frame 4800-5250,
    then stage), a11-a53, ex01-10 (stages), bb00b, bb01a-b06 robo scenes/battles, bb06c (robo GAME OVER), b07,
    bc07, ba02, ba03, de03-05, de07 (credits), de07e (-> Y_EDSAVE save screen), load, option (サウンド).
- **Next (phase 2):**
  1. Re-run `--all` with the new HOLD (story/menu scenes stop mashing once loaded, so the final frame should be
     the first story box). Not yet run since the change; check ds01-07 finals show the dialogue box.
  2. Broken scenes: **de01, de02, save** hang right after D_SYS loads (trace: `--trace`, no further loads);
     **edsave, gage, cardms, ivent, ba05** end on black; **ademo, bb00c** end back at the title and **b00** in an
     action stage (need a mid-run proof shot, not final). DE_ST0n are reached in the real game from the B_ST0n
     script (chapter switch at B_ST01.PAC/1_16 0x7b2e, after winning the robo battle), so a 50xx swap in the
     opening context may be wrong for them; try swapping from a B-context load, or decode what DE_ST03 does that
     DE_ST01 doesn't. Y_SAVE is loaded from B_ST scripts (0x7a5a) too.
  3. Missing scene kinds: action-stage game over (no-input run), pause menu (START in a stage: seen working in
     ba01b's final), title wheel items (データのロード, サウンド, しんどう, つづきから with a saved card), difficulty
     select, the minigame ザ・あべし (O_TITLE strings; how to reach unknown), A_ST010 (table says a_st01y.pac,
     id 0x5100). GOD mode: player HP address not found yet (warp.lua logs "not mapped").
  4. `--sav` a blank card per run (`tools/pcsx/memcard1.mcd` is shared by parallel runs) and `--state` library.
  5. Then phase 3: identity rebuild (+ a moved-file test, since lookup is by name).
- **Open questions (non-blocking):**
  - FMV burned-in Japanese not checked yet (`XA/*.STR`: OP0, RB0-5, RN0-2).
  - Title logo: keep Japanese unless an official English logo exists (D5) - check in phase 8.
  - Graphics are the bulk of the work (menus, name plates, banners, game over, credits); dialogue text is small.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
