-- Free-space survey: which RAM / VRAM blocks were ever non-zero during the run (subtitle engine home, docs/re/fmv.md).
--   warp.py SCENE.. --script tools/lua/memfree.lua [--var EVERY=30]  -> memfree.txt in the run dir at the end
-- RAM: 256-byte blocks of 0x80000000-0x80200000. VRAM: 16x16-pixel tiles of 1024x512 (u16 pixels).
-- Blocks never seen non-zero are written as runs: "RAM free 800c0000-800c8000" / "VRAM free x y w h" (per tile row).
local ffi = require("ffi")
EVERY = EVERY or 30
local ram = ffi.cast("uint8_t*", PCSX.getMemPtr())
local rused, vused = {}, {}
local function scan()
  local q = ffi.cast("uint32_t*", ram)
  for b = 0, 0x2000 - 1 do
    if not rused[b] then
      local base = b * 64
      for i = 0, 63 do if q[base + i] ~= 0 then rused[b] = true; break end end
    end
  end
  local v = PCSX.GPU.getVRAM()
  local vp = ffi.cast("const uint16_t*", type(v.data) == "function" and v:data() or v.data)  -- a Support.Slice
  for ty = 0, 31 do
    for tx = 0, 63 do
      local k = ty * 64 + tx
      if not vused[k] then
        for y = ty * 16, ty * 16 + 15 do
          local row = y * 1024 + tx * 16
          for x = 0, 15 do if vp[row + x] ~= 0 then vused[k] = true; break end end
          if vused[k] then break end
        end
      end
    end
  end
end
L.on_frame(function(f)
  if f % EVERY == 0 then scan() end
end)
local function report()
  local out = {}
  local s = nil
  for b = 0, 0x2000 do
    local free = b < 0x2000 and not rused[b]
    if free and not s then s = b end
    if not free and s then
      if b - s >= 16 then out[#out + 1] = string.format("RAM free %08x-%08x", 0x80000000 + s * 256, 0x80000000 + b * 256) end
      s = nil
    end
  end
  for ty = 0, 31 do
    local sx = nil
    for tx = 0, 64 do
      local free = tx < 64 and not vused[ty * 64 + tx]
      if free and not sx then sx = tx end
      if not free and sx then out[#out + 1] = string.format("VRAM free %d %d %d 16", sx * 16, ty * 16, (tx - sx) * 16); sx = nil end
    end
  end
  L.write_file("memfree.txt", table.concat(out, "\n") .. "\n")
end
L.on_frame(function(f) if f % 600 == 0 then scan(); report() end end)
