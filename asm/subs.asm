; In-game voice subtitles (docs/re/fmv.md §In-game voice). Built by tools/build.py over the asm/vwf.asm output:
;   armips asm/subs.asm -strequ EXE_IN <EXE> -strequ EXE_OUT <out> -strequ SUBDATA <tools/subs.py output>
;
; The XA driver keeps its state in globals: play mode (gp+0x290), XA flag (gp+0x2ac), LBA of the last sector read
; (gp+0x2a8) and the filter channel (gp+0x2b5). Once a frame, on the main thread, FindRow looks that sector up in
; SubTable (file, channel, sector range); once a new row has held for DEBOUNCE passes Render draws the line into a 304x28 4bpp canvas (the English
; VWF font, white with a 1 px black outline) and uploads it to free VRAM. The VSync-callback flip then draws the
; game's OT and, while a line is up, two sprites of the canvas over it. Pauses and stops follow the audio by
; themselves (the sector stops moving / the mode drops to 0).
;
; Code and data live in a blob at 0x800C8000 (free in every scene, tools/memfree.py; the PAC buffer starts at
; 0x800CD000). It is appended to the EXE image (t_size grows) at 0x80064000, inside the BSS that crt0 clears, so a
; stub at the entry point copies it out first. The two hooks call guarded stubs in dead EXE code that check the
; blob's magic and code checksum every frame and fall back to the original calls if it was ever overwritten.
.psx
.open EXE_IN, EXE_OUT, 0x80010000 - 0x800

BLOB        equ 0x800C8000
BLOB_LIMIT  equ 0x800CD000  ; the PAC buffer
TAIL        equ 0x80064000  ; image address of the blob (the original image ends here)
TAIL_FILE   equ 0x54800     ; its file offset
SUB_MAGIC   equ 0x53554253  ; "SBUS"
DrawSync    equ 0x8003866C
DrawOTag    equ 0x80038C60
LoadImage   equ 0x80038918
FileEntry   equ 0x80022C8C  ; file table lookup(u16 id) -> entry {u32 id, u32 lba, u32 size, name}
CANVAS_W    equ 304
CANVAS_H    equ 28          ; 2 lines x 14 rows (12 glyph rows + outline)
MASK_STRIDE equ 48          ; 12 words: guard, 10 words = 320 px, guard
MASK_ROWS   equ (CANVAS_H + 2) ; a zero guard row above and below (equ is text: compound values need the parens)
VRAM_X      equ 768         ; free VRAM (tools/memfree.py): x 768-831 (halfwords), y 416-511
VRAM_Y      equ 416
CLUT_X      equ 800
CLUT_Y      equ 412
CLUT_ID     equ ((CLUT_Y << 6) | (CLUT_X >> 4))
TPAGE       equ ((VRAM_X / 64) | (1 << 4) | (1 << 10))  ; tx 12, ty 256, 4bpp, drawing to display area allowed
DEBOUNCE    equ 4           ; main-loop passes (~30/s) a new line must persist before it shows
BOTTOM      equ 56         ; canvas top = clip bottom - BOTTOM: ends 28 px above it (some screens show only 224 lines)

; ---- hooks
.org 0x8004C970             ; crt0 entry: lui v0,0x8006 / addiu v0,v0,0x3bf0 (start of the BSS clear loop)
  j     CopyStub
  nop
.org 0x8002E468             ; flip (VSync callback): jal DrawOTag(game OT)
  jal   FlipStub
.org 0x8002E8B4             ; frame end (main thread): jal DrawSync(0); a0 = 0 in the delay slot
  jal   MainStub

; ---- stubs in dead code: 0x8002F10C, a window function no code or data reaches (build.DEAD, verify)
.org 0x8002F10C
CopyStub:
  li    t0, TAIL
  li    t1, BLOB
  li    t2, BLOB_END
@@copy:
  lw    t3, 0(t0)
  addiu t0, t0, 4
  sw    t3, 0(t1)
  addiu t1, t1, 4
  bne   t1, t2, @@copy
  nop
  lui   v0, 0x8006
  j     0x8004C978
  addiu v0, v0, 0x3BF0

