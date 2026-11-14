# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator in progress: all graphics text English incl. credits (2026-11-14).
  Last build: `build/gaoranger_en.bin` SHA-1 1020559e095b..., build+verify exit 0, smoke ok, check.py green.
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
  - Phase 8 session 4: card/option scenes (savefmt, savefull, savenc, loadnc, loadbad, savepull, fmtpull, loadpull,
    tsoundset, tvibset; warp.lua `NOCARD=1`, KEYS key `pull` = card pulled; blankcard full/corrupt cards). textptr.lua
    now logs the next string of a table (pointer steps past an FF). **Text coverage gate passes**: `tools/tour.py`
    (all 101 scenes, text scenes shot every 30 frames, HOLD=0) -> `textcov.py work/qa/tour --waive
    script/text_unshown.tsv` = 0 unshown (waivers D15). Fixed: option-screen title showed VIBRATIO (sprite is only
    しんどう wide; TIM 131 rect 88 px, xscale 0.85). inkbox: save/load Yes/No + titles, Stereo/Mono, On/Off centred
    (EN margins 32/33, 36/37 vs JP 22/22, 39/40 etc.); game-over choices sit where the JP ones do (by eye: busy bg).
    Tour manifest `work/qa/tour/manifest.tsv` (432 sheets, build 1020559e); visual QA by codex
    (`tools/vqa_codex.py work/qa/tour`, brief docs/visual-qa-brief.md) -> `work/qa/tour/verdicts/`.
- **Next (phase 8):** read `work/qa/vqa1.log` (codex verdict issues), fix, re-tour changed scenes, write
  `verdicts/recheck_N.tsv`, until `qa_gate.py check work/qa/tour/manifest.tsv work/qa/tour/verdicts` exits 0.
  The tour's overb never reached game over (tour's HOLD=0 overrides the scene's HOLD=200: keeps fighting); its EN
  game over is in work/qa/p8/w5/overb. In-game shots still missing for banners (TIM 136: 12_17 groups g00-g05 in
  DS_ST01/04 and DE_ST03-05; the DS ones live in the story PACs' slot-12 script 12_18, which no traced path runs
  (chapter intros run slot 13); DE_ST03-05 slot 12 runs in de03-05 but no banner seen: decode op 0x9001/0x9002
  object/group args in 12_18), ORGETTE (TIM 5; maybe only in extra stages ex01-10, which load A_OGET*), CHANCE!
  (robo battle prompt; needs enemy HP low: find it). Space = normal ASCII space (VWF glyph); never `{sp81}`.
- **Open questions (non-blocking):**
  - Action-stage game over not in the scene list: player HP not found (0x8007c6f8 is a sprite x, not HP; idle 15000
    frames barely dents the bar). It uses the same game-over texture as the robo one (scene overb). Find HP for
    GOD/kill if phase 8 needs the action layout.
  - FMV burned-in Japanese not checked yet (`XA/*.STR`: OP0, RB0-5, RN0-2).
  - Title logo: keep Japanese unless an official English logo exists (D5) - check in phase 8.
  - Graphics are the bulk of the work (menus, name plates, banners, game over, credits); dialogue text is small.
  - Card table (Y_TITLE/21, CARDMS/0) never shown by any tour: its 232 px budget is a guess; find its screen in
    phase 8 (maybe no-card / minigame high-score flows).
  - Debug menu tables left Japanese (unreachable); they would draw as garbage now that hiragana cells hold English.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) D13: brush hit kanji (斬 etc.) kept as decoration; say if they should
  become English words.
