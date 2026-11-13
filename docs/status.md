# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done 2026-11-14). Last build: none yet.
- **Done:**
  - Step 0: repo setup (PCSX-Redux nightly + SCPH-5500 BIOS in tools/, mkpsxiso 2.30, armips 0.11.0, pre-commit
    hook runs `tools/check.py`, guard hook verified, rom.sha1). Original boots: `work/qa/smoke-orig`.
  - Phase 1: disc unpacked (`docs/re/disc.md`), PAC add/lzs format + decoder (`docs/re/pac.md`), text encoding,
    control codes, string tables (22 tables, 307 strings incl. duplicates; `docs/re/text.md`), font geometry,
    graphics-text static sweep of 164 unique TIMs (`docs/re/graphics.md`).
- **Next (phase 2, debug tool):**
  - Leftover debug menu strings in O_TITLE.PAC/1 (テスト, ステージセレクト, RANGER/ROBO/DEMO): find how to open it
    (button combo at title, or a RAM flag) and use it for warps; else find the stage/scene id variable in RAM.
  - Scene list: each A_ST*/B_ST*/BA/BB/BC stage, DS_ST01-07 intermissions, DE_ST01-07 endings/credits, game over
    (A_DEMO 16_3), title/options/save/load, OP0.STR and other FMVs.
  - Then phase 3: identity rebuild; find how the game locates files (no names/LBA table found: disc.md).
- **Open questions (non-blocking):**
  - FMV burned-in Japanese not checked yet (`XA/*.STR`).
  - Title logo: keep Japanese unless an official English logo exists (D5) - check in phase 8.
  - Graphics are the bulk of the work (menus, name plates, banners, game over, credits); dialogue text is small.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