MainStub:
  li    t0, BLOB
  lw    t1, 0(t0)           ; magic
  lw    t3, 4(t0)           ; code checksum
  lui   t2, SUB_MAGIC >> 16
  ori   t2, t2, SUB_MAGIC & 0xFFFF
  bne   t1, t2, @@bad
  nop
  la    t4, CODE_START
  la    t5, CODE_END
  move  t6, zero
@@sum:
  lw    t7, 0(t4)
  addiu t4, t4, 4
  bne   t4, t5, @@sum
  addu  t6, t6, t7
  bne   t6, t3, @@bad
  addiu t1, zero, 1
  la    t0, OkFlag
  j     SubMain
  sw    t1, 0(t0)
@@bad:
  la    t0, OkFlag
  j     DrawSync
  sw    zero, 0(t0)

FlipStub:
  la    t0, OkFlag
  lw    t0, 0(t0)
  nop
  beqz  t0, @@orig
  nop
  j     SubFlip
  nop
@@orig:
  j     DrawOTag
  nop

.align 4
OkFlag:
  .word 0
.if . > 0x8002F444
  .error "stubs run past the dead function"
.endif

; ---- the blob
.headersize BLOB - TAIL_FILE
.org BLOB
  .word SUB_MAGIC
  .word 0                   ; code checksum: written by tools/build.py (sum of the words CODE_START..CODE_END)
CODE_START:

; Main thread, frame end (replaces DrawSync(0)): find the line for the XA sector being played; on a change draw it.
SubMain:
  addiu sp, sp, -32
  sw    ra, 24(sp)
  sw    s0, 16(sp)
  jal   DrawSync
  move  a0, zero
  jal   FindRow
  nop
  move  s0, v0
  la    t0, CurRow
  lw    t1, 0(t0)
  lw    t2, 4(t0)           ; PendRow
  beq   s0, t1, @@done
  lw    t3, 8(t0)           ; PendCnt
  beqz  s0, @@set           ; a line ends at once
  nop
  beq   s0, t2, @@same      ; a new line shows once FindRow has returned it DEBOUNCE times in a row: a clip's
  nop                       ; last sectors can hold the next line's first words (a few-frame flash)
  sw    s0, 4(t0)
  move  t3, zero
@@same:
  addiu t3, t3, 1
  sltiu t4, t3, DEBOUNCE
  bnez  t4, @@done
  sw    t3, 8(t0)
  jal   Render
  move  a0, s0
  jal   DrawSync            ; uploads done before the flip draws them
  move  a0, zero
@@set:
  la    t0, CurRow
  sw    s0, 0(t0)
  sw    zero, 8(t0)         ; PendCnt
@@done:
  lw    ra, 24(sp)
  lw    s0, 16(sp)
  jr    ra
  addiu sp, sp, 32

; VSync callback (replaces DrawOTag(game OT)): small stack, no waits.
SubFlip:
  addiu sp, sp, -24
  sw    ra, 16(sp)
  jal   DrawOTag
  nop
  la    t0, CurRow
  lw    t0, 0(t0)
  nop
  beqz  t0, @@out
  lui   t1, 0x800A
  lh    t2, 0x2448(t1)      ; DRAWENV clip x
  lh    t3, 0x244A(t1)      ; clip y
  lh    t4, 0x244C(t1)      ; clip w
  lh    t5, 0x244E(t1)      ; clip h
  lh    t6, 0x2450(t1)      ; ofs x
  lh    t7, 0x2452(t1)      ; ofs y
  subu  t2, t2, t6
  addiu t4, t4, -CANVAS_W
  sra   t4, t4, 1
  addu  t2, t2, t4          ; x (relative to the drawing offset)
  subu  t3, t3, t7
  addu  t3, t3, t5
  addiu t3, t3, -BOTTOM     ; y
  sll   t3, t3, 16
  andi  t8, t2, 0xFFFF
  or    t8, t8, t3
  la    t9, PrimL
  sw    t8, 8(t9)
  addiu t8, t2, 256
  andi  t8, t8, 0xFFFF
  or    t8, t8, t3
  la    t9, PrimR
  sw    t8, 8(t9)
  la    a0, PrimTP
  jal   DrawOTag
  nop
@@out:
  lw    ra, 16(sp)
  nop
  jr    ra
  addiu sp, sp, 24

