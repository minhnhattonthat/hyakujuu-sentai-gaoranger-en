-- Log the first read of each address in LO..HI with frame and pc (needs the debugger: warp.py --trace). Tells which
-- records of a loaded table the game ever touches (e.g. 12_17 sprite groups: is a banner group drawn at all?).
--   warp.py de03 --trace --script tools/lua/readaddrs.lua --var LO=0x801cd000 --var HI=0x801cd6d3 --var READ_AT=4600
-- READ_AT: ignore reads before this frame (heap memory is reused: the table lands there late).
-- BUCKET=N: log an address again in each later N-frame window (when is it read, not just whether).
READ_AT = READ_AT or 0
local seen = {}
L.on_read(LO, HI, function(addr, width, cause)
  local a = tonumber(addr)
  local key = BUCKET and string.format("%x/%d", a, math.floor(L.frame / BUCKET)) or a
  if L.frame >= READ_AT and not seen[key] then
    seen[key] = true
    L.log(string.format("frame %d read %08x w%d pc %08x", L.frame, a, width, tonumber(PCSX.getRegisters().pc)))
  end
end)
