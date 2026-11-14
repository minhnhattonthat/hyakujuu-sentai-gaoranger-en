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

## Repack (verified, tests/test_disc.py)
- `pac.parse(d)` -> tree, `pac.build(tree)` -> bytes; every PAC rebuilds byte-identical. Rules: entry table right
  after the 0x20 header, children in slot order, each 4-aligned (offset relative to its add) with zero padding, an
  add's size includes the padding after its last child, lzs/raw entry sizes are exact. Empty slots have offset/size
  0 but some carry a value at +8 (1107 of them): `parse` keeps their raw 16 bytes.
- Change a leaf by replacing its node: `{"kind": "raw", "raw": b".."}`, or set `"payload"` on an lzs node (re-encoded
  on build). `tools/movetest.py` re-encodes every block of every PAC (the moved-file test, disc.md §Rebuild).
- **No block may start earlier than in the original** (verified, phase 5): the English font TIM (DE_ST01 9_7) packed
  0x2e7 bytes smaller, 9_8..9_10 moved up, and the chapter-1 ending's cloud picture (9_10, 8bpp) came out in wrong
  colours; re-encoding 9_7 unchanged (+0xb8, blocks moved later) was fine. Mechanism not traced (decoding near the
  still-packed data, guess). `insert.py` pads every replaced block (lzs: `pad_to`, zeros after the stream) to at
  least its original size and `check_offsets` fails the build if any block starts earlier.

## Leaf kinds (from unpack_all.py)
840 TIM (`10 00 00 00`, flags with bit 31 set: `08 00 00 80`), 613 `41 00 00 00` (models/anim, guess), 119 VAB
(`pBAV`), 11 MIPS code blocks (`0c 80 02 3c` = lui; overlays), string tables (see text.md), many raw tables.
