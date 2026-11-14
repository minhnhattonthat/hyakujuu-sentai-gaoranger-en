; English VWF and window widths for the EXE (docs/re/text.md §Renderer). Built by tools/build.py:
;   armips asm/vwf.asm -strequ EXE_IN <orig EXE> -strequ EXE_OUT <out> -strequ WIDTHS <font.py widths()>
; build.py checks the original bytes at every site below before assembling (HOOKS in build.py).
.psx
.open EXE_IN, EXE_OUT, 0x80010000 - 0x800

; Width table: one advance byte per glyph code 0xA0..0x1F4. It replaces two host-file (PCdrv) I/O functions,
; 0x80022A6C read and 0x80022B34 write: no jal, pointer word or lui pair reaches them in the EXE or any PRG.
.org 0x80022A6C
WTAB:
.incbin WIDTHS
.if . > 0x80022BC4
  .error "width table runs into load_file"
.endif

; Cell renderer 0x800271D8: x was window x + column * 12 (13 with cell attr 0x80). Now a running offset per row
; in s4 (free after the row's first cell index is computed at 0x8002723C).
.org 0x80027260
  move  s4, zero              ; row start (was the nop in lbu v0,4(t2)'s load delay slot)

.org 0x80027290
  lhu   v0, 0x0(a0)           ; cell glyph code
  lui   v1, hi(WTAB - 0xA0)
  andi  v0, v0, 0x3FF
  addu  v1, v1, v0
  lbu   v1, lo(WTAB - 0xA0)(v1)
  addu  t4, s0, s4            ; x = row x + offset
  addu  s4, s4, v1            ; offset += advance
.fill 0x800272C8 - ., 0
.if . != 0x800272C8
  .error "renderer hook size"
.endif

; Story box (0x80015490): columns per row 20 -> 48 for both layouts (2 rows / 3 rows). Cell pool: 384.
.org 0x800154D8
  addiu a3, zero, 48
.org 0x80015504
  addiu a3, zero, 48

.close
