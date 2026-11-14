-- In-game voice subtitles on a build (asm/subs.asm, docs/re/fmv.md §In-game voice): logs each change of the shown
-- row and takes a shot 20 frames into it. No debugger needed.
--   warp.py SCENE --cue build/gaoranger_en.cue --script tools/lua/subshot.lua --var CURROW=0x... --var OKFLAG=0x...
-- (addresses from build/subs.sym: CurRow, OkFlag). Log: "SUB frame N row R ok K" (R = SubTable row address, 0 = none).
local mem = PCSX.getMemPtr()
local function u32(a) a = a & 0x1fffff; return mem[a] + mem[a+1]*256 + mem[a+2]*65536 + mem[a+3]*16777216 end
local last, due = 0, nil
L.on_frame(function(f)
  local row = u32(CURROW)
  if row ~= last then
    last = row
    L.log(string.format("SUB frame %d row %08x ok %d", f, row, u32(OKFLAG)))
    if row ~= 0 then due = f + (SHOT_DELAY or 20) end
  end
  if f % 300 == 0 then  -- blob magic, OkFlag, XA driver state FindRow reads (mode, XA flag, last LBA, channel)
    L.log(string.format("STATE frame %d magic %08x ok %d mode %04x xa %04x lba %d ch %d", f, u32(0x800C8000),
      u32(OKFLAG), u32(0x80063DE4) & 0xffff, u32(0x80063E00) & 0xffff, u32(0x80063DFC), mem[0x63E09]))
  end
  if due and f == due then L.shot(string.format("sub%06d.png", f)) due = nil end
end)
