-- Log file loads and CD seeks (docs/re/disc.md, docs/re/flow.md). Needs --debugger.
--   emu.py CUE --out D --route R --script tools/lua/cdlog.lua --debugger ; then tools/cdmap.py D/log.txt
-- CD:   CdIntToPos(lba) at 0x800544d4 (game copy; libcd's own is 0x80043cb0)
-- SEQ:  sequence-script op "load file", script ptr = *(*(0x80063d20) + 0x94), bytes from ptr-12
-- FILE: load_file(id, dest) at 0x80022bc4, id = the file table's id (tools/filetable.py)
-- READ: 0x800345c4(a0 = &entry.lba, a1 = offset, a2 = length, a3 = dest)
local mem = PCSX.getMemPtr()
local function u32(a) a = a & 0x1fffff; return mem[a] + mem[a+1]*256 + mem[a+2]*65536 + mem[a+3]*16777216 end
local function reg() return PCSX.getRegisters().GPR.n end

local function hook(addr, tag)
  L.on_exec(addr, function()
    local r = reg()
    L.log(string.format("CD %s frame %d lba %d ra %08x", tag, L.frame, tonumber(r.a0), tonumber(r.ra)))
  end)
end
hook(0x800544d4, "game")
hook(0x80043cb0, "lib")

L.on_exec(0x80029e04, function()
  local p = u32(u32(0x80063d20) + 0x94)
  local s = {}
  for i = -12, 23 do s[#s + 1] = string.format("%02x", mem[(p + i) & 0x1fffff]) end
  L.log(string.format("SEQ frame %d ptr %08x  %s", L.frame, p, table.concat(s, " ")))
end)
L.on_exec(0x80022bc4, function()
  local r = reg()
  L.log(string.format("FILE frame %d id %04x dst %08x ra %08x", L.frame, tonumber(r.a0) & 0xffff, tonumber(r.a1),
    tonumber(r.ra)))
end)
L.on_exec(0x800345c4, function()
  local r = reg()
  local e = tonumber(r.a0)
  L.log(string.format("READ frame %d ent %08x lba %d size %d off %x len %x dst %08x ra %08x", L.frame, e,
    u32(e), u32(e + 4), tonumber(r.a1), tonumber(r.a2), tonumber(r.a3), tonumber(r.ra)))
end)
