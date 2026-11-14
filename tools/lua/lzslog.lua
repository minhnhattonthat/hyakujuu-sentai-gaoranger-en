-- Log every lzs decode: decompress(src a0, dst a1) at 0x8002f858 (docs/re/pac.md). Needs --debugger.
--   warp.py SCENE --trace --script tools/lua/lzslog.lua ; then tools/lzsmap.py DIR (overlaps of grown blocks)
-- LZS frame F src S dst D size N ra R head H
--   N = unpacked size from the block header (src+0x24); H = first 16 stream bytes (src+0x20+hdrlen), hex:
--   lzsmap.py names the block by H against the built PACs.
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a & 0x1fffff] end
local function u32(a) return u8(a) + u8(a+1)*256 + u8(a+2)*65536 + u8(a+3)*16777216 end
L.on_exec(0x8002f858, function()
  local r = PCSX.getRegisters().GPR.n
  local src = tonumber(r.a0)
  local s = src + 0x20 + u8(src + 0x22) + u8(src + 0x23) * 256
  local h = {}
  for i = 0, 15 do h[#h + 1] = string.format("%02x", u8(s + i)) end
  L.log(string.format("LZS frame %d src %08x dst %08x size %d ra %08x head %s", L.frame, src, tonumber(r.a1),
    u32(src + 0x24), tonumber(r.ra), table.concat(h)))
end)
