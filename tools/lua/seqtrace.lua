-- Trace the sequence-script interpreter (docs/re/flow.md). Needs --debugger.
-- Logs "OP frame F ptr P off O op XXXX args.." once per new script pointer (wait loops print once), and the
-- 32 script vars (s16 at ctx+0x40) whenever they change. ctx = *(0x80063d20); ptr = ctx+0x94; base = ctx+0x80.
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a & 0x1fffff] end
local function u16(a) return u8(a) + u8(a + 1) * 256 end
local function u32(a) return u16(a) + u16(a + 2) * 65536 end
local last, lastvars = -1, ""
L.on_exec(0x8002c3c8, function()
  local ctx = u32(0x80063d20)
  local p = u32(ctx + 0x94)
  local v = {}
  for i = 0, 31 do v[#v + 1] = string.format("%x", u16(ctx + 0x40 + 2 * i)) end
  local vs = table.concat(v, " ")
  if vs ~= lastvars then L.log(string.format("VARS frame %d %s", L.frame, vs)); lastvars = vs end
  if p == last then return end
  last = p
  local s = {}
  for i = 0, 11 do s[#s + 1] = string.format("%02x", u8(p + i)) end
  L.log(string.format("OP frame %d ptr %08x off %x op %04x  %s", L.frame, p, p - u32(ctx + 0x80), u16(p),
    table.concat(s, " ")))
end)
