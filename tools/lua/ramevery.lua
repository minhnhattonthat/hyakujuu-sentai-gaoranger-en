-- warp.py --script tools/lua/ramevery.lua --var DUMP_AT=6300 --var DUMP_STEP=300: RAM -> ram_<frame>.bin every
-- DUMP_STEP frames from DUMP_AT (not FROM/TO: warp.lua's swap ids). RAM search over a fight:
-- python $SKILL/scripts/ramsearch.py ram_a.bin dec ram_b.bin .. --base 0x80000000
DUMP_AT = DUMP_AT or 0
DUMP_STEP = DUMP_STEP or 300
L.on_frame(function(f)
  if f >= DUMP_AT and (f - DUMP_AT) % DUMP_STEP == 0 then L.dump_ram(string.format("ram_%06d.bin", f)) end
end)
