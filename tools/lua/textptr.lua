-- Text coverage probe (docs/re/text.md §Renderer): each frame, read the 4 text windows' text pointers (+0x28) and
-- log the RAM around each pointer that jumped (a new string; the typewriter itself moves a few bytes per frame):
-- "TEXTPTR f<frame> w<win> <ptr hex> <hex of ptr-400 .. ptr+400>". A pressed button finishes a box at once, so the
-- logged pointer is often a string's end (its FF), not its start.
-- tools/textcov.py matches those windows against the build's encoded strings. No debugger needed.
local mem = PCSX.getMemPtr()
local WIN, SPAN = 0x9ec88, 400
local prev = {}
L.on_frame(function(f)
  for w = 0, 3 do
    local a = WIN + w * 0x54 + 0x28
    local p = mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216
    local off = p - 0x80000000
    -- a small forward step past an FF is the next string in the table (option-00b2 -> 00e6), not the typewriter
    local crossed = false
    if prev[w] and off > prev[w] and off <= prev[w] + 8 then
      for i = prev[w], off - 1 do if mem[i] == 0xff then crossed = true end end
    end
    if off ~= prev[w] and off > SPAN and off < 0x1ff000 - SPAN
        and (prev[w] == nil or off < prev[w] or off > prev[w] + 8 or crossed) then
      local t = {}
      for i = off - SPAN, off + SPAN - 1 do t[#t + 1] = string.format("%02x", mem[i]) end
      L.log(string.format("TEXTPTR f%d w%d %08x %s", f, w, p, table.concat(t)))
    end
    prev[w] = off
  end
end)
