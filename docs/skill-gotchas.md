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
