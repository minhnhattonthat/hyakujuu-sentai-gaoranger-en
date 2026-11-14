-- Log every XA voice/FMV-audio start (docs/re/fmv.md §In-game voice). Needs --debugger.
--   warp.py SCENE --script tools/lua/xalog.lua --var GPU=1 ; GPU=1 also logs who starts GPU DMA (unique pc/ra)
-- xa_play(flags a0, a1 = &{u32 channel, u32 lba, u32 length in sectors}) at 0x80034f78; flags & 1 = start.
local mem = PCSX.getMemPtr()
local function u32(a) a = a & 0x1fffff; return mem[a] + mem[a+1]*256 + mem[a+2]*65536 + mem[a+3]*16777216 end
L.on_exec(0x80034f78, function()
  local r = PCSX.getRegisters().GPR.n
  local p = tonumber(r.a1)
  L.log(string.format("XA frame %d flags %d ch %d lba %d len %d ra %08x", L.frame, tonumber(r.a0), u32(p),
    u32(p + 4), u32(p + 8), tonumber(r.ra)))
end)
if GPU then
  local seen = {}
  L.on_write(0x1f8010a0, 0x1f8010ab, function(addr)
    local r = PCSX.getRegisters()
    local key = string.format("%08x %08x %08x", tonumber(addr), tonumber(r.pc), tonumber(r.GPR.n.ra))
    if not seen[key] then seen[key] = true; L.log(string.format("GPU frame %d %s", L.frame, key)) end
  end)
end