; -> v0 = the SubTable row whose file, channel and sector range hold the XA sector last read, or 0.
FindRow:
  addiu sp, sp, -32
  sw    ra, 24(sp)
  sw    s0, 12(sp)
  sw    s1, 16(sp)
  sw    s2, 20(sp)
  lui   t0, 0x8006          ; gp = 0x80063B54
  lhu   t1, 0x3DE4(t0)      ; gp+0x290 play mode
  lhu   t2, 0x3E00(t0)      ; gp+0x2ac XA (not CD-DA)
  andi  t1, t1, 3
  beqz  t1, @@none
  lw    s0, 0x3DFC(t0)      ; gp+0x2a8 LBA last read
  beqz  t2, @@none
  lbu   s2, 0x3E09(t0)      ; gp+0x2b5 channel
  lw    t1, 0x3DF8(t0)      ; gp+0x2a4 clip end LBA: the drive reads on past it until the stop, unheard
  nop
  sltu  t1, s0, t1
  beqz  t1, @@none
  move  s1, zero
@@file:
  jal   FileEntry
  ori   a0, s1, 0xFA00      ; XA/CDXA0<n>.XA
  beqz  v0, @@next
  nop
  lw    t3, 4(v0)           ; lba
  lw    t4, 8(v0)           ; size in bytes
  subu  t3, s0, t3          ; sector in the file
  srl   t4, t4, 11
  sltu  t5, t3, t4
  bnez  t5, @@scan
  nop
@@next:
  addiu s1, s1, 1
  sltiu t5, s1, 3
  bnez  t5, @@file
  nop
  b     @@none
  nop
@@scan:
  la    v0, SubTable
@@row:
  lbu   t5, 0(v0)
  lbu   t6, 1(v0)
  lhu   t7, 4(v0)
  lhu   t8, 6(v0)
  addiu t9, zero, 0xFF
  beq   t5, t9, @@none
  nop
  bne   t5, s1, @@skip
  nop
  bne   t6, s2, @@skip
  sltu  t9, t3, t7          ; before the first sector
  bnez  t9, @@skip
  sltu  t9, t3, t8          ; before the end sector
  bnez  t9, @@out
  nop
@@skip:
  b     @@row
  addiu v0, v0, 12
@@none:
  move  v0, zero
@@out:
  lw    ra, 24(sp)
  lw    s0, 12(sp)
  lw    s1, 16(sp)
  lw    s2, 20(sp)
  jr    ra
  addiu sp, sp, 32

; a0 = SubTable row: draw its text into Mask (1 bit per pixel), turn that into the 4bpp canvas (2 = ink, 1 = outline
; = any of the 8 neighbours inked, 0 = clear) and upload canvas + CLUT.
Render:
  addiu sp, sp, -48
  sw    ra, 44(sp)
  sw    s0, 8(sp)
  sw    s1, 12(sp)
  sw    s2, 16(sp)
  sw    s3, 20(sp)
  sw    s4, 24(sp)
  sw    s5, 28(sp)
  sw    s6, 32(sp)
  sw    s7, 36(sp)
  lw    s0, 8(a0)           ; text
  la    t0, Mask
  la    t1, Mask + MASK_ROWS * MASK_STRIDE
@@clr:
  sw    zero, 0(t0)
  addiu t0, t0, 4
  bne   t0, t1, @@clr
  nop
  move  t0, s0              ; s1 = lines (1 or 2)
  addiu s1, zero, 1
@@cnt:
  lbu   t1, 0(t0)
  addiu t0, t0, 1
  beqz  t1, @@cntdone
  addiu t2, t1, -10
  bnez  t2, @@cnt
  nop
  b     @@cnt
  addiu s1, s1, 1
@@cntdone:
  sltiu t0, s1, 2           ; one line: it goes in the lower half
  sll   t1, t0, 4
  sll   t2, t0, 1
  subu  s2, t1, t2          ; s2 = canvas row of the line's top (0 or 14)
@@line:
  move  t0, s0              ; s3 = width
  move  s3, zero
@@meas:
  lbu   t1, 0(t0)
  addiu t0, t0, 1
  beqz  t1, @@measdone
  addiu t2, t1, -10
  beqz  t2, @@measdone
  addiu t1, t1, -0x20       ; glyph index
  sltiu t2, t1, 0x5F
  bnez  t2, @@mok
  nop
  addiu t1, zero, 0x1F      ; '?'
