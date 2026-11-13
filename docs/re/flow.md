# Game flow: sequence script, file loads, progress

## File table and loader (verified: cdlog.lua run `work/qa/p2cd`, every load matches the disc LBAs)
- EXE table at 0x80059b18, 0x2c-byte entries `{u32 id, u32 lba, u32 size, char name[0x20]}`, names lowercase with
  padding (`DATA\o_logo  .pac`); lba/size filled at boot from the CD directory. `python -X utf8 tools/filetable.py`.
- Ids: 0x48xx logos/title, 0x41xx robo sound banks, 0x40xx robo (BA/BB/B/BC), 0x30xx ranger action (A_*),
  0x50xx story/menus (Y_*, DS_*, DE_*), 0x59xx gauge/card/event, 0xc00x overlays (OPN, A_SYS, B_SYS, D_SYS, DEBUG).
  The table has `a_st01y.pac` (0x5100) where the disc has A_ST010.PAC.
- `load_file(id, dest)` 0x80022bc4 -> lookup 0x80022c8c -> 0x80034524 -> read 0x800345c4(&entry.lba, off, len,
  dest) -> CdIntToPos 0x800544d4. PAC data lands at 0x800cd000, overlays at 0x800a6ae8.
- Debug leftovers: 0x80022b60.. opens host files (PCdrv-style open 0x80036af0 flags 0x202) before the CD path.

## Sequence script (verified: `tools/lua/seqtrace.lua` traces match the bytes in the files)
- Context `ctx = *(0x80063d20)`; script ptr `ctx+0x94`, base `ctx+0x80` (targets are offsets from it), return
  `ctx+0x98`, 32 s16 vars at `ctx+0x40`. Dispatcher 0x8002c3c8: op u16; ops < 0x1000 via table 0x8005b120, ops
  0x1000+ via 0x8005b234. Several contexts run (one per task).
- Ops seen: 03 load file (u16 id), 04 wait for load, 10 goto (u32), 11 random jump, 12 call (u32), 13 return,
  14/15 if var ==/!= value goto, 2a/2b/2c/2d switch-like jumps on game globals; 2b = jump table indexed by the
  chapter (u16 at 0x8009ec28, 1-based).
- Each scene file carries its own script part (`1_16.bin` robo files, `11.bin` action stages, `13_18.bin` story
  and option, `12_18.bin` endings); `python -X utf8 tools/loadgraph.py` lists the files each one loads next.
  New game: OPN loads BA_ST01 (opening) -> BA_ST01B -> op 2b on the chapter -> DS_ST0<n> -> A_ST<n>1 ...

## Progress (verified for the chapter: forcing 3 at the op-2b switch loads DS_ST03 then A_ST31)
- 0x8009ec28 u16 chapter (1..7), +2 and +4 u16 sub-state (set by script ops 0x29.. at 0x8002aa30), +0xc u16.
- 0x8002def0 sets chapter 1 (new game); 0x8002deb4 sets chapter 6 and +0x6 = 1 (another mode).

## Debug tool
`tools/debug/warp.py` + `warp.lua`: new-game route, then the first story load (DS_ST01) is swapped for the
scene's file id and the chapter is set, so the scene's own script runs from its start. Scene list:
`tools/debug/scenes.txt`.
