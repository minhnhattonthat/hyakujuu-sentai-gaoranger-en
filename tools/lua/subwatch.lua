-- Subtitle engine homes (docs/re/fmv.md §In-game voice), checked on the ORIGINAL disc: logs any execution in the
-- EXE stub site (dead code 0x8002f10c-0x8002f444) and any CPU write into the blob range 0x800c8000-0x800cd000.
-- Needs --debugger (warp.py --trace). A clean run logs no "HIT" line.
local function hit(kind)
  return function(addr)
    local r = PCSX.getRegisters()
    L.log(string.format("HIT %s frame %d addr %08x pc %08x ra %08x", kind, L.frame, tonumber(addr or r.pc),
      tonumber(r.pc), tonumber(r.GPR.n.ra)))
  end
end
L.on_exec(0x8002f10c, hit("exec"))  -- the dead function's entry (an exec range bp would also fire on fetch-ahead)
L.on_read(0x8002f10c, 0x8002f443, hit("read"))
L.on_write(0x800c8000, 0x800ccfff, hit("write"))
