-- At frame 30 (after --state-in): VRAM -> v.vram.bin, RAM -> ram.bin, shot x.png. Render with tools/vram.py.
L.on_frame(function(f) if f==30 then L.dump_ppu("v"); L.dump_ram("ram.bin"); L.shot("x.png") end end)
