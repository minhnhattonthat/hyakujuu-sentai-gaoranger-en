-- Subtitle engine hook points (docs/re/fmv.md §In-game voice): main-thread frame end (DrawSync call 0x8002e8b4) and
-- the VSync-callback flip (DrawOTag call 0x8002e468). Logs call counts and the lowest sp seen every 600 frames.
-- Needs --debugger.
local n = { main = 0, flip = 0 }
local lo = { main = 0xffffffff, flip = 0xffffffff }
local function on(addr, k)
  L.on_exec(addr, function()
    n[k] = n[k] + 1
    local sp = tonumber(PCSX.getRegisters().GPR.n.sp)
    if sp < lo[k] then lo[k] = sp end
  end)
end
on(0x8002e8b4, "main")
on(0x8002e468, "flip")
L.on_frame(function(f)
  if f % 600 == 0 then
    L.log(string.format("SP frame %d main %d sp>=%08x flip %d sp>=%08x", f, n.main, lo.main, n.flip, lo.flip))
  end
end)
