# Skill gotchas

One line each: the reference file it belongs in, then the fact.

- references/pipeline.md §Recon: relative search (`relsearch.py`) misses encodings where code = row*32 + col of a
  21-column font sheet (gaps at every row end); here the font itself in VRAM gave the table in minutes - dump VRAM at
  a text box and read the font layout before brute-forcing.
- references/pipeline.md §Recon: to find a game's decompressor, put a read breakpoint (`L.on_read`, `--debugger`) on
  the first stream bytes of a PAC found raw in a RAM dump; the decode loop PC shows up in the first hits.
- scripts/iso9660.py: running it without arguments crashes with IndexError instead of printing usage (no --help).
- references/platform-ps1.md: a heredoc `python - <<'X'` with an empty body drops into the interactive interpreter
  under the Bash tool (blocked heredocs make this tempting); write the script with the file tool.
- references/emulator-qa.md §Debug tool: PCSX-Redux `--debugger` (needed for `L.on_exec`) is several times slower;
  three parallel 7000-frame debugger runs hit a 1200 s timeout. For warps, poll RAM in `L.on_frame` instead (here:
  rewrite the script's load op in RAM, detect loads by the CdlLOC seek position) - 75 scenes ran in 8 min.
- references/emulator-qa.md §emu.py: PCSX-Redux runs without `--sav` all share `tools/pcsx/memcard1.mcd`, so
  parallel runs can leak saves into each other; pass `--sav` with a blank card for warps.
- references/emulator-qa.md §Debug tool: `L.press` from a hook only queues behind the route; check
  `L.route_done()` first, and a game may ignore START-to-skip until the cutscene is actually rendering.
- references/pipeline.md §Recon: search for file names case-insensitively; this EXE's lowercase
  `DATA\o_logo  .pac` table was missed in phase 1 and the disc looked like it had no file lookup.
- references/emulator-qa.md §Debug tool: PCSX-Redux + real BIOS rewrites memory-card frame 63 (header write test)
  on any card access, so "did the game save?" must compare the save blocks (offset 8192+), not the whole .mcd.
- references/emulator-qa.md §Debug tool: a title menu can change once the card holds a save (here the wheel opens
  on つづきから and gains a minigame item); scene routes that depend on the card must pin the card they start from.
- references/emulator-qa.md §Debug tool: a stage HUD bar's prim coordinate looks like HP in a RAM search (drops in
  step with hits) but is a sprite x position; poke-test before trusting it (here it changed nothing).
- references/platform-ps1.md (Rebuild): dumpsxiso + mkpsxiso 2.30 did not rebuild this 2001 disc 1:1. Needed: a
  committed layout with `cdvd_style="false"`, blank `system`/`application` ids (else "PLAYSTATION"), a 150-sector
  `<dummy type="32">` postgap, and a post-pass for the PVD submode (0x08), a 1901 root-dir date, postgap subheaders,
  and a cue `PREGAP` the .bin doesn't store (dumpsxiso wrote `<pregap 00:04:00>`: wrong). Paths in the xml resolve
  relative to the xml's folder. Python EDC/ECC for form-1 sectors: tools/mkdisc.py (checked on original sectors).
- references/pipeline.md §Extract: in a 2-byte big-endian glyph encoding whose high byte can be 00, zero padding
  between strings is indistinguishable from a glyph start; take string starts from the pointer table and treat a
  non-zero gap as an unreferenced string starting at the even byte before its first non-zero byte.
- references/pipeline.md §Marker (PS1, compressed archives): a re-encoded block that packs SMALLER moved the next
  blocks earlier in the archive and a later picture decoded with wrong colours (likely decoded over still-packed
  data); pad every rebuilt block to >= its original size and fail the build if any block starts earlier.
- scripts/jp_left.py: can't see text inside compressed archive blocks; a per-table check that reads the built
  archives back (here tools/jpleft.py) is needed instead.
- references/platform-ps1.md: a cheap PS1 VWF when the renderer emits one 12 px quad per text cell: keep the cells,
  replace `x = col * 12` by a running per-row offset + a width byte table; dead PCdrv host-file I/O functions
  (no callers) in the EXE make a safe home for the table.
- references/pipeline.md §Checks (compressed archives, disc images): `romdiff.py` on a re-encoded archive or a
  relaid disc diffs everywhere; compare decoded leaves instead (same leaf set, only text/font leaves changed) and
  dump the built disc back to files (here tools/verify.py, run by build.py).
- references/pipeline.md §Checks: text tables decoded from compressed blocks grow (+50% here); log the decoder's
  (src, dst, size) at runtime (tools/lua/lzslog.lua) and check nothing else lands in the grown tail.
- references/pipeline.md §Checks: name a runtime decode by its first stream bytes matched against the built
  archives, never by decoded size (identical sizes misnamed tables, and a run that decoded no grown table "passed");
  give each traced scene the table it must decode, and cap each table's size in the build at what was traced.
- references/emulator-qa.md: a read breakpoint on where a PAC sat at the title fires later on whatever file the
  game loads to the same buffer (a false "card table decoded" hit); confirm a block by its content, not its address.
- references/graphics.md §Edit: a logo sprite can be drawn taller than its ink box (here rows 0-~72 of a 64-row logo); the top rows of the label packed below it then show under the logo, so clear those rows and drop the label a few px.
- references/graphics.md §Edit: logos split into pieces drawn side by side (ゲームオーバ + a separate ー, データ+の+ロ+ード, ドッ+キリ): find each piece's rect from ink column gaps, render the English once across the pieces' total width and cut it (tools/gfx_edit.py composite); pair pieces shared by several labels with right-aligned + left-aligned halves.
