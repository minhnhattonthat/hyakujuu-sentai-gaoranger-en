-- Scene warp (docs/re/flow.md §Debug tool). Driven by tools/debug/warp.py (tools/debug/scenes.txt). No debugger.
-- Globals (from --var):
--   CHAPTER  chapter (u16 at 0x8009ec28, 1-based) written once the opening's chapter switch script is in RAM; the
--            new game then plays DS_ST0<n>, the chapter's own story intro. 0 = leave it (chapter 1).
--   FROM, TO file ids: every sequence-script op "03 00 <FROM>" (load file) found in heap RAM is rewritten to load TO
--            instead, before it runs. Pick FROM of the same kind as TO (story/menu 0x50xx, action 0x30xx, robo
--            0x40xx): the script around the op loads the matching overlay. 0 = no swap.
--   FROM2, TO2 an optional second swap (chains; see swap_ops).
--   AFTER    chapter to write once TO has been seen loaded (robo scenes start from chapter 6's DS_ST06). 0 = none.
--   EXPECT   file id whose load proves the warp: logged as LOADED when the loader's CD seek position (CdlLOC
--            at 0x80063da8 = gp+0x254) reaches that file's LBA (from the file table in RAM, 0x80059b18). 0 = none.
--   SKIP     overlay file id (c002 A_SYS, c003 B_SYS, c004 D_SYS): from the opening on (once the route is done),
--            tap START every 30 frames (skips cutscenes and story) until that overlay's CD seek is seen after
--            EXPECT has loaded (the target's own overlay load). 0 = off.
--   HOLD     frames after EXPECT loads at which mashing (--mash) stops, so the run ends inside the scene (story
--            boxes wait for a press). 0 = keep mashing.
--   KEYS     {{frames, 'key'}, ..}: press each key that many frames after the scene settled (SKIPPED, or LOADED
--            when there is no SKIP); mashing stops at the first one. E.g. {{1500,'start'}} = pause menu.
--            Key 'pull' removes the memory card from slot 1 instead (card errors mid-save/format/load).
--   NOCARD   1 = no memory card in slot 1.
--   MODE     story-loop mode (u16 gp+0x134 = 0x80063c88, script op "02 0 v") written the first time it reads 0x13
--            after EXPECT loads. The opening leaves 0x13, whose D_SYS loop never steps fades (op 1c/1d), so the
--            de03-05 endings stall on their white flash; a robo battle enters them with 0x15/0x16. 0 = off.
--   GOD      1 = refill the player's health (not mapped yet: logs a warning).
-- Logs: CHAPTER frame F n, SWAP frame F at ADDR, LOADED frame F, SKIPPED frame F.
local mem = PCSX.getMemPtr()
CHAPTER = CHAPTER or 0
FROM = FROM or 0
TO = TO or 0
AFTER = AFTER or 0
EXPECT = EXPECT or 0
SKIP = SKIP or 0
HOLD = HOLD or 0
local loaded_at = nil
local settled_at = nil
local CH = 0x9ec28
local LO, HI = 0x100000, 0x1ff000 -- heap: scripts live in decompressed PAC parts here
local opening = false -- the opening's chapter switch script has been seen in RAM
local loaded = EXPECT == 0
local skipping = SKIP ~= 0
local swaps = 0
local function u32(a) return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local function bcd(v) return (v >> 4) * 10 + (v & 15) end
local function lba_of(id)
  for e = 0x59b18, 0x59b18 + 0x2c * 120, 0x2c do
    if u32(e) == id then return u32(e + 4) end
  end
end
local function seek_lba()
  local a = 0x63da8
  return (bcd(mem[a]) * 60 + bcd(mem[a + 1])) * 75 + bcd(mem[a + 2]) - 150
end

-- the opening's chapter switch table: "03 00 10 50 10 00" = load DS_ST01; goto (BA_ST01B.PAC/1_16 at 0x938)
local function find_switch()
  for a = LO, HI, 2 do
    if mem[a] == 3 and mem[a + 1] == 0 and mem[a + 2] == 0x10 and mem[a + 3] == 0x50 and mem[a + 4] == 0x10
      and mem[a + 5] == 0 and mem[a + 10] == 3 and mem[a + 12] == 0x20 and mem[a + 13] == 0x50 then
      return a
    end
  end
end

-- FROM2/TO2: a second swap for chains, e.g. 5010>5079 (DE_ST07E) then 5008>5007: DE_ST07E's own script then
-- loads Y_SAVE instead of Y_EDSAVE, from the story context those screens expect.
local pairs_ = { { FROM, TO } }
if (FROM2 or 0) > 0 then pairs_[2] = { FROM2, TO2 } end
local function swap_ops()
  for _, p in ipairs(pairs_) do
    local fl, fh, tl, th = p[1] & 0xff, p[1] >> 8, p[2] & 0xff, p[2] >> 8
    for a = LO, HI, 2 do
      if mem[a + 2] == fl and mem[a + 3] == fh and mem[a] == 3 and mem[a + 1] == 0 then
        mem[a + 2] = tl; mem[a + 3] = th
        swaps = swaps + 1
        L.log(string.format("SWAP frame %d at %08x %04x -> %04x", L.frame, 0x80000000 + a, p[1], p[2]))
      end
    end
  end
end

if GOD == 1 then L.log("GOD not mapped yet") end
-- NOCARD=1: memory card slot 1 empty (the game's "no Memory Card" messages)
if NOCARD == 1 then PCSX.settings.emulator.Mcd1Inserted = false; L.log("NOCARD slot 1 empty") end

L.on_frame(function(f)
  if f % 4 == 0 and not opening and find_switch() then
    opening = true
    if CHAPTER > 0 then
      mem[CH] = CHAPTER & 0xff; mem[CH + 1] = CHAPTER >> 8
      L.log(string.format("CHAPTER frame %d %d", f, CHAPTER))
    end
  end
  if f % 4 == 0 and FROM > 0 and (not loaded or swaps == 0) then swap_ops() end
  if skipping and opening then
    local lba = lba_of(SKIP)
    if loaded and lba and lba > 0 and seek_lba() == lba then -- the overlay load that follows the target's
      skipping = false
      L.log(string.format("SKIPPED frame %d (overlay %04x seen)", f, SKIP))
    elseif f % 30 == 0 and L.route_done() then
      L.press("start", 4)
    end
  end
  if not loaded then
    local lba = lba_of(EXPECT)
    if lba and lba > 0 and seek_lba() == lba then
      loaded = true
      loaded_at = f
      L.log(string.format("LOADED frame %d id %04x lba %d", f, EXPECT, lba))
      if AFTER > 0 then mem[CH] = AFTER & 0xff; mem[CH + 1] = AFTER >> 8 end
    end
  end
  if (MODE or 0) > 0 and loaded_at and mem[0x63c88] == 0x13 and mem[0x63c89] == 0 then
    mem[0x63c88] = MODE & 0xff; mem[0x63c89] = MODE >> 8
    L.log(string.format("MODE frame %d 13 -> %x", f, MODE))
    MODE = 0
  end
  if KEYS and not settled_at and loaded_at and not skipping then settled_at = f end
  if KEYS and settled_at then
    for _, k in ipairs(KEYS) do
      if f == settled_at + k[1] then
        MASH = 0
        if k[2] == "pull" then PCSX.settings.emulator.Mcd1Inserted = false else L.press(k[2], 6) end
        L.log(string.format("KEY frame %d %s", f, k[2]))
      end
    end
  end
  if HOLD > 0 and loaded_at and f == loaded_at + HOLD then
    MASH = 0
    L.log(string.format("HOLD frame %d: mashing stopped", f))
  end
end)
