-- Log unique (pc, ra) of CPU reads in LO..HI (needs emu.py --debugger). Found the lzs decoder (docs/re/pac.md).
--   emu.py CUE --out D --route R --script tools/lua/readbp.lua --var LO=0x800cd378 --var HI=0x800cd37f --debugger
local seen = {}
local n = 0
L.on_read(LO, HI, function(addr, width, cause)
  local r = PCSX.getRegisters()
  local pc = tonumber(r.pc)
  local ra = tonumber(r.GPR.n.ra)
  local key = string.format("%08x %08x", pc, ra)
  if not seen[key] and n < 40 then
    seen[key] = true; n = n + 1
    L.log(string.format("frame %d read %08x w%d pc %08x ra %08x", L.frame, tonumber(addr), width, pc, ra))
  end
end)
