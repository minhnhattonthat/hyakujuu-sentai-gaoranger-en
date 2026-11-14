-- warp.py --script tools/lua/brawl.lua --var BRAWL_AT=2500: from frame BRAWL_AT stop the circle mash and fight
-- (action stages: square/triangle/cross combos while walking both ways), to get kills (ORGETTE counter, TIM 5).
BRAWL_AT = BRAWL_AT or 2500
local seq = { "square", "-", "square", "-", "triangle", "-", "right+square", "-", "cross+square", "-",
              "left+square", "-", "square", "-", "triangle", "-" }
local i = 0
L.on_frame(function(f)
  if f >= BRAWL_AT and L.route_done() then
    MASH = 0
    i = i % #seq + 1
    L.press(seq[i], 6)
  end
end)