@@mok:
  la    t3, SubAdv
  addu  t3, t3, t1
  lbu   t4, 0(t3)
  b     @@meas
  addu  s3, s3, t4          ; (t4 used 2 slots after its load: the branch is between)
@@measdone:
  addiu t0, zero, CANVAS_W
  subu  t0, t0, s3
  sra   s4, t0, 1           ; s4 = x of the next glyph
  bgtz  s4, @@draw
  nop
  addiu s4, zero, 1
@@draw:
  lbu   t1, 0(s0)
  nop
  beqz  t1, @@drawn
  addiu t2, t1, -10
  beqz  t2, @@nextline
  addiu s0, s0, 1
  addiu t1, t1, -0x20
  sltiu t2, t1, 0x5F
  bnez  t2, @@gok
  nop
  addiu t1, zero, 0x1F
@@gok:
  la    t3, SubAdv
  addu  t3, t3, t1
  lbu   s5, 0(t3)           ; advance
  sll   t2, t1, 3           ; glyph rows: SubRows + index * 24
  sll   t3, t1, 4
  addu  t2, t2, t3
  la    s6, SubRows
  addu  s6, s6, t2
  addiu t2, s2, 2           ; mask row of glyph row 0 = canvas row s2 + 1, +1 guard row
  sll   t3, t2, 5           ; * 48
  sll   t2, t2, 4
  addu  t2, t2, t3
  la    s7, Mask
  addu  s7, s7, t2
  addiu t9, zero, 12
@@grow:
  lhu   t0, 0(s6)
  move  t1, s4
@@gbit:
  beqz  t0, @@growend
  andi  t2, t0, 1
  beqz  t2, @@gskip
  sltiu t3, t1, 319
  beqz  t3, @@gskip
  srl   t4, t1, 5
  sll   t4, t4, 2
  addu  t4, t4, s7
  lw    t5, 4(t4)           ; +4: the left guard word
  andi  t6, t1, 31
  addiu t7, zero, 1
  sllv  t7, t7, t6
  or    t5, t5, t7
  sw    t5, 4(t4)
@@gskip:
  srl   t0, t0, 1
  b     @@gbit
  addiu t1, t1, 1
@@growend:
  addiu s6, s6, 2
  addiu t9, t9, -1
  bnez  t9, @@grow
  addiu s7, s7, MASK_STRIDE
  b     @@draw
  addu  s4, s4, s5
@@nextline:
  b     @@line
  addiu s2, s2, 14
@@drawn:
  la    s0, Mask            ; mask row above the canvas row
  la    s1, OutL
  la    s2, OutR
  addiu s3, zero, CANVAS_H
  la    s4, DBuf
  la    s5, HBuf
@@orow:
  move  t0, zero            ; D[w] = rows above | this | below
@@dw:
  addu  t1, s0, t0
  lw    t2, 0(t1)
  lw    t3, MASK_STRIDE(t1)
  lw    t4, MASK_STRIDE * 2(t1)
  or    t2, t2, t3
  or    t2, t2, t4
  addu  t5, s4, t0
  sw    t2, 0(t5)
  addiu t0, t0, 4
  sltiu t6, t0, MASK_STRIDE
  bnez  t6, @@dw
  nop
  addiu t0, zero, 4         ; H[w] = D[w] spread one pixel left and right (w = 1..10)
@@hw:
  addu  t1, s4, t0
  lw    t2, 0(t1)
  lw    t3, -4(t1)
  lw    t4, 4(t1)
  sll   t5, t2, 1
  or    t5, t5, t2
  srl   t6, t2, 1
  or    t5, t5, t6
  srl   t6, t3, 31
  or    t5, t5, t6
  sll   t6, t4, 31
  or    t5, t5, t6
  addu  t7, s5, t0
  sw    t5, 0(t7)
  addiu t0, t0, 4
  sltiu t6, t0, MASK_STRIDE - 4
  bnez  t6, @@hw
  nop
  move  s6, zero            ; x, 8 pixels (one output word) at a time
@@px8:
  move  t9, zero
  move  t8, zero            ; nibble shift
