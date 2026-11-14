# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9. Released v1.0 2026-11-15 (GitHub release, repo public): `release/GaoRanger_EN_v1.0.zip`
  (xdelta 18114151 bytes, SHA-1 50ff3c1e...; + README.txt; FMV + in-game voice subtitles included).
  `tools/release.py --version 1.0 --skip-build` exit 0 (check 51 passed, smoke ok, jpleft 0, story 8/8, tour
  waived for the subtitle-only build, D23). Patched .bin SHA-1 cbc12bae5221..., CRC32 f154eb9b. Next tour must
  re-init the tour manifest on the new build.
  **warp.py's default --cue is the original disc: always pass `--cue build/gaoranger_en.cue` for English shots.**
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
  - Phase 8 session 5 (D16): visual-QA round 1 fixed. Label rects now follow the sprite records (docs/re/graphics.md
    §Redraw status): plates u 144-239 at one size (Sans Bold 10), START LOADING u 136-247, option titles u 24+,
    title-wheel Vibration u 8-79 / Relaxed 80-151, LOAD/SAVE DATA kept to the panel (u 25-128). Pause menu
    たたかい+つづける: `gfx/edits.py SPRITE_FIXES` (37 leaves) drops the first sprite, centres CONTINUE
    (tests/test_sprite_fix.py). Post-ending save-screen junk proved original behaviour (VRAM dumps, docs/re/pac.md;
    JP refs work/qa/warp/de03s-05s; brief updated). `GFX_SKIP=sha,..` bisects graphics edits;
    `tools/lua/vdumpat.lua` dumps VRAM/RAM at frame AT. Full re-tour (build 7e1e4d1c) + codex round 2
    (work/qa/vqa2.log): 4 new issues, 2 fixed since (tload LOAD DATA), 2 = FMV caption (below).
  - Phase 8 session 6 (D17, docs/re/fmv.md): FMVs surveyed (every STR); robot-name captions at the end of RB0/RB2/RB4
    now GAOKING / GAOMUSCLE STRIKER / GAOICARUS, seen in game (work/qa/p8/fmv: bb01c ~f6150, bb04c ~f4350, bb06c
    ~f4800). Own STR v2 codec `tools/strv.py` (jPSXdec jar refused by the permission check), `tools/fmvcap.py`
    (build.py step, cached in build/fmvcache), verify.check_fmv, tests/test_strv.py, `tools/fmvmap.py` (scene ->
    STR). Logo, brush kanji and the RN0 破邪百獣剣 flash kept. visual-qa brief updated for FMVs.
  - Phase 8 session 7: tour of build 9c143a4a completed (the killed run's warps had all finished: `tour.py
    --sheets-only`), stale D16 junk verdicts dropped, codex round 3 (work/qa/vqa3.log): 130 sheets, 0 issues.
    **`qa_gate.py check work/qa/tour/manifest.tsv work/qa/tour/verdicts` exits 0**; textcov 0 unshown. In-game:
    CHANCE! (TIM 77) in b01 f6600 (work/qa/p8/w7/chance_b01_f6600.png, JP same blend), ORGETTE (TIM 5) on the
    ofight result "6 ORGETTE" (w7/orgette_ofight.png; needs `tools/lua/brawl.lua`: the circle mash never kills).
    New probes: `tools/lua/ramevery.lua` (RAM dumps every N frames), `readaddrs.lua` (which table bytes are read,
    when; `--trace`), `brawl.lua`, `tools/sprfind.py` (sprite records showing a tpage area). Lua vars must not be
    named FROM/TO (warp.lua's swap ids); LuaJIT has no `//`.
  - Phase 8 session 8: TIM 136 banners seen in game, EN beside JP (de03 GAOMUSCLE STRIKER IS BORN!, de04 GAOSILVER
    AWAKENS!, de05 GAOICARUS IS BORN!, ~f5400; work/qa/p8/bnm, bnm45). Cause of the stall: the endings' fade-to-white
    (script ops 1c/1d) is stepped only in D_SYS story-loop modes 0x15/0x16; the warp's opening entry left 0x13
    (docs/re/flow.md). warp.lua `MODE` var, scenes de03-05 set MODE=0x15. Re-toured de03-05, codex round 4
    (work/qa/vqa4.log): 18 sheets, 0 issues; `qa_gate.py check` exits 0, textcov 0 unshown, check.py green.
  - Phase 9 (D18-D20): story pass `tools/story.py --review` (chapter files ds01-07 + menus, codex read-only per
    chapter, reports work/qa/story/reports): 8/8 ok, 0 Critical/Important; menus' 4 Minors were a prompt error
    (3-line save box), waived in docs/polish.md. docs/synopsis.md + docs/style-reference.md written. Credits: 4
    staff names fixed from other Natsume games' English credits (Ohta, Kazuhito Yamada, Shinpo, Hiroshi Inagaki),
    seen in game (de07 f9750/f10200, work/qa/p9_names.png); the 18 unsourced readings waived as a README known
    issue. tour.py fixed: a one-scene tour wrote into the tour root (warp.py's --out is the scene dir for one scene).
    de07 re-toured on build 22954f04 (sheets unchanged: the staff pages sit past the sheet's 24 frames).
    `tools/release.py` + `docs/release-readme.txt` (zip README with base/patched hashes); repo README filled.
  - Post-release session (2026-11-14, user report): title PRESS START!! was invisible (TIM 159 drawn with no
    outline on the logo's white glow; outline restored, seen in game work/qa/ts_en f1510). FMV subtitles (D21,
    docs/re/fmv.md §Subtitles): `script/subs.tsv` burned in by fmvcap.py; xawav.py + asr.py (Whisper) transcribe;
    fmvdiff.py checks re-encode damage (0 on all). Seen in game: bb01c (RB0, f3420-6060), a11 (RN1). Build
    4a4ffc1d4385, check 48 passed, smoke ok. RB0 frame 1190's right-edge stripe is original (frame untouched).
    **v1.0 release zip is stale** (rebuild with release.py when the user asks).
  - In-game voice subtitles (2026-11-15, D22, docs/re/fmv.md §In-game voice): engine hook `asm/subs.asm` (stubs in
    dead code 0x8002F10C, blob appended to the EXE and copied to 0x800C8000 at boot) + `tools/subs.py`; 94 CDXA rows
    in script/subs.tsv (transcripts work/subs/asr2.tsv: `asr.py --prompt` with the cast names, not committed).
    Skipped: lines already shown as text, chants/grunts, 4 unclear lines (listed in subs.tsv). Seen in game on every
    scene (`warp.py --all` with tools/lua/subshot.lua: 101 OK; one shot per line checked by eye). tests/test_subs.py.
- **Next:** user check of the in-game subtitle wording, esp. guesses: CDXA00_c2 22.0/23.8 ("You never give it a
  thought." / "Isn't that so?", opening narration), CDXA00_c11 6.44 (which Highness Duke: Whisper hears only
  "ハイネスデュークオルグ"), CDXA01_c1 "Yabaiba" pun. Re-tour + visual QA of the subtitled FMV scenes before a new release. Publishing is the user's call (pipeline.md §Publish: `gh release create v1.0 release/GaoRanger_EN_v1.0.zip`,
  notes with base hashes + patch SHA-1). Optional: player bug reports (GitHub issues).
  Known gap (non-blocking): action-stage game over (TIM 7) never shown in game: player HP not found (ramsearch
  over work/qa/p8/hp dumps leaves ~6.5k candidates); TIM 7 uses the same rects/edit as TIM 96, seen in overb.
  The tour's overb never reached game over (tour's HOLD=0 overrides the scene's HOLD=200: keeps fighting); its EN
  game over is in work/qa/p8/w5/overb. Space = normal ASCII space (VWF glyph); never `{sp81}`.
- **Open questions (non-blocking):**
  - Card table (Y_TITLE/21, CARDMS/0) never shown by any tour: its 232 px budget is a guess (D11).
  - Debug menu tables left Japanese (unreachable); they would draw as garbage now that hiragana cells hold English.
- **Open bugs:** none known. Visual-QA round 1's five bugs and the round-2 FMV caption fixed.
- **Waiting on the user:** (non-blocking) D13: brush hit kanji (斬 etc.) kept as decoration; say if they should
  become English words. (non-blocking) 18 staff-name readings in the credits are guesses (docs/polish.md D18).
  Release v1.0 is built, not published: say when to publish.
