# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise. No earlier fan translation exists (web search
2026-11-14: none found).

| File | Covers | State |
|---|---|---|
| [disc.md](disc.md) | disc layout, files, LBAs, file lookup by name, byte-identical rebuild, moved-file test | verified (tests/test_disc.py, warps) |
| [pac.md](pac.md) | PAC "add" archives, "lzs" compression (EXE 0x8002f700), repack + compressor | verified (identity repack, all blocks roundtrip, in game) |
| [text.md](text.md) | glyph encoding, control codes, string tables, font geometry, debug menu strings | verified (known lines) |
| [flow.md](flow.md) | file table + loader, sequence script ops, chapter variable, debug tool | verified (traces, warps) |
| [graphics.md](graphics.md) | graphics-text survey (TIM static sweep) | sweep done; non-TIM open |
| [fmv.md](fmv.md) | STR video format, own codec, burned-in text survey, caption replacement, scene map | verified (in game, work/qa/p8/fmv) |

Recon tools (all in `tools/`): `unpack_all.py`, `pac.py`, `catpac.py` (one blob + `where`), `textscan.py`,
`runscan.py`, `loosetbl.py`, `make_tbl.py`, `fontsheet.py`, `timscan.py`, `vram.py`, `ramfind.py`, `relscan.py`,
`patscan.py`, `sjis_scan.py`, `disc_lba.py`; build: `build.py`, `mkdisc.py`, `movetest.py`, `verify.py`, `lzsmap.py`; Lua probes `tools/lua/readbp.lua`, `seqdump.lua`, `vdump.lua`, `lzslog.lua`.