@@px:
  srl   t1, t8, 2
  addu  t1, t1, s6          ; pixel x
  srl   t2, t1, 5
  sll   t2, t2, 2
  addiu t2, t2, 4
  addu  t3, s0, t2
  lw    t3, MASK_STRIDE(t3) ; ink row = mask row + 1
  addu  t4, s5, t2
  lw    t4, 0(t4)
  andi  t5, t1, 31
  srlv  t3, t3, t5
  andi  t3, t3, 1
  srlv  t4, t4, t5
  andi  t4, t4, 1
  beqz  t3, @@noink
  move  t6, t4
  addiu t6, zero, 2
@@noink:
  sllv  t6, t6, t8
  or    t9, t9, t6
  addiu t8, t8, 4
  sltiu t7, t8, 32
  bnez  t7, @@px
  nop
  sltiu t0, s6, 256
  beqz  t0, @@right
  srl   t1, s6, 1
  addu  t1, t1, s1
  b     @@stored
  sw    t9, 0(t1)
@@right:
  addiu t1, t1, -128
  addu  t1, t1, s2
  sw    t9, 0(t1)
@@stored:
  addiu s6, s6, 8
  sltiu t0, s6, CANVAS_W
  bnez  t0, @@px8
  nop
  addiu s0, s0, MASK_STRIDE
  addiu s1, s1, 128
  addiu s2, s2, 24
  addiu s3, s3, -1
  bnez  s3, @@orow
  nop
  la    a0, RectL
  la    a1, OutL
  jal   LoadImage
  nop
  la    a0, RectR
  la    a1, OutR
  jal   LoadImage
  nop
  la    a0, RectC
  la    a1, ClutData
  jal   LoadImage
  nop
  lw    ra, 44(sp)
  lw    s0, 8(sp)
  lw    s1, 12(sp)
  lw    s2, 16(sp)
  lw    s3, 20(sp)
  lw    s4, 24(sp)
  lw    s5, 28(sp)
  lw    s6, 32(sp)
  lw    s7, 36(sp)
  jr    ra
  addiu sp, sp, 48
.align 4
CODE_END:

; ---- data (not checksummed: the prims and CurRow change at run time)
CurRow:
  .word 0
PendRow:                    ; SubMain's debounce: candidate row and how many passes in a row FindRow returned it
  .word 0
PendCnt:
  .word 0
PrimTP:                     ; texture page + no texture window, then the two halves of the canvas
  .word (2 << 24) | (PrimL & 0xFFFFFF)
  .word 0xE1000000 | TPAGE
  .word 0xE2000000
PrimL:
  .word (4 << 24) | (PrimR & 0xFFFFFF)
  .word 0x65808080          ; textured sprite, opaque, raw texture
  .word 0                   ; y << 16 | x (SubFlip)
  .word (CLUT_ID << 16) | ((VRAM_Y - 256) << 8)
  .word (CANVAS_H << 16) | 256
PrimR:
  .word (4 << 24) | 0xFFFFFF
  .word 0x65808080
  .word 0
  .word (CLUT_ID << 16) | ((VRAM_Y + CANVAS_H - 256) << 8)
  .word (CANVAS_H << 16) | (CANVAS_W - 256)
RectL:
  .halfword VRAM_X, VRAM_Y, 64, CANVAS_H
RectR:
  .halfword VRAM_X, VRAM_Y + CANVAS_H, (CANVAS_W - 256) / 4, CANVAS_H
RectC:
  .halfword CLUT_X, CLUT_Y, 16, 1
ClutData:                   ; 0 clear, 1 outline (black, STP set so it isn't transparent), 2 ink
  .halfword 0x0000, 0x8000, 0x7FFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

.include SUBDATA
BLOB_END:
.align 0x800                ; the EXE image is whole sectors

; work buffers after the blob (RAM only)
.definelabel Mask, BLOB_END
.definelabel DBuf, Mask + MASK_ROWS * MASK_STRIDE
.definelabel HBuf, DBuf + MASK_STRIDE
.definelabel OutL, HBuf + MASK_STRIDE
.definelabel OutR, OutL + CANVAS_H * 128
.definelabel WORK_END, OutR + CANVAS_H * 24
.if WORK_END > BLOB_LIMIT
  .error "subtitle blob + buffers run into the PAC buffer"
.endif

; t_size in the PS-X EXE header: the original 0x54000 + the blob
.headersize 0
.org 0x1C
  .word 0x54000 + ((BLOB_END - BLOB + 0x7FF) & ~0x7FF)

.close
