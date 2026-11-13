# Disc layout

- Redump: Hyakujuu Sentai GaoRanger (Japan), SLPS-03353, Bandai / Natsume, 2001-11-29. One .bin: track 1 MODE2/2352
  data, track 2 audio (index 01 at 13:50:37). SHA-1 in `rom.sha1`.
- Unpack: `tools/mkpsxiso/mkpsxiso-2.30-win64/dumpsxiso.exe -x work/disc/tree -s work/disc/layout.xml <cue>`.
  129 files: `SLPS_033.53` (PS-X EXE, load 0x80010000, size 0x54000, entry 0x8004c970), `SYSTEM.CNF`,
  `DATA/*.PAC` (PAC containers, pac.md), `DATA/*.PRG` (A_SYS, B_SYS, D_SYS, OPN overlays; DEBUG.PRG is 84 bytes of
  `jr ra` stubs; MAIN.PRG is empty), `DUMMY.WAV` (37 MB padding), `XA/*.XA` (audio), `XA/*.STR` (FMV).
- LBAs: `python -X utf8 tools/disc_lba.py <bin>` (copy in `work/disc/lba.txt`).
- **How files are found: unknown.** No file names in EXE/PRGs and no LBA table found (u32, u16 or BCD MSF search,
  `tools/disc_lba.py` + ad hoc scan). Until found, the safe plan is to keep every file at its original LBA and size
  in sectors (rebuild with the same layout order, pad new PACs to the old sector count). Find the loader in phase 3.
- Overlays in RAM at the title: OPN.PRG at 0x800a6ae8, Y_TITLE.PAC raw at 0x800cd000, O_TITLE.PAC raw at 0x800e6668
  (from RAM search, `work/tmp/findpac.py`).

## Free space
- Inside PACs: each file can grow only up to its sector allocation (2048-byte rounding) while the LBA question is
  open; each lzs block also has to fit the game's load buffer (unknown).
- DUMMY.WAV (37 MB) is padding that could be shrunk to make room once LBA references are understood.
