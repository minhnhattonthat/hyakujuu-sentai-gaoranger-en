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
  (`tools/filetable.py`, flow.md). So files may move and grow; the directory record is what counts (moved-file
  test passed, §Rebuild). XA/STR files go through a separate path (0x80034fbc, 0x80029560).
- Overlays in RAM at the title: OPN.PRG at 0x800a6ae8, Y_TITLE.PAC raw at 0x800cd000, O_TITLE.PAC raw at 0x800e6668
  (from RAM search, `work/tmp/findpac.py`).

## Rebuild (verified 2026-11-14, tests/test_disc.py: byte-identical .bin)
- `tools/mkdisc.py OUT.bin [--overlay DIR]` (build.py calls it): mkpsxiso from `disc/layout.xml` (dumpsxiso's, with
  `cdvd_style="false"`, blank system/application ids, a 150-sector form-2 `<dummy>` postgap at the end of the data
  track, track 2 pregap 2 s), then `fix_image` makes what mkpsxiso can't express match the original mastering:
  - PVD sector subheader submode 0x08 (mkpsxiso: 0x09; `cdvd_style="true"` fixes that but drops EOF/EOR 0x89 from
    the path tables and directories), EDC/ECC recomputed (`fix_form1`, checked against original sectors);
  - root directory date 1901-10-01 05:47:50 +9 (year byte 1) in the PVD and every record pointing at the root;
  - postgap: the first 148 sectors have subheader 0 and no EDC, the last two are form 2 with EDC;
  - the track-2 pregap counts in disc LBAs (DUMMY.DA extent, volume size 78187) but is not stored in the .bin: the
    150 silent sectors mkpsxiso writes are cut and the cue gets `PREGAP 00:02:00`.
- DUMMY.WAV is not padding: it is track 2 (CD-DA, 32 MB, linked by DUMMY.DA).
- Moved files: `tools/movetest.py` re-encodes every lzs block of every PAC (65 PACs change sector count, so nearly
  every file after the first moves) and builds `work/movetest/gao.cue`. **Verified 2026-11-14:** `warp.py --all` on
  it reached all 87 scenes (OK), the expected files loaded from their new LBAs (a11: id 3011 at 3927, was 3910;
  de07: 5078 at 14817, was 14745), every final frame shows the right scene with intact models and textures (dynamic
  scenes differ only in moment), and the save written in scene savedone has the same save blocks. Shots:
  `work/movetest/warp/`, pairs `work/movetest/cmp_sheet.png`.

## Build verification (phase 7, tools/verify.py, run by build.py; tests/test_verify.py proves each check fails)
- EXE: `romdiff.check` vs the original. Expected writes come from assembling asm/vwf.asm again over 0x00- and
  0xff-filled dummies (independent of the built EXE); each must sit in a build.HOOKS site (original bytes checked)
  or the width-table range. No branch/j/jal in the EXE, no j/jal in a PRG, and no aligned word in either lands
  inside a replaced span or the width table (lui/addiu pairs: checked by hand once, asm/vwf.asm).
- PACs: same leaf set (lzs payloads decoded and walked); only text-table and font leaves differ (37 of 275 leaves in
  the 20 changed PACs), others may only gain zero padding. Every string reads back through every pointer slot as
  the en (or untouched jp) text; `jpleft.scan` finds no Japanese left. The overlay holds only the EXE and DATA/*.PAC.
- Disc: dumpsxiso of the built .bin = original tree with the overlay files swapped in, byte for byte.
- Runtime (not in build.py, emulator traces): decoded table growth, docs/re/pac.md §Decode targets; insert.TRACED
  caps each table at its traced size.

## Free space
- Inside PACs: files are found by name, so a PAC may grow; each PAC is read whole to 0x800cd000,
  so its size is capped by the buffer below the next RAM user (unknown), and each lzs block has to fit its target.
- On disc: files may grow and move (mkpsxiso relays everything out; the game reads LBAs from the directory).
