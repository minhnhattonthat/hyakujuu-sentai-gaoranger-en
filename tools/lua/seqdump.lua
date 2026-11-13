-- RAM dump + shot every STEP frames between frames A and B (text-pointer hunts, RAM diffs).
--   emu.py CUE --out D --state-in S --frames N --script tools/lua/seqdump.lua --var A=900 --var B=1700 --var STEP=20
L.on_frame(function(f)
  if f >= A and f <= B and f % STEP == 0 then
    L.dump_ram(string.format("ram_%06d.bin", f))
    L.shot(string.format("f%06d.png", f))
  end
end)
