-- Log every lzs decode: decompress(src a0, dst a1) at 0x8002f858 (docs/re/pac.md). Needs --debugger.
--   warp.py SCENE --trace --script tools/lua/lzslog.lua ; then tools/lzsmap.py DIR (overlaps of grown blocks)
-- LZS frame F src S dst D size N ra R   (N = unpacked size from the block header, src+0x24)
local mem = PCSX.getMemPtr()
local function u32(a) a = a & 0x1fffff; return mem[a] + mem[a+1]*256 + mem[a+2]*65536 + mem[a+3]*16777216 end
L.on_exec(0x8002f858, function()
  local r = PCSX.getRegisters().GPR.n
  local src = tonumber(r.a0)
  L.log(string.format("LZS frame %d src %08x dst %08x size %d ra %08x", L.frame, src, tonumber(r.a1),
    u32(src + 0x24), tonumber(r.ra)))
end)
