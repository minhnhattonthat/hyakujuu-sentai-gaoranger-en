# Disc layout

- Redump: Hyakujuu Sentai GaoRanger (Japan), SLPS-03353, Bandai / Natsume, 2001-11-29. One .bin: track 1 MODE2/2352
  data, track 2 audio (index 01 at 13:50:37). SHA-1 in `rom.sha1`.
- Unpack: `tools/mkpsxiso/mkpsxiso-2.30-win64/dumpsxiso.exe -x work/disc/tree -s work/disc/layout.xml <cue>`.
  129 files: `SLPS_033.53` (PS-X EXE, load 0x80010000, size 0x54000, entry 0x8004c970), `SYSTEM.CNF`,
  `DATA/*.PAC` (PAC containers, pac.md), `DATA/*.PRG` (A_SYS, B_SYS, D_SYS, OPN overlays; DEBUG.PRG is 84 bytes of
  `jr ra` stubs; MAIN.PRG is empty), `DUMMY.WAV` (37 MB padding), `XA/*.XA` (audio), `XA/*.STR` (FMV).
- LBAs: `python -X utf8 tools/disc_lba.py <bin>` (copy in `work/disc/lba.txt`).
- **How files are found (verified 2026-11-14, phase 2):** by name. The EXE holds a file table at 0x80059b18
  (`{u32 id, u32 lba, u32 size, char name[0x20]}`, names lowercase like `DATA\o_logo  .pac`, missed by the
  phase-1 search for upper-case names); lba/size are filled at boot from the CD directory, and the game loads by id
  (`tools/filetable.py`, flow.md). So files may move and grow; the directory record is what counts. Verify with an
  identity rebuild plus a moved-file test in phase 3. XA/STR files go through a separate path (0x80034fbc, 0x80029560).
- Overlays in RAM at the title: OPN.PRG at 0x800a6ae8, Y_TITLE.PAC raw at 0x800cd000, O_TITLE.PAC raw at 0x800e6668
  (from RAM search, `work/tmp/findpac.py`).

## Free space
- Inside PACs: files are found by name, so a PAC may grow (confirm in phase 3); each PAC is read whole to 0x800cd000,
  so its size is capped by the buffer below the next RAM user (unknown), and each lzs block has to fit its target.
- DUMMY.WAV (37 MB) is padding that could be shrunk to make room once LBA references are understood.
