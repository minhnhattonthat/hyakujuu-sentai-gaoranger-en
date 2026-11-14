# PAC containers (`DATA/*.PAC`)

Tools: `tools/pac.py list|unpack`, `tools/unpack_all.py` (all PACs -> `work/pac/<PAC>/<path>.bin`).

## add archive (verified: every PAC parses, 2491 leaves)
- `+0` "add\0", `+4` u32 4, `+8` u32 0x20 = entry table offset, `+0xC` u32 count, `+0x10` u32 0x10 = entry size.
- Entry i at `+0x20 + 16*i`: u32 offset (relative to this add), u32 size, 8 bytes zero. size 0 = empty slot (slots are
  sparse: e.g. Y_TITLE uses 3, 12, 13, 14, 20-22). Entries are nested adds, lzs blocks or raw data.
- A decompressed lzs payload can itself be an add (83 of them): `unpack_all.py` continues the path with `_z_`.

## lzs block (verified: decoder in EXE, all blocks decode)
- Check routine EXE `0x8002f628`, decode loop `0x8002f700` (found with a read breakpoint on Y_TITLE's first stream,
  `work/tmp/readbp.lua`; Y_TITLE.PAC sits raw at 0x800cd000 at the title).
- `+0` "lzs\0", `+4` u32 0, `+8` u32 1 (must be 1), zero to +0x20.
- `+0x20`: u16 3 (must be 3), u16 hdrlen (0x18), u32 unpacked size, u16 flag bits (8/16/32, always 32 seen),
  u16 length bits L (2..7; 4-6 seen), u32 packed size of the block, 8-byte name ("000000").
- Stream at `+0x20+hdrlen`: flag word little-endian, LSB first, 1 = literal byte; 0 = big-endian u16 w:
  length = (w & (2^L-1)) + 3, distance = w >> L (copy from out[-distance]). Stops when unpacked size is reached.
- Every stream ends inside its block; BC_ST07.PAC `1_12_3` leaves 0x85 bytes of slack before the next entry.
- Compressor: `pac.lzs_encode(data, L, name)` (greedy, hash chains, keeps the block's L and name; packed size field =
  whole block). Roundtrips all 2252 blocks; output is 0.8% bigger than the original overall (worst block +10%).
  Load buffer limits per block still unknown: check when a block grows a lot.
- Decode targets (verified 2026-11-14, English build, every scene in `lzsmap.py --scenes`, 33 runs in
  `work/qa/lzs_all`; command in the `tools/lzsmap.py` docstring): decompress(src, dst) is 0x8002f858; lzslog.lua
  logs src/dst/size and the first 16 stream bytes, which lzsmap matches against the built PACs to name the block.
  Story/menu PAC blocks (D_SYS script slots, ra 0x80017a20/a64/ab8/b14, ending/menu tables ra 0x800ac4c0) are
  decoded back to back from 0x801cd000, each dst = the previous block's end (aligned), so a grown text table moves
  the later blocks up instead of overwriting them. Every grown table is decoded by its scene (lzsmap EXPECT) with 0
  overlaps on its grown tail; decodes over the table's original bytes too are the next scene reusing the heap.
  Per table (dst, end): ds01-07 0x801cde70-88 .. at most 0x801ce048; option 0x801cdf1c..0x801ce0e0; load
  0x801ce19c..0x801ce4ba; save (DE_ST01-05 save prompt, Y_SAVE, Y_EDSAVE) 0x801ce178..0x801ce648 (largest end).
  What sits far above (stack near 0x801fff00) is a guess, ~200 KB away. `insert.TRACED` caps each table at the
  size traced here: a release build that grows one further fails until the trace is re-run.
- The card table (Y_TITLE/21 = CARDMS/0, 1434 -> 2128 bytes) is decoded by no scene: none of the 33 runs (title
  wheel, continue/load with and without a save, options, the オルゲットファイト menu and stage, Y_TITLE loaded as a
  story file: scene `ytitle`) decodes it; no code asks for slot 21 by a constant (`tools/slotcalls.py --index 21`:
  OPN.PRG, which owns Y_TITLE, asks for 1, 3, 12, 13, 14 and loops over slot 12's children only); its first 24
  slots are a `12345678901234567890` ruler, like the debug tables in Y_TITLE/20 and /22. Treated as unused (D11).
  CARDMS has no loader (flow.md). The player's memory-card messages come from the save and load tables.

## Repack (verified, tests/test_disc.py)
- `pac.parse(d)` -> tree, `pac.build(tree)` -> bytes; every PAC rebuilds byte-identical. Rules: entry table right
  after the 0x20 header, children in slot order, each 4-aligned (offset relative to its add) with zero padding, an
  add's size includes the padding after its last child, lzs/raw entry sizes are exact. Empty slots have offset/size
  0 but some carry a value at +8 (1107 of them): `parse` keeps their raw 16 bytes.
- Change a leaf by replacing its node: `{"kind": "raw", "raw": b".."}`, or set `"payload"` on an lzs node (re-encoded
  on build). `tools/movetest.py` re-encodes every block of every PAC (the moved-file test, disc.md §Rebuild).
- **No block may start earlier than in the original** (verified, phase 5): the English font TIM (DE_ST01 9_7) packed
  0x2e7 bytes smaller, 9_8..9_10 moved up, and the chapter-1 ending's cloud picture (9_10, 8bpp) came out in wrong
  colours; re-encoding 9_7 unchanged (+0xb8, blocks moved later) was fine. `insert.py` pads every replaced block
  (lzs: `pad_to`, zeros after the stream) to at least its original size and `check_offsets` fails the build if any
  block starts earlier. **Probably not corruption at all** (phase 8, 2026-11-14): the same "wrong colours" came back
  with every block in place once DE_ST07E 9_3 (THE END) was re-encoded, even with unchanged pixels. VRAM dumps
  (`tools/lua/vdumpat.lua`) at the post-ending save prompt: every texture and CLUT identical to the original; only
  the framebuffers differ. That screen never redraws its background, so it shows one of two leftover buffers (one
  with the rendered sky, one with an 8bpp texture copied raw = orange/green), and which one depends on how many
  frames loading took, i.e. on the packed sizes. The original disc shows the orange buffer itself in de03s-05s.
  Kept the padding rule anyway (cheap). Bisect a build by graphics edit: `GFX_SKIP=sha,.. tools/build.py --out ..`.

## Leaf kinds (from unpack_all.py)
840 TIM (`10 00 00 00`, flags with bit 31 set: `08 00 00 80`), 613 `41 00 00 00` (models/anim, guess), 119 VAB
(`pBAV`), 11 MIPS code blocks (`0c 80 02 3c` = lui; overlays), string tables (see text.md), many raw tables.
