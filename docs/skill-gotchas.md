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
