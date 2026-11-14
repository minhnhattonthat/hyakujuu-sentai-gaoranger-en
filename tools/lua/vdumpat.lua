-- warp.py --script tools/lua/vdumpat.lua --var AT=6150: at frame AT dump VRAM -> v.vram.bin, RAM -> ram.bin
-- (render with tools/vram.py; compare two runs' dumps to find what a build changed in VRAM/RAM)
L.on_frame(function(f) if f == (AT or 30) then L.dump_ppu("v"); L.dump_ram("ram.bin") end end)
